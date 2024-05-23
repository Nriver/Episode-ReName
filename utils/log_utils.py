try:
    from loguru import logger
except:
    # 兼容无loguru模块的环境，例如docker和群晖
    class logger:
        def info(s):
            print(f'| INFO     | {s}')

        def warning(s):
            print(f'| WARNING  | {s}')
