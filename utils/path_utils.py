import os
import platform

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
