import os
import shutil
import subprocess
import sys
import typing as t
from pathlib import Path
from subprocess import DEVNULL, PIPE

PYTHON = "py" if sys.platform.startswith("win") else "python"

DEFAULT_APPS = ["usuario", "configuracao_core"]

PROJECT_DIRECTORY = Path(os.path.realpath(os.path.curdir)).parent

REQUIREMENTS = [
    Path(f"{PROJECT_DIRECTORY}/requirements.txt"),
    Path(f"{PROJECT_DIRECTORY}/requirements-dev.txt"),
]

SECRET_COMMAND = [PYTHON, "contrib/secret_gen.py"]

EMOJIS = {"success": "\u2705", "error": "\u274C", "wait": "\u231B"}

GIT_COMMANDS = [
    "git init --initial-branch=master",
    "git add .",
    'git commit -am "Primeiro Commit"',
    "git checkout -b desenvolvimento",
]


def run_command(
    command: t.Union[str, list], silent: bool = False, exit_on_fail=False
) -> bool:
    """Método para executar um comando"""

    try:
        if silent:
            command = subprocess.run(
                command,
                cwd=PROJECT_DIRECTORY,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
            )
        else:
            command = subprocess.run(command, cwd=PROJECT_DIRECTORY)

        return command.returncode == 0

    except Exception as e:
        if exit_on_fail:
            raise Exception(f"Erro ao executar {command}: {e}") from e

        print(f"{EMOJIS['error']} Erro ao executar {command}: {e}")

        return False


def init_git() -> None:
    """Método para inicializar o git"""

    print(f"{EMOJIS['wait']} Inicializando o git")

    for command in GIT_COMMANDS:
        if run_command(command, silent=True):
            print(f"{EMOJIS['success']} {command}")


def get_secret_key() -> str:
    """Executa o comando python contrib/secrets.py
    para gerar uma SECRET_KEY e retorna a mesma"""

    process = subprocess.run(SECRET_COMMAND, stdout=PIPE, cwd=PROJECT_DIRECTORY)
    return process.stdout.decode("utf-8").strip()


def update_env_file(file) -> None:
    """Atualiza o arquivo inserindo a SECRET KEY gerada"""

    secret = get_secret_key()

    with open(file, "r+") as f:
        env_file = f.read()
        f.seek(0)

        for line in env_file.splitlines():
            if line.startswith("SECRET_KEY"):
                env_file = env_file.replace(line, f"SECRET_KEY={secret}")

        f.write(env_file)
        f.truncate()


def copy_file_env_example_to_env() -> None:
    """Método para copiar o arquivo .env.example para .env"""

    try:
        path_env_example = Path(PROJECT_DIRECTORY, ".env.example")
        path_env = Path(PROJECT_DIRECTORY, ".env")
        if not path_env.exists():
            shutil.copyfile(path_env_example, path_env)
            update_env_file(path_env)

    except Exception as e:
        print(f"{EMOJIS['error']} Erro ao copiar o arquivo .env.example para .env: {e}")
        sys.exit(1)


def remove_subdirectory_project() -> None:
    """Método para remover a subpasta do projeto"""

    try:
        path_root = Path.cwd()
        source_dir = Path(path_root)
        print("*" * 100)
        print("=" * 100)
        print(f"Lembre de apagar manualmente o diretório:\n")
        print(f"{source_dir} \n")
        print("=" * 100)
        print("*" * 100)

    except Exception as e:
        print(f"{EMOJIS['error']} Erro ao remover a subpasta do projeto: {e}")


def copy_all_files_to_root_dir() -> None:
    """Método responsável para copiar todos os arquivos
    da subpasta para a pasta principal"""

    try:
        print(f"{EMOJIS['success']} Copiando arquivos para a pasta principal")

        path_root = Path.cwd()
        source_dir = Path(path_root)

        for file_name in Path(source_dir).glob("*"):
            shutil.move(source_dir.joinpath(file_name), PROJECT_DIRECTORY)

    except Exception as e:
        print(f"{EMOJIS['error']} Erro ao obter o caminho do projeto: {e}")
        sys.exit(1)


def pip_install_requirements() -> bool:
    """Método para instalar as dependências do projeto"""

    try:
        print(f"{EMOJIS['wait']} Instalando as dependências do projeto")

        for requirement in REQUIREMENTS:
            if not requirement.exists():
                print(f"{EMOJIS['error']} O arquivo {requirement} não existe")
                return False

        # pip install -r req.txt -r req-dev.txt
        requirements = " -r ".join([str(requirement) for requirement in REQUIREMENTS])

        returncode = run_command(
            f"{PYTHON} -m pip install -r {requirements}", silent=True
        )

        if returncode is False:
            print(
                f"{EMOJIS['error']} Erro ao instalar requirements, instalando manualmente e faça o build das apps padrões"
            )
            return False

        else:
            print(f"{EMOJIS['success']} Requirements instalados com sucesso")
            return True

    except Exception as e:
        print(f"{EMOJIS['error']} Erro ao instalar as dependências do projeto: {e}")
        sys.exit(1)


def build_default_apps() -> None:
    """Método para construir as apps padrões do projeto"""
    try:
        for app in DEFAULT_APPS:
            returncode = run_command(f"{PYTHON} manage.py build {app} --all")

            if not returncode:
                print(
                    f"{EMOJIS['error']} Erro ao construir as apps padrões do projeto: {app}"
                )

    except Exception as e:
        print(f"{EMOJIS['error']} Erro ao construir as apps padrões do projeto: {e}")
        sys.exit(1)


copy_all_files_to_root_dir()
copy_file_env_example_to_env()
if pip_install_requirements():
    build_default_apps()
init_git()
remove_subdirectory_project()
