import traceback
import logging
import requests

logger = logging.getLogger(__name__)

FRONTEND = ""

def dispatch(message, frontend: str, config: dict) -> None:
    global FRONTEND
    FRONTEND = frontend
    try:
        logger.info(message)
        
        payload = {
            "frontend": frontend,
            "context": {
                "group_id": str(message.group_id),
                "user_id": str(message.user_id),
                "user_name": getattr(message, "user_name", ""),
                "message_id": str(message.message_id),
                "self_id": str(message.self_id),
                "ated": getattr(message, "call_by_intension", False),
                "frontend_system_info": f"nemo-bot-frontend-qq ({frontend}) by nemo, 0.2.0\n由 Python {__import__('platform').python_version()} 所执行, \n运行在节点 {__import__('platform').node()}, \n由 {__import__('platform').platform()} 所承载。"
            },
            "request": {
                "command": "",
                "args": message.text,
                "imgs": message.imgs,
                "raw_message": message.raw_message
            }
        }
        
        reply_to = getattr(message, "reply_to", None)
        if reply_to:
            payload["request"]["reply_to"] = reply_to
            
        requests.post('http://127.0.0.1:42164/ingest', json=payload)
    except:
        traceback.print_exc()
