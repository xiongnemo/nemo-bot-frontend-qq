import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor
import os
import json
from classes import *
from rules import dispatch
import json

frontend_config = {}

from flask import Flask, jsonify, request

app = Flask(__name__)

if os.environ.get('WERKZEUG_RUN_MAIN'):

    with open("config.json", encoding='utf-8') as config_file:
        frontend_config = json.load(config_file)
        # create if not exist: alias
        if 'alias' not in frontend_config:
            frontend_config['alias'] = {}
        # make alias a DictProxy, as we will be updating it in Pool
        # this is not a ProcessPool, so we don't need to use Manager.dict()
        # frontend_config['alias'] = DictProxy(frontend_config['alias'])

    from multiprocessing.managers import DictProxy
    def save_on_exit(outer_config: dict) -> None:
        logger.info('User requested shutdown...')
        logger.info('Saving the final config before exiting.')
        # logger.info(f'{outer_config}')
        # logger.info(f'{inner_config}')
        # outer_config['alias'] = {k: v._getvalue() if type(v) is DictProxy else v for k, v in inner_config.items()}
        with open("config.json", "w", encoding='utf-8') as config_file:
            json.dump(outer_config, config_file, indent=4, ensure_ascii=False)
        logger.info('config saved on disk')
        logger.info('nemo-bot-frontend-qq is now ready to exit, bye bye...')

    import atexit
    logger.info('Now registering atexit handler...')
    atexit.register(save_on_exit, frontend_config)

    pool = ThreadPoolExecutor(max_workers=10)

    def message_dispatch(message: SatoriMessage, frontend) -> tuple[bool, str]:
        try:
            exe = dispatch
        except Exception as e:
            return False, str(e)
        pool.submit(exe, message, frontend, frontend_config)
        return True, ""

    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify(status_code=404, error=str(e), msg="Route or resource not found."), 404


    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(status_code=500, error=str(e), msg="Other exception occured."), 500

    @app.route('/nemo-bot-frontend-satori-http', methods=['POST'])
    def bot_satori():
        satori_event = json.loads(request.data.decode())
        # logger.info(satori_event)
        satori_message = SatoriMessage(SatoriEvent(satori_event))
        if satori_message.self_id == satori_message.user_id:
            return jsonify(status_code=200, error="", msg="Self"), 200
        satori_message = SatoriMessage(SatoriEvent(satori_event))
        ok, reason = message_dispatch(satori_message, 'satori_http')
        if ok:
            return jsonify(status_code=200, error="", msg="Bot acknowledged."), 200
        else:
            return jsonify(status_code=500, error=reason, msg="Exception in dispatching."), 500
        
    @app.route('/nemo-bot-frontend-onebot-http', methods=['POST'])
    def bot_onebot():
        onebot_event = request.get_json()
        # logger.info(onebot_event)
        if onebot_event['post_type'] == 'notice':
            if onebot_event.get('sub_type', '') == 'poke':
                if onebot_event['self_id'] == onebot_event['target_id']:
                    onebot_event['post_type'] = 'message'
                    onebot_event['message'] = [{'type': 'text', 'data': {'text': '[CQ:poke,id=' + str(onebot_event['user_id']) + ']'}}]
                    onebot_event['message_id'] = -1
            elif 'recall' in onebot_event['notice_type']:
                # 撤回
                onebot_event['post_type'] = 'message'
                onebot_event['message'] = [{'type': 'text', 'data': {'text': '[CQ:recall,id=' + str(onebot_event['user_id']) + ']'}}]
                onebot_event['message_id'] = -1
        if onebot_event['post_type'] == 'message':
            onebot_message = OnebotMessage(OnebotEvent(onebot_event))
            ok, reason = message_dispatch(onebot_message, 'onebot')
            if ok:
                return jsonify(status_code=200, error="", msg="Bot acknowledged."), 200
            else:
                return jsonify(status_code=500, error=reason, msg="Exception in dispatching."), 500
        else:
            return jsonify(status_code=200, error="", msg="Bot acknowledged."), 200
