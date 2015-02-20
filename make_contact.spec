# -*- mode: python -*-
import glob

a = Analysis(['make_contact.py'],
             pathex=['F:]]'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

for i in ["FreeSans.ttf", "make_contact.bat", "make_contact_gui.bat", "register.bat"]:
    a.datas.append( (i, i, 'DATA') )

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='make_contact.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='make_contact')
