import os


def get_season(parent_folder_name):
    """
    获取季数
    """

    # 兼容
    # 'Season 2'
    # 'Season2'
    # 's2'
    # 'S2'
    season = None

    if parent_folder_name == 'Specials':
        # 兼容SP
        return '0'

    try:
        if 'season' in parent_folder_name.lower():
            s = str(int(parent_folder_name.lower().replace('season', '').strip()))
            season = s.zfill(2)
        elif parent_folder_name.lower()[0] == 's':
            season = str(int(parent_folder_name[1:])).strip().zfill(2)
    except:
        pass

    return season


def get_season_cascaded(full_path):
    """
    逐级向上解析目录季数
    """
    full_path = os.path.abspath(full_path).replace('\\', '/').replace('//', '/')
    parent_folder_names = full_path.split('/')[::-1]
    season = None
    for parent_folder_name in parent_folder_names:
        season = get_season(parent_folder_name)
        if season:
            break
    return season


def get_season_path(file_path):
    """
    获取season目录
    """
    b = os.path.dirname(file_path.replace('\\', '/'))
    season_path = None
    while b:
        if not '/' in b:
            break
        b, fo = b.rsplit('/', 1)
        offset = None
        if get_season(fo):
            season_path = b + '/' + fo
    return season_path
