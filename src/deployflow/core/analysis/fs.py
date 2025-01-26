import os
from typing import Callable

"""
This module provides utilities to interact with the file system or remote repositories.

The `init_target` function initializes a target (a directory, a zip file, a tar file, or a Git repository) and returns
three functions: `ls`, `cat`, and `close`.
"""


def _onerror(func, path, exc_info):
    import stat
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def _process_ls_items(items: list[str], isdir: Callable[[str], bool] = lambda _: False) -> list[str]:
    return [name + ('/' if isdir(name) else '') for name in items]


def _init_repo(repo_url: str) -> tuple[Callable[[str | None], list[str]], Callable[[str], str], Callable[[], None]]:
    from git import Repo
    import os
    import time
    import shutil

    temp_dir = "".join(x for x in repo_url.split("/")[-1] if x.isalnum()) + str(hash(time.time()))
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, onerror=_onerror)
    try:
        repo = Repo.clone_from(repo_url, temp_dir, no_checkout=True, depth=1, filter=['blob:none'])

        def ls(subdir: str = None) -> list[str]:
            if subdir:
                if subdir.endswith('/'):
                    subdir = subdir[:-1]
                files = [item.path for item in repo.commit().tree[subdir].traverse(depth=1)]

                def is_dir(path):
                    return repo.commit().tree[path].type == 'tree'
            else:
                files = [item.path for item in repo.commit().tree.traverse(depth=1)]

                def is_dir(path):
                    return repo.commit().tree[path].type == 'tree'
            return _process_ls_items(files, is_dir)

        def cat(file_path: str) -> str:
            sparse_checkout_file = os.path.join(temp_dir, '.git', 'info', 'sparse-checkout')
            with open(sparse_checkout_file, 'w') as f:
                f.write(f'/{file_path}\n')
            repo.git.config('core.sparseCheckout', 'true')
            repo.git.checkout()
            with open(temp_dir + "/" + file_path, 'r', encoding='utf8') as f:
                content = f.read()
            return content

        def close():
            repo.close()
            shutil.rmtree(temp_dir, onerror=_onerror)

        return ls, cat, close
    except Exception as e:
        raise ValueError(f"Failed to clone repository: {e}")


def _init_dir(dir_path: str) -> tuple[Callable[[str | None], list[str]], Callable[[str], str], Callable[[], None]]:
    _dir = dir_path if dir_path.endswith('/') else dir_path + '/'

    def ls(subdir: str = None) -> list[str]:
        items = os.listdir(_dir + subdir if subdir else _dir)
        if subdir:
            subdir = subdir if subdir.endswith('/') else subdir + '/'
            items = [subdir + item for item in items]
            print(items)

        def is_dir(name):
            return os.path.isdir(_dir + name)

        return _process_ls_items(items, is_dir)

    def cat(file_path: str) -> str:
        with open(_dir + file_path, 'r', encoding='utf8') as f:
            return f.read()

    def close():
        pass

    return ls, cat, close


def _init_zip(archive_path: str) -> tuple[Callable[[str | None], list[str]], Callable[[str], str], Callable[[], None]]:
    import zipfile
    if archive_path.startswith("http"):
        import requests
        import io
        response = requests.get(archive_path)
        zip_ref = zipfile.ZipFile(io.BytesIO(response.content))
    else:
        zip_ref = zipfile.ZipFile(archive_path, "r")

    def ls(subdir: str = None) -> list[str]:
        items = zip_ref.namelist()
        if not subdir:
            items = [item for item in items if not '/' in item or (item.endswith('/') and item.count('/') == 1)]
        else:
            subdir = subdir if subdir.endswith('/') else subdir + '/'
            items = [item for item in items if item.startswith(subdir) and item != subdir  # is not the directory itself
                     and (item[len(subdir):].count('/') == 0 or  # is file
                          (item[len(subdir):].endswith('/') and item[len(subdir):].count('/') == 1))]  # is directory

        def is_dir(name):
            return False  # zip already has / at the end of directory names

        return _process_ls_items(items, is_dir)

    def cat(file_path: str) -> str:
        with zip_ref.open(file_path) as f:
            return f.read().decode("utf-8")

    def close():
        zip_ref.close()

    return ls, cat, close


