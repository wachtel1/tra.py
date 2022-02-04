import os
import sys
import res
import microsoftranslate_config
import libretranslate_config
import formatHelper
import configHelper
import styleHelper
from microsofttranslate import MicrosoftTranslator
from libretranslatepy import LibreTranslateAPI
from googletrans import Translator
import pyperclip
from PyQt5.QtWidgets import *
from PyQt5.QtCore import (
    QDir,
    QAbstractNativeEventFilter,
    QAbstractEventDispatcher,
    QPoint,
    Qt,
    pyqtSignal,
    QCoreApplication,
    QProcess,
)
from PyQt5.QtGui import QFontDatabase, QKeySequence, QFocusEvent, QTextCursor
from pyqtkeybind import keybinder

global translator

configPath = ""
settings = {}

tips = [
    "Type / to toggle cheatsheet",
    "Press ESC to exit EDIT MODE",
    "[M]acro",
    "[N]acro",
    "[P]aste",
    "[F]ormat",
    "[G]ormat",
    "[T]ranslate",
    "[Y]ank",
    "Delete [E]mpty lines",
    "Delete new [L]ines",
    "Delete [S]paces",
    "[D]elete text",
    "Open [C]onfiguration file",
    "Override [T]ranslation",
    "Show [C]onfiguration dialog"
]


def reload(mainWindow):
    QCoreApplication.quit()
    QProcess.startDetached(sys.executable, sys.argv)
    mainWindow.showWindow()


