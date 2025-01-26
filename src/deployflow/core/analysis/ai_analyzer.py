"""
AI analysis module for deployment configuration analysis.

This module provides an AI-based analysis tool to extract deployment details from a repository.

This module does not write to the repository or execute any commands.
"""
import json
from typing import Dict, List
from deployflow.core import colors
from deployflow.core.ai import get_ai
from deployflow.core.analysis.prompts import SYSTEM_PROMPT, INSTRUCTIONS
from deployflow.logger import logger


def _prompt_system(task):
    task = f"""
User specified task:
\"""
{task}
\"""
""".strip() if task else ""
    return f"""
{SYSTEM_PROMPT}
{task}
""".strip()


def _prompt_file_list(evidences, directory, files, extra_files=None):
    if extra_files is None:
        extra_files = []
    extra_files_p = ""
    for name, content in extra_files:
        extra_files_p += f"=== file: {name}\n{content}\n===\n"
    return f"""
Analyze the following directory for deployment evidence:
=== folder: {directory}
{json.dumps(files)}
===
{extra_files_p}Current Evidence:
{json.dumps(evidences, indent=2)}

{INSTRUCTIONS}
""".strip()


def _prompt_file_content(evidences, filename, file):
    return f"""
Analyze file contents for deployment evidence:
=== file: {filename}
{file}
===
Current Evidence
{json.dumps(evidences, indent=2)}

{INSTRUCTIONS}
""".strip()


def _prompt_ans(evidences, question, answer):
    return f"""
=== You asked
"{question}"
=== User response
"{answer}"
===
Current Evidence
{json.dumps(evidences, indent=2)}

{INSTRUCTIONS}
""".strip()


def ai_analysis(evidences: Dict[str, List[str]], ls: callable, cat: callable, task: str) -> \
        Dict[str, List[str]]:
    client = get_ai()
    mode = "read_dir"
    target = ""
    question = ""
    print(colors.BOLD + "Starting AI Analysis" + colors.ENDC)
    while True:
        if mode == "read_dir":
            target_files = ls(target)
            print(
                f"\t{colors.YELLOW}ai is reading directory {target if target else '/'} -> {target_files}{colors.ENDC}")
            important_files = [(name, cat(name)) for name in ['README', 'README.md', 'README.txt', 'Dockerfile'] if
                               name in target_files]
            messages = [
                {"role": "system", "content": _prompt_system(task)},
                {"role": "user", "content": _prompt_file_list(evidences, target, target_files, important_files)},
            ]
        elif mode == "read_file":
            target_content = cat(target)
            print(f"\t{colors.YELLOW}ai is reading file {target} -> {len(target_content)} bytes{colors.ENDC}")
            messages = [
                {"role": "system", "content": _prompt_system(task)},
                {"role": "user", "content": _prompt_file_content(evidences, target, target_content)},
            ]
        elif mode == "ask":
            logger.debug(f"ai is asking a question: {question}")
            answer = input('AI: ' + question + ' ')
            messages = [
                {"role": "system", "content": _prompt_system(task)},
                {"role": "user", "content": _prompt_ans(evidences, question, answer)},
            ]
        else:
            raise ValueError(f"Invalid mode: {mode}")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=750,
            stream=False,
            response_format={
                'type': 'json_object'
            }
        )
        response_text = response.choices[0].message.content
        if not response_text:
            logger.error("ai response is empty")
            raise ValueError("AI response is empty")
        if response_text.startswith('```json') and response_text.endswith('```'):
            logger.debug("ai response is JSON but wrapped in markdown, unwrapping")
            response_text = response_text[7:-3].strip()
        logger.debug(response.usage)
        try:
            ai_evidences = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"ai response is not valid JSON: {response_text}")
            raise e
        evidences = ai_evidences["evidences"]
        next_task = ai_evidences["next_task"]
        # logger.debug(json.dumps(evidences, indent=2))
        print(colors.BLUE + ai_evidences["summary"] + colors.ENDC)
        if next_task["mode"] == "read_file":
            mode = "read_file"
            target = next_task["target"]
        elif next_task["mode"] == "read_dir":
            mode = "read_dir"
            target = next_task["target"]
        elif next_task["mode"] == "ask":
            mode = "ask"
            question = next_task["question"]
        elif next_task["mode"] == "deploy":
            logger.debug("ai analysis complete")
            logger.debug("=" * 24)
            logger.debug(json.dumps(evidences, indent=2))
            return evidences
        else:
            logger.error(f"ai halted with error: {next_task['error']}")
            print(colors.BOLD + colors.RED + next_task['error'] + colors.ENDC)
            exit(1)
