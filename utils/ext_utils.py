from itertools import product

# 后缀名工具


COMMON_MEDIA_EXTS = [
    'flv',
    'mkv',
    'mp4',
    'avi',
    'rmvb',
    'm2ts',
    'wmv',
    'nfo',
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
    # 特殊命名处理
    'chs&jpn',
    'cht&jpn',
    'scjp',
    'tcjp',
    # 一般命名
    'cn',
    'chs',
    'cht',
    'zh',
    'sc',
    'tc',
    'jp',
    'jap',
    'jpn',
    'en',
    'eng',
]

# 混合后缀
COMPOUND_EXTS = (
    COMMON_MEDIA_EXTS
    + ['.'.join(x) for x in list(product(COMMON_LANG, COMMON_CAPTION_EXTS))]
    + COMMON_CAPTION_EXTS
)


def fix_ext(ext):
    # 文件扩展名修正
    # 1.统一小写
    # 2.字幕文件 把sc替换成chs, tc替换成cht, jap替换成jpn
    new_ext = ext.lower()

    # 双重生成器
    ori_list = [f'{y}.{x}' for x in COMMON_CAPTION_EXTS for y in ['sc', 'tc', 'jap']]
    new_list = [f'{y}.{x}' for x in COMMON_CAPTION_EXTS for y in ['chs', 'cht', 'jpn']]

    for i, x in enumerate(ori_list):
        if new_ext == x:
            new_ext = new_list[i]
            break

    return new_ext


def get_file_name_ext(file_full_name):
    # 获取文件名和后缀

    # 特殊情况处理
    if '.' not in file_full_name:
        return file_full_name, ''

    file_name = None
    ext = None

    for x in COMPOUND_EXTS:
        if file_full_name.lower().endswith(x):
            ext = x
            file_name = file_full_name[: -(len(x) + 1)]
            break
    if not ext:
        file_name, ext = file_full_name.rsplit('.', 1)

    return file_name, ext
