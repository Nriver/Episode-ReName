import json
import os
from utils.log_utils import logger


def get_qrm_config(application_path):
    qrm_config = None
    config_ern_path_tmp = os.path.join(application_path, 'config_ern.json')
    config_path_tmp = os.path.join(application_path, 'config.json')
    if os.path.exists(config_ern_path_tmp):
        try:
            logger.debug(f"找到配置文件: {config_ern_path_tmp}")
            with open(config_ern_path_tmp, encoding='utf-8') as f:
                qrm_config_file = json.loads(f.read())['qrm_config_file']
            logger.debug(f"QRM配置文件路径: {qrm_config_file}")
            with open(qrm_config_file, encoding='utf-8') as f:
                qrm_config = json.loads(f.read())
            logger.info(f"成功加载QRM配置文件: {qrm_config_file}")
        except Exception as e:
            logger.error(f"config_ern.json 读取错误: {str(e)}")
    elif os.path.exists(config_path_tmp):
        try:
            logger.debug(f"找到配置文件: {config_path_tmp}")
            with open(config_path_tmp, encoding='utf-8') as f:
                qrm_config = json.loads(f.read())
            logger.info(f"成功加载配置文件: {config_path_tmp}")
        except Exception as e:
            logger.error(f"config.json 读取错误: {str(e)}")

    return qrm_config
