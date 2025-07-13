import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil

BLENDER_VERSION = "4.4.3"
BLENDER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../blender'))

class BlenderManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.blender_path = None
        self.ensure_blender()

    def get_blender_path(self):
        """返回Blender可执行文件路径"""
        return self.blender_path

    def ensure_blender(self):
        """确保blender已安装，若无则自动下载（仅win/linux）"""
        if self.system == 'windows':
            exe_path = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-windows-x64', 'blender.exe')
            if not os.path.exists(exe_path):
                self._download_and_extract_windows()
            self.blender_path = exe_path
        elif self.system == 'linux':
            exe_path = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-linux-x64', 'blender')
            if not os.path.exists(exe_path):
                self._download_and_extract_linux()
            self.blender_path = exe_path
        elif self.system == 'darwin':
            # macOS 需手动放置
            app_path = os.path.join(BLENDER_DIR, 'Blender.app', 'Contents', 'MacOS', 'Blender')
            if not os.path.exists(app_path):
                print('请手动下载Blender 4.4.3并放置到blender/Blender.app')
            self.blender_path = app_path
        else:
            raise RuntimeError(f'不支持的系统: {self.system}')

    def _download_and_extract_windows(self):
        # url = f'https://www.blender.org/download/release/Blender{BLENDER_VERSION[:3]}/blender-{BLENDER_VERSION}-windows-x64.zip'
        url = "https://download.blender.org/release/Blender4.4/blender-4.4.3-windows-x64.zip"
        zip_path = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-windows-x64.zip')
        extract_dir = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-windows-x64')
        os.makedirs(BLENDER_DIR, exist_ok=True)
        print(f"Downloading Blender for Windows: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
            out_file.write(response.read())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(BLENDER_DIR)
        os.remove(zip_path)
        print(f"Blender解压完成: {extract_dir}")

    def _download_and_extract_linux(self):
        # url = f'https://www.blender.org/download/release/Blender{BLENDER_VERSION[:3]}/blender-{BLENDER_VERSION}-linux-x64.tar.xz'
        # https://www.blender.org/download/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz/
        url = "https://mirror.freedif.org/blender/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz"
        tar_path = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-linux-x64.tar.xz')
        extract_dir = os.path.join(BLENDER_DIR, f'blender-{BLENDER_VERSION}-linux-x64')
        os.makedirs(BLENDER_DIR, exist_ok=True)
        print(f"Downloading Blender for Linux: {url}")
        urllib.request.urlretrieve(url, tar_path)
        with tarfile.open(tar_path, 'r:xz') as tar_ref:
            tar_ref.extractall(BLENDER_DIR)
        os.remove(tar_path)
        print(f"Blender解压完成: {extract_dir}") 