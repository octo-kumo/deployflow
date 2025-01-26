# How it works

## Step 1: Analysis

- The AI runs almost fully autonomously, searches the repository for _evidence_, such as framework, language, etc.
  - The AI also looks for network settings to change, such as ports, etc.
  - The AI also looks for build commands, such as `npm install`, etc.
  - The AI also looks for runtime commands, such as `npm start`, etc.
- The compiled evidence is saved.

```json
{
    "target": "", // Deployment target (e.g. aws, gcp)
    "region": "", // Deployment region (defaults to us-east-1)
    "instance_type": "", // Instance type (defaults to t2.micro)
    "frameworks": [], // Application frameworks (e.g. Flask, Express)
    "platform": [],  // Runtime platforms (e.g. Python, Node.js)
    "config_files": [], // Configuration files found
    "ports": [],  // Network ports to expose
    "build_commands": [], // Dependency/build commands
    "update_commands": [], // Necessary changes to files
    "deployment_commands": [], // Runtime commands
    "notes": [] // Warnings/conflicts/notes
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
