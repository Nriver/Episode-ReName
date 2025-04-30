import os
import sys
from datetime import datetime

try:
    from loguru import logger

    # 注意：不在这里初始化logger
    # 移除默认的处理器和添加新处理器的操作将在EpisodeReName.py中完成
    # 这样可以确保使用命令行参数指定的日志等级

except ImportError:
    # 兼容无loguru模块的环境，例如docker和群晖
    class Logger:
        def __init__(self):
            self.log_file = None
            self.log_level = "INFO"
            self.levels = {
                "DEBUG": 10,
                "INFO": 20,
                "WARNING": 30,
                "ERROR": 40,
                "CRITICAL": 50
            }

        def _log(self, level, message):
            import os
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pid = os.getpid()
            formatted_message = f"{timestamp} | {level: <8} | PID:{pid} | {message}"

            # 检查是否应该记录此级别的日志
            if self.levels.get(level, 0) >= self.levels.get(self.log_level, 0):
                # 打印到控制台
                print(formatted_message)

                # 如果设置了日志文件，也写入文件
                if self.log_file:
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(formatted_message + "\n")

        def add(self, sink=None, level="INFO", format=None, rotation=None, retention=None, compression=None, encoding="utf-8", **kwargs):
            """设置日志文件和日志级别，兼容loguru的参数风格"""
            # 设置日志级别
            if level in self.levels:
                self.log_level = level
                print(f"日志等级已设置为: {level}")
            else:
                print(f"无效的日志等级: {level}，使用默认等级: {self.log_level}")

            # 如果sink是sys.stdout或sys.stderr，则不设置日志文件
            if sink == sys.stdout or sink == sys.stderr:
                return self

            # 否则，将sink视为文件路径
            self.log_file = sink

            # 确保日志目录存在
            if self.log_file:
                log_dir = os.path.dirname(self.log_file)
                if log_dir and not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir)
                    except Exception as e:
                        print(f"创建日志目录失败: {str(e)}")

                # 测试日志文件是否可写
                try:
                    with open(self.log_file, "a", encoding=encoding) as f:
                        f.write("")
                except Exception as e:
                    print(f"日志文件不可写: {str(e)}")
                    self.log_file = None

            return self

        def remove(self):
            """移除所有处理器"""
            self.log_file = None
            return self

        def debug(self, message):
            self._log("DEBUG", message)

        def info(self, message):
            self._log("INFO", message)

        def warning(self, message):
            self._log("WARNING", message)

        def error(self, message):
            self._log("ERROR", message)

        def critical(self, message):
            self._log("CRITICAL", message)

    # 创建全局logger实例
    logger = Logger()
