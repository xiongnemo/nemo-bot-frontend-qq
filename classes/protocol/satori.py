from ..errors import MessageParsingError

from bs4 import BeautifulSoup


{
    "id": 7,
    "type": "message-created",
    "platform": "chronocat",
    "self_id": "1735920271",
    "timestamp": 1713802840000,
    "user": {
        "id": "1735920271",
        "name": "nemo",
        "avatar": "http://thirdqq.qlogo.cn/headimg_dl?dst_uin=1735920271&spec=640"
    },
    "channel": {
        "type": 1,
        "id": "private:3240295516",
        "name": ""
    },
    "message": {
        "id": "7360727147171570041",
        "content": "2"
    }
}

{
    "id": 12,
    "type": "message-created",
    "platform": "chronocat",
    "self_id": "1735920271",
    "timestamp": 1713803463000,
    "user": {
        "id": "1735920271",
        "name": "nemo",
        "avatar": "http://thirdqq.qlogo.cn/headimg_dl?dst_uin=1735920271&spec=640"
    },
    "channel": {
        "type": 0,
        "id": "329320673",
        "name": "xdlddw"
    },
    "guild": {
        "id": "329320673",
        "name": "xdlddw",
        "avatar": "https://p.qlogo.cn/gh/329320673/329320673/640"
    },
    "member": {},
    "message": {
        "id": "7434946857234439896",
        "content": "2"
    }
}

{
    "id": 11729,
    "type": "message-created",
    "platform": "chronocat",
    "self_id": "1735920271",
    "timestamp": 1716788293000,
    "user": {
        "id": "3240295516",
        "avatar": "http: //thirdqq.qlogo.cn/headimg_dl?dst_uin=3240295516&spec=640"
    },
    "channel": {
        "type": 0,
        "id": "485541033",
        "name": "排挤渣男"
    },
    "guild": {
        "id": "485541033",
        "name": "排挤渣男",
        "avatar": "https://p.qlogo.cn/gh/485541033/485541033/640"
    },
    "member": {
        "nick": "Python 3.12.2 [MSC v.1937 64 bit (AMD64)] on win32"
    },
    "message": {
        "id": "7373549573177957029",
        "content": "<img src=\"http://127.0.0.1:5500/v1/assets/eyJtc2dJZCI6IjczNzM1NDk1NzMxNzc5NTcwMjkiLCJjaGF0VHlwZSI6MiwicGVlclVpZCI6IjQ4NTU0MTAzMyIsImVsZW1lbnRJZCI6IjczNzM1NDk1NzMxNzc5NTcwMjciLCJ0aHVtYlNpemUiOjB9\"/>111"
    }
}

class SatoriEvent:
    '''
    https://satori.js.org/zh-CN/protocol/events.html
    '''
    def __init__(self, raw_event_data: dict):
        self.timestamp: int = raw_event_data['timestamp']
        self.type: str = raw_event_data['type']
        self.self_id: int = raw_event_data['self_id']
        self.__dict__ = raw_event_data

class SatoriMessage:
    '''
    https://satori.js.org/zh-CN/resources/message.html
    '''
    def __init__(self, event: SatoriEvent):
        if not event.type.startswith('message'):
            raise MessageParsingError('上报类型不是 message')
        self.self_id = event.self_id
        self.user_id: int = event.__dict__['user']['id']
        self.group_id: int = '' if 'private' in event.__dict__['channel']['id'] else event.__dict__['channel']['id']
        self.message_id: int = event.__dict__['message']['id']
        self.message: str = event.__dict__['message']['content']
        self.raw_message: str = event.__dict__['message']
        self.user_name: str = event.__dict__.get('member', {}).get('nick') or event.__dict__['user'].get('name', '')
        # message is html, we need all the segments
        soup = BeautifulSoup(self.message, 'html.parser')
        self.imgs = list([i['src'] for i in soup.find_all('img')])
        
        quote = soup.find('quote')
        self.reply_to = None
        if quote:
            self.reply_to = {
                "message_id": quote.get("id", ""),
                "user_id": "",
                "user_name": "",
                "text": quote.text,
                "timestamp": 0
            }
            self.text = soup.text.removeprefix(quote.text).strip()
        else:
            self.text = soup.text

    def __str__(self) -> str:
        return f'''===
前端：satori
发出请求的用户 ID：{self.user_id}
群组 ID：{self.group_id}
消息 ID：{self.message_id}
消息段：{self.message}
文字消息：{self.text}
===
'''

    @property
    def call_by_intension(self) -> bool:
        result = False
        if self.group_id:
            # print(self.message)
            for segement in self.message:
                if segement['type'] == 'at':
                    if str(segement['data']['qq']) == str(self.self_id):
                        result = True
                        return result
        else:
            return True
            
