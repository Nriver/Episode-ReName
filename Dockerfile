# 阶段一：构建阶段
FROM python:3.9 as builder

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY *.py .

# 执行 PyInstaller 打包
RUN pyinstaller -F EpisodeReName.py

# 阶段二：运行阶段
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制打包好的可执行文件
COPY --from=builder /app/dist/EpisodeReName /bin/EpisodeReName

# 设置入口命令
CMD ["EpisodeReName"]
