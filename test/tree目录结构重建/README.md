# 🌲 Tree to File 目录结构重建工具

这个工具可以根据 `tree` 命令的输出重建文件结构。这对于快速创建测试目录结构或者复制文件组织结构非常有用。

## 使用方法

### 从文件读取 tree 输出并重建结构

```bash
python tree_to_file.py -i tree输出.txt -o 重建目录
```

### 直接从 tree 命令输出重建结构

```bash
tree /路径/到/目录 | python tree_to_file.py -o 重建目录
```

### 参数说明

- `-i, --input`: 包含 tree 输出的输入文件 (默认: 标准输入)
- `-o, --output`: 将创建结构的输出目录 (默认: 'output')

## 示例

假设有以下 tree 命令输出:

```
.
├── 测试子目录
│   ├── S01E03.mp4
│   ├── S01E03.nfo
│   ├── S01E04 aaaaa.mp4
│   └── S01E04 aaaaa.nfo
├── S03E01-mediainfo.json
├── S03E01.mp4
├── S03E01.nfo
├── S03E02-mediainfo.json
├── S03E02.mp4
└── S03E02.nfo
```

可以使用以下命令重建这个结构:

```bash
# 假设上面的输出保存在 sample_tree_output.txt 文件中
python tree_to_file.py -i sample_tree_output.txt -o 测试重建目录
```

## 注意事项

- 此工具只创建目录和空文件结构，不复制文件内容
- 文件名中的特殊字符会被保留
- 现有文件不会被覆盖，但会被更新时间戳
- 现有目录将被重用