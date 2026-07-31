from classes.errors import MessageParsingError
from typing import List

class GoCqhttpEvent:
    '''
    https://docs.go-cqhttp.org/event/#所有上报
    '''
    def __init__(self, raw_event_data: dict):
        self.time: int = raw_event_data.get('time', 0)
        self.post_type: str = raw_event_data.get('post_type', '')
        self.self_id: str = str(raw_event_data.get('self_id', ''))
        self.__dict__.update(raw_event_data)

class GoCqhttpMessage:
    '''
    https://docs.go-cqhttp.org/event/#消息上报
    '''
    def __init__(self, event: GoCqhttpEvent):
        if event.post_type != 'message':
            raise MessageParsingError('上报类型不是 message')
        self.self_id: str = str(event.self_id)
        self.user_id: str = str(event.__dict__.get('user_id', ''))
        self.group_id: str = str(event.__dict__.get('group_id', ''))
        self.message_id: str = str(event.__dict__.get('message_id', ''))
        self.raw_message: str = event.__dict__.get('raw_message', '')
        self.user_name: str = str(event.__dict__.get('sender', {}).get('nickname', ''))
        self.raw_cqcodes: List[str] = []
        self.parsed_cqcodes: List[dict] = []
        self.text = self._text
        self.imgs = [attrs['data']['url'] for attrs in self.parsed_cqcodes if attrs['type'] == 'image' and 'url' in attrs['data']]
        # https://multimedia.nt.qq.com.cn should be http://multimedia.nt.qq.com.cn
        self.imgs = [i.replace('https://multimedia.nt.qq.com.cn', 'http://multimedia.nt.qq.com.cn').replace('https://gchat.qpic.cn', 'http://gchat.qpic.cn') for i in self.imgs]

    def __str__(self) -> str:
        return f'''===
发出请求的用户 ID：{self.user_id}
群组 ID：{self.group_id}
消息 ID：{self.message_id}
原生消息：{self.raw_message}
去 CQ 码消息：{self.text}
CQ 码：{self.raw_cqcodes}
解析过后的 CQ 码：{self.parsed_cqcodes}
===
'''

    @property
    def _text(self) -> str:
        '''处理并干掉所有的 CQ 码'''
        t = self.raw_message
        while t.find('[CQ') != -1:
            start_index = t.index('[CQ')
            end_index = t.index(']', start_index)
            self.raw_cqcodes.append(t[start_index:end_index + 1])
            t = t[:start_index].strip() + t[end_index + 1:].strip()
        self.parse_cq_code()
        return t.strip()

    def parse_cq_code(self):
        '''
        https://docs.go-cqhttp.org/cqcode/#cq-码-cq-code
        '''
        for raw_cqcode in self.raw_cqcodes:
            attrs = {}
            raw_cqcode = raw_cqcode[1:-1]
            cq_attrs = raw_cqcode.split(',')
            if not cq_attrs or ':' not in cq_attrs[0]:
                continue
            attrs['type'] = cq_attrs[0].split(':')[1]
            attrs['data'] = {}
            for cq_attr in cq_attrs[1:]:
                if '=' not in cq_attr:
                    continue
                position = cq_attr.index('=')
                attr = cq_attr[:position]
                value = cq_attr[position + 1:]
                # TODO: HTML 反转义
                attrs['data'][attr] = value
            self.parsed_cqcodes.append(attrs)