class WinEventFilter(QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0


def load_fonts_from_dir(directory):
    families = set()
    for fi in QDir(directory).entryInfoList(["*.ttf"]):
        _id = QFontDatabase.addApplicationFont(fi.absoluteFilePath())
        families |= set(QFontDatabase.applicationFontFamilies(_id))
    return families


class TrapyTextEdit(QPlainTextEdit):
    focusInSignal = pyqtSignal()
    focusOutSignal = pyqtSignal()

    def focusInEvent(self, e: QFocusEvent) -> None:
        self.focusInSignal.emit()
        return super().focusInEvent(e)

    def focusOutEvent(self, e: QFocusEvent) -> None:
        self.focusOutSignal.emit()
        return super().focusOutEvent(e)


class ModeLabel(QLabel):
    def setInput(self):
        self.setText("EDIT:INPUT")
        self.setStyleSheet("background-color: " +
                           settings["visuals"]["editInputMode"] + ";")

    def setOutput(self):
        self.setText("EDIT:OUTPUT")
        self.setStyleSheet("background-color: " +
                           settings["visuals"]["editOutputMode"] + ";")

    def setNormal(self):
        self.setText("NORMAL")
        self.setStyleSheet("background-color: " +
                           settings["visuals"]["normalMode"] + ";")


class HelpDialog(QMessageBox):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.initUI()
        self.setWindowTitle("tra.py help")

    def initUI(self):
        self.setStyleSheet("font-size: 12px; width: 800px;")
        self.setTextFormat(Qt.RichText)
        self.setText("<p>TRANSLATION SETTINGS:</p><p>- the source language is autodected when translating with T</p><p>- the default target language for all of the detected languages is set in default target language</p><p>- language pairs can be used to override the default target language</p><p>- in language pairs, the first language of the source will be translated to the first language of the target and so on</p><p>- when specifying multiple languages each language should be separated by \", \"(comma followed by a space)</p><p>- override translation (Ctrl+T) can be used to specify both target and source language</p><p>- to autodetect the source language in override mode use \"auto\" keyword</p><p>- all languages must be specified in ISO 639-1 (two letter codes) format</p><p>FORMAT:</p><p>- \"save new lines after special symbols\" option lets you list all special symbols after which you want a new line to be saved when using the \"delete new lines\" function</p><p>- this setting is effective in Format, Gormat and when using \"delete new lines\" function by itself</p><p>VISUALS:</p><p>- all colors must be specified in HEX format, without transparency</p><p>- border radius must follow Npx format</p><p>I BROKE IT:</p><p>- go to ~/.config/ and delete trapy.config file to hard reset everything</p><br><p>© Anton Vakhtel (_was) and contributors</p><p>licensed under GNU GPLv3 license</p><p><a href='https://github.com/was-games/tra.py' style=\"color:" +
                     settings["visuals"]["buttonText"] + "\">GitHub</a></p>")


class ConfigDialog(QDialog):
    translatorSetting = None
    translatorWarning = None
    translatorRequireAPIKey = None
    translatorApiKey = None
    translatorUrl = None
    translatorLocation = None

    defaultTargetLanguage = None
    languagePairsSource = None
    languagePairsTarget = None
    overrideSource = None
    overrideTarget = None

    macroPaste = None
    macroFormat = None
    macroGormat = None
    macroYank = None
    macroShow = None

    nacroPaste = None
    nacroFormat = None
    nacroGormat = None
    nacroYank = None
    nacroShow = None

    formatDelEmptyLines = None
    formatDelNewLines = None
    formatDelSpaces = None

    gormatDelEmptyLines = None
    gormatDelNewLines = None
    gormatDelSpaces = None

    saveNewLinesAfterSpecialSymbols = None
    specialSymbols = None

    borderRadius = None
    background = None
    textBackground = None
    text = None
    buttonText = None
    buttonHover = None
    buttonClicked = None
    normalMode = None
    editInputMode = None
    editOutputMode = None

    pasteShortcut = None
    pasteEnabled = None
    macroShortcut = None
    macroEnabled = None
    nacroShortcut = None
    nacroEnabled = None

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.initUI(parent)
        self.setWindowTitle("tra.py configuration editor")

    def initUI(self, parent):
        mainLayout = QVBoxLayout()
        dialogButtons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Help)
        dialogButtons.accepted.connect(lambda: self.accept(parent))
        dialogButtons.rejected.connect(self.reject)
        dialogButtons.helpRequested.connect(self.help)

        contentsWidget = QWidget()
        contentsWidget.setMinimumHeight(400)
        contentsWidget.setMinimumWidth(800)
        contentsWidget.setStyleSheet("font-size: 12px;")
        contentsLayout = QVBoxLayout()

        generalSectionName = QLabel("---GENERAL---")
        generalSectionName.setStyleSheet(
            "color: " + settings["visuals"]["buttonText"] + ";")

        generalSectionLayout = QHBoxLayout()
        generalLeftPart = QVBoxLayout()
        generalLeftPart.setContentsMargins(8, 0, 8, 0)
        translatorLabel = QLabel("Translator")
        self.translatorSetting = QComboBox()
        self.translatorSetting.addItem("Microsoft Translator API")
        self.translatorSetting.addItem("LibreTranslate")
        self.translatorSetting.addItem("Google Translate Web")
        self.translatorSetting.setCurrentIndex(
            self.translatorSetting.findText(settings["translator"]))
        self.translatorWarning = QLabel()
        self.translatorWarning.setWordWrap(True)
        self.translatorWarning.setMaximumWidth(300)
        self.translatorWarning.setMinimumWidth(300)
        self.translatorSetting.currentTextChanged.connect(
            lambda: self.changeTranslatorSettings())

        generalLeftPart.addWidget(translatorLabel)
        generalLeftPart.addWidget(self.translatorSetting)
        generalLeftPart.addWidget(self.translatorWarning)

        generalRightPart = QVBoxLayout()
        generalRightPart.setContentsMargins(8, 0, 8, 0)
        translatorUrlGroup = QHBoxLayout()
        translatorUrlLabel = QLabel("URL")
        self.translatorUrl = QLineEdit()
        translatorUrlGroup.addWidget(translatorUrlLabel)
        translatorUrlGroup.addWidget(self.translatorUrl)
        translatorRequireApiKeyGroup = QHBoxLayout()
        translatorRequireApiKeyLabel = QLabel("Require API Key")
        self.translatorRequireAPIKey = QCheckBox()
        translatorRequireApiKeyGroup.addWidget(self.translatorRequireAPIKey)
        translatorRequireApiKeyGroup.addWidget(
            translatorRequireApiKeyLabel, Qt.AlignLeft)
        translatorApiKeyGroup = QHBoxLayout()
        translatorApiKeyLabel = QLabel("API key")
        self.translatorApiKey = QLineEdit()
        translatorApiKeyGroup.addWidget(translatorApiKeyLabel)
        translatorApiKeyGroup.addWidget(self.translatorApiKey)
        translatorLocationGroup = QHBoxLayout()
        translatorLocationLabel = QLabel("Location")
        self.translatorLocation = QLineEdit()
        translatorLocationGroup.addWidget(translatorLocationLabel)
        translatorLocationGroup.addWidget(self.translatorLocation)

        generalRightPart.addLayout(translatorUrlGroup)
        generalRightPart.addLayout(translatorRequireApiKeyGroup)
        generalRightPart.addLayout(translatorApiKeyGroup)
        generalRightPart.addLayout(translatorLocationGroup)

        generalSectionLayout.addLayout(generalLeftPart)
        generalSectionLayout.addLayout(generalRightPart)

        translationSectionName = QLabel("---TRANSLATION---")
        translationSectionName.setStyleSheet(
            "color: " + settings["visuals"]["buttonText"] + ";")

        translationSectionLayout = QHBoxLayout()
        translationLeftPart = QVBoxLayout()
        translationTargetLanguageGroup = QHBoxLayout()
        translationTargetLanguageLabel = QLabel("Default target language")
        self.translationTargetLanguage = QLineEdit()
        self.translationTargetLanguage.setText(
            settings["translation"]["defaultTargetLanguage"])
        translationTargetLanguageGroup.addWidget(
            translationTargetLanguageLabel)
        translationTargetLanguageGroup.addWidget(
            self.translationTargetLanguage)

        languagePairsLabel = QLabel("Language pairs")
        languagePairsSourceGroup = QHBoxLayout()
        languagePairsSourceLabel = QLabel("Source")
        self.languagePairsSource = QLineEdit()
        self.languagePairsSource.setText(configHelper.listToStr(
            settings["translation"]["languagePairs"]["source"]))
        languagePairsSourceGroup.addWidget(languagePairsSourceLabel)
        languagePairsSourceGroup.addWidget(self.languagePairsSource)
        languagePairsTargetGroup = QHBoxLayout()
        languagePairsTargetLabel = QLabel("Target")
        self.languagePairsTarget = QLineEdit()
        self.languagePairsTarget.setText(configHelper.listToStr(
            settings["translation"]["languagePairs"]["target"]))
        languagePairsTargetGroup.addWidget(languagePairsTargetLabel)
        languagePairsTargetGroup.addWidget(self.languagePairsTarget)

        translationLeftPart.addLayout(translationTargetLanguageGroup)
        translationLeftPart.addWidget(languagePairsLabel)
        translationLeftPart.addLayout(languagePairsSourceGroup)
        translationLeftPart.addLayout(languagePairsTargetGroup)

        translationRightPart = QVBoxLayout()
        overrideLabel = QLabel("Override translation default languages")
        overrideGroup = QVBoxLayout()
        overrideSourceGroup = QHBoxLayout()
        overrideSourceLabel = QLabel("Source")
        self.overrideSource = QLineEdit()
        self.overrideSource.setText(
            settings["translation"]["override"]["defaultSource"])
        overrideSourceGroup.addWidget(overrideSourceLabel)
        overrideSourceGroup.addWidget(self.overrideSource)
        overrideTargetGroup = QHBoxLayout()
        overrideTargetLabel = QLabel("Target")
        self.overrideTarget = QLineEdit()
        self.overrideTarget.setText(
            settings["translation"]["override"]["defaultTarget"])
        overrideTargetGroup.addWidget(overrideTargetLabel)
        overrideTargetGroup.addWidget(self.overrideTarget)

        overrideGroup.addLayout(overrideSourceGroup)
        overrideGroup.addLayout(overrideTargetGroup)

        translationRightPart.addWidget(overrideLabel, 0, Qt.AlignCenter)
        translationRightPart.addLayout(overrideGroup)

        translationSectionLayout.addLayout(translationLeftPart)
        translationSectionLayout.addLayout(translationRightPart)

        macroSectionName = QLabel("---MACRO AND FORMAT---")
        macroSectionName.setStyleSheet(
            "color: " + settings["visuals"]["buttonText"] + ";")

        macroSectionLayout = QHBoxLayout()

        macroGroup = QVBoxLayout()
        macroGroup.setContentsMargins(8, 0, 8, 0)
        macroLabel = QLabel("Macro")
        macroPasteGroup = QHBoxLayout()
        self.macroPaste = QCheckBox()
        self.macroPaste.setChecked(settings["macro"]["runPaste"])
        macroPasteLabel = QLabel("Paste")
        macroPasteGroup.addWidget(self.macroPaste)
        macroPasteGroup.addWidget(macroPasteLabel, Qt.AlignLeft)

        macroFormatGroup = QHBoxLayout()
        self.macroFormat = QCheckBox()
        self.macroFormat.setChecked(settings["macro"]["runFormat"])
        macroFormatLabel = QLabel("Format")
        macroFormatGroup.addWidget(self.macroFormat)
        macroFormatGroup.addWidget(macroFormatLabel, Qt.AlignLeft)

        macroGormatGroup = QHBoxLayout()
        self.macroGormat = QCheckBox()
        self.macroGormat.setChecked(settings["macro"]["runGormat"])
        macroGormatLabel = QLabel("Gormat")
        macroGormatGroup.addWidget(self.macroGormat)
        macroGormatGroup.addWidget(macroGormatLabel, Qt.AlignLeft)

        macroYankGroup = QHBoxLayout()
        self.macroYank = QCheckBox()
        self.macroYank.setChecked(settings["macro"]["runYank"])
        macroYankLabel = QLabel("Yank")
        macroYankGroup.addWidget(self.macroYank)
        macroYankGroup.addWidget(macroYankLabel, Qt.AlignLeft)

        macroShowGroup = QHBoxLayout()
        self.macroShow = QCheckBox()
        self.macroShow.setChecked(settings["macro"]["showWindow"])
        macroShowLabel = QLabel("Show")
        macroShowGroup.addWidget(self.macroShow)
        macroShowGroup.addWidget(macroShowLabel, Qt.AlignLeft)

        macroGroup.addWidget(macroLabel, 0, Qt.AlignCenter)
        macroGroup.addLayout(macroPasteGroup)
        macroGroup.addLayout(macroFormatGroup)
        macroGroup.addLayout(macroGormatGroup)
        macroGroup.addLayout(macroYankGroup)
        macroGroup.addLayout(macroShowGroup)

        nacroGroup = QVBoxLayout()
        nacroGroup.setContentsMargins(8, 0, 8, 0)
        nacroLabel = QLabel("Nacro")
        nacroPasteGroup = QHBoxLayout()
        self.nacroPaste = QCheckBox()
        self.nacroPaste.setChecked(settings["nacro"]["runPaste"])
        nacroPasteLabel = QLabel("Paste")
        nacroPasteGroup.addWidget(self.nacroPaste)
        nacroPasteGroup.addWidget(nacroPasteLabel, Qt.AlignLeft)

        nacroFormatGroup = QHBoxLayout()
        self.nacroFormat = QCheckBox()
        self.nacroFormat.setChecked(settings["nacro"]["runFormat"])
        nacroFormatLabel = QLabel("Format")
        nacroFormatGroup.addWidget(self.nacroFormat)
        nacroFormatGroup.addWidget(nacroFormatLabel, Qt.AlignLeft)

        nacroGormatGroup = QHBoxLayout()
        self.nacroGormat = QCheckBox()
        self.nacroGormat.setChecked(settings["nacro"]["runGormat"])
        nacroGormatLabel = QLabel("Gormat")
        nacroGormatGroup.addWidget(self.nacroGormat)
        nacroGormatGroup.addWidget(nacroGormatLabel, Qt.AlignLeft)

        nacroYankGroup = QHBoxLayout()
        self.nacroYank = QCheckBox()
        self.nacroYank.setChecked(settings["nacro"]["runYank"])
        nacroYankLabel = QLabel("Yank")
        nacroYankGroup.addWidget(self.nacroYank)
        nacroYankGroup.addWidget(nacroYankLabel, Qt.AlignLeft)

        nacroShowGroup = QHBoxLayout()
        self.nacroShow = QCheckBox()
        self.nacroShow.setChecked(settings["nacro"]["showWindow"])
        nacroShowLabel = QLabel("Show")
        nacroShowGroup.addWidget(self.nacroShow)
        nacroShowGroup.addWidget(nacroShowLabel, Qt.AlignLeft)

        nacroGroup.addWidget(nacroLabel, 0, Qt.AlignCenter)
        nacroGroup.addLayout(nacroPasteGroup)
        nacroGroup.addLayout(nacroFormatGroup)
        nacroGroup.addLayout(nacroGormatGroup)
        nacroGroup.addLayout(nacroYankGroup)
        nacroGroup.addLayout(nacroShowGroup)

        formatLayout = QVBoxLayout()
        formatLayout.setContentsMargins(8, 0, 8, 0)
        formatSection = QHBoxLayout()
        formatSection.setContentsMargins(8, 0, 8, 0)
        formatGroup = QVBoxLayout()
        gormatGroup = QVBoxLayout()

        formatLabel = QLabel("Format")
        formatDelEmptyLinesGroup = QHBoxLayout()
        self.formatDelEmptyLines = QCheckBox()
        self.formatDelEmptyLines.setChecked(
            settings["format"]["delEmptyLines"])
        formatDelEmptyLinesLabel = QLabel("Delete empty lines")
        formatDelEmptyLinesGroup.addWidget(self.formatDelEmptyLines)
        formatDelEmptyLinesGroup.addWidget(
            formatDelEmptyLinesLabel, Qt.AlignLeft)

        formatDelNewLinesGroup = QHBoxLayout()
        self.formatDelNewLines = QCheckBox()
        self.formatDelNewLines.setChecked(
            settings["format"]["delNewLines"])
        formatDelNewLinesLabel = QLabel("Delete new lines")
        formatDelNewLinesGroup.addWidget(self.formatDelNewLines)
        formatDelNewLinesGroup.addWidget(
            formatDelNewLinesLabel, Qt.AlignLeft)

        formatDelSpacesGroup = QHBoxLayout()
        self.formatDelSpaces = QCheckBox()
        self.formatDelSpaces.setChecked(
            settings["format"]["delSpaces"])
        formatDelSpacesLabel = QLabel("Delete spaces")
        formatDelSpacesGroup.addWidget(self.formatDelSpaces)
        formatDelSpacesGroup.addWidget(formatDelSpacesLabel, Qt.AlignLeft)

        formatGroup.addWidget(formatLabel, 0, Qt.AlignCenter)
        formatGroup.addLayout(formatDelEmptyLinesGroup)
        formatGroup.addLayout(formatDelNewLinesGroup)
        formatGroup.addLayout(formatDelSpacesGroup)

        gormatLabel = QLabel("Gormat")
        gormatDelEmptyLinesGroup = QHBoxLayout()
        self.gormatDelEmptyLines = QCheckBox()
        self.gormatDelEmptyLines.setChecked(
            settings["gormat"]["delEmptyLines"])
        gormatDelEmptyLinesLabel = QLabel("Delete empty lines")
        gormatDelEmptyLinesGroup.addWidget(self.gormatDelEmptyLines)
        gormatDelEmptyLinesGroup.addWidget(
            gormatDelEmptyLinesLabel, Qt.AlignLeft)

        gormatDelNewLinesGroup = QHBoxLayout()
        self.gormatDelNewLines = QCheckBox()
        self.gormatDelNewLines.setChecked(
            settings["gormat"]["delNewLines"])
        gormatDelNewLinesLabel = QLabel("Delete new lines")
        gormatDelNewLinesGroup.addWidget(self.gormatDelNewLines)
        gormatDelNewLinesGroup.addWidget(
            gormatDelNewLinesLabel, Qt.AlignLeft)

        gormatDelSpacesGroup = QHBoxLayout()
        self.gormatDelSpaces = QCheckBox()
        self.gormatDelSpaces.setChecked(
            settings["gormat"]["delSpaces"])
        gormatDelSpacesLabel = QLabel("Delete spaces")
        gormatDelSpacesGroup.addWidget(self.gormatDelSpaces)
        gormatDelSpacesGroup.addWidget(gormatDelSpacesLabel, Qt.AlignLeft)

        gormatGroup.addWidget(gormatLabel, 0, Qt.AlignCenter)
        gormatGroup.addLayout(gormatDelEmptyLinesGroup)
        gormatGroup.addLayout(gormatDelNewLinesGroup)
        gormatGroup.addLayout(gormatDelSpacesGroup)

        formatSection.addLayout(formatGroup)
        formatSection.addLayout(gormatGroup)

        delNewLinesSection = QVBoxLayout()
        delNewLinesSection.setContentsMargins(8, 16, 8, 0)
        saveNewLinesAfterSpecialSymbolsGroup = QHBoxLayout()
        self.saveNewLinesAfterSpecialSymbols = QCheckBox()
        self.saveNewLinesAfterSpecialSymbols.setChecked(
            settings["delNewLines"]["saveNewLinesAfterSpecialSymbols"])
        saveNewLinesAfterSpecialSymbolsLabel = QLabel(
            "Save new lines after special symbols")
        saveNewLinesAfterSpecialSymbolsGroup.addWidget(
            self.saveNewLinesAfterSpecialSymbols)
        saveNewLinesAfterSpecialSymbolsGroup.addWidget(
            saveNewLinesAfterSpecialSymbolsLabel, Qt.AlignLeft)

        specialSymbolsGroup = QHBoxLayout()
        specialSymbolsLabel = QLabel("Special symbols")
        self.specialSymbols = QLineEdit()
        self.specialSymbols.setText(configHelper.listToStr(
            settings["delNewLines"]["specialSymbols"]))
        self.specialSymbols.setMinimumWidth(400)
        specialSymbolsGroup.addWidget(specialSymbolsLabel)
        specialSymbolsGroup.addWidget(self.specialSymbols)

        delNewLinesSection.addLayout(saveNewLinesAfterSpecialSymbolsGroup)
        delNewLinesSection.addLayout(specialSymbolsGroup)

        formatLayout.addLayout(formatSection)
        formatLayout.addLayout(delNewLinesSection)

        macroSectionLayout.addLayout(macroGroup)
        macroSectionLayout.addLayout(nacroGroup)
        macroSectionLayout.addLayout(formatLayout)

        visualsSectionName = QLabel("---VISUALS AND GLOBAL SHORTCUTS---")
        visualsSectionName.setStyleSheet(
            "color: " + settings["visuals"]["buttonText"] + ";")

        visualsSectionLayout = QHBoxLayout()

        visualsGroup = QHBoxLayout()
        visualsLeftGroup = QVBoxLayout()
        visualsRightGroup = QVBoxLayout()

        borderRadiusGroup = QHBoxLayout()
        borderRadiusLabel = QLabel("Border radius")
        self.borderRadius = QLineEdit()
        self.borderRadius.setText(settings["visuals"]["borderRadius"])
        borderRadiusGroup.addWidget(borderRadiusLabel)
        borderRadiusGroup.addWidget(self.borderRadius)
        visualsLeftGroup.addLayout(borderRadiusGroup)

        backgroundGroup = QHBoxLayout()
        backgroundLabel = QLabel("Background")
        self.background = QLineEdit()
        self.background.setText(settings["visuals"]["background"])
        backgroundGroup.addWidget(backgroundLabel)
        backgroundGroup.addWidget(self.background)
        visualsLeftGroup.addLayout(backgroundGroup)

        textBackgroundGroup = QHBoxLayout()
        textBackgroundLabel = QLabel("Text background")
        self.textBackground = QLineEdit()
        self.textBackground.setText(settings["visuals"]["textBackground"])
        textBackgroundGroup.addWidget(textBackgroundLabel)
        textBackgroundGroup.addWidget(self.textBackground)
        visualsLeftGroup.addLayout(textBackgroundGroup)

        textGroup = QHBoxLayout()
        textLabel = QLabel("Text color")
        self.text = QLineEdit()
        self.text.setText(settings["visuals"]["text"])
        textGroup.addWidget(textLabel)
        textGroup.addWidget(self.text)
        visualsLeftGroup.addLayout(textGroup)

        buttonTextGroup = QHBoxLayout()
        buttonTextLabel = QLabel("Buttons color")
        self.buttonText = QLineEdit()
        self.buttonText.setText(settings["visuals"]["buttonText"])
        buttonTextGroup.addWidget(buttonTextLabel)
        buttonTextGroup.addWidget(self.buttonText)
        visualsLeftGroup.addLayout(buttonTextGroup)

        buttonHoverGroup = QHBoxLayout()
        buttonHoverLabel = QLabel("Buttons hover")
        self.buttonHover = QLineEdit()
        self.buttonHover.setText(settings["visuals"]["buttonHover"])
        buttonHoverGroup.addWidget(buttonHoverLabel)
        buttonHoverGroup.addWidget(self.buttonHover)
        visualsRightGroup.addLayout(buttonHoverGroup)

        buttonClickedGroup = QHBoxLayout()
        buttonClickedLabel = QLabel("Buttons clicked")
        self.buttonClicked = QLineEdit()
        self.buttonClicked.setText(settings["visuals"]["buttonClicked"])
        buttonClickedGroup.addWidget(buttonClickedLabel)
        buttonClickedGroup.addWidget(self.buttonClicked)
        visualsRightGroup.addLayout(buttonClickedGroup)

        normalModeGroup = QHBoxLayout()
        normalModeLabel = QLabel("Normal mode")
        self.normalMode = QLineEdit()
        self.normalMode.setText(settings["visuals"]["normalMode"])
        normalModeGroup.addWidget(normalModeLabel)
        normalModeGroup.addWidget(self.normalMode)
        visualsRightGroup.addLayout(normalModeGroup)

        editInputModeGroup = QHBoxLayout()
        editInputModeLabel = QLabel("Edit input mode")
        self.editInputMode = QLineEdit()
        self.editInputMode.setText(settings["visuals"]["editInputMode"])
        editInputModeGroup.addWidget(editInputModeLabel)
        editInputModeGroup.addWidget(self.editInputMode)
        visualsRightGroup.addLayout(editInputModeGroup)

        editOutputModeGroup = QHBoxLayout()
        editOutputModeLabel = QLabel("Edit output mode")
        self.editOutputMode = QLineEdit()
        self.editOutputMode.setText(settings["visuals"]["editOutputMode"])
        editOutputModeGroup.addWidget(editOutputModeLabel)
        editOutputModeGroup.addWidget(self.editOutputMode)
        visualsRightGroup.addLayout(editOutputModeGroup)

        visualsGroup.addLayout(visualsLeftGroup)
        visualsGroup.addLayout(visualsRightGroup)
        visualsSectionLayout.addLayout(visualsGroup)

        globalGroup = QVBoxLayout()

        pasteGroup = QHBoxLayout()
        self.pasteEnabled = QCheckBox()
        self.pasteEnabled.setChecked(settings["global"]["paste"]["enabled"])
        pasteLabel = QLabel("Paste")
        self.pasteShortcut = QLineEdit()
        self.pasteShortcut.setText(settings["global"]["paste"]["shortcut"])
        pasteGroup.addWidget(self.pasteEnabled)
        pasteGroup.addWidget(pasteLabel, Qt.AlignLeft)
        pasteGroup.addWidget(self.pasteShortcut)
        globalGroup.addLayout(pasteGroup)

        macroGroup = QHBoxLayout()
        self.macroEnabled = QCheckBox()
        self.macroEnabled.setChecked(settings["global"]["macro"]["enabled"])
        macroLabel = QLabel("Macro")
        self.macroShortcut = QLineEdit()
        self.macroShortcut.setText(settings["global"]["macro"]["shortcut"])
        macroGroup.addWidget(self.macroEnabled)
        macroGroup.addWidget(macroLabel, Qt.AlignLeft)
        macroGroup.addWidget(self.macroShortcut)
        globalGroup.addLayout(macroGroup)

        nacroGroup = QHBoxLayout()
        self.nacroEnabled = QCheckBox()
        self.nacroEnabled.setChecked(settings["global"]["nacro"]["enabled"])
        nacroLabel = QLabel("Macro")
        self.nacroShortcut = QLineEdit()
        self.nacroShortcut.setText(settings["global"]["nacro"]["shortcut"])
        nacroGroup.addWidget(self.nacroEnabled)
        nacroGroup.addWidget(nacroLabel, Qt.AlignLeft)
        nacroGroup.addWidget(self.nacroShortcut)
        globalGroup.addLayout(nacroGroup)

        visualsSectionLayout.addLayout(globalGroup)

        contentsLayout.addWidget(generalSectionName, 0, Qt.AlignCenter)
        contentsLayout.addLayout(generalSectionLayout)
        contentsLayout.addWidget(translationSectionName, 0, Qt.AlignCenter)
        contentsLayout.addLayout(translationSectionLayout)
        contentsLayout.addWidget(macroSectionName, 0, Qt.AlignCenter)
        contentsLayout.addLayout(macroSectionLayout)
        contentsLayout.addWidget(visualsSectionName, 0, Qt.AlignCenter)
        contentsLayout.addLayout(visualsSectionLayout)
        contentsWidget.setLayout(contentsLayout)

        mainLayout.addWidget(contentsWidget)
        mainLayout.addWidget(dialogButtons)

        self.changeTranslatorSettings()

        self.setLayout(mainLayout)

    def changeTranslatorSettings(self):
        if self.translatorSetting.currentText() == "Microsoft Translator API":
            self.translatorApiKey.setText(
                settings["MicrosoftTranslator"]["apiKey"])
            self.translatorRequireAPIKey.setChecked(True)
            self.translatorUrl.setText(
                settings["MicrosoftTranslator"]["url"])
            self.translatorLocation.setText(
                settings["MicrosoftTranslator"]["location"])
            if microsoftranslate_config.apiKey == "":
                self.translatorWarning.setText(
                    microsoftranslate_config.warningNoKey)
            else:
                self.translatorWarning.setText(
                    microsoftranslate_config.warningHasKey)
            self.translatorApiKey.setEnabled(True)
            self.translatorLocation.setEnabled(True)
            self.translatorUrl.setEnabled(True)
            self.translatorRequireAPIKey.setEnabled(False)
        elif self.translatorSetting.currentText() == "LibreTranslate":
            self.translatorApiKey.setText(
                settings["LibreTranslate"]["apiKey"])
            if settings["LibreTranslate"]["requireKey"]:
                self.translatorRequireAPIKey.setChecked(True)
            else:
                self.translatorRequireAPIKey.setChecked(False)
            self.translatorUrl.setText(
                settings["LibreTranslate"]["url"])
            self.translatorLocation.setEnabled(False)
            if libretranslate_config.url == "":
                self.translatorWarning.setText(
                    libretranslate_config.warningNoConfig)
            else:
                self.translatorWarning.setText(
                    libretranslate_config.warningHasConfig)
            self.translatorApiKey.setEnabled(True)
            self.translatorLocation.setEnabled(False)
            self.translatorUrl.setEnabled(True)
            self.translatorRequireAPIKey.setEnabled(True)
        elif self.translatorSetting.currentText() == "Google Translate Web":
            self.translatorApiKey.setText("")
            self.translatorLocation.setText("")
            self.translatorUrl.setText("")
            self.translatorWarning.setText("")
            self.translatorRequireAPIKey.setChecked(False)
            self.translatorApiKey.setEnabled(False)
            self.translatorLocation.setEnabled(False)
            self.translatorUrl.setEnabled(False)
            self.translatorRequireAPIKey.setEnabled(False)

    def reject(self) -> None:
        return super().reject()

    def accept(self, parent) -> None:
        settings["translator"] = self.translatorSetting.currentText()
        match settings["translator"]:
            case "LibreTranslate":
                settings["LibreTranslate"]["url"] = self.translatorUrl.text()
                settings["LibreTranslate"]["requireKey"] = self.translatorRequireAPIKey.isChecked(
                )
                settings["LibreTranslate"]["apiKey"] = self.translatorApiKey.text()
            case "Microsoft Translator API":
                settings["MicrosoftTranslator"]["url"] = self.translatorUrl.text()
                settings["MicrosoftTranslator"]["apiKey"] = self.translatorApiKey.text()
                settings["MicrosoftTranslator"]["location"] = self.translatorLocation.text()
        settings["translation"]["defaultTargetLanguage"] = self.translationTargetLanguage.text()
        settings["translation"]["languagePairs"]["source"] = configHelper.strToList(
            self.languagePairsSource.text())
        settings["translation"]["languagePairs"]["target"] = configHelper.strToList(
            self.languagePairsTarget.text())
        settings["translation"]["override"]["defaultSource"] = self.overrideSource.text()
        settings["translation"]["override"]["defaultTarget"] = self.overrideTarget.text()
        settings["macro"]["runPaste"] = self.macroPaste.isChecked()
        settings["macro"]["runFormat"] = self.macroFormat.isChecked()
        settings["macro"]["runGormat"] = self.macroGormat.isChecked()
        settings["macro"]["runYank"] = self.macroYank.isChecked()
        settings["macro"]["showWindow"] = self.macroShow.isChecked()
        settings["nacro"]["runPaste"] = self.nacroPaste.isChecked()
        settings["nacro"]["runFormat"] = self.nacroFormat.isChecked()
        settings["nacro"]["runGormat"] = self.nacroGormat.isChecked()
        settings["nacro"]["runYank"] = self.nacroYank.isChecked()
        settings["nacro"]["showWindow"] = self.nacroShow.isChecked()
        settings["format"]["delEmptyLines"] = self.formatDelEmptyLines.isChecked()
        settings["format"]["delNewLines"] = self.formatDelNewLines.isChecked()
        settings["format"]["delSpaces"] = self.formatDelSpaces.isChecked()
        settings["gormat"]["delEmptyLines"] = self.gormatDelEmptyLines.isChecked()
        settings["gormat"]["delNewLines"] = self.gormatDelNewLines.isChecked()
        settings["gormat"]["delSpaces"] = self.gormatDelSpaces.isChecked()
        settings["delNewLines"]["saveNewLinesAfterSpecialSymbols"] = self.saveNewLinesAfterSpecialSymbols.isChecked()
        settings["delNewLines"]["specialSymbols"] = configHelper.strToList(
            self.specialSymbols.text())
        settings["visuals"]["borderRadius"] = self.borderRadius.text()
        settings["visuals"]["background"] = self.background.text()
        settings["visuals"]["textBackground"] = self.textBackground.text()
        settings["visuals"]["text"] = self.text.text()
        settings["visuals"]["buttonText"] = self.buttonText.text()
        settings["visuals"]["buttonHover"] = self.buttonHover.text()
        settings["visuals"]["buttonClicked"] = self.buttonClicked.text()
        settings["visuals"]["normalMode"] = self.normalMode.text()
        settings["visuals"]["editInputMode"] = self.editInputMode.text()
        settings["visuals"]["editOutputMode"] = self.editOutputMode.text()
        settings["global"]["paste"]["shortcut"] = self.pasteShortcut.text()
        settings["global"]["paste"]["enabled"] = self.pasteEnabled.isChecked()
        settings["global"]["macro"]["shortcut"] = self.macroShortcut.text()
        settings["global"]["macro"]["enabled"] = self.macroEnabled.isChecked()
        settings["global"]["nacro"]["shortcut"] = self.nacroShortcut.text()
        settings["global"]["nacro"]["enabled"] = self.nacroEnabled.isChecked()

        configHelper.writeConfig(settings, configPath)
        reload(parent)

        return super().accept()

    def help(self) -> None:
        helpDialog = HelpDialog(self)
        helpDialog.exec_()


