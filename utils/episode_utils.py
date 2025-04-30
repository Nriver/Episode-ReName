import os
import re

from custom_rules import starts_with_rules
from utils.config_utils import get_qrm_config
from utils.ext_utils import get_file_name_ext
from utils.file_name_utils import zero_fix
from utils.log_utils import logger
from utils.path_utils import format_path
from utils.season_utils import get_season, get_season_cascaded, get_season_path


def ep_format(ep):
    """格式化ep, 兼容 .5 格式"""
    if '.' in ep:
        ep_int, ep_tail = ep.split('.', 1)
        ep = str(int(ep_int)).zfill(2) + '.' + ep_tail
    else:
        ep = str(int(ep)).zfill(2)
    return ep


def extract_season_and_ep_from_standard_patterns(file_name, force_rename=0):
    """
    从文件名中提取已经按标准格式命名的季数和集数

    Args:
        file_name: 文件名
        force_rename: 是否强制重命名

    Returns:
        tuple: (season, ep) 季数和集数，如果不匹配则返回 (None, None)
    """
    # 忽略已按规则命名的文件
    pat = r'S(\d{1,4})E(\d{1,4}(\.5)?)'
    res = re.match(pat, file_name)
    if res:
        logger.info(f"{'忽略识别: 已按规则命名'}")
        if force_rename:
            season, ep = res[1], res[2]
            season = str(int(season)).zfill(2)
            ep = ep_format(ep)
            return season, ep
        else:
            return None, None

    # 如果文件已经有 S01EP01 或者 S01E01 直接读取
    pat = r'[Ss](\d{1,4})[Ee](\d{1,4}(\.5)?)'
    res = re.findall(pat, file_name.upper())
    if res:
        season, ep = res[0][0], res[0][1]
        season = str(int(season)).zfill(2)
        ep = ep_format(ep)
        return season, ep
    pat = r'[Ss](\d{1,4})[Ee][Pp](\d{1,4}(\.5)?)'
    res = re.findall(pat, file_name.upper())
    if res:
        season, ep = res[0][0], res[0][1]
        season = str(int(season)).zfill(2)
        ep = ep_format(ep)
        return season, ep

    return None, None


def extract_ep_from_outside_brackets(file_name, bracket_pairs, res):
    """
    从括号外的内容中提取集数

    Args:
        file_name: 文件名
        bracket_pairs: 括号对列表
        res: 分割后的字符串列表

    Returns:
        tuple: (season, ep) 季数和集数，如果未找到则返回 (None, None)
    """
    season = None
    ep = None

    # 部分资源命名
    # 找 第x集
    pat = r'第(\d{1,4}(\.5)?)[集话話]'
    for y in res:
        y = y.strip()
        res_sub = re.search(pat, y)
        if res_sub:
            ep = res_sub.group(1)
            break
    if not ep:
        # 找 EPXX
        pat = r'[Ee][Pp](\d{1,4}(\.5)?)'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y.upper())
            if res_sub:
                ep = res_sub.group(1)
                break

    # 特殊命名 SExx.xx 第2季第10集 SE02.10
    if not ep:
        # logger.info(f"{'找 EXX'}")
        pat = r'[Ss][Ee](\d{1,2})\.(\d{1,2})'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y.upper())
            if res_sub:
                season = res_sub.group(1)
                ep = res_sub.group(2)
                break

    # 特殊命名 Sxx.xx 第2季第10集 s02.10
    if not ep:
        # logger.info(f"{'找 EXX'}")
        pat = r'[Ss](\d{1,2})\.(\d{1,2})'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y.upper())
            if res_sub:
                season = res_sub.group(1)
                ep = res_sub.group(2)
                break

    # 匹配顺序调整
    if not ep:
        # logger.info(f"{'找 EXX'}")
        pat = r'[Ee](\d{1,4}(\.5)?)'
        for y in res:
            y = y.strip()
            res_sub = re.search(pat, y.upper())
            if res_sub:
                ep = res_sub.group(1)
                break

    def extract_ending_ep(s):
        """从字符串中提取末尾是数字的部分作为集数"""
        logger.debug(f"尝试从字符串中提取末尾数字: '{s}'")
        s = s.strip()
        ep = None

        # 兼容v2和.5格式 不兼容 9.33 格式
        # 例如: 12.5, 13.5, 10v2, 10.5v2
        pat = r'(\d{1,4}(\.5)?)[Vv]?\d?'
        res_sub = re.search(pat, s)
        if res_sub:
            ep = res_sub.group(1)
            logger.debug(f"匹配到数字+可能的v2格式: {ep}, 匹配: {res_sub.group(0)}")
            return ep

        # 兼容END命名
        # 例如: 12END, 12_END, 12 END
        pat = r'(\d{1,4}(\.5)?)\s?(?:_)?(?i:END)?'
        res_sub = re.search(pat, s)
        if res_sub:
            ep = res_sub.group(1)
            logger.debug(f"匹配到END格式: {ep}, 匹配: {res_sub.group(0)}")
            return ep

        # 匹配字符串末尾的数字
        pat = r'\d{1,4}(\.5)?$'
        res_sub = re.search(pat, s)
        if res_sub:
            ep = res_sub.group(0)
            logger.debug(f"匹配到末尾数字: {ep}")
            return ep

        logger.debug(f"未能从字符串中提取到集数: '{s}'")
        return ep

    if not ep:
        for s in res:
            ep = extract_ending_ep(s)
            if ep:
                break

    return season, ep


