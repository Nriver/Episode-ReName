import os
import re
import sys
import platform
import subprocess
import time
from itertools import product
import json

# print('''
#     -- 警告 --
#     如果用这个程序导致文件乱了后果自负哈哈哈哈哈哈哈
#
#     -- 运行环境 --
#     需要python3环境 不推荐使用群晖的python3.5套件环境,可能出现部分字符不兼容

#     -- 使用方法 --
#     1.命令行运行
#     python3 rename.py "/path/to/folder"
#     2.直接运行
#     修改 target_path的路径
#     python3 rename.py

#     -- 程序原理 --

#     优先解析括号
#     [] 【】()内的1-4位纯数字优先
#     部分特殊处理

#     括号没有
#     取剩余部分结尾的数字
#     部分特殊处理

#     应该能解析出大部分的命名规则了
# ''')

scirpt_path = os.path.dirname(os.path.realpath(__file__))
target_path = ''

if len(sys.argv) > 1:
    # 读取命令行目标路径
    target_path = sys.argv[1]
    print('target_path', target_path)

rename_delay = 0
if len(sys.argv) > 2:
    # 重命名延迟(秒) 配合qb使用的参数, 默认为0秒
    rename_delay = int(sys.argv[2])
    print('rename_delay', rename_delay)

if not target_path:
    # 没有路径参数直接退出
    sys.exit()
    # 1 / 0
    # 直接运行的目标路径
    target_path = r'E:\test\极端试验样本'

target_path = target_path.replace('\\', '/').replace('//', '/')

# 需要重命名的文件后缀
COMMON_MEDIA_EXTS = [
    'flv',
    'mkv',
    'mp4',
    'avi',
    'rmvb',
    'm2ts',
    'wmv',
]

# 字幕文件
COMMON_CAPTION_EXTS = [
    'srt',
    'ass',
    'ssa',
    'sub',
    'smi',
]

# 语言文件
COMMON_LANG = [
    'cn',
    'chs',
    'cht',
    'zh',
    'sc',
    'tc',
    'jp',
    'jpn',
    'en',
    'eng',
]

# 混合后缀
COMPOUND_EXTS = COMMON_MEDIA_EXTS + ['.'.join(x) for x in
                                     list(product(COMMON_LANG, COMMON_CAPTION_EXTS))] + COMMON_CAPTION_EXTS


def get_file_name_ext(file_full_name):
    # 获取文件名和后缀
    file_name = None
    ext = None

    for x in COMPOUND_EXTS:
        if file_full_name.lower().endswith(x):
            ext = x
            file_name = file_full_name[:-(len(x) + 1)]
            break
    if not ext:
        file_name, ext = file_full_name.rsplit('.', 1)

    return file_name, ext


# 输出结果列表
file_lists = []
unknown = []

# 当前系统类型
system = platform.system()


def zero_fix(s):
    # 统一补0
    if not s:
        return s
    # 删0
    s = s.lstrip('0')
    # 补0
    s = s.zfill(2)
    if '.' in s and s.index('.') == 1:
        s = '0' + s
    return s


def get_season(parent_folder_name):
    # 获取季数

    # 兼容
    # 'Season 2'
    # 'Season2'
    # 's2'
    # 'S2'
    season = None

    if parent_folder_name == 'Specials':
        # 兼容SP
        return '0'

    try:
        if 'season ' in parent_folder_name.lower():
            s = str(int(parent_folder_name.lower().replace('season ', '').strip()))
            season = s.zfill(2)
        elif parent_folder_name.lower()[0] == 's':
            season = str(int(parent_folder_name[1:])).strip().zfill(2)
    except:
        pass

    return season


def format_path(file_path):
    # 修正路径斜杠
    if system == 'Windows':
        return file_path.replace('//', '/').replace('/', '\\')
    return file_path.replace('\\', '/').replace('//', '/')


def get_season_cascaded(full_path):
    # 逐级向上解析目录季数
    full_path = os.path.abspath(full_path).replace('\\', '/').replace('//', '/')
    parent_folder_names = full_path.split('/')[::-1]
    season = None
    for parent_folder_name in parent_folder_names:
        season = get_season(parent_folder_name)
        if season:
            break
    return season


