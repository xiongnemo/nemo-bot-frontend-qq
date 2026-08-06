import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import sys
import yaml
import argparse
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from classes import *
from classes.protocol.onebot import OnebotEvent, OnebotMessage
from classes.protocol.satori import SatoriEvent, SatoriMessage
from classes.protocol.cqhttp import GoCqhttpEvent, GoCqhttpMessage

app = FastAPI()

# Load config
try:
    with open("config.yml", encoding='utf-8') as f:
        frontend_config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("config.yml not found. Please create one.")
    sys.exit(1)

BACKEND_URL = frontend_config.get("backend", {}).get("url", "http://127.0.0.1:42164/ingest")

async def dispatch_to_backend(message, frontend: str):
    payload = {
        "frontend": frontend,
        "context": {
            "group_id": str(getattr(message, "group_id", "")),
            "group_name": str(getattr(message, "group_name", "")),
            "user_id": str(getattr(message, "user_id", "")),
            "user_name": str(getattr(message, "user_name", getattr(message, "nickname", ""))),
            "message_id": str(getattr(message, "message_id", "")),
            "self_id": str(getattr(message, "self_id", "")),
            "ated": getattr(message, "call_by_intension", getattr(message, "ated", False)),
            "frontend_system_info": f"nemo-bot-frontend-qq ({frontend}) by nemo, 0.2.0\n由 Python {__import__('platform').python_version()} 所执行, \n运行在节点 {__import__('platform').node()}, \n由 {__import__('platform').platform()} 所承载。"
        },
        "request": {
            "command": "",
            "args": getattr(message, "text", ""),
            "imgs": getattr(message, "imgs", []),
            "raw_message": getattr(message, "raw_message", "")
        }
    }
    
    reply_to = getattr(message, "reply_to", None)
    if reply_to:
        payload["request"]["reply_to"] = reply_to

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BACKEND_URL, json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info(f"[{frontend}] Dispatched message {payload['context']['message_id']} to backend.")
    except Exception as e:
        logger.error(f"[{frontend}] Failed to dispatch message to backend: {e}")
        raise HTTPException(status_code=500, detail="Backend dispatch failed")

@app.post('/nemo-bot-frontend-satori-http')
async def bot_satori(request: Request):
    satori_event_data = await request.json()
    satori_event = SatoriEvent(satori_event_data)
    
    if satori_event.post_type == 'notice' and satori_event.sub_type == 'poke':
        if satori_event.self_id == satori_event.target_id:
            satori_event.post_type = 'message'
            satori_event.message = [{'type': 'text', 'data': {'text': '[CQ:poke,id=' + str(satori_event.user_id) + ']'}}]
            satori_event.message_id = "-1"
            
    if satori_event.post_type == 'message':
        try:
            satori_message = SatoriMessage(satori_event)
        except Exception as e:
            logger.warning(f"Failed to parse Satori message: {e}")
            return JSONResponse(status_code=400, content={"error": str(e)})
            
        if satori_message.self_id == satori_message.user_id:
            return JSONResponse(status_code=200, content={"msg": "Self"})
            
        await dispatch_to_backend(satori_message, 'satori_http')
        return JSONResponse(status_code=200, content={"msg": "Bot acknowledged."})
        
    return JSONResponse(status_code=200, content={"msg": "Event ignored."})

@app.post('/nemo-bot-frontend-onebot-http')
async def bot_onebot(request: Request):
    onebot_event_data = await request.json()
    
    post_type = onebot_event_data.get('post_type')
    
    if post_type == 'notice':
        if onebot_event_data.get('sub_type', '') == 'poke':
            if onebot_event_data.get('self_id') == onebot_event_data.get('target_id'):
                onebot_event_data['post_type'] = 'message'
                onebot_event_data['message'] = [{'type': 'text', 'data': {'text': '[CQ:poke,id=' + str(onebot_event_data['user_id']) + ']'}}]
                onebot_event_data['message_id'] = -1
        elif 'recall' in onebot_event_data.get('notice_type', ''):
            onebot_event_data['post_type'] = 'message'
            onebot_event_data['message'] = [{'type': 'text', 'data': {'text': '[CQ:recall,id=' + str(onebot_event_data['user_id']) + ']'}}]
            onebot_event_data['message_id'] = -1
            
    if onebot_event_data.get('post_type') == 'message':
        try:
            onebot_message = OnebotMessage(OnebotEvent(onebot_event_data))
        except Exception as e:
            logger.warning(f"Failed to parse OneBot message: {e}")
            return JSONResponse(status_code=400, content={"error": str(e)})
            
        if onebot_message.self_id == onebot_message.user_id:
            return JSONResponse(status_code=200, content={"msg": "Self"})
            
        await dispatch_to_backend(onebot_message, 'onebot')
        return JSONResponse(status_code=200, content={"msg": "Bot acknowledged."})
        
    return JSONResponse(status_code=200, content={"msg": "Event ignored."})

@app.post('/nemo-bot-frontend-cqhttp')
async def bot_cqhttp(request: Request):
    cqhttp_event_data = await request.json()
    
    if cqhttp_event_data.get('post_type') == 'message':
        try:
            cqhttp_message = GoCqhttpMessage(GoCqhttpEvent(cqhttp_event_data))
        except Exception as e:
            logger.warning(f"Failed to parse CQHTTP message: {e}")
            return JSONResponse(status_code=400, content={"error": str(e)})
            
        if cqhttp_message.self_id == cqhttp_message.user_id:
            return JSONResponse(status_code=200, content={"msg": "Self"})
            
        await dispatch_to_backend(cqhttp_message, 'cqhttp')
        return JSONResponse(status_code=200, content={"msg": "Bot acknowledged."})
        
    return JSONResponse(status_code=200, content={"msg": "Event ignored."})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help="Check syntax and config, then exit.")
    args = parser.parse_args()
    
    if args.check:
        logger.info("Syntax check passed.")
        sys.exit(0)
        
    import uvicorn
    host = frontend_config.get("frontend", {}).get("host", "0.0.0.0")
    port = frontend_config.get("frontend", {}).get("port", 27468)
    uvicorn.run("app:app", host=host, port=port)
