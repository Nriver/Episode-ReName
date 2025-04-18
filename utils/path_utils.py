import os
import platform
import re

from utils.ext_utils import get_file_name_ext
from utils.log_utils import logger
from utils.season_utils import get_season_cascaded

# 当前系统类型
system = platform.system()


def format_path(file_path):
    """
    修正路径斜杠
    :param file_path:
    :return:
    """

    # samba路径特殊处理
    if file_path.startswith('//'):
        return '\\' + file_path.replace('//', '/').replace('/', '\\')
    else:
        if system == 'Windows':
            return file_path.replace('//', '/').replace('/', '\\')
        return file_path.replace('\\', '/').replace('//', '/')


def get_absolute_path(file_path):
    """
    获取绝对路径
    :param file_path:
    :return:
    """
    if file_path.startswith(r'\\'):
        # samba 路径特殊处理
        return file_path.replace('\\', '/')
    else:
        return os.path.abspath(file_path.replace('\\', '/'))


def delete_empty_dirs(root_dir):
    """
    删除空的子目录
    :param root_dir:
    :return:
    """
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            if not os.listdir(dir_full_path):
                logger.info(f'删除空目录: {dir_full_path}')
                os.rmdir(dir_full_path)


def check_and_delete_redundant_file(file_path):
    """
    删除多余文件 不在 Season 目录下不处理

    :param file_path:
    :return: 返回值表示文件是否已经删除
    """
    # 父级文件夹
    parent_folder_path = os.path.dirname(file_path)
    file_full_name = os.path.basename(file_path)

    _ = get_season_cascaded(parent_folder_path)
    if not _:
        # logger.info(f"{'不在season文件夹内 忽略'}")
        return False

    # 忽略部分文件
    if file_full_name.lower() in ['clearlogo.png', 'season.nfo', 'all.txt']:
        return False
    file_name, ext = get_file_name_ext(file_full_name)

    # 只处理特定后缀
    if not ext.lower() in ['jpg', 'png', 'nfo', 'torrent']:
        return False

    res = re.findall(r'^S(\d{1,4})E(\d{1,4}(\.5)?)', file_name.upper())
    if res:
        return False
    else:
        logger.info(f'{file_path}')
        os.remove(file_path)
        return True
