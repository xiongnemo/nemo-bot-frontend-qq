from ..errors import MessageParsingError
import logging
import json
import re
logger = logging.getLogger(__name__)

class MessageSegement:
    '''
    https://whitechi73.github.io/OpenShamrock/message/format.html#消息段

    消息段是一个 JSON 对象，以下是一个消息段的基本格式：
    ```json
    {
        "type": "text", // 消息段类型
        "data": {
            // 消息段数据/参数
            "text": "Hello!"
        }
    }
    ```
    '''
    def __init__(self, raw: dict):
        self.type = raw['type']
        self.data = raw['data']

    def __str__(self) -> str:
        return f'[{self.type}, {self.data}]'

class Message:
    '''
    https://whitechi73.github.io/OpenShamrock/message/format.html#消息

    消息是一个 JSON 数组，以下是一个消息的基本格式：
    ```json
    [
        {
            "type": "text",
            "data": {
                "text": "Hello!"
            }
        },
        {
            "type": "image",
            "data": {
                "file": "https://example.com/image.jpg"
            }
        }
    ]
    ```
    '''
    def __init__(self, raw: list):
        self.raw = raw
        self.segements = []
        for segement in raw:
            self.segements.append(MessageSegement(segement))

    def __str__(self) -> str:
        return str(self.segements)

class OnebotEvent:
    '''
    https://whitechi73.github.io/OpenShamrock/event/general-data.html#所有上报
    '''
    def __init__(self, raw_event_data: dict):
        self.time: int = raw_event_data['time']
        self.post_type: str = raw_event_data['post_type']
        self.self_id: int = raw_event_data['self_id']
        self.__dict__ = raw_event_data

import httpx

def get_message_by_id(message_id: str) -> dict:
    '''
    https://llonebot.apifox.cn/api-147574979
    POST /get_msg
    '''
    try:
        response = httpx.post(f'http://127.0.0.1:5700/get_msg', json={
            "message_id": message_id
        }, timeout=2.0)
        return response.json().get('data', {})
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to fetch message {message_id}: {e}")
        return {}

def get_group_info(group_id: str) -> dict:
    try:
        response = httpx.post(f'http://127.0.0.1:5700/get_group_info', json={
            "group_id": int(group_id)
        }, timeout=2.0)
        return response.json().get('data', {})
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to fetch group info {group_id}: {e}")
def get_group_file_url(group_id: str, file_id: str) -> str:
    '''
    Fetch download URL for a group file via OneBot / LLOneBot HTTP API.
    POST /get_group_file_url
    '''
    try:
        response = httpx.post('http://127.0.0.1:5700/get_group_file_url', json={
            "group_id": int(group_id),
            "file_id": file_id
        }, timeout=5.0)
        data = response.json().get('data', {})
        if data and isinstance(data, dict):
            url = data.get('url', '')
            if url:
                logger.info(f"[OneBot File] Resolved group file URL for {file_id}: {url[:100]}...")
            return url
    except Exception as e:
        logger.warning(f"[OneBot File] Failed to get group file url for {file_id}: {e}")
    return ''

