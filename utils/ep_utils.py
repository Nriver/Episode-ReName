def ep_format(ep):
    # 格式化ep, 兼容 .5 格式
    if '.' in ep:
        ep_int, ep_tail = ep.split('.', 1)
        ep = str(int(ep_int)).zfill(2) + '.' + ep_tail
    else:
        ep = str(int(ep)).zfill(2)
    return ep