def get_season_and_ep(file_path, ignores, force_rename=0):
    """
    从文件路径中解析季数和集数

    Args:
        file_path: 文件路径
        ignores: 忽略字符串列表
        force_rename: 是否强制重命名

    Returns:
        tuple: (season, ep) 季数和集数
    """
    logger.info(f"开始解析文件: {file_path}")

    # 去掉ignore文件中忽略的字符串，防止解析错误
    original_path = file_path
    for x in ignores:
        if x in file_path:
            file_path = file_path.replace(x, '')
            logger.debug(f"应用忽略规则，移除字符串: '{x}'")

    if original_path != file_path:
        logger.debug(f"应用忽略规则后的路径: {file_path}")

    season = None
    ep = None

    file_full_name = os.path.basename(file_path)

    # 父级文件夹
    parent_folder_path = os.path.dirname(file_path)

    # 获取文件名和后缀
    file_name, _ = get_file_name_ext(file_full_name)

    _ = get_season_cascaded(parent_folder_path)
    if not _:
        # logger.info(f"{'不在season文件夹内 忽略'}")
        return None, None

    # 尝试从标准命名格式中提取季数和集数
    season, ep = extract_season_and_ep_from_standard_patterns(file_name, force_rename)
    if season is not None and ep is not None:
        logger.info(f"从标准命名格式中提取到季数和集数: S{season}E{ep}")
        return season, ep

    # 从父级目录获取季数
    season = get_season_cascaded(parent_folder_path)
    if season:
        logger.debug(f"从父级目录获取到季数: {season}")
    else:
        logger.warning(f"无法从父级目录获取季数，退出解析")
        return None, None

    # 根据文件名获取集数

    # 特殊文件名使用配置的匹配规则
    # 确定是否满足特殊规则
    use_custom_rule = False
    for starts_str, rules in starts_with_rules:
        if file_name.startswith(starts_str):
            use_custom_rule = True
            logger.debug(f"文件名满足特殊规则前缀: '{starts_str}'")
            for rule in rules:
                try:
                    logger.debug(f"尝试应用特殊规则: {rule}")
                    res = re.findall(rule, file_name)
                    if res:
                        ep = res[0]
                        season = str(int(season)).zfill(2)
                        ep = ep_format(ep)
                        logger.info(f"根据特殊规则找到了集数: S{season}E{ep}, 规则: {rule}")
                        return season, ep
                except Exception as e:
                    logger.error(f"应用特殊规则时出错: {str(e)}")

    # 如果满足特殊规则还没找到ep 直接返回空
    if use_custom_rule and not ep:
        logger.warning(f"文件名满足特殊规则前缀，但未能提取到集数: {file_name}")
        return None, None

    # 其它不在特殊规则的继续往下正常查找匹配

    # 常见的括号
    bracket_pairs = [
        [r'\[', r'\]'],
        [r'\(', r'\)'],
        ['【', '】'],
        # 日语括号
        ['「', '」'],
    ]
    # 内容
    patterns = [
        # 1到4位数字
        r'(\d{1,4}(\.5)?)',
        # 特殊文字处理
        r'第(\d{1,4}(\.5)?)集',
        r'第(\d{1,4}(\.5)?)话',
        r'第(\d{1,4}(\.5)?)話',
        r'[Ee][Pp](\d{1,4}(\.5)?)',
        r'[Ee](\d{1,4}(\.5)?)',
        # 兼容SP01等命名
        r'[Ss][Pp](\d{1,4}(\.5)?)',
        # 兼容v2命名
        r'(\d{1,4}(\.5)?)[Vv]?\d?',
        # 兼容END命名
        r'(\d{1,4}(\.5)?)\s?(?:_)?(?i:END)?',
    ]
    # 括号和内容组合起来
    pats = []
    for pattern in patterns:
        for bracket_pair in bracket_pairs:
            pats.append(bracket_pair[0] + pattern + bracket_pair[1])
    # 查找
    for pat in pats:
        res = re.search(pat, file_name)
        if res:
            ep = res.group(1)
            break

    if not ep:
        logger.info(f"括号内未识别到集数，开始寻找括号外内容")
        # 把括号当分隔符排除掉括号内的文字
        pat = ''
        for bracket_pair in bracket_pairs:
            pat += bracket_pair[0] + '.*?' + bracket_pair[1] + '|'
        pat = pat[:-1]
        # 兼容某些用 - 分隔的文件
        pat += r'|\-|\_'
        logger.debug(f'使用分隔符模式: {pat}')

        res = re.split(pat, file_name)
        # 过滤空字符串
        res = list(filter(None, res))
        # 从后向前查找数字, 一般集数在剧集名称后面, 防止剧集有数字导致解析出问题
        res = res[::-1]

        logger.debug(f'分割后的文件名部分: {res}')

        # 从括号外内容中提取集数
        season_from_outside, ep_from_outside = extract_ep_from_outside_brackets(file_name, bracket_pairs, res)
        if ep_from_outside:
            ep = ep_from_outside
        if season_from_outside:
            season = season_from_outside

    season = zero_fix(season)
    ep = zero_fix(ep)

    return season, ep


