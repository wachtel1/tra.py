import PyInstaller.__main__
import os

cmd = "echo ##teamcity[blockClosed name='Python run in Venv']"
os.system(cmd)

PyInstaller.__main__.run([
    'tra.py',
    '--onefile',
    '--windowed'
])
