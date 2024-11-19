import os
import subprocess
import sys
import urllib.request
import webbrowser
import zipfile

import requests
from pathlib import Path
from typing import Optional, Tuple

version = '0.0.1'

intro = f'''
战舰世界莱服Steam端→LGC端转换器
Copyright 2024 LocalizedKorabli
基于GNU GPL-3.0许可证分发
版本：{version}
源码：https://github.com/LocalizedKorabli/Korabli-Steam2LGC
国内访问：https://gitee.com/localized-korabli/Korabli-Steam2LGC

按回车键继续。
'''

info_dir_current = '''
第1/3步：
检测到程序运行目录可能是战舰世界莱服安装目录，是否直接进行转换操作？
若是，请直接按下回车；
若否，请输入需要进行转换操作的目录路径再按回车。
（提示，您可以尝试将目录根文件夹直接拖入本页面中来快速填写路径）

请输入：
'''

info_dir_normal = '''
第1/3步：
请输入需要进行转换操作的目录路径再按回车。
（提示，您可以尝试将目录根文件夹直接拖入本页面中来快速填写路径）

请输入：
'''

info_dir_retry = '''
第1/3步：
目录不存在或不是有效的战舰世界莱服安装目录，请检查后重新输入。

请输入：
'''

info_local_file_input = '''
第2/3步：
请输入本地转换包文件的路径再按回车。
（提示，您可以尝试将转换包文件直接拖入本页面中来快速填写路径）
若您需要下载，请留空再按回车，将会弹出蓝奏云下载网页。

请输入：
'''


info_will_execute = '''
第3/3步：
即将应用转换包。
若之后游戏不能正常运行，请通过LGC或Steam“验证游戏文件的完整性”。

按回车键继续。
'''


metadata_download_choice = '''
第2/3步：
请选择转换包的来源（留空则默认选择Gitee线路）：
1. 通过Gitee线路下载（大陆用户）
2. 通过GitHub线路下载（港澳台/海外用户）
3. 本地文件

请选择：
''', 1, 3



const_lanzou_url = 'https://tapio.lanzn.com/b0nym5huh'

def run() -> None:
    input(intro)
    dir_choice = input(info_dir_current if check_dir_validity(Path('.')) else info_dir_normal)
    while not check_dir_validity(Path(dir_choice)):
       dir_choice = input(info_dir_retry)
    src_choice = get_num_choice(metadata_download_choice)
    downloaded = download_or_await_input(src_choice)
    for retry_count in range(5):
        if downloaded is not None:
            break
        print('第{}次重试…'.format(str(retry_count + 1)))
        downloaded = download_or_await_input(src_choice)
    input(info_will_execute)
    try:
        with zipfile.ZipFile(downloaded, 'r') as cvp:
            process_possible_gbk_zip(cvp)
            cvp.extractall(dir_choice)
        print('转换包应用成功！')
        input('按回车键启动游戏。')
        subprocess.run(Path(dir_choice).joinpath('lgc_api.exe'))
    except Exception as cvp_ex:
        print(f'应用转换包时出现错误。错误信息：{cvp_ex}')
        input('按回车键退出。')


def download_or_await_input(src_choice: int) -> Optional[Path]:
    if src_choice == 3:
        local_file = input(info_local_file_input)
        while not Path(local_file).is_file():
            should_popup = local_file == ''
            if should_popup:
                webbrowser.open(const_lanzou_url)
            else:
                print('文件不存在，请检查后重新输入。')
            local_file = input(info_local_file_input)
            if not check_cvp_validity(Path(local_file)):
                local_file = ''
        return Path(local_file)
    else:
        is_gitee = src_choice == 1
        print('开始连接{}线路…'.format('Gitee' if is_gitee else 'GitHub'))
        proxies = {scheme: proxy for scheme, proxy in urllib.request.getproxies().items()}
        output_file = get_master_dir().joinpath('lgc.zip')
        try:
            d_url = ('https://{}/Korabli-Steam2LGC/raw/main/packages/lgc.zip'
                     .format('gitee.com/localized-korabli' if is_gitee else 'github.com/LocalizedKorabli'))
            response = requests.get(
                d_url, stream=True, proxies=proxies, timeout=5000
            )
            status = response.status_code
            if status == 200:
                print('连接成功，下载中…')
                with open(output_file, 'wb') as f:
                    for ck in response.iter_content(chunk_size=1024):
                        if ck:
                            f.write(ck)
                print('下载完成！')
                return output_file if check_cvp_validity(output_file) else None
            else:
                print(f'连接失败，状态码：{status}')
                return None
        except Exception as d_ex:
            print(f'下载时发生错误。错误信息：{d_ex}')
            return None


def check_dir_validity(target_dir: Path) -> bool:
    if not target_dir.is_dir():
        return False
    return target_dir.joinpath('Korabli.exe').is_file() and target_dir.joinpath('bin').is_dir()


def check_cvp_validity(file_path: Path) -> bool:
    print('检查转换包可用性…')
    try:
        with zipfile.ZipFile(file_path, 'r') as cvp:
            process_possible_gbk_zip(cvp)
            filenames = [info.filename for info in cvp.filelist]
            for file_name in filenames:
                if 'lgc_api.exe' in file_name:
                    return True
            print('指定的转换包未包含必需的文件（lgc_api.exe）！')
            return False
    except Exception as cvp_ex:
        print(f'检查转换包可用性时发生错误。错误信息：{cvp_ex}')
        return False


def get_num_choice(choice_metadata: Tuple[str, int, int]) -> int:
    raw_choice = None
    while raw_choice is None:
        raw_choice = parse_num_choice(input(choice_metadata[0]), choice_metadata[1], choice_metadata[2])
    return raw_choice


def parse_num_choice(raw_choice: str, min_num: int, max_num: int) -> Optional[int]:
    try:
        parsed_choice = int(raw_choice)
        return parsed_choice if min_num <= parsed_choice <= max_num else None
    except ValueError:
        return None

def get_master_dir() -> Path:
    master_dir = Path('korabli_client_converter')
    os.makedirs(master_dir, exist_ok=True)
    return master_dir


def process_possible_gbk_zip(zip_file: zipfile.ZipFile) -> zipfile.ZipFile:
    name2info = zip_file.NameToInfo
    for name, info in name2info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name2info[name]
            name2info[real_name] = info
    return zip_file



if not sys.executable.endswith('python.exe'):
    os.chdir(Path(sys.executable).parent)
try:
    run()
except Exception as ex:
    print(f'发生错误，错误信息：{ex}')
    input('若需反馈问题，请在保存错误信息的截图后按回车键打开反馈网页。')
    webbrowser.open('https://gitee.com/localized-korabli/Korabli-Steam2LGC/issues')