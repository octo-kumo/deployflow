import os
import subprocess

from deployflow.core import colors
from deployflow.core.utils import fatal
from deployflow.logger import logger


def write_file(target_folder, file, content):
    print(f'\t{colors.YELLOW}ai creating file {file}{colors.ENDC}')
    with open(os.path.join(target_folder, file), "w") as f:
        f.write(content)


def execute_command(target_folder, command) -> tuple[str, str]:
    print(f'\t{colors.YELLOW}ai executing command {command}{colors.ENDC}')
    confirmation = input(f"Execute command '{colors.RED}{command}{colors.ENDC}'? (yes): ") or 'yes'
    if confirmation.lower() != "yes" and confirmation.lower() != "y":
        fatal("Command execution aborted")
    try:
        result = subprocess.run(
            command,
            cwd=target_folder,
            input="yes\n",
            text=True,
            capture_output=True,
            check=False
        )
        logger.debug(result.stdout)
        if result.returncode != 0:
            logger.error(result.stderr)
            print(f'{colors.RED}Error executing command: {result.stderr}{colors.ENDC}')
        else:
            print(f'{colors.GREEN}Command executed successfully{colors.ENDC}')
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f'{colors.RED}Error executing command: {e.stderr}{colors.ENDC}')
        logger.error(e.stderr)
        return "", e.stderr