def get_season_and_ep(file_path):
    print('解析文件', file_path)
    season = None
    ep = None

    file_full_name = os.path.basename(file_path)

    # 父级文件夹
    parent_folder_path = os.path.dirname(file_path)

    # 获取文件名和后缀
    file_name, ext = get_file_name_ext(file_full_name)

    _ = get_season_cascaded(parent_folder_path)
    if not _:
        # print('不在season文件夹内 忽略')
        return None, None

    # 忽略已按规则命名的文件
    pat = 'S\d{1,4}E\d{1,4}(\.5)?'
    if re.match(pat, file_name):
        print('忽略')
        return None, None

    # 如果文件已经有 S01EP01 或者 S01E01 直接读取
    pat = '[Ss](\d{1,4})[Ee](\d{1,4}(\.5)?)'
    res = re.findall(pat, file_name.upper())
    if res:
        season, ep = res[0][0], res[0][1]
        season = str(int(season)).zfill(2)
        ep = str(int(ep)).zfill(2)
        return season, ep
    pat = '[Ss](\d{1,4})[Ee][Pp](\d{1,4}(\.5)?)'
    res = re.findall(pat, file_name.upper())
    if res:
        season, ep = res[0][0], res[0][1]
        season = str(int(season)).zfill(2)
        ep = str(int(ep)).zfill(2)
        return season, ep

    season = get_season_cascaded(parent_folder_path)

    # 获取不到季数 退出
    if not season:
        return None, None

    # 根据文件名获取集数

    # 常见的括号
    bracket_pairs = [
        ['\[', '\]'],
        ['\(', '\)'],
        ['【', '】'],
        # 日语括号
        ['「', '」'],
    ]
    # 内容
    patterns = [
        # 1到4位数字
        '(\d{1,4}(\.5)?)',
        # 特殊文字处理
        '第(\d{1,4}(\.5)?)集',
        '第(\d{1,4}(\.5)?)话',
        '第(\d{1,4}(\.5)?)話',
        '[Ee][Pp](\d{1,4}(\.5)?)',
        '[Ee](\d{1,4}(\.5)?)',
        # 兼容SP01等命名
        '[Ss][Pp](\d{1,4}(\.5)?)',
    ]
    # 括号和内容组合起来
    pats = []
    for pattern in patterns:
        for bracket_pair in bracket_pairs:
            pats.append(bracket_pair[0] + pattern + bracket_pair[1])
    # 查找
    for pat in pats:
        res = re.search(pat, file_name)
        if res:
            ep = res.group(1)
            break

    if not ep:
        print('括号内未识别, 开始寻找括号外内容')
        # 把括号当分隔符排除掉括号内的文字
        pat = ''
        for bracket_pair in bracket_pairs:
            pat += bracket_pair[0] + '.*?' + bracket_pair[1] + '|'
        pat = pat[:-1]
        # 兼容某些用 - 分隔的文件
        pat += '|\-'
        res = re.split(pat, file_name)
        # 过滤空字符串
        res = list(filter(None, res))
        # 从后向前查找数字, 一般集数在剧集名称后面, 防止剧集有数字导致解析出问题
        res = res[::-1]

        # print(res)

        def extract_ending_ep(s):
            # 找到末尾是数字的子字符串
            s = s.strip()
            # print(s)
            ep = None

            # 兼容v2和.5格式 不兼容 9.33 格式
            # 12.5
            # 13.5
            # 10v2
            # 10.5v2
            pat = '(\d{1,4}(\.5)?)[Vv]?\d?'
            ep = None
            res_sub = re.search(pat, s)
            if res_sub:
                print(res_sub)
                ep = res_sub.group(1)
                return ep

            pat = '\d{1,4}(\.5)?$'
            res_sub = re.search(pat, s)
            if res_sub:
                print(res_sub)
                ep = res_sub.group(0)
                return ep
            return ep

        for s in res:
            ep = extract_ending_ep(s)
            if ep:
                break

    if not ep:
        # 部分资源命名
        # 找 第x集
        pat = '第(\d{1,4}(\.5)?)[集话話]'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y)
            if res_sub:
                ep = res_sub.group(1)
                break
    if not ep:
        # 找 EPXX
        pat = '[Ee][Pp](\d{1,4}(\.5)?)'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y.upper())
            if res_sub:
                ep = res_sub.group(1)
                break

    season = zero_fix(season)
    ep = zero_fix(ep)

    return season, ep


def get_season_path(file_path):
    # 获取season目录
    b = os.path.dirname(file_path.replace('\\', '/'))
    season_path = None
    while (b):
        if not '/' in b:
            break
        b, fo = b.rsplit('/', 1)
        offset = None
        if get_season(fo):
            season_path = b + '/' + fo
    return season_path


