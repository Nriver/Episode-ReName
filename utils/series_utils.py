import os
import re


def get_series_from_season_path(season_path):
    """修正系列名称获取 去掉结尾的年份"""
    series = os.path.basename(os.path.dirname(season_path))
    pat = r'\(\d{4}\)$'
    res = re.search(pat, series)
    if res:
        series = series[:-6].strip()
    return series
