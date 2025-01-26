import json
import os.path
import re
import shutil
from typing import Dict, List
from pathlib import Path
from deployflow.core import colors
from deployflow.core.ai import get_ai
from deployflow.core.analysis.fs import identify_target, copy_target
from deployflow.core.deployment.actions import execute_command, write_file
from deployflow.core.deployment.prompts import STAGE_PROMPT, SYSTEM_PROMPT
from deployflow.core.utils import fatal
from deployflow.logger import logger

CODE_REGEX = r"```\w+ \[?(.+)\]?\s*([\s\S]*?)\s*```"
SHELL_REGEX = r"```shell\s*(.*?)\s*```"


def deploy_target(repo, task, evidences: Dict[str, List[str]]):
    print("・┈┈・┈┈・┈┈・")
    repo_type, repo_name = identify_target(repo)
    repo_name = ''.join([c for c in repo_name if c.isalnum()])
    _DEFAULT_DIR = repo_name + "_deploy"
    target_dir = input(f"Enter the local directory to store deployment details ({_DEFAULT_DIR}): ") or _DEFAULT_DIR
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    if repo_type == "zip":
        shutil.copyfile(repo, target_dir + "/src.zip")
    else:
        if repo_type == 'dir':
            p1 = Path(repo).resolve()
            p2 = Path(target_dir).resolve()
            if p1 in p2.parents or p2 in p1.parents or p1 == p2:
                fatal("Target directory cannot be a subdirectory of the repository (or vice versa)")
        copy_target(repo, target_dir + "/src")
        shutil.make_archive(target_dir + "/src", 'zip', target_dir + "/src")
        shutil.rmtree(target_dir + "/src")
    print("Creating ssh keypair (this will be used to access the server)")
    execute_command(target_dir, f'ssh-keygen -t rsa -b 4096 -C "{repo_name}" -f id_rsa -N ""')
    execute_command(target_dir, 'chmod 400 id_rsa')
    print(f'Deploying "{colors.GREEN}{task}{colors.ENDC}" on "{colors.GREEN}{repo}{colors.ENDC}" ...{colors.ENDC}')
    client = get_ai()
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.replace("%%EVIDENCE%%", json.dumps(evidences, indent=2)).replace("%%TASK%%", task)
        },
        {
            "role": "user",
            "content": STAGE_PROMPT[0]
        }
    ]
    stage = 0
    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=1000,
            stream=False
        )
        res_text = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": res_text})
        logger.debug(res_text)
        if stage == 0:
            search = re.search(CODE_REGEX, res_text)
            if search:
                file_name, file_content = search.groups()
                if file_name != "main.tf":
                    fatal(f"AI provided wrong terraform configuration file name '{file_name}'")
                write_file(target_dir, file_name, file_content)
            else:
                fatal("AI did not provide terraform configuration file 'main.tf'")
            print()
            print()
            print(colors.BLUE + res_text.split('\n')[-1] + colors.ENDC)
            std, err = execute_command(target_dir, 'terraform init')
            if err.strip():
                fatal(f"Error initializing terraform:\n{colors.RED}{err}{colors.ENDC}")
            stage = 1
            messages.append({
                "role": "user",
                "content": f"Result of `terraform init`:\n{std}\n{'Error: ' + err if err.strip() else ''}\n\n" +
                           STAGE_PROMPT[1]
            })
        elif stage == 1:
            search = re.search(CODE_REGEX, res_text)
            if search:
                file_name, file_content = search.groups()
                if file_name != "auto-deploy.sh":
                    fatal(f"AI provided wrong auto-deploy script file name '{file_name}'")
                print()
                print()
                print(colors.BLUE + res_text.split('\n')[-1] + colors.ENDC)
                write_file(target_dir, file_name, file_content)
            else:
                print(res_text)
                fatal("AI did not provide auto-deploy script file 'auto-deploy.sh'")
            stage = 2
            messages.append({
                "role": "user",
                "content": f"created file `auto-deploy.sh`"
            })
        elif '<<COMPLETION>>' in res_text:
            print()
            print()
            print(colors.GREEN + res_text + colors.ENDC)
            break
        elif '<<ERROR>>' in res_text:
            print()
            print()
            print(colors.RED + res_text + colors.ENDC)
            break
        else:
            file_write = re.search(CODE_REGEX, res_text)
            shell_command = re.search(SHELL_REGEX, res_text)
            print()
            print()
            print(colors.BLUE + res_text.split('\n')[-1] + colors.ENDC)
            if file_write:
                file_name, file_content = file_write.groups()
                write_file(target_dir, file_name, file_content)
                messages.append({
                    "role": "user",
                    "content": f"created file `{file_name}`"
                })
            if shell_command:
                command = shell_command.groups()[0]
                std, err = execute_command(target_dir, command)
                messages.append({
                    "role": "user",
                    "content": f"Result of `{command}`:\n{std}\n{'Error: ' + err if err.strip() else ''}"
                })
            if not file_write and not shell_command:
                print(f'{colors.RED}AI did not give an response.{colors.ENDC}')
