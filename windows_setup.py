"""Instalação e inicialização em Windows sem privilégios de administrador."""
import argparse
import os
from pathlib import Path
import struct
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    parser.add_argument('pdf', nargs='?')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise RuntimeError('Este instalador é para Windows. No Linux, siga o README.')
    if not ((3, 10) <= sys.version_info[:2] <= (3, 14)) or struct.calcsize('P') != 8:
        raise RuntimeError('Instale Python 3.12 ou 3.13 de 64 bits em python.org e tente novamente.')
    python = ROOT / '.venv' / 'Scripts' / 'python.exe'
    if not python.exists():
        print('Criando ambiente Python do aplicativo...')
        venv.EnvBuilder(with_pip=True).create(ROOT / '.venv')
    check = subprocess.run([str(python), '-c', 'import PySide6, pymupdf; assert PySide6.__version__ == "6.10.2"; assert pymupdf.VersionBind == "1.27.2.3"'], capture_output=True)
    if args.install or check.returncode:
        print('Instalando dependencias. Este passo precisa de internet na primeira vez.')
        wheels = ROOT / 'wheels'
        command = [str(python), '-m', 'pip', 'install']
        if wheels.is_dir():
            command.extend(['--no-index', '--find-links', str(wheels)])
        command.extend(['-r', str(ROOT / 'requirements.txt')])
        subprocess.run(command, cwd=ROOT, check=True)
    if args.install:
        print('Pronto. Abra iniciar_windows.bat para usar o editor.')
        return
    command = [str(python), str(ROOT / 'main.py')]
    if args.pdf:
        command.append(str(Path(args.pdf).resolve()))
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print('\nNao foi possivel iniciar o editor:\n' + str(exc))
        print('Verifique o Python, a conexao na primeira instalacao e a permissao de escrita nesta pasta.')
        sys.exit(1)
