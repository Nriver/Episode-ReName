import argparse
import os
import platform
import re
import sys
import time
from datetime import datetime

from custom_rules import starts_with_rules
from utils.config_utils import get_qrm_config
from utils.episode_utils import get_season_and_ep, ep_offset_patch, ep_format
from utils.ext_utils import COMPOUND_EXTS, get_file_name_ext, fix_ext
from utils.file_name_utils import clean_name, zero_fix, name_format_bypass_check
from utils.log_utils import logger
from utils.path_utils import (
    format_path,
    get_absolute_path,
    delete_empty_dirs,
    check_and_delete_redundant_file,
)
from utils.resolution_utils import get_resolution_in_name, resolution_dict
from utils.season_utils import get_season_cascaded, get_season, get_season_path
from utils.series_utils import get_series_from_season_path

# print('''
#     -- 警告 --
#     如果用这个程序导致文件乱了后果自负哈哈哈哈哈哈哈
#
#     -- 运行环境 --
#     需要python3环境 不推荐使用群晖的python3.5套件环境,可能出现部分字符不兼容
#     -- 使用方法 --
#     1.命令行运行
#     python3 rename.py "/path/to/folder"
#     2.直接运行
#     修改 target_path的路径
#     python3 rename.py
#     -- 程序原理 --
#     优先解析括号
#     [] 【】()内的1-4位纯数字优先
#     部分特殊处理
#     括号没有
#     取剩余部分结尾的数字
#     部分特殊处理
#     应该能解析出大部分的命名规则了
# ''')

script_path = os.path.dirname(os.path.realpath(__file__))
target_path = ''

# 重命名的文件移动到season目录下
move_up_to_season_folder = True

# pyinstaller打包后, 通过命令行调用, 必须这样才能获取到exe文件路径, 普通的script_path获取的是临时文件路径
# 拿到这个路径之后才能方便地读取到exe同目录的文件
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.realpath(sys.executable))
elif __file__:
    application_path = os.path.dirname(os.path.realpath(__file__))


# if len(sys.argv) < 2:
#     exit()

# 默认配置
rename_delay = 0
rename_overwrite = True
rename_interval = 0  # 每次重命名操作之间的间隔时间（秒）

# # 测试
# if not getattr(sys, 'frozen', False) and len(sys.argv) == 1:
#     # 直接运行的目标路径
#     # sys.argv.append(r'\\DSM\DSM_share5\season1\aaa E02 AAA.mp4')
#     # sys.argv.append(r'\\DSM\DSM_share5\season1')
#     # sys.argv.append(r'E:\test\极端试验样本\s01\极端试验样本 - S01E01.mp4')
#     # sys.argv.append(r'E:\test\极端试验样本\s01\S01E01 - 720p.mp4')
#     sys.argv.append(r'E:\test\极端试验样本\s01')

if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
    # 旧版的命令解析
    # 简单通过判断是否有 - 来区分新旧参数
    # python EpisodeReName.py E:\test\极端试验样本\S1

    # 读取命令行目标路径
    target_path = sys.argv[1]
    logger.info(f"目标路径: {target_path}")
    if len(sys.argv) > 2:
        # 重命名延迟(秒) 配合qb使用的参数, 默认为0秒
        rename_delay = int(sys.argv[2])
        logger.info(f"重命名延迟: {rename_delay}秒")
    name_format = 'S{season}E{ep}'
    # name_format = '{series} - S{season}E{ep}'
    # name_format = 'S{season}E{ep} - {resolution}'
    name_format_bypass = True
    force_rename = 0
    custom_replace_pair = ""
    use_folder_as_season = 0
    del_empty_folder = 0
    priority_match = 0
    ignore_file_count_check = 0
    log_to_file = 0  # 默认关闭日志文件输出
    log_level = 'INFO'  # 默认日志等级
