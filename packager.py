import PyInstaller.__main__
import os

cmd = "echo hello world"
os.system(cmd)

PyInstaller.__main__.run([
    'tra.py',
    '--onefile',
    '--windowed'
])
