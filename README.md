# nemo-bot-ng-frontend-cqhttp

nemo-bot-ng 的 cqhttp 前端（go-cqhttp 变种）

## 思路

规则匹配：

    * 普通命令：形似 '命令 [参数]'
    * NLP
    * 自定义正则

处理函数都需要返回解析出来的命令和参数。

启动的时候为每个普通命令的别名都注册一个 mapping, 若均未命中则转 NLP

```python
@normal_command(['command_start'])
def 
```

## 开发用例子

```python
{
    'post_type': 'message',
    'message_type': 'private',
    'time': 1667956145,
    'self_id': 1735920271,
    'sub_type': 'friend',
    'sender': {
        'age': 0,
        'nickname': 'ANZUPOP\\Nemo',
        'sex': 'unknown',
        'user_id': 3240295516,
        },
    'message_id': 822559292,
    'user_id': 3240295516,
    'target_id': 1735920271,
    'message': '111',
    'raw_message': '111',
    'font': 0,
}
```

```python
{
    'post_type': 'message',
    'message_type': 'group',
    'time': 1667956201,
    'self_id': 1735920271,
    'sub_type': 'normal',
    'sender': {
        'age': 0,
        'area': '',
        'card': '',
        'level': '',
        'nickname': 'ANZUPOP\\Nemo',
        'role': 'owner',
        'sex': 'unknown',
        'title': '',
        'user_id': 3240295516,
        },
    'message_id': 270434028,
    'font': 0,
    'group_id': 329320673,
    'message_seq': 1151,
    'raw_message': '222',
    'user_id': 3240295516,
    'anonymous': None,
    'message': '222',
}
```

```python
{
    'post_type': 'message',
    'message_type': 'group',
    'time': 1667956539,
    'self_id': 1735920271,
    'sub_type': 'normal',
    'group_id': 527208532,
    'message_seq': 622509,
    'sender': {
        'age': 0,
        'area': '',
        'card': '仓鼠',
        'level': '',
        'nickname': '茄子',
        'role': 'admin',
        'sex': 'unknown',
        'title': '',
        'user_id': 2467613973,
        },
    'message_id': 763557478,
    'anonymous': None,
    'font': 0,
    'message': '[CQ:image,file=890f28256ebc33f7cff68c8809eaca7e.image,subType=0,url=https://gchat.qpic.cn/gchatpic_new/2467613973/527208532-2905521904-890F28256EBC33F7CFF68C8809EACA7E/0?term=3&amp;is_origin=0]',
    'raw_message': '[CQ:image,file=890f28256ebc33f7cff68c8809eaca7e.image,subType=0,url=https://gchat.qpic.cn/gchatpic_new/2467613973/527208532-2905521904-890F28256EBC33F7CFF68C8809EACA7E/0?term=3&amp;is_origin=0]',
    'user_id': 2467613973,
}
```

```python
{
    'post_type': 'message',
    'message_type': 'group',
    'time': 1667956794,
    'self_id': 1735920271,
    'sub_type': 'normal',
    'user_id': 3240295516,
    'anonymous': None,
    'group_id': 329320673,
    'message': '[CQ:reply,id=1729711738][CQ:at,qq=1527445228] [CQ:at,qq=1527445228] 3333',
    'message_seq': 1152,
    'raw_message': '[CQ:reply,id=1729711738][CQ:at,qq=1527445228] [CQ:at,qq=1527445228] 3333',
    'font': 0,
    'sender': {
        'age': 0,
        'area': '',
        'card': '',
        'level': '',
        'nickname': 'ANZUPOP\\Nemo',
        'role': 'owner',
        'sex': 'unknown',
        'title': '',
        'user_id': 3240295516,
        },
    'message_id': -1994969258,
}
```
