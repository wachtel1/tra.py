def constructStyleSheet(borderRadius, background, textBackground, text, buttonText, buttonHover, buttonClicked):
    styleSheet = "QWidget { background-color: " + background + "; font-family: 'Noto Sans' } QPlainTextEdit { margin-left: 16px; margin-right: 16px; margin-bottom: 8px; border-radius: " + borderRadius + "; background-color: " + textBackground + "; color: " + text + "; border: none; font-size: 16px } QLineEdit { margin-left: 16px; margin-right: 16px; margin-bottom: 8px; margin-top: 8px; border-radius: " + borderRadius + "; background-color: " + textBackground + "; color: " + text + "; border: none; font-size: 16px; font-weight: bold; text-align: center } QLabel { color: " + text + "; border: none; font-size: 16px } QLabel#mode { margin-left: 16px; margin-bottom: 8px; margin-top: 8px; font-weight: bold; text-align: center } QPushButton { margin: 16px; background-color: " + background + "; border-style: solid; border-width: 0px; font-size: 20px; font-weight: bold; color: " + \
        buttonText + " } QPushButton:hover { color: " + buttonHover + " } QPushButton:pressed { color: " + buttonClicked + " } QComboBox { color: " + text + \
        "; background: " + textBackground + \
        "; } QComboBox QAbstractItemView { color: " + text + \
        "; background: " + textBackground + \
        "; } QComboBox:editable { background: " + textBackground + \
        "; } QScrollBar:vertical {border-width: 0px;border-style: solid; background-color: " + background + ";width: 8px;margin: 8px 0 8px 0; } QScrollBar::handle:vertical {background-color: " + buttonText + \
        " ;min-height: 16px;} QScrollBar::add-line:vertical { border: 0px solid black;background-color: " + buttonText + \
        "; height: 8px;subcontrol-position: bottom;subcontrol-origin: margin;} QScrollBar::sub-line:vertical { border: 0px solid black;background-color: " + buttonText + \
        "; height: 8px;subcontrol-position: top;subcontrol-origin: margin;}"
    return styleSheet