class OnebotMessage:
    '''
    https://whitechi73.github.io/OpenShamrock/event/message.html#消息事件
    '''
    def __init__(self, event: OnebotEvent):
        if event.post_type != 'message':
            raise MessageParsingError('上报类型不是 message')
        self.self_id = event.self_id
        self.user_id: str = str(event.__dict__['user_id'])
        self.group_id: str = str(event.__dict__.get('group_id', ''))
        self.message_id: str = str(event.__dict__['message_id'])
        self.message: str = event.__dict__['message']
        self.raw_message: str = event.__dict__['message']
        sender = event.__dict__.get('sender', {})
        self.user_name: str = str(sender.get('card') or sender.get('nickname', ''))
        self.group_name: str = ""
        if self.group_id:
            ginfo = get_group_info(self.group_id)
            self.group_name = ginfo.get("group_name", "")
        # 获取回复消息
        # [{'type': 'reply', 'data': {'id': '1297990874'}}, {'type': 'text', 'data': {'text': 'g 这上面写了什么'}}]
        reply = [i for i in self.message if i['type'] == 'reply']
        self.reply_to = None
        if reply:
            try:
                reply_id = reply[0]["data"]["id"]
                full_reply_data = get_message_by_id(reply_id)
                if full_reply_data:
                    reply_msg_segments = full_reply_data.get('message', [])
                    reply_text = ' '.join([s['data']['text'] for s in reply_msg_segments if s['type'] == 'text']).strip()
                    reply_imgs = list([s['data']['url'] for s in reply_msg_segments if s['type'] == 'image' and 'url' in s['data']])
                    self.reply_to = {
                        "message_id": str(full_reply_data.get("message_id", reply_id)),
                        "user_id": str(full_reply_data.get("user_id", "")),
                        "user_name": str(full_reply_data.get("sender", {}).get("nickname", "")),
                        "text": reply_text,
                        "imgs": reply_imgs,
                        "timestamp": full_reply_data.get("time", 0)
                    }
            except Exception as e:
                logger.error(f"Failed to fetch reply message: {e}")
        self.imgs = list([i['data']['url'] for i in self.message if i['type'] == 'image'])
        # https://multimedia.nt.qq.com.cn should be http://multimedia.nt.qq.com.cn
        # https://gchat.qpic.cn should be http://gchat.qpic.cn
        self.imgs = [i.replace('https://multimedia.nt.qq.com.cn', 'http://multimedia.nt.qq.com.cn').replace('https://gchat.qpic.cn', 'http://gchat.qpic.cn') for i in self.imgs]
        for seg in self.message:
            if not isinstance(seg, dict):
                continue
            stype = seg.get('type')
            sdata = seg.get('data', {})
            if stype == 'json':
                try:
                    raw_data = sdata.get('data', '')
                    jdata = json.loads(raw_data) if isinstance(raw_data, str) else (raw_data or {})
                    meta = jdata.get('meta', {})
                    for k, v in meta.items():
                        if isinstance(v, dict):
                            preview = (v.get('preview') or v.get('cover') or '').strip()
                            if preview and preview not in self.imgs:
                                self.imgs.append(preview)
                                break
                except Exception:
                    pass
            elif stype == 'xml':
                try:
                    raw_xml = sdata.get('data', '')
                    cover_m = re.search(r'(?:cover|preview)="([^"]+)"', raw_xml)
                    if cover_m:
                        cover_url = cover_m.group(1).strip()
                        if cover_url and cover_url not in self.imgs:
                            self.imgs.append(cover_url)
                except Exception:
                    pass
        self.files = []
        for seg in self.message:
            if isinstance(seg, dict) and seg.get("type") == "file":
                fdata = seg.get("data", {})
                raw_file = str(fdata.get("file") or "").strip()
                file_id = str(fdata.get("file_id") or fdata.get("id") or raw_file or "")

                # Determine file_name (in LLOneBot/OneBot, 'file' often contains the filename like 'paper.pdf')
                file_name = str(fdata.get("file_name") or fdata.get("name") or "").strip()
                if not file_name:
                    if raw_file and not raw_file.startswith(("/", "\\", "file://")):
                        file_name = raw_file
                    elif file_id and not file_id.startswith(("/", "\\", "file://")):
                        file_name = file_id
                    else:
                        file_name = "unknown_file"

                try:
                    file_size = int(fdata.get("file_size") or fdata.get("size") or 0)
                except (ValueError, TypeError):
                    file_size = 0

                url = str(fdata.get("url") or "").strip()
                # If url is missing and this is a group file, query LLOneBot/OneBot API
                if not url and self.group_id and file_id:
                    url = get_group_file_url(self.group_id, file_id)

                path = str(raw_file if raw_file.startswith(("/", "\\", "file://")) else "")

                logger.info(
                    f"[OneBot File] Parsed file segment: name='{file_name}', size={file_size} bytes, id='{file_id}', has_url={'YES' if url else 'NO'}, has_path={'YES' if path else 'NO'}"
                )

                self.files.append({
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "url": url,
                    "path": path,
                })
        self.text = self._text

    def __str__(self) -> str:
        return f'''===
前端：onebot
发出请求的用户 ID：{self.user_id}
群组 ID：{self.group_id}
消息 ID：{self.message_id}
消息段：{self.message}
文字消息：{self.text}
===
'''

    @property
    def _text(self) -> str:
        '''将所有文字消息段、AT、以及卡片/小程序解析拼接成字符串'''
        parts = []
        for segment in self.message:
            if type(segment) is not dict:
                continue
            stype = segment.get('type')
            sdata = segment.get('data', {})
            if stype == 'text':
                parts.append(sdata.get('text', ''))
            elif stype == 'at':
                name = sdata.get('name')
                qq = sdata.get('qq')
                if name:
                    parts.append(f"@{name} ")
                elif str(qq) != "all":
                    parts.append(f"@{qq} ")
                else:
                    parts.append("@全体成员 ")
            elif stype == 'json':
                try:
                    raw_data = sdata.get('data', '')
                    jdata = json.loads(raw_data) if isinstance(raw_data, str) else (raw_data or {})
                    prompt = (jdata.get('prompt') or '').strip()
                    meta = jdata.get('meta', {})
                    title = ""
                    desc = ""
                    url = ""
                    for k, v in meta.items():
                        if isinstance(v, dict):
                            title = (v.get('title') or '').strip()
                            desc = (v.get('desc') or '').strip()
                            url = (v.get('qqdocurl') or v.get('jumpUrl') or v.get('url') or '').strip()
                            if title or url:
                                break
                    card_title = desc or title or prompt or "小程序/卡片分享"
                    if prompt.startswith("[") and "]" in prompt:
                        tag = prompt[:prompt.index("]") + 1]
                    else:
                        tag = "[小程序分享]"
                    body = f"{tag} {card_title}"
                    if url:
                        body += f" 链接: {url}"
                    parts.append(body)
                except Exception as e:
                    logger.debug(f"[OneBot] Error parsing json segment: {e}")
            elif stype == 'xml':
                try:
                    raw_xml = sdata.get('data', '')
                    title_m = re.search(r"<title[^>]*>(.*?)</title>", raw_xml)
                    url_m = re.search(r'url="([^"]+)"', raw_xml)
                    title = title_m.group(1).strip() if title_m else "XML卡片分享"
                    url = url_m.group(1).strip() if url_m else ""
                    body = f"[XML卡片] {title}"
                    if url:
                        body += f" 链接: {url}"
                    parts.append(body)
                except Exception as e:
                    logger.debug(f"[OneBot] Error parsing xml segment: {e}")
        return ''.join(parts).lstrip()
    
    @property
    def call_by_intension(self) -> bool:
        result = False
        if self.group_id:
            
            for segement in self.message:
                if type(segement) is not dict:
                    continue
                if segement['type'] == 'at':
                    if str(segement['data']['qq']) == str(self.self_id):
                        result = True
                        return result
        else:
            return True
            
