"""Gera a distribuição Windows e verifica que ela consegue iniciar sem Python externo."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def build():
    if sys.platform != 'win32':
        raise RuntimeError('Execute no Windows: o PyInstaller nao gera executaveis Windows no Linux.')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt'), 'PyInstaller==6.22.0'], check=True)
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', str(ROOT / 'EditorPDF.spec')], cwd=ROOT, check=True)
    executable = ROOT / 'dist' / 'EditorPDF' / 'EditorPDF.exe'
    subprocess.run([str(executable), '--smoke-test'], cwd=ROOT, check=True, timeout=90)
    for file in ROOT.iterdir():
        if file.is_file() and (file.suffix == '.md' or file.name in {'LICENSE.txt', 'interface.png', 'edicao-texto.png', 'ajuda.png', 'inicio.png'}):
            shutil.copy2(file, executable.parent / file.name)
    source = executable.parent / 'codigo-fonte'
    source.mkdir(exist_ok=True)
    for file in ROOT.iterdir():
        if file.is_file() and (file.suffix in {'.py', '.txt', '.md', '.bat', '.html', '.qss', '.svg', '.ico', '.spec'} or file.name == 'exemplo.pdf'):
            shutil.copy2(file, source / file.name)
    for name in ('.gitignore', '.gitattributes'):
        shutil.copy2(ROOT / name, source / name)
    shutil.copytree(ROOT / 'third_party_licenses', executable.parent / 'third_party_licenses', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'third_party_licenses', source / 'third_party_licenses', dirs_exist_ok=True)
    output = shutil.make_archive(str(ROOT / 'dist' / 'EditorPDF-Windows-x64'), 'zip', ROOT / 'dist', 'EditorPDF')
    print('Pacote pronto: ' + output)


if __name__ == '__main__':
    try:
        build()
    except Exception as exc:
        print(str(exc))
        sys.exit(1)