class OverrideTranslationDialog(QDialog):
    sourceInput = None
    targetInput = None

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.initUI(parent)
        self.setWindowTitle("override translation")

    def initUI(self, parent):
        self.sourceInput = QLineEdit()
        self.sourceInput.setFixedWidth(128)
        self.sourceInput.setText(settings["translation"]
                                 ["override"]["defaultSource"])
        self.targetInput = QLineEdit()
        self.targetInput.setFixedWidth(128)
        self.targetInput.setText(settings["translation"]
                                 ["override"]["defaultTarget"])
        mainLayout = QVBoxLayout()
        elementsLayout = QHBoxLayout()
        sourceLabel = QLabel("SOURCE: ")
        targetLabel = QLabel("TARGET: ")
        elementsLayout.addWidget(sourceLabel)
        elementsLayout.addWidget(self.sourceInput)
        elementsLayout.addWidget(targetLabel)
        elementsLayout.addWidget(self.targetInput)

        dialogButtons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialogButtons.accepted.connect(lambda: self.accept(parent))
        dialogButtons.rejected.connect(self.reject)

        mainLayout.addLayout(elementsLayout)
        mainLayout.addWidget(dialogButtons)
        self.sourceInput.setFocus()
        self.sourceInput.selectAll()

        self.setLayout(mainLayout)

    def reject(self) -> None:
        return super().reject()

    def accept(self, parent) -> None:
        source = self.sourceInput.text()
        target = self.targetInput.text()
        parent.overrideTranslate(source, target)
        return super().accept()


class HelpWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setFixedHeight(0)
        self.setStyleSheet("font-size: 12px;")
        helpLayout = QHBoxLayout()

        leftLayout = QVBoxLayout()
        normalLabel = QLabel("NORMAL MODE")
        normalLabel.setStyleSheet("font-size: 16px;")
        leftLayoutContents = QHBoxLayout()
        leftContents1 = QLabel(
            "/ - toggle this cheatsheet\r\nM - run macro\r\nN - run nacro (macro #2)\r\nP - paste the text from the clipboard\r\nF - run format\r\nG - run gormat (format #2)\r\nT - translate\r\nCtrl+T - override translation\r\nY - yank the translated text\r\nD - delete text"
        )
        leftContents2 = QLabel(
            "Q - quit trapy\r\nC - show config editor\r\nCtrl+C - open config file\r\nI - enter the EDIT MODE on the input text\r\nO - enter the EDIT MODE on the output text\r\n\r\nFORMAT OPTIONS:\r\nE - delete empty lines\r\nL - delete new lines\r\nS - delete spaces"
        )
        leftContents1.setMargin(8)
        leftContents2.setMargin(8)
        leftLayoutContents.addWidget(
            leftContents1, 0, Qt.AlignCenter | Qt.AlignTop)
        leftLayoutContents.addWidget(
            leftContents2, 0, Qt.AlignCenter | Qt.AlignTop)
        leftLayout.addWidget(normalLabel, 0, Qt.AlignCenter)
        leftLayout.addLayout(leftLayoutContents)
        leftLayout.setAlignment(Qt.AlignTop)

        centerLayout = QVBoxLayout()
        editLabel = QLabel("EDIT MODE")
        editLabel.setStyleSheet("font-size: 16px;")
        centerLayoutContents = QLabel(
            "ESC - exit the EDIT MODE\r\nCtrl+Q - quit trapy")
        centerLayoutContents.setMargin(8)

        centerLayout.addWidget(editLabel, 0, Qt.AlignCenter)
        centerLayout.addWidget(centerLayoutContents, 0,
                               Qt.AlignCenter | Qt.AlignTop)
        centerLayout.setAlignment(Qt.AlignTop)

        rightLayout = QVBoxLayout()
        globalLabel = QLabel("GLOBAL SHORTCUTS")
        globalLabel.setStyleSheet("font-size: 16px;")
        rightLayoutContents = QLabel(
            settings["global"]["macro"]["shortcut"]
            + " - run macro\r\n"
            + settings["global"]["nacro"]["shortcut"]
            + " - run macro #2 (nacro)\r\n"
            + settings["global"]["paste"]["shortcut"]
            + " - paste the text from the clipboard and show trapy"
        )
        rightLayoutContents.setMargin(8)
        rightLayout.addWidget(globalLabel, 0, Qt.AlignCenter)
        rightLayout.addWidget(rightLayoutContents, 0,
                              Qt.AlignCenter | Qt.AlignTop)
        rightLayout.setAlignment(Qt.AlignTop)

        helpLayout.addLayout(leftLayout)
        helpLayout.addLayout(centerLayout)
        helpLayout.addLayout(rightLayout)

        self.setLayout(helpLayout)

    def toggle(self):
        if self.height() == 0:
            self.setFixedHeight(240)
        else:
            self.setFixedHeight(0)


