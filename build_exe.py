import PyInstaller.__main__
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--name=BOJ-Graph',
    '--onefile',
    '--windowed',
    '--icon=NONE',
    f'--add-data={os.path.join(project_root, "domain")}{os.pathsep}domain',
    f'--add-data={os.path.join(project_root, "services")}{os.pathsep}services',
    f'--add-data={os.path.join(project_root, "gui")}{os.pathsep}gui',
    '--hidden-import=PyQt5',
    '--hidden-import=matplotlib',
    '--hidden-import=bs4',
    '--hidden-import=requests',
    '--hidden-import=dotenv',
    '--collect-all=matplotlib',
    '--collect-all=PyQt5',
    '--noupx',
    '--clean',
])
