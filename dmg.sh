#!/usr/bin/env bash

pyinstaller --clean --windowed --onefile --add-data 'src/assistants:assistants' --noconsole --icon=app.icns --name=tbuddy --codesign-identity "Payam Khaninejad" src/gui.py --exclude-module charset_normalizer --name test.bin

APP_NAME="tbuddy"
DMG_FILE_NAME="dist/${APP_NAME}-Installer.dmg"
VOLUME_NAME="${APP_NAME} Installer"
SOURCE_FOLDER_PATH="dist/"

if [[ -e ../../create-dmg ]]; then
  # We're running from the repo
  CREATE_DMG=create-dmg
else
  # We're running from an installation under a prefix
  CREATE_DMG=/usr/local/bin/create-dmg
fi

# Since create-dmg does not clobber, be sure to delete previous DMG
[[ -f "${DMG_FILE_NAME}" ]] && rm "${DMG_FILE_NAME}"


# codesign --options=runtime --force --deep --sign "Payam Khaninejad" dist/tbuddy.app/Contents/MacOS/tbuddy && \
# Create the DMG
$CREATE_DMG \
  --codesign "Payam Khaninejad" \
  --volname "${VOLUME_NAME}" \
  --background "installer_background.png" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 185 \
  "${DMG_FILE_NAME}" \
  "${SOURCE_FOLDER_PATH}"