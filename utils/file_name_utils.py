# 文件名工具
def clean_name(s):
    # 解析为空，清理末尾
    s = s.strip()
    if s.endswith('-'):
        s = s[:-1].strip()
    return s
