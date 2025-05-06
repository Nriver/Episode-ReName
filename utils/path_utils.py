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
    删除空的子目录，如果根目录也为空则一并删除
    :param root_dir: 根目录路径
    :return: 删除的空目录数量
    """
    deleted_count = 0
    logger.debug(f"开始检查并删除空目录，根目录: {root_dir}")

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            if not os.listdir(dir_full_path):
                try:
                    logger.info(f'删除空目录: {dir_full_path}')
                    os.rmdir(dir_full_path)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"删除空目录失败: {dir_full_path}, 错误: {str(e)}")

    # 检查根目录是否为空，如果为空则删除
    if os.path.isdir(root_dir) and not os.listdir(root_dir):
        try:
            logger.info(f'删除空的根目录: {root_dir}')
            os.rmdir(root_dir)
            deleted_count += 1
        except Exception as e:
            logger.error(f"删除空的根目录失败: {root_dir}, 错误: {str(e)}")

    if deleted_count > 0:
        logger.info(f"共删除 {deleted_count} 个空目录")
    else:
        logger.debug("未发现空目录")

    return deleted_count


def check_and_delete_redundant_file(file_path):
    """
    删除多余文件 不在 Season 目录下不处理

    :param file_path: 文件路径
    :return: 返回值表示文件是否已经删除
    """
    # 父级文件夹
    parent_folder_path = os.path.dirname(file_path)
    file_full_name = os.path.basename(file_path)

    logger.debug(f"检查文件是否需要删除: {file_path}")

    # 检查是否在season文件夹内
    season_num = get_season_cascaded(parent_folder_path)
    if not season_num:
        logger.debug(f"文件不在season文件夹内，忽略: {file_path}")
        return False

    # 忽略部分文件
    if file_full_name.lower() in ['clearlogo.png', 'season.nfo', 'all.txt']:
        logger.debug(f"文件在白名单中，忽略: {file_full_name}")
        return False

    file_name, ext = get_file_name_ext(file_full_name)

    # 只处理特定后缀
    if not ext.lower() in ['jpg', 'png', 'nfo', 'torrent']:
        logger.debug(f"文件后缀不在处理范围内，忽略: {ext}")
        return False

    # 检查文件名是否符合标准格式
    res = re.findall(r'^S(\d{1,4})E(\d{1,4}(\.5)?)', file_name.upper())
    if res:
        logger.debug(f"文件名符合标准格式，保留: {file_full_name}")
        return False
    else:
        logger.warning(f"删除多余文件: {file_path}")
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, 错误: {str(e)}")
            return False
