import json
import os
from loguru import logger


def get_qrm_config(application_path):
    qrm_config = None
    config_ern_path_tmp = os.path.join(application_path, 'config_ern.json')
    config_path_tmp = os.path.join(application_path, 'config.json')
    if os.path.exists(config_ern_path_tmp):
        try:
            with open(config_ern_path_tmp, encoding='utf-8') as f:
                qrm_config_file = json.loads(f.read())['qrm_config_file']
            with open(qrm_config_file, encoding='utf-8') as f:
                qrm_config = json.loads(f.read())
        except Exception as e:
            logger.info(f"{'config_ern.json 读取错误', e}")
    elif os.path.exists(config_path_tmp):
        try:
            with open(config_path_tmp, encoding='utf-8') as f:
                qrm_config = json.loads(f.read())
        except Exception as e:
            logger.info(f'{e}')

    return qrm_config
