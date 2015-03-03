set PATH=%PATH%;C:\Python27;C:\Python27\Scripts;C:\Scratch\upx391w;

rmdir /s /q dist build

pyinstaller --noconfirm -F make_contact.spec

set /p VER=<current_version.txt

cd dist

copy make_contact-gui\make_contact-gui.exe make_contact

move make_contact make_contact_%VER%

..\7z.exe a -sfx make_contact_%VER%.exe  make_contact_%VER%

cd ..


