#!/usr/bin/env python3
"""
tree_to_file.py - 根据tree命令输出重建文件结构

此脚本接收'tree'命令的输出，并在指定的输出目录中重建其表示的文件结构。
它可以从文件或标准输入读取数据。

脚本解析tree输出，根据缩进和分支指示符识别目录和文件，并创建相应的结构。

使用方法:
    python tree_to_file.py [-i 输入文件] [-o 输出目录]

    cat tree输出.txt | python tree_to_file.py -o 我的输出目录

    tree /某个/目录 > tree输出.txt
    python tree_to_file.py -i tree输出.txt -o 重建的结构

输入格式:
    输入应该是'tree'命令的标准输出，看起来像这样:
    .
    ├── 目录1
    │   ├── 文件1.txt
    │   └── 文件2.txt
    └── 目录2
        └── 文件3.txt

选项:
    -i, --input    包含tree输出的输入文件 (默认: 标准输入)
    -o, --output   将创建结构的输出目录 (默认: 'output')

注意:
    - 脚本只创建空文件；不复制文件内容
    - 文件名中的特殊字符会被保留
    - 现有文件不会被覆盖，但会被touch更新时间戳
    - 现有目录将被重用
"""

import sys
import argparse
from pathlib import Path


def parse_tree_line(line):
    """解析tree输出的一行，确定缩进级别和项目名称。"""
    if not line.strip() or line.strip() == '.':
        return None, None

    # 通过计算 '│   ' 或 '    ' 模式的数量来计算缩进级别
    indent_count = 0
    i = 0
    while i < len(line):
        if line[i:i+4] in ['│   ', '    ']:
            indent_count += 1
            i += 4
        else:
            break

    # 提取项目名称
    item_name = line[i:].strip()

    # 移除tree分支指示符
    if item_name.startswith('├── '):
        item_name = item_name[4:]
    elif item_name.startswith('└── '):
        item_name = item_name[4:]
    elif item_name.startswith('│   ├── ') or item_name.startswith('│   └── '):
        item_name = item_name[8:]

    return indent_count, item_name


def create_file_structure(tree_output, output_dir):
    """根据tree命令输出创建文件结构。"""
    # 如果输出目录不存在，则创建它
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 解析tree输出并创建结构
    lines = tree_output.strip().split('\n')
    path_stack = [output_path]

    # 第一遍：通过检查是否有子项来识别目录
    is_directory = {}
    for i, line in enumerate(lines):
        indent, item_name = parse_tree_line(line)
        if indent is None or item_name is None:
            continue

        # 如果下一行有更大的缩进，这是一个目录
        if i + 1 < len(lines):
            next_indent, _ = parse_tree_line(lines[i + 1])
            if next_indent is not None and next_indent > indent:
                is_directory[(indent, item_name)] = True

    # 第二遍：创建文件结构
    path_stack = [output_path]  # 重置路径栈，准备第二遍处理

    for line in lines:
        indent, item_name = parse_tree_line(line)
        if indent is None or item_name is None:
            continue

        # 根据缩进级别调整路径栈
        while len(path_stack) > indent + 1:
            path_stack.pop()

        # 创建项目（文件或目录）
        current_path = path_stack[-1] / item_name

        # 检查是否是目录
        if (indent, item_name) in is_directory:
            # 这是一个目录
            current_path.mkdir(parents=True, exist_ok=True)
            path_stack.append(current_path)
        else:
            # 这是一个文件
            current_path.parent.mkdir(parents=True, exist_ok=True)  # 确保父目录存在
            current_path.touch(exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description='根据tree命令输出重建文件结构',
        epilog='''
示例:
  python tree_to_file.py -i tree输出.txt -o 重建目录
  tree /路径/到/目录 | python tree_to_file.py -o 重建目录

注意: 此脚本只创建目录和文件结构，不创建文件内容。
'''
    )
    parser.add_argument('-i', '--input',
                      help='包含tree输出的输入文件 (默认: 标准输入)')
    parser.add_argument('-o', '--output', default='output',
                      help='将创建结构的输出目录 (默认: output)')
    args = parser.parse_args()

    # 从文件或标准输入读取tree输出
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            tree_output = f.read()
    else:
        tree_output = sys.stdin.read()

    # 创建文件结构
    create_file_structure(tree_output, args.output)
    output_path = Path(args.output).resolve()
    print(f"文件结构已成功创建在: {output_path}")
    print(f"要查看创建的结构，请运行: tree {output_path}")


if __name__ == '__main__':
    main()
