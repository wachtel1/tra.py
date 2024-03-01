# tra.py
Performance-oriented and highly customizable GUI client for translation APIs.
![image](https://user-images.githubusercontent.com/89310925/152538329-04a351ec-76e3-4f64-a4cd-f26cf374c20c.png)

## Supports:
- Google Translate (uses https://github.com/ssut/py-googletrans)
- LibreTranslate API
- Microsoft Translator API (requires an API key)

## Features:
- Multiple macro
- Global shortcuts to run macro or paste the text from the clipboard
- Separate macro for formatting the input text
- Multiple format options to automate input text clean up and formatting
- Language pairs (source-target) to never change the target language manually again
- Customizable colors

## Plans:
- [ ] Make it readable on 4k displays.
- [ ] Fix bugs.
- [ ] Test and release for Linux.
- [ ] Test and release for Mac OS.
- [ ] Add Google Translate API.
- [ ] Make the path to store the configuration file customizable.
- [ ] Add check for languages and warn user if the language was not found.

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
- Make sure to store the default.config file in the same folder as executable.