def ep_offset_patch(file_path, ep, application_path):
    """
    多季集数修正

    Args:
        file_path: 文件路径
        ep: 集数
        application_path: 应用程序路径

    Returns:
        str: 修正后的集数
    """
    logger.debug(f"开始进行集数修正，原始集数: {ep}")

    # 多季集数修正
    # 20220721 修改集数修正修正规则：可以用 + - 符号标记修正数值, 表达更直观
    b = os.path.dirname(file_path.replace('\\', '/'))
    offset_str = None

    # 向上查找目录，寻找all.txt文件
    while b:
        if offset_str:
            break
        if not '/' in b:
            break

        b, fo = b.rsplit('/', 1)
        offset_str = None

        if get_season(fo):
            logger.debug(f"检查季文件夹是否有集数修正文件: {b}/{fo}")
            try:
                for fn in os.listdir(b + '/' + fo):
                    if fn.lower() != 'all.txt':
                        continue

                    all_txt_path = f"{b}/{fo}/{fn}"
                    logger.debug(f"找到集数修正文件: {all_txt_path}")

                    with open(all_txt_path, encoding='utf-8') as f:
                        offset_str = f.read()
                        logger.info(f"从 {all_txt_path} 读取到集数修正值: {offset_str}")
                        break
            except Exception as e:
                logger.error(f"读取集数修正文件时出错: {str(e)}")
                return ep
    # 没有找到all.txt 尝试寻找qb-rss-manager的配置文件
    # 1. config_ern.json 配置
    # 2. 这两个exe在同一个目录下, 直接读取配置
    if not offset_str:
        qrm_config = get_qrm_config(application_path)

        if qrm_config:
            # logger.info(f"{'qrm_config', qrm_config}")
            # logger.info(f"{'file_path', file_path}")
            season_path = get_season_path(file_path)
            # logger.info(f"{'season_path', season_path}")
            if 'data_list' in qrm_config:
                logger.info('检测到 qb-rss-manager 的 旧版 格式数据')
                for x in qrm_config['data_list']:
                    if format_path(x[5]) == format_path(season_path):
                        if x[4]:
                            try:
                                offset_str = x[4]
                                logger.info(f"{'QRM获取到 offset_str', offset_str}")
                            except:
                                pass
            else:
                logger.info('检测到 qb-rss-manager 的 v1 格式数据')
                for data_group in qrm_config['data_dump']['data_groups']:
                    for x in data_group['data']:
                        if format_path(x['savePath']) == format_path(season_path):
                            if x['rename_offset']:
                                try:
                                    offset_str = x['rename_offset']
                                    logger.info(f"{'QRM获取到 offset_str', offset_str}")
                                except:
                                    pass
    # 集数修正
    if offset_str:
        try:
            offset_str = offset_str.strip().replace(' ', '')

            if '|' not in offset_str:
                logger.info(f'单一数字类型的offset: {offset_str}')
                # 直接取整数, 正数为减少, 负数是增加
                offset = int(offset_str)
            else:
                logger.info(f'多组数据的offset解析: {offset_str}')
                # 和 QRM 多组匹配对应的多组offset
                # 比如: 格式 `12|0|-11` 第一组集数减12, 第二组不变, 第三组加11

                if not qrm_config:
                    logger.info('未获取到QRM的配置，默认取第一个offset')
                    offset = int(offset_str.split('|')[0].strip())
                    logger.debug(f'使用第一个offset值: {offset}')
                else:
                    # 查找QRM配置匹配的组序号
                    index = 0
                    logger.debug(f'开始查找QRM配置匹配的组序号')

                    for data_group in qrm_config['data_dump']['data_groups']:
                        for x in data_group['data']:
                            if format_path(x['savePath']) == format_path(season_path):
                                try:
                                    must_contain_tmp = x['mustContain']
                                    logger.debug(f'找到匹配的保存路径，mustContain: {must_contain_tmp}')

                                    if '|' not in must_contain_tmp:
                                        logger.debug('mustContain不包含多组数据，使用默认index=0')
                                        break
                                    else:
                                        for i, keywords in enumerate(must_contain_tmp.split('|')):
                                            keywords_list = keywords.strip().split(' ')
                                            logger.debug(f'检查第{i+1}组关键词: {keywords_list}')

                                            if all([keyword.strip() in file_path for keyword in keywords_list]):
                                                index = i
                                                logger.debug(f'文件路径匹配第{i+1}组关键词，使用index={index}')
                                                break
                                except Exception as e:
                                    logger.error(f'解析mustContain时出错: {str(e)}')

                    # 获取offset
                    offset_parts = offset_str.split('|')
                    if index < len(offset_parts):
                        offset = int(offset_parts[index].strip())
                        logger.info(f'使用第{index+1}组offset值: {offset}')
                    else:
                        logger.warning(f'索引{index}超出offset分组范围，使用第一个offset')
                        offset = int(offset_parts[0].strip())

            # 处理带小数点的集数（如12.5）
            if '.' in ep:
                ep_int, ep_tail = ep.split('.')
                ep_int = int(ep_int)

                # 只有当集数大于等于offset时才进行修正（防止负数集数）
                if int(ep_int) >= offset:
                    original_ep = ep
                    ep_int = ep_int - offset
                    ep = str(ep_int) + '.' + ep_tail
                    logger.info(f"集数修正: {original_ep} -> {ep} (offset={offset})")
                else:
                    logger.warning(f"集数({ep_int})小于offset({offset})，不进行修正")
            else:
                # 处理整数集数
                ep_int = int(ep)
                if ep_int >= offset:
                    original_ep = ep
                    ep = str(ep_int - offset)
                    logger.info(f"集数修正: {original_ep} -> {ep} (offset={offset})")
                else:
                    logger.warning(f"集数({ep_int})小于offset({offset})，不进行修正")
        except Exception as e:
            logger.error(f"应用集数修正时出错: {str(e)}")
            return ep

    return zero_fix(ep)
