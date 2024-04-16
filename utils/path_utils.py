import os
import platform

from loguru import logger

# 当前系统类型
system = platform.system()


def format_path(file_path):
    # 修正路径斜杠

    # samba路径特殊处理
    if file_path.startswith('//'):
        return '\\' + file_path.replace('//', '/').replace('/', '\\')
    else:
        if system == 'Windows':
            return file_path.replace('//', '/').replace('/', '\\')
        return file_path.replace('\\', '/').replace('//', '/')


def get_absolute_path(file_path):
    # 获取绝对路径
    if file_path.startswith(r'\\'):
        # samba 路径特殊处理
        return file_path.replace('\\', '/')
    else:
        return os.path.abspath(file_path.replace('\\', '/'))


def delete_empty_dirs(root_dir):
    # 删除空的子目录
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            if not os.listdir(dir_full_path):
                logger.info(f'删除空目录: {dir_full_path}')
                os.rmdir(dir_full_path)