def ep_offset_patch(file_path, ep):
    # 多季集数修正
    b = os.path.dirname(file_path.replace('\\', '/'))
    while (b):
        if not '/' in b:
            break
        b, fo = b.rsplit('/', 1)
        offset = None
        if get_season(fo):
            try:
                for fn in os.listdir(b + '/' + fo):
                    if fn.lower() != 'all.txt':
                        continue
                    with open(b + '/' + fo + '/' + fn, encoding='utf-8') as f:
                        offset = int(f.read().strip())
                        break
            except Exception as e:
                print('集数修正报错了', e)
                return ep
    # 没有找到all.txt 尝试寻找qb-rss-manager的配置文件
    # 1. config_ern.json 配置
    # 2. 这两个exe在同一个目录下, 直接读取配置
    if not offset:
        qrm_config = None
        if os.path.exists('config_ern.json'):
            try:
                with open('config_ern.json', encoding='utf-8') as f:
                    qrm_config_file = json.loads(f.read())['qrm_config_file']
                with open(qrm_config_file, encoding='utf-8') as f:
                    qrm_config = json.loads(f.read())
            except Exception as e:
                print('config_ern.json 读取错误', e)
        elif os.path.exists('config.json'):
            try:
                with open('config.json', encoding='utf-8') as f:
                    qrm_config = json.loads(f.read())
            except Exception as e:
                print(e)
        if qrm_config:
            print('qrm_config', qrm_config)
            print('file_path', file_path)
            season_path = get_season_path(file_path)
            print('season_path', season_path)
            for x in qrm_config['data_list']:
                if format_path(x[5]) == format_path(season_path):
                    if x[4]:
                        try:
                            offset = int(x[4])
                            print('QRM获取到offset', offset)
                        except:
                            pass

    if offset:
        if '.' in ep:
            ep_int, ep_tail = ep.split('.')
            ep_int = int(ep_int)
            if int(ep_int) >= offset:
                ep_int = ep_int - offset
                ep = str(ep_int) + '.' + ep_tail
        else:
            ep_int = int(ep)
            if ep_int >= offset:
                ep = str(ep_int - offset)

    return zero_fix(ep)


if os.path.isdir(target_path):
    print('文件夹处理')
    # 删除多余文件
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name).replace('\\', '/')
            file_path = os.path.abspath(file_path)
            # 不在 Season 目录下不处理
            # 父级文件夹
            parent_folder_path = os.path.dirname(file_path)

            _ = get_season_cascaded(parent_folder_path)
            if not _:
                # print('不在season文件夹内 忽略')
                continue

            # 忽略部分文件
            if name.lower() in ['season.nfo', 'all.txt']:
                continue
            file_name, ext = get_file_name_ext(name)

            # 只处理特定后缀
            if not ext.lower() in ['jpg', 'png', 'nfo', 'torrent']:
                continue

            res = re.findall('^S(\d{1,4})E(\d{1,4}(\.5)?)', file_name.upper())
            if res:
                continue
            else:
                print(file_path)
                os.remove(file_path)

    # 遍历文件夹
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:

            # 只处理媒体文件
            file_name, ext = get_file_name_ext(name)
            if not ext.lower() in COMPOUND_EXTS:
                continue

            # 完整文件路径
            file_path = os.path.join(root, name).replace('\\', '/')
            file_path = os.path.abspath(file_path)
            parent_folder_path = os.path.dirname(file_path)
            season, ep = get_season_and_ep(file_path)
            print(season, ep)
            # 重命名
            if season and ep:
                # 修正集数
                ep = ep_offset_patch(file_path, ep)
                new_name = 'S' + season + 'E' + ep + '.' + ext
                print(new_name)
                new_path = parent_folder_path + '/' + new_name
                file_lists.append([format_path(file_path), format_path(new_path)])
            else:
                print('未能识别')
                unknown.append(file_path)

else:
    print('单文件处理')
    print(target_path)
    file_path = os.path.abspath(target_path.replace('\\', '/'))
    file_name, ext = get_file_name_ext(target_path)
    parent_folder_path = os.path.dirname(file_path)
    if ext.lower() in COMPOUND_EXTS:
        season, ep = get_season_and_ep(file_path)
        if season and ep:
            # 修正集数
            ep = ep_offset_patch(file_path, ep)
            new_name = 'S' + season + 'E' + ep + '.' + ext
            print(new_name)
            new_path = parent_folder_path + '\\' + new_name
            file_lists.append([file_path, new_path])
        else:
            print('未能识别')
            unknown.append(file_path)

if unknown:
    print('----- 未识别文件 -----')
    for x in unknown:
        print(x)

if rename_delay:
    # 自动运行改名
    print('重命名延迟等待中...')
    # 程序运行太快 会导致重命名失败 估计是文件被锁了 这里故意加个延迟(秒)
    time.sleep(rename_delay)

print('file_lists', file_lists)

for old, new in file_lists:
    try:
        # 检测文件能否重命名 报错直接忽略
        tmp_name = new + '.new'
        os.rename(old, tmp_name)

        # 目标文件已存在, 先删除
        if os.path.exists(new):
            os.remove(new)

        # 临时文件重命名
        os.rename(tmp_name, new)

    except:
        pass

print('运行完毕')
