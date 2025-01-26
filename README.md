# TLDR

The project almost works, it analyzes the repository and generates evidence for deployment, creates terraform files, and
bash scripts for deployment.

The entire process is autonomous, but the generated deployment script (to be run on server) is not working correctly.

## Does

Fully functional parts.

- Fully autonomous
    - Except asking user for confirmation when executing commands
- Analyzes repository into evidence file
- Generates terraform files
- Generates bash scripts for deployment
- Execute terraform commands
- Server starts
- Uploads files to server
- SSH key generation
- SSH to server

## Does not

Only the last step is not working.

- Execute the deployment bash script on server
    - The bash script is not working correctly.
    - Generated bash script uses venv, but there is not `venv` on remote.

# How it works

## Step 1: Analysis

- The AI runs almost fully autonomously, searches the repository for _evidence_, such as framework, language, etc.
    - The AI also looks for network settings to change, such as ports, etc.
    - The AI also looks for build commands, such as `npm install`, etc.
    - The AI also looks for runtime commands, such as `npm start`, etc.
- The compiled evidence is saved.

```json
{
  "target": "",
  // Deployment target (e.g. aws, gcp)
  "region": "",
  // Deployment region (defaults to us-east-1)
  "instance_type": "",
  // Instance type (defaults to t2.micro)
  "frameworks": [],
  // Application frameworks (e.g. Flask, Express)
  "platform": [],
  // Runtime platforms (e.g. Python, Node.js)
  "config_files": [],
  // Configuration files found
  "ports": [],
  // Network ports to expose
  "build_commands": [],
  // Dependency/build commands
  "update_commands": [],
  // Necessary changes to files
  "deployment_commands": [],
  // Runtime commands
  "notes": []
  // Warnings/conflicts/notes
}
```

## Step 2: Deployment

The AI is given evidence from before and constructs `main.tf` and `auto-deploy.sh`.

- `main.tf` is a Terraform file that deploys the application to the cloud.
- `auto-deploy.sh` is a bash script that runs on the instance to deploy the application.

It then runs shell commands or edit files to deploy the application.
This runs in a loop until the application is deployed successfully or the AI gives up.

# How to use

```bash
pip install -e .
```

```
 Usage: deployflow deploy [OPTIONS] [COMMAND]

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   command      [COMMAND]  Natural language deployment command, e.g. 'Deploy Flask app on AWS'                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --repo           -r      TEXT  Path/URL to repository or zip file                                                    │
│ --evidence-file  -e      TEXT  Path to AI analysis evidence file [default: None]                                     │
│ --analyze-only                 Only analyze and repository, do not deploy                                            │
│ --verbose        -v            Enable verbose output                                                                 │
│ --help                         Show this message and exit.                                                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Example

Deploy local folder.

```bash
deployflow deploy "deploy this to aws" -r hello_world-main
```

Deploy local zip.

```bash
deployflow deploy "deploy this to aws" -r hello_world-main.zip
```

Deploy git repository.

```bash
deployflow deploy "deploy this to aws" -r "https://github.com/Arvo-AI/hello_world.git"
```

# Dependencies used

- OpenAI
- GitPython
- Requests
- Typer

# Source code structure

## Folder `src/deployflow/core/`

### `ai.py`

- Contains the OpenAI api object.
- Asks user for API key and API endpoint if not found in config file.
- Saves API key and endpoint to config file.
- Config file is located at `~/.deployflow.ini`

### `colors.py`

Fancy ANSI colors for terminal output.

### `utils.py`

Currently only contains `fatal` to print error messages and exit.

## Folder `src/deployflow/core/analysis/`

### `analyze.py`

```python
def analyze_repository(target: str, task: str = "") -> Dict[str, List[str] | str]:
```

- AI-Driven Deployment Analysis: The module uses an AI model to analyze deployment configurations in a repository. It
  identifies and processes key files and directories to extract evidence for deployment automation.
- Dynamic Interaction with AI: Based on the repository structure and content, the AI interacts dynamically in three
  modes: reading directories, reading files, and asking questions for clarification.
- Evidence Accumulation and Processing: Extracts and updates deployment evidence by analyzing directory structures, file
  contents (like README files, Dockerfiles), and user-provided answers.
- Deployment Summary and Next Steps: Provides a summary of findings and determines the next steps, such as reading
  files, asking further questions, or finalizing deployment preparation.

### `fs.py`

- This file contains a function to abstract away the target into three functions: `ls`, `cat`, `close`.
- Used by `analyze.py` to read files in the repository without cloning everything.
- Does not unzip files, and does not download unnecessary files.
    - Uses `sparse-checkout` to download only necessary files for git.

### `prompts.py`

- Contains the system prompt.
- Contains the instruction for the AI.
- Also contains the evidence schema.

## Folder `src/deployflow/core/deployment/`

### `ai_deploy.py`

- Deployment Automation: Automates deployment of tasks for a repository by generating necessary files, like Terraform
  configurations and deployment scripts, and executing required commands.
- Repository Handling: Identifies the repository type (e.g., zip or directory), prepares the target directory, and
  manages source files, including zipping and cleanup.
- AI Integration: Interacts with an AI model to generate deployment configurations and scripts, ensuring correctness and
  handling errors if AI provides invalid responses.
- Key Generation & Command Execution: Creates an SSH key pair for server access and executes system commands like
  terraform init or deployment scripts as part of the process.

### `actions.py`

- `write_file` and `execute_command` functions for the AI to interact with the system.

### `prompts.py`

- Contains the system prompt.
- Contains the instruction for the AI.

# Major Bugs and Issues

1. The deployment script generated by the AI is not working correctly.
2. `auto-deploy.sh` uses `\r\n` line endings, which causes issues on Linux.
    - Fixed
3. The AI does not look for hardcoded urls in files, after reading README.md.
    - Fixed
4. The AI does not generate correct JSON for the evidence file.
    - Fixed

# Future Work

1. The AI will be given SSH access to the server to deploy the application.
    - It will be able to read errors and fix them on the fly.