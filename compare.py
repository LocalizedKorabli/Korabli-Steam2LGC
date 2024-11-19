import os
import hashlib
import zipfile
import fnmatch

# 定义需要排除的目录和文件模式
EXCLUDED_DIRS = ['profile', 'replays', 'updates', 'GameCheck', 'Reports', 'crashes', 'l10n_installer', 'screenshot', 'res_mods', 'l10n']
# EXCLUDED_FILES = ['*.tmp', '*.log', 'exclude_file.txt']
EXCLUDED_FILES = ['*.tmp', '*.log', 'exclude_file.txt']

def get_file_hash(filepath):
    """计算文件的 SHA-256 哈希值，用于比较文件内容是否一致"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def is_excluded(file_path, root):
    """判断文件或目录是否需要排除"""
    # 检查是否在排除的目录中
    for excluded_dir in EXCLUDED_DIRS:
        if os.path.commonpath([os.path.join(root, excluded_dir)]) in os.path.commonpath([file_path]):
            return True
    # 检查文件名是否匹配排除模式
    for pattern in EXCLUDED_FILES:
        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True
    return False

def get_all_files(directory: str):
    """获取目录中所有文件的相对路径（递归，并按排除规则过滤）"""
    all_files = {}
    for root, dirs, files in os.walk(directory):
        # 排除指定的目录
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d), root)]
        for file in files:
            if not is_excluded(os.path.join(root, file), root):
                rel_path = os.path.relpath(os.path.join(root, file), directory)
                all_files[rel_path] = os.path.join(root, file)
    return all_files

def compare_directories(dir_a: str, dir_b: str):
    files_a = get_all_files(dir_a)
    files_b = get_all_files(dir_b)
    
    # ① A有而B无的文件
    only_in_a = set(files_a.keys()) - set(files_b.keys())
    
    # ② A无而B有的文件
    only_in_b = set(files_b.keys()) - set(files_a.keys())
    
    # ③ A、B都有但内容不一致的文件
    common_files = set(files_a.keys()) & set(files_b.keys())
    content_diff_files = []
    for file in common_files:
        file_a_path = files_a[file]
        file_b_path = files_b[file]
        if get_file_hash(file_a_path) != get_file_hash(file_b_path):
            content_diff_files.append(file)
    
    return list(only_in_a), list(only_in_b), content_diff_files

def create_zip_from_files(target_dir, files_to_zip, output_zip_path):
    """将指定文件压缩到 ZIP 文件中，保留原文件结构"""
    os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            abs_path = str(os.path.join(target_dir, file))
            if os.path.isfile(abs_path):
                zipf.write(abs_path, arcname=file)
    print(f'\n压缩完成，输出文件: {output_zip_path}')

def main():
    dir_a = input('请输入目录A的路径: ').strip()
    dir_b = input('请输入目录B的路径: ').strip()
    output_zip_a = 'output/a.zip'
    
    if not os.path.isdir(dir_a) or not os.path.isdir(dir_b):
        print('其中一个目录路径无效，请检查后重试！')
        return
    
    # 比较两个目录
    only_in_a, only_in_b, content_diff_files = compare_directories(dir_a, dir_b)

    # 创建 ZIP 文件
    create_zip_from_files(
        dir_a,
        only_in_a + content_diff_files,
        'output/a.zip'
    )

    create_zip_from_files(
        dir_b,
        only_in_b + content_diff_files,
        'output/b.zip'
    )

    print(f'\n① A有而B无的文件:')
    for file in only_in_a:
        print(file)

    print(f'\n② A无而B有的文件:')
    for file in only_in_b:
        print(file)
    
    print(f'\n③ A、B都有但内容不一致的文件:')
    for file in content_diff_files:
        print(file)

if __name__ == '__main__':
    main()