else:
    # 新的argparse解析
    # python EpisodeReName.py --path E:\test\极端试验样本\S1 --delay 1 --overwrite 1
    # python EpisodeReName.py --path E:\test\极端试验样本\S1 --delay 1 --overwrite 0
    # EpisodeReName.exe --path E:\test\极端试验样本\S1 --delay 1 --overwrite 0
    # python EpisodeReName.py --path /home/nate/data/极端试验样本/s1/ --delay 1 --overwrite 1 --name_format "S{season}E{ep} - {resolution}"

    ap = argparse.ArgumentParser()
    ap.add_argument('--path', required=True, help='目标路径')
    ap.add_argument(
        '--delay',
        required=False,
        help='重命名延迟(秒) 配合qb使用的参数, 默认为0秒不等待',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--overwrite',
        required=False,
        help='强制重命名, 默认为1开启覆盖模式, 0为不覆盖, 遇到同名文件会跳过, 结果输出到error.log',
        type=int,
        default=1,
    )
    ap.add_argument(
        '--name_format',
        required=False,
        help='(慎用) 自定义重命名格式, 参数需要加引号 默认为 "S{season}E{ep}" 可以选择性加入 系列名称如 "{series} - S{season}E{ep}" ',
        default='S{season}E{ep}',
    )
    ap.add_argument(
        '--name_format_bypass',
        required=False,
        help='(慎用) 自定义重命名格式, 对满足格式的文件忽略重命名步骤',
        default=0,
    )
    ap.add_argument(
        '--parse_resolution',
        required=False,
        help='(慎用) 识别分辨率，输出结果类似于 `S01E01 - 1080p.mp4`, 1为开启, 0为不开启. 开启后传入的 name_format 参数会失效, 强制设置为 "S{season}E{ep} - {resolution}"',
        default=0,
    )
    ap.add_argument(
        '--force_rename',
        required=False,
        help='(慎用) 即使已经是标准命名, 也强制重新改名, 默认为0不开启, 1是开启',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--replace',
        required=False,
        type=str,
        nargs='+',
        action='append',
        help='自定义替换关键字, 一般是给字幕用, 用法 `--replace chs chi --replace cht chi` 就能把chs和cht替换成chi, 可以写多组关键字',
        default=[],
    )
    ap.add_argument(
        '--use_folder_as_season',
        required=False,
        help='优先使用父级文件夹中的季数来代替文件名中的季数, 默认为0不开启, 1是开启',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--del_empty_folder',
        required=False,
        help='删除空的子目录, 默认为0不开启, 1是开启',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--priority_match',
        required=False,
        help='(慎用) 目标文件如果存在，会导致覆盖操作的时候，优先保留满足第一组匹配规则的文件，如果新文件不满足匹配，则删除新文件。默认为0不开启, 1是开启',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--ignore_file_count_check',
        required=False,
        help='忽略旧文件数量和新文件数量不一致的检查，即使可能会覆盖文件也继续执行。默认为0不开启, 1是开启',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--rename_interval',
        required=False,
        help='每次重命名操作之间的间隔时间(秒)，用于网盘挂载等情况下避免重命名太快而客户端未及时响应导致重命名异常。默认为0秒不等待',
        type=float,
        default=0,
    )
    ap.add_argument(
        '--log_to_file',
        required=False,
        help='是否将日志输出到文件，默认为0关闭，1为开启。关闭时只在控制台显示日志',
        type=int,
        default=0,
    )
    ap.add_argument(
        '--log_level',
        required=False,
        help='设置日志输出等级，可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL。默认为INFO',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
    )

    args = vars(ap.parse_args())
    target_path = args['path']
    rename_delay = args['delay']
    rename_overwrite = args['overwrite']
    name_format = args['name_format']
    name_format_bypass = args['name_format_bypass']
    parse_resolution = args['parse_resolution']
    force_rename = args['force_rename']
    custom_replace_pair = args['replace']
    use_folder_as_season = args['use_folder_as_season']
    del_empty_folder = args['del_empty_folder']
    priority_match = args['priority_match']
    ignore_file_count_check = args['ignore_file_count_check']
    rename_interval = args['rename_interval']
    log_to_file = args['log_to_file']
    log_level = args['log_level']

    if parse_resolution:
        name_format = 'S{season}E{ep} - {resolution}'

# 配置日志输出 - 在解析完命令行参数后设置
# 首先移除默认的处理器
try:
    logger.remove()
except:
    pass

# 添加控制台处理器，使用指定的日志等级
try:
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <blue>PID:{process}</blue> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    logger.debug(f"日志等级已设置为: {log_level}")
except Exception as e:
    print(f"设置控制台日志等级失败: {str(e)}")

# 如果启用了文件日志，添加文件处理器
if log_to_file:
    log_file = os.path.join(application_path, 'app.log')
    try:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | PID:{process} | {message}",
            rotation="10 MB",  # 日志文件达到10MB时轮转
            retention="1 month",  # 保留1个月的日志
            compression="zip",  # 压缩旧日志
            level=log_level,
            encoding="utf-8",
        )
        logger.info(f"日志文件已启用: {log_file}，日志等级: {log_level}")
    except Exception as e:
        logger.error(f"设置文件日志失败: {str(e)}")

logger.info(f"程序启动 - 版本: {os.path.basename(sys.argv[0])}")
logger.info(f"命令行参数: {sys.argv}")
logger.info(f"运行环境: {platform.system()} {platform.release()}")
logger.info(f"Python版本: {platform.python_version()}")
logger.info(f"工作目录: {application_path}")