class MainWindow(QWidget):
    modeLabel = None
    tipsLabel = None
    inputBox = None
    outputBox = None
    helpWidget = None

    def macro(self):
        self.tipsLabel.setText(tips[2])
        if settings["macro"]["runPaste"]:
            self.paste()
        if settings["macro"]["runFormat"]:
            self.format(self.inputBox.toPlainText())
        if settings["macro"]["runGormat"]:
            self.gormat(self.inputBox.toPlainText())
        self.translate(self.inputBox.toPlainText())
        if settings["macro"]["runYank"]:
            self.yank(self.outputBox.toPlainText())

    def nacro(self):
        self.tipsLabel.setText(tips[3])
        if settings["nacro"]["runPaste"]:
            self.paste()
        if settings["nacro"]["runFormat"]:
            self.format(self.inputBox.toPlainText())
        if settings["nacro"]["runGormat"]:
            self.gormat(self.inputBox.toPlainText())
        self.translate(self.inputBox.toPlainText())
        if settings["nacro"]["runYank"]:
            self.yank(self.outputBox.toPlainText())

    def paste(self):
        self.tipsLabel.setText(tips[4])
        self.modeLabel.setFocus()
        t = pyperclip.paste()
        t = formatHelper.basicCleanup(t)
        self.inputBox.setPlainText(t)

    def format(self, t):
        self.tipsLabel.setText(tips[5])
        if settings["format"]["delEmptyLines"]:
            t = formatHelper.delEmptyLines(t)
        if settings["format"]["delNewLines"]:
            t = formatHelper.delNewLines(t)
        if settings["format"]["delSpaces"]:
            t = formatHelper.delSpaces(t)
        self.inputBox.setPlainText(t)

    def gormat(self, t):
        self.tipsLabel.setText(tips[6])
        if settings["gormat"]["delEmptyLines"]:
            t = formatHelper.delEmptyLines(t)
        if settings["gormat"]["delNewLines"]:
            t = formatHelper.delNewLines(t)
        if settings["gormat"]["delSpaces"]:
            t = formatHelper.delSpaces(t)
        self.inputBox.setPlainText(t)

    def delEmptyLines(self, t):
        self.tipsLabel.setText(tips[9])
        t = formatHelper.delEmptyLines(t)
        self.inputBox.setPlainText(t)

    def delNewLines(self, t):
        self.tipsLabel.setText(tips[10])
        t = formatHelper.delNewLines(
            t, settings["delNewLines"]["saveNewLinesAfterSpecialSymbols"], settings["delNewLines"]["specialSymbols"])
        self.inputBox.setPlainText(t)

    def delSpaces(self, t):
        self.tipsLabel.setText(tips[11])
        t = formatHelper.delSpaces(t)
        self.inputBox.setPlainText(t)

    def translate(self, t):
        self.tipsLabel.setText(tips[7])
        match settings["translator"]:
            case "LibreTranslate":
                language = translator.detect(t)[0]["language"]
                if settings["translation"]["languagePairs"]["source"].count(language) > 0:
                    languageId = settings["translation"]["languagePairs"]["source"].index(
                        language)
                    self.outputBox.setPlainText(
                        translator.translate(
                            t, source=language, target=settings["translation"]["languagePairs"]["target"][languageId])
                    )
                else:
                    self.outputBox.setPlainText(
                        translator.translate(
                            t, source=language, target=settings["translation"]["defaultTargetLanguage"])
                    )
            case "Google Translate Web":
                language = translator.detect(t).lang
                if settings["translation"]["languagePairs"]["source"].count(language) > 0:
                    languageId = settings["translation"]["languagePairs"]["source"].index(
                        language)
                    self.outputBox.setPlainText(
                        translator.translate(t, dest=settings["translation"]["languagePairs"]["target"][languageId]).text)
                else:
                    self.outputBox.setPlainText(
                        translator.translate(t, dest=settings["translation"]["defaultTargetLanguage"]).text)
            case "Microsoft Translator API":
                language = translator.detect(t)
                if settings["translation"]["languagePairs"]["source"].count(language) > 0:
                    languageId = settings["translation"]["languagePairs"]["source"].index(
                        language)
                    self.outputBox.setPlainText(
                        translator.translate(t, target=settings["translation"]["languagePairs"]["target"][languageId]))
                else:
                    self.outputBox.setPlainText(
                        translator.translate(t, target=settings["translation"]["defaultTargetLanguage"]))

    def showOverrideDialog(self):
        self.tipsLabel.setText(tips[14])
        overrideDialog = OverrideTranslationDialog(self)
        overrideDialog.exec_()

    def overrideTranslate(self, source, target):
        t = self.inputBox.toPlainText()
        match settings["translator"]:
            case "LibreTranslate":
                if source == "auto":
                    language = translator.detect(t)[0]["language"]
                    self.outputBox.setPlainText(
                        translator.translate(
                            t, source=language, target=target)
                    )
                else:
                    self.outputBox.setPlainText(
                        translator.translate(
                            t, source=source, target=target)
                    )
            case "Google Translate Web":
                if source == "auto":
                    self.outputBox.setPlainText(
                        translator.translate(t, dest=target).text)
                else:
                    self.outputBox.setPlainText(
                        translator.translate(t, dest=target, src=source).text)
            case "Microsoft Translator API":
                if source == "auto":
                    self.outputBox.setPlainText(
                        translator.translate(t, target=target))
                else:
                    self.outputBox.setPlainText(
                        translator.translate(t, source, target=target))

    def yank(self, t):
        self.tipsLabel.setText(tips[8])
        pyperclip.copy(t)

    def clear(self):
        self.tipsLabel.setText(tips[12])
        self.inputBox.setPlainText("")
        self.outputBox.setPlainText("")

    def showConfig(self):
        self.tipsLabel.setText(tips[15])
        configDialog = ConfigDialog(self)
        configDialog.exec_()

    def openConfigFile(self):
        self.tipsLabel.setText(tips[13])
        configHelper.openConfigFile(configPath)

    def enterInputFocus(self):
        self.inputBox.setFocus()
        self.inputBox.moveCursor(QTextCursor.End)

    def enterOutputFocus(self):
        self.outputBox.setFocus()
        self.outputBox.moveCursor(QTextCursor.End)

    def inputFocusIn(self):
        self.modeLabel.setInput()
        self.tipsLabel.setText(tips[1])

    def outputFocusIn(self):
        self.modeLabel.setOutput()
        self.tipsLabel.setText(tips[1])

    def editFocusOut(self):
        self.modeLabel.setNormal()
        self.tipsLabel.setText(tips[0])

    def universalEditFocusOut(self):
        self.modeLabel.setFocus()
        self.tipsLabel.setText(tips[0])

    def showWindow(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(Qt.WindowActive)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setGeometry(100, 100, 1200, 600)
        self.setWindowTitle("tra.py")
        self.initUI()
        self.initShortcut()

    def initShortcut(self):
        macroShortcut = QShortcut(QKeySequence("M"), self.modeLabel)
        nacroShortcut = QShortcut(QKeySequence("N"), self.modeLabel)
        pasteShortcut = QShortcut(QKeySequence("P"), self.modeLabel)
        formatShortcut = QShortcut(QKeySequence("F"), self.modeLabel)
        gormatShortcut = QShortcut(QKeySequence("G"), self.modeLabel)
        eLinesShortcut = QShortcut(QKeySequence("E"), self.modeLabel)
        nLinesShortcut = QShortcut(QKeySequence("L"), self.modeLabel)
        spacesShortcut = QShortcut(QKeySequence("S"), self.modeLabel)
        deleteShortcut = QShortcut(QKeySequence("D"), self.modeLabel)
        translateShortcut = QShortcut(QKeySequence("T"), self.modeLabel)
        overrideTranslationShortcut = QShortcut(
            QKeySequence("Ctrl+T"), self.modeLabel)
        yankShortcut = QShortcut(QKeySequence("Y"), self.modeLabel)
        configShortcut = QShortcut(QKeySequence("Ctrl+C"), self.modeLabel)
        configDialogShortcut = QShortcut(QKeySequence("C"), self.modeLabel)

        helpShortcut = QShortcut(QKeySequence("/"), self.modeLabel)
        helpShortcut.activated.connect(lambda: self.helpWidget.toggle())
        enterInputFocus = QShortcut(QKeySequence("I"), self.modeLabel)
        enterOutputFocus = QShortcut(QKeySequence("O"), self.modeLabel)
        exitEditFocus = QShortcut(QKeySequence("Esc"), self)
        quitShortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quitShortcut_local = QShortcut(QKeySequence("Q"), self.modeLabel)
        reloadShortcut = QShortcut(QKeySequence("R"), self.modeLabel)

        macroShortcut.activated.connect(lambda: self.macro())
        nacroShortcut.activated.connect(lambda: self.nacro())
        pasteShortcut.activated.connect(lambda: self.paste())
        formatShortcut.activated.connect(
            lambda: self.format(self.inputBox.toPlainText()))
        gormatShortcut.activated.connect(
            lambda: self.gormat(self.inputBox.toPlainText()))

        eLinesShortcut.activated.connect(
            lambda: self.delEmptyLines(self.inputBox.toPlainText()))
        nLinesShortcut.activated.connect(
            lambda: self.delNewLines(self.inputBox.toPlainText()))
        spacesShortcut.activated.connect(
            lambda: self.delSpaces(self.inputBox.toPlainText()))
        deleteShortcut.activated.connect(lambda: self.clear())
        translateShortcut.activated.connect(
            lambda: self.translate(self.inputBox.toPlainText()))
        overrideTranslationShortcut.activated.connect(
            lambda: self.showOverrideDialog())
        yankShortcut.activated.connect(
            lambda: self.yank(self.outputBox.toPlainText()))
        configShortcut.activated.connect(lambda: self.openConfigFile())
        configDialogShortcut.activated.connect(lambda: self.showConfig())

        enterInputFocus.activated.connect(lambda: self.enterInputFocus())
        enterOutputFocus.activated.connect(lambda: self.enterOutputFocus())
        exitEditFocus.activated.connect(lambda: self.universalEditFocusOut())
        quitShortcut.activated.connect(lambda: self.close())
        quitShortcut_local.activated.connect(lambda: self.close())
        reloadShortcut.activated.connect(lambda: reload(self))

        self.inputBox.focusInSignal.connect(lambda: self.inputFocusIn())
        self.inputBox.focusOutSignal.connect(lambda: self.editFocusOut())
        self.outputBox.focusInSignal.connect(lambda: self.outputFocusIn())
        self.outputBox.focusOutSignal.connect(lambda: self.editFocusOut())

    def initUI(self):
        self.modeLabel = ModeLabel()
        self.tipsLabel = QLabel(tips[0])
        self.inputBox = TrapyTextEdit()
        self.outputBox = TrapyTextEdit()
        self.helpWidget = HelpWidget()
        mainLayout = QVBoxLayout()

        labelLayout = QHBoxLayout()

        self.modeLabel.setNormal()
        self.modeLabel.setObjectName("mode")
        self.modeLabel.setFixedWidth(160)
        self.modeLabel.setAlignment(Qt.AlignCenter)

        labelLayout.addWidget(self.modeLabel)
        labelLayout.addWidget(self.tipsLabel)

        textLayout = QHBoxLayout()
        textLayout.addWidget(self.inputBox)
        textLayout.addWidget(self.outputBox)

        mainLayout.addLayout(textLayout)
        mainLayout.addLayout(labelLayout)
        mainLayout.addWidget(self.helpWidget)
        self.setLayout(mainLayout)
        self.modeLabel.setFocus()


def main():
    app = QApplication(sys.argv)
    font_dir = ":/fonts"
    load_fonts_from_dir(os.fspath(font_dir))

    app.setStyleSheet(styleHelper.constructStyleSheet(
        settings["visuals"]["borderRadius"], settings["visuals"]["background"], settings["visuals"]["textBackground"], settings["visuals"]["text"], settings["visuals"]["buttonText"], settings["visuals"]["buttonHover"], settings["visuals"]["buttonClicked"]))

    mainWindow = MainWindow()

    keybinder.init()

    def macroGlobal():
        mainWindow.macro()
        if settings["macro"]["showWindow"]:
            mainWindow.showWindow()

    def nacroGlobal():
        mainWindow.nacro()
        if settings["nacro"]["showWindow"]:
            mainWindow.showWindow()

    def pasteGlobal():
        mainWindow.paste()
        mainWindow.showWindow()

    if settings["global"]["macro"]["enabled"]:
        keybinder.register_hotkey(
            mainWindow.winId().__int__(
            ), settings["global"]["macro"]["shortcut"], macroGlobal
        )
    if settings["global"]["nacro"]["enabled"]:
        keybinder.register_hotkey(
            mainWindow.winId().__int__(
            ), settings["global"]["nacro"]["shortcut"], nacroGlobal
        )
    if settings["global"]["paste"]["enabled"]:
        keybinder.register_hotkey(
            mainWindow.winId().__int__(
            ), settings["global"]["paste"]["shortcut"], pasteGlobal
        )

    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)

    mainWindow.show()
    app.exec_()