def _init_tar(archive_path: str) -> tuple[Callable[[str | None], list[str]], Callable[[str], str], Callable[[], None]]:
    import tarfile
    if archive_path.startswith("http"):
        import requests
        import io
        response = requests.get(archive_path)
        tar_ref = tarfile.open(fileobj=io.BytesIO(response.content),
                               mode="r:" if archive_path.endswith(".tar") else "r:gz")
    else:
        tar_ref = tarfile.open(archive_path, "r:" if archive_path.endswith(".tar") else "r:gz")

    def ls(subdir: str = None) -> list[str]:
        items = tar_ref.getnames()
        if not subdir:
            items = [item for item in items if not '/' in item]
        else:
            subdir = subdir if subdir.endswith('/') else subdir + '/'
            items = [item for item in items if item.startswith(subdir) and item != subdir  # is not the directory itself
                     and item[len(subdir):].count('/') == 0]  # is file (tar does not have / at the end of directory

        def is_dir(name):
            return tar_ref.getmember(name).isdir()

        return _process_ls_items(items, is_dir)

    def cat(file_path: str) -> str:
        with tar_ref.extractfile(file_path) as f:
            return f.read().decode("utf-8")

    def close():
        tar_ref.close()

    return ls, cat, close


def identify_target(target: str) -> tuple[str, str]:
    target = target.replace("\\", "/")
    target = target[:-1] if target.endswith("/") else target
    if (target.startswith("http") and target.endswith(".git")) or target.startswith("git@"):
        return "git", target.split("/")[-1]
    elif target.endswith(".zip"):
        return "zip", target.split("/")[-1].replace(".zip", "")
    elif target.endswith(".tar.gz") or target.endswith(".tar"):
        return "tar", target.split("/")[-1].replace(".tar.gz", "").replace(".tar", "")
    elif os.path.isdir(target):
        return "dir", target.split("/")[-1]
    else:
        raise ValueError("Unsupported target type")


def init_target(target: str) -> tuple[Callable[[str | None], list[str]], Callable[[str], str], Callable[[], None]]:
    if (target.startswith("http") and target.endswith(".git")) or target.startswith("git@"):
        return _init_repo(target)
    elif target.endswith(".zip"):
        return _init_zip(target)
    elif target.endswith(".tar.gz") or target.endswith(".tar"):
        return _init_tar(target)
    elif os.path.isdir(target):
        return _init_dir(target)
    else:
        raise ValueError("Unsupported target type")


def copy_target(target: str, dest: str):
    import os
    import shutil
    if os.path.exists(dest):
        print(f"Destination directory {dest} already exists. Skipping copy.")
        return
    os.makedirs(dest)
    if (target.startswith("http") and target.endswith(".git")) or target.startswith("git@"):
        from git import Repo
        Repo.clone_from(target, dest)
    elif target.endswith(".zip"):
        import zipfile
        if target.startswith("http"):
            import requests
            import io
            response = requests.get(target)
            target = io.BytesIO(response.content)

        with zipfile.ZipFile(target, 'r') as zip_ref:
            zip_ref.extractall(dest)
    elif target.endswith(".tar.gz") or target.endswith(".tar"):
        import tarfile
        if target.startswith("http"):
            import requests
            import io
            response = requests.get(target)
            target = io.BytesIO(response.content)
        with tarfile.open(target, 'r:*') as tar_ref:
            tar_ref.extractall(dest)
    elif os.path.isdir(target):
        shutil.copytree(target, dest, dirs_exist_ok=True)
    else:
        raise ValueError("Unsupported target type")