if not target_path:
    # 没有路径参数直接退出
    sys.exit()

# 除samba格式的路径外 其它格式的路径斜杠统一处理
if not target_path.startswith(r'\\'):
    target_path = target_path.replace('\\', '/').replace('//', '/')

# 忽略字符串, 用于处理剧集名字中带数字的文件, 提取信息时忽略这些字符串
# ignore 文件必须用utf-8编码
ignores = []
ignore_file = os.path.join(application_path, 'ignore')
if os.path.exists(ignore_file):
    with open(ignore_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and line not in ignores:
                ignores.append(line)


# 输出结果列表
file_lists = []
unknown = []

# 当前系统类型
system = platform.system()


if os.path.isdir(target_path):
    logger.info(f"开始处理文件夹: {target_path}")
    logger.info(f"处理模式: 批量处理")

    # 遍历文件夹
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files:
            # 完整文件路径
            file_path = get_absolute_path(os.path.join(root, name))

            # 删除多余文件
            if check_and_delete_redundant_file(file_path):
                logger.warning(f'多余文件, 删除 {file_path}')
                continue

            # 只处理媒体文件
            file_name, ext = get_file_name_ext(name)
            if not ext.lower() in COMPOUND_EXTS:
                continue

            parent_folder_path = os.path.dirname(file_path)
            try:
                season, ep = get_season_and_ep(file_path, ignores, force_rename)
            except ValueError as e:
                logger.error(e)
                season, ep = None, None
            # 是否从父级目录获取季数
            if use_folder_as_season:
                season = get_season_cascaded(file_path)

            resolution = get_resolution_in_name(name)
            logger.info(f'文件 "{name}" 识别结果: 季={season}, 集={ep}')
            # 重命名
            if season and ep:
                # 修正集数
                ep = ep_offset_patch(file_path, ep, application_path)
                season_path = get_season_path(file_path)
                # 系列名称
                series = get_series_from_season_path(season_path)
                # new_name = f'S{season}E{ep}' + '.' + fix_ext(ext)
                if name_format_bypass and name_format_bypass_check(
                    file_name, name_format, series, resolution_dict
                ):
                    logger.info('命名已满足 name_format 跳过')
                    continue

                new_name = clean_name(name_format.format(**locals())) + '.' + fix_ext(ext)

                if custom_replace_pair:
                    # 自定义替换关键字
                    for replace_old_part, replace_new_part in custom_replace_pair:
                        new_name = new_name.replace(replace_old_part, replace_new_part)

                logger.info(f'重命名为: {new_name}')
                if move_up_to_season_folder:
                    new_path = season_path + '/' + new_name
                    logger.info(f'目标位置: 季文件夹 ({season_path})')
                else:
                    new_path = parent_folder_path + '/' + new_name
                    logger.info(f'目标位置: 原文件夹 ({parent_folder_path})')
                file_lists.append([format_path(file_path), format_path(new_path)])
            else:
                logger.info(f"{'未能识别 season 和 ep'}")
                unknown.append(file_path)

else:
    logger.info(f"开始处理文件: {target_path}")
    logger.info(f"处理模式: 单文件处理")
    file_path = get_absolute_path(target_path)
    file_full_name = os.path.basename(file_path)
    file_name, ext = get_file_name_ext(file_full_name)
    parent_folder_path = os.path.dirname(file_path)
    if ext.lower() in COMPOUND_EXTS:
        season, ep = get_season_and_ep(file_path, ignores, force_rename)
        # 是否从父级目录获取季数
        if use_folder_as_season:
            season = get_season_cascaded(file_path)

        resolution = get_resolution_in_name(file_name)
        logger.info(f'文件 "{file_full_name}" 识别结果: 季={season}, 集={ep}')
        if season and ep:
            # 修正集数
            ep = ep_offset_patch(file_path, ep, application_path)
            season_path = get_season_path(file_path)
            # 系列名称
            series = get_series_from_season_path(season_path)
            # new_name = f'S{season}E{ep}' + '.' + fix_ext(ext)
            if name_format_bypass and name_format_bypass_check(
                file_name, name_format, series, resolution_dict
            ):
                logger.info('当前命名已满足 name_format 的格式, 退出')
                exit()
            new_name = clean_name(name_format.format(**locals())) + '.' + fix_ext(ext)

            if custom_replace_pair:
                # 自定义替换关键字
                for replace_old_part, replace_new_part in custom_replace_pair:
                    new_name = new_name.replace(replace_old_part, replace_new_part)

            logger.info(f'重命名为: {new_name}')
            if move_up_to_season_folder:
                new_path = format_path(season_path + '/' + new_name)
                logger.info(f'目标位置: 季文件夹 ({season_path})')
            else:
                new_path = format_path(parent_folder_path + '/' + new_name)
                logger.info(f'目标位置: 原文件夹 ({parent_folder_path})')

            file_lists.append([file_path, new_path])
        else:
            logger.info(f"{'未能识别 season 和 ep'}")
            unknown.append(file_path)

if unknown:
    logger.warning(f"----- 未能识别的文件 ({len(unknown)}) -----")
    for i, x in enumerate(unknown, 1):
        logger.warning(f'{i}. {x}')
    logger.warning(f"--------------------")

if rename_delay:
    # 自动运行改名
    logger.info(f"重命名延迟等待中... {rename_delay}秒")
    # 程序运行太快 会导致重命名失败 估计是文件被锁了 这里故意加个延迟(秒)
    time.sleep(rename_delay)


if file_lists:
    logger.info(f"----- 待重命名文件列表 ({len(file_lists)}) -----")
    for i, (old, new) in enumerate(file_lists, 1):
        logger.info(f'{i}. {old} -> {new}')
    logger.info(f"-----------------------")

# 检查旧的文件数量和新的文件数量是否一致，防止文件被覆盖
new_set = set([x[1] for x in file_lists])
if len(new_set) != len(file_lists) and not ignore_file_count_check:
    logger.warning(f"安全检查: 旧文件数量({len(file_lists)})和新文件数量({len(new_set)})不一致，可能会导致文件被覆盖")
    new_list = [x[1] for x in file_lists]
    duplicate_files = []
    for file in new_set:
        count = new_list.count(file)
        if count > 1:
            duplicate_files.append((file, count))

    if duplicate_files:
        logger.warning(f"检测到{len(duplicate_files)}个重复目标文件:")
        for file, count in duplicate_files:
            logger.warning(f"  - {file} (重复{count}次)")

    logger.info(f"如需忽略此检查并继续执行，请使用 --ignore_file_count_check 1 参数")
    logger.error(f"程序已停止执行，未进行任何文件重命名")
    sys.exit()
elif len(new_set) != len(file_lists) and ignore_file_count_check:
    logger.warning(f"安全检查: 旧文件数量({len(file_lists)})和新文件数量({len(new_set)})不一致，可能会导致文件被覆盖")
    logger.warning(f"已启用忽略检查(--ignore_file_count_check 1)，将继续执行重命名操作")

    new_list = [x[1] for x in file_lists]
    duplicate_files = []
    for file in new_set:
        count = new_list.count(file)
        if count > 1:
            duplicate_files.append((file, count))

    if duplicate_files:
        logger.warning(f"以下文件将被多次覆盖:")
        for file, count in duplicate_files:
            logger.warning(f"  - {file} (将被覆盖{count-1}次)")

# 错误记录
error_logs = []

logger.info(f"开始执行重命名操作 (共{len(file_lists)}个文件)...")

for index, (old, new) in enumerate(file_lists, 1):
    # 添加每次重命名操作之间的间隔时间
    if rename_interval > 0:
        if index > 1:  # 第一个文件不需要等待
            logger.debug(f"重命名间隔等待 {rename_interval}秒...")
            time.sleep(rename_interval)

    logger.info(f"[{index}/{len(file_lists)}] 重命名: {os.path.basename(old)} -> {os.path.basename(new)}")

    if not rename_overwrite:
        # 如果设置不覆盖 遇到已存在的目标文件不强制删除 只记录错误
        if os.path.exists(new):
            error_message = f'重命名失败: 目标文件已存在 - {new}'
            logger.warning(error_message)
            error_logs.append(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {error_message}'
            )
            continue

    # new路径文件如果存在，会导致覆盖操作的时候，优先保留满足第一组匹配规则的文件
    # 如果old文件不满足匹配，则删除old文件。跳过本次重命名操作。
    # 如果old文件满足匹配，则删除new文件，继续重命名。
    if priority_match and os.path.exists(new):

        if old == new:
            # --overwrite 1 的时候必须做这个检测，不然会误判
            logger.info('新文件和已存在文件相同，跳过匹配检测')
            continue

        qrm_config = get_qrm_config(application_path)
        if qrm_config:
            logger.info('分析第一组匹配规则位满足情况')
            season_path = get_season_path(old)
            logger.info(f'season_path {season_path}')
            must_contain = ''
            for data_group in qrm_config['data_dump']['data_groups']:
                for x in data_group['data']:
                    if format_path(x['savePath']) == format_path(season_path):
                        if x['mustContain']:
                            try:
                                must_contain = x['mustContain']
                                logger.info(f"{'QRM获取到 must_contain', must_contain}")
                            except:
                                pass
            first_match = must_contain.split(' ')[0]
            logger.info(f'分离第一组匹配规则条件 first_match: {first_match}')
            if first_match:
                file_full_name = os.path.basename(old)
                if not (first_match.lower() in file_full_name.lower()):
                    logger.info(f'已存在文件情况下，新文件未满足第一组匹配规则，删除当前文件: {old}')
                    try:
                        os.remove(old)
                        logger.info(f"✓ 文件删除成功: {old}")
                    except Exception as e:
                        logger.error(f"文件删除失败: {old}, 错误: {str(e)}")
                    continue
                else:
                    logger.info('满足优先规则，重命名当前文件')

    # 默认遇到文件存在则强制删除已存在文件
    try:
        # 检测文件能否重命名
        tmp_name = new + '.new'
        logger.info(f"步骤1: 重命名 {old} -> {tmp_name} (临时文件)")
        try:
            os.rename(old, tmp_name)
            logger.info(f"✓ 临时重命名成功: {old} -> {tmp_name}")
        except Exception as e:
            logger.error(f"临时重命名失败: {old} -> {tmp_name}, 错误: {str(e)}")
            raise  # 重新抛出异常，让外层的异常处理捕获

        # 目标文件已存在, 先删除
        if os.path.exists(new):
            logger.info(f"步骤2: 删除已存在的目标文件 {new}")
            try:
                os.remove(new)
                logger.info(f"✓ 目标文件删除成功: {new}")
            except Exception as e:
                logger.error(f"目标文件删除失败: {new}, 错误: {str(e)}")
                raise  # 重新抛出异常，让外层的异常处理捕获

        # 临时文件重命名
        logger.info(f"步骤3: 重命名 {tmp_name} -> {new} (最终文件)")
        try:
            os.rename(tmp_name, new)
            logger.info(f"✓ 重命名成功: {os.path.basename(old)} -> {os.path.basename(new)}")
        except Exception as e:
            logger.error(f"最终重命名失败: {tmp_name} -> {new}, 错误: {str(e)}")
            # 尝试恢复原始文件
            try:
                logger.warning(f"尝试恢复原始文件: {tmp_name} -> {old}")
                os.rename(tmp_name, old)
                logger.info(f"✓ 原始文件恢复成功: {tmp_name} -> {old}")
            except Exception as recover_error:
                logger.error(f"原始文件恢复失败: {tmp_name} -> {old}, 错误: {str(recover_error)}")
            raise  # 重新抛出原始异常，让外层的异常处理捕获
    except Exception as e:
        error_message = f"重命名失败: {os.path.basename(old)} -> {os.path.basename(new)}, 错误: {str(e)}"
        logger.error(error_message)
        error_logs.append(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {error_message}')

if del_empty_folder:
    logger.info('删除空的子目录')
    delete_empty_dirs(target_path)

if error_logs:
    # 在日志中显示前5个错误
    if len(error_logs) > 0:
        logger.warning(f"部分文件重命名失败 ({len(error_logs)}个)")
        logger.warning("错误摘要 (前5个):")
        for i, error in enumerate(error_logs[:5], 1):
            logger.warning(f"  {i}. {error}")
        if len(error_logs) > 5:
            logger.warning(f"  ... 还有 {len(error_logs) - 5} 个错误未显示")

    # 如果启用了日志文件，则写入错误日志
    if log_to_file:
        error_file = os.path.join(application_path, 'error.log')
        logger.warning(f'详细错误信息已记录到: {error_file}')

        try:
            if not os.path.exists(error_file):
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(error_logs))
            else:
                with open(error_file, 'a', encoding='utf-8') as f:
                    f.write('\n' + '\n'.join(error_logs))
            logger.info(f"错误日志已保存到: {error_file}")
        except Exception as e:
            logger.error(f"写入错误日志文件失败: {str(e)}")
    else:
        logger.warning(f"日志文件输出已禁用，错误信息仅在控制台显示")

# 统计处理结果
success_count = len(file_lists) - len(error_logs) if file_lists else 0
logger.info(f"处理统计:")
logger.info(f"  - 总文件数: {len(file_lists) if file_lists else 0}")
logger.info(f"  - 成功重命名: {success_count}")
logger.info(f"  - 失败: {len(error_logs) if error_logs else 0}")
logger.info(f"  - 未识别: {len(unknown) if unknown else 0}")

logger.info(f"程序运行完毕 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