if __name__ == "__main__":
    configPath = configHelper.getConfigPath()
    settings = configHelper.readConfig(configPath)
    match settings["translator"]:
        case "Google Translate Web": translator = Translator()
        case "LibreTranslate":
            if settings["LibreTranslate"]["url"] == "":
                if libretranslate_config.requireKey:
                    translator = LibreTranslateAPI(
                        libretranslate_config.url, libretranslate_config.apiKey
                    )
                else:
                    translator = LibreTranslateAPI(libretranslate_config.url)
            else:
                if settings["LibreTranslate"]["requireKey"]:
                    translator = LibreTranslateAPI(
                        settings["LibreTranslate"]["url"], settings["LibreTranslate"]["apiKey"]
                    )
                else:
                    translator = LibreTranslateAPI(
                        settings["LibreTranslate"]["url"])
        case "Microsoft Translator API":
            if settings["MicrosoftTranslator"]["apiKey"] == "":
                translator = MicrosoftTranslator(
                    microsoftranslate_config.url, microsoftranslate_config.apiKey, microsoftranslate_config.location)
            else:
                translator = MicrosoftTranslator(
                    settings["MicrosoftTranslator"]["url"], settings["MicrosoftTranslator"]["apiKey"], settings["MicrosoftTranslator"]["location"])

    main()
