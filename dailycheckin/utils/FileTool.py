import os
import shutil
import zipfile
from typing import List


def copy_file(src_path, dest_path, print_log=False):
    if os.path.exists(src_path):
        dst_dir = os.path.dirname(dest_path)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        if print_log:
            print(f'copy from:{src_path} to:{dest_path}')
        shutil.copyfile(src_path, dest_path)
    else:
        print("path not exit:", src_path)


# 删除文件
def remove_file(path):
    if os.path.exists(path):
        print("rmove path:" + path)
        os.remove(path)


def remove_path(path):
    if os.path.exists(path):
        print("rmove path:" + path)
        shutil.rmtree(path, True)


def remove_path_ignore(path, ignorepathlist: List[str]):
    print("rmove path ingore:" + path + f'{ignorepathlist}')
    if os.path.exists(path):
        for file in os.listdir(path):
            path_tmp = os.path.join(path, file)
            if os.path.isdir(path_tmp):
                abs_tmppath = os.path.abspath(path_tmp)
                if abs_tmppath in ignorepathlist:
                    continue
                else:
                    shutil.rmtree(path_tmp, True)
                    print(f'remove {path_tmp}')
            else:
                os.remove(path_tmp)


def copy_folder_to(srcpath, destpath):
    if os.path.exists(srcpath):
        for file in os.listdir(srcpath):
            path_tmp = os.path.join(srcpath, file)
            dst_path_tmp = os.path.join(destpath, file)
            print(f'copy {path_tmp} to {dst_path_tmp}')
            if os.path.isdir(path_tmp):
                shutil.copytree(path_tmp, dst_path_tmp)
            else:
                shutil.copyfile(path_tmp, dst_path_tmp)


def remove_dir_child(path):
    if os.path.exists(path) and os.path.isdir(path):
        for file in os.listdir(path):
            from_file = os.path.join(path, file)
            if os.path.isdir(from_file):  # 如果是文件夹，递归
                shutil.rmtree(from_file)
            else:
                os.remove(from_file)


# to_file文件时间新 返回false
# 比较文件新旧
def cmp_file_new(from_file, to_file):
    from_file_modify_time = round(os.stat(from_file).st_mtime, 1)  # 这里精确度为0.1秒
    to_file_modify_time = round(os.stat(to_file).st_mtime, 1)  # 拿到　两边文件的最后修改时间
    if from_file_modify_time > to_file_modify_time:  # 比较　两边文件的　最后修改时间
        return True
    return False


# 同步两个文件夹以原文件为主，根据时间戳 source_folder:参照文件夹 target_folder：目录文件夹


def sync_folder(source_folder, target_folder, force_copy=False, need_copy_callback=None):
    for file in os.listdir(source_folder):
        from_file = os.path.join(source_folder, file)
        to_file = os.path.join(target_folder, file)
        if os.path.isdir(from_file):  # 如果是文件夹，递归
            if force_copy:
                if not os.path.exists(to_file):
                    os.mkdir(to_file)
            sync_folder(from_file, to_file, force_copy, need_copy_callback)
        else:
            copy_flag = False
            if force_copy:
                copy_flag = True
            else:
                if need_copy_callback is not None:
                    if need_copy_callback(from_file):
                        copy_flag = True

                else:
                    if os.path.exists(to_file) == False:
                        copy_flag = True
                    elif cmp_file_new(from_file, to_file):
                        copy_flag = True
            if copy_flag:
                shutil.copy2(from_file, target_folder)  # 执行copy。。。
                print(f'copy {file} from {from_file} to {to_file}')  # 上面注释掉的２种写法都对。现在用的这种，更像是一句话。。。


def find_dir(path, end_str):
    for root, dir_names, _ in os.walk(path):
        for dir_name in dir_names:
            if dir_name.endswith(end_str):
                return os.path.join(root, dir_name)
    return ""


def find_file_by_ext(path, ext):
    g = os.walk(path)
    for path2, _, file_list in g:
        for file_name in file_list:
            if file_name.endswith(ext):
                return os.path.join(path2, file_name)

    return ""


    #压缩文件
def zip_dir(dirname, zipfilename):
    filelist = []
    #Check input ...
    print("Start to zip %s to %s ..." % (dirname, zipfilename))
    if not os.path.exists(dirname):
        print("Dir/File %s is not exist, Press any key to quit..." % dirname)
        return
    if os.path.exists(zipfilename):
        os.remove(zipfilename)

    #Get file(s) to zip ...
    if os.path.isfile(dirname):
        filelist.append(dirname)
        dirname = os.path.dirname(dirname)
    else:
        #get all file in directory
        for root, dirlist, files in os.walk(dirname):
            for filename in files:
                filelist.append(os.path.join(root, filename))

    #Start to zip file ...
    destZip = zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED)
    for eachfile in filelist:
        destfile = eachfile[len(dirname):]
        #print("Zip file %s..." % destfile)
        destZip.write(eachfile, destfile)
    destZip.close()
    print("Zip folder succeed!")


# # 压缩文件
# def zip_dir(path, zip_path):
#     file_list = []
#     # Check input ...
#     print(f'Start to zip {path} to {zip_path} ...')
#     if not os.path.exists(path):
#         print(f'Dir/File {path} is not exist, Press any key to quit...')
#         return
#     if os.path.exists(zip_path):
#         os.remove(zip_path)

#     # Get file(s) to zip ...
#     if os.path.isfile(path):
#         file_list.append(path)
#         path = os.path.dirname(path)
#     else:
#         # get all file in directory
#         for root, _, files in os.walk(path):
#             for filename in files:
#                 file_list.append(os.path.join(root, filename))

#     # Start to zip file ...
#     with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as dest_zip:
#         for file_item in file_list:
#             file_path = file_item[len(path):]
#             dest_zip.write(file_item, file_path)
#         print("Zip folder succeed!")

# 解压缩


def unzip_dir(zip_path, dest_path):
    print(f'Start to unzip file {zip_path} to folder {dest_path} ...')
    # Check input ...
    if not os.path.exists(zip_path):
        print(zip_path + " is not exit")
        return
    # 删除旧的
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path, True)
    os.mkdir(dest_path)

    # Start extract files ...
    with zipfile.ZipFile(zip_path, "r") as src_zip:
        for src_path in src_zip.namelist():
            dst_path = os.path.normpath(os.path.join(dest_path, src_path))
            dst_dir = os.path.dirname(dst_path)
            print(f'Unzip file src_path:{src_path} dst_dir:{dst_dir} dst_path:{dst_path}')
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            if src_path.endswith("/") and not os.path.exists(dst_path):
                os.makedirs(dst_path)
            else:
                with open(dst_path, "wb") as fd:
                    fd.write(src_zip.read(src_path))
        print("Unzip file succeed!")
