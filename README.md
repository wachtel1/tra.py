# tra.py
Performance-oriented and highly customizable GUI client for translation APIs.

## Supports:
- Google Translate (uses https://github.com/ssut/py-googletrans)
- LibreTranslate API
- Microsoft Translator API (requires an API key)

## Plans:
- Add Google Translate API.
- Make the path to store the configuration file customizable.
- Check the specified languages format and warn user that the language was not found.

## How to use
Type / to open the cheatsheet.

## How to configure
Type C to open the configuration editor.

## It broke
Open your home folder and delete trapy.config file to reset the configuration.

## Packaging into executable
- tra.py is build using PyQt5.
- You can hide API keys in binary to not expose it in the config file. To do it, find the related <API_name>config.py file and configure your access in it, instead of configuring it in configuration file.
- tra.py can be easily packaged using the pyinstaller:
  ```
  pip install pyinstaller
  ```
  ```
  pyinstaller --onefile --windowed tra.py
  ```
- Make sure to store the default.config file in the same folder as the resulting executable.
