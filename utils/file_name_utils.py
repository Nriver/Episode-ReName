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
