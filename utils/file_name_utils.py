import re

# 文件名工具


def clean_name(s):
    """解析为空，清理末尾"""
    s = s.strip()
    if s.endswith('-'):
        s = s[:-1].strip()
    return s


def zero_fix(s):
    """统一补0"""
    if not s:
        return s
    # 删0
    s = s.lstrip('0')
    # 补0
    s = s.zfill(2)
    if '.' in s and s.index('.') == 1:
        s = '0' + s
    return s


def name_format_bypass_check(name, name_format, series, resolution_dict):
    """检查是否已满足 name_format"""
    tmp_pat = (
        '^'
        + name_format.replace('{season}', '\d+')
        .replace('{ep}', '\d+')
        .replace('{series}', series)
        .replace('{resolution}', '(' + '|'.join(resolution_dict.values()) + ')')
        + '$'
    )
    # logger.info(name)
    # logger.info(tmp_pat)
    res = re.match(tmp_pat, name)
    if res:
        return True
    return False
