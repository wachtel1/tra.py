import ast
from pathlib import Path
import webbrowser


def listToStr(list):
    return ", ".join(list)


def strToList(string):
    return list(string.split(", "))


def openConfigFile(configPath):
    if Path.is_file(configPath):
        webbrowser.open(configPath)


def getConfigPath():
    return Path(str(Path.home()) + "/.config/trapy.config")


def readDefaultConfig():
    with open("default.config", "r", encoding="utf-8") as f:
        t = f.read()
    settings = ast.literal_eval(t)
    return settings


def writeConfig(settings, configPath):
    t = str(settings)
    with open(str(configPath), "w", encoding="utf-8") as f:
        f.write(t)


def readConfig(configPath):
    if Path.is_file(configPath):
        with open(str(configPath), "r", encoding="utf-8") as f:
            t = f.read()
        settings = ast.literal_eval(t)
        defaultSettings = readDefaultConfig()
        if defaultSettings["version"] != settings["version"]:
            settings = defaultSettings
            writeConfig(settings, configPath)
    else:
        settings = readDefaultConfig()
        writeConfig(settings, configPath)
    return settings
