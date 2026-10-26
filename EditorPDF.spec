# Execute com PyInstaller no Windows; todos os recursos são incluídos localmente.
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata
root = Path(SPECPATH)
datas = [(str(root / name), '.') for name in ('ajuda.html', 'style.qss', 'exemplo.pdf', 'LICENSE.txt', 'app.svg')]
for dependency in ('PyMuPDF', 'PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6'):
    datas += copy_metadata(dependency)
a = Analysis([str(root / 'main.py')], pathex=[str(root)], binaries=[], datas=datas,
             hiddenimports=['PySide6.QtSvg'], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='EditorPDF', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False, icon=str(root / 'app.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='EditorPDF')
