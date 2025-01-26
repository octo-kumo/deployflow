import logging
from datetime import datetime

import typer
from typing import Optional

from deployflow.core import colors
from deployflow.logger import logger

app = typer.Typer(help="""
AI AutoDeployment System
""", rich_markup_mode="rich", add_completion=True)


@app.callback(invoke_without_command=True, no_args_is_help=True)
def default():
    pass


@app.command(rich_help_panel="AI assisted deployment")
def deploy(
        command: str = typer.Argument(
            '',
            help="Natural language deployment command, e.g. 'Deploy Flask app on AWS'"
        ),
        repo: Optional[str] = typer.Option(
            "",
            "--repo", "-r",
            help="Path/URL to repository or zip file"
        ),
        evidence_file: Optional[str] = typer.Option(
            None,
            "--evidence-file", '-e',
            help="Path to AI analysis evidence file"
        ),
        analyze: bool = typer.Option(
            False,
            "--analyze-only",
            help="Only analyze and repository, do not deploy"
        ),
        # dry_run: bool = typer.Option(
        #     False,
        #     "--dry-run",
        #     help="Simulate deployment without making changes"
        # ),
        verbose: bool = typer.Option(
            False, "--verbose", "-v", help="Enable verbose output"
        ),
):
    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    if not command:
        command = input("What would you like to do?: ")
        if not command:
            typer.echo("No command specified, exiting")
            raise typer.Exit()
    if not repo:
        repo = input("Enter repository path/URL/file path/folder path (.): ") or "."
    _deploy_app(command, repo, analyze, evidence_file)


def _deploy_app(command: str, repo: str, analyze: bool, evidence_file: str = None):
    # Implementation placeholder
    logger.debug(f"Would deploy {repo} with command: {command}")
    if analyze:
        logger.debug("Analyze only mode enabled - no deployment made")
    if evidence_file:
        logger.debug(f"Using evidence file {evidence_file}")
        print(colors.BOLD + f"Using evidence file {evidence_file}" + colors.ENDC)
        with open(evidence_file, "r") as f:
            import json
            evidences = json.load(f)
    else:
        from deployflow.core.analysis.analyze import analyze_repository
        evidences = analyze_repository(repo, command)
        if not evidences["target"]:
            evidences["target"] = input("Enter deployment target (aws): ") or 'aws'
        evidences['target'] = evidences['target'].lower()
        logger.debug(f"analysis complete")
        print(colors.BOLD + "Analysis complete" + colors.ENDC)
        evidence_file = "evidences_" + ''.join(c for c in (repo + str(datetime.now())) if c.isalnum()) + ".json"
        with open(evidence_file, "w") as f:
            import json
            print(f'\t{colors.YELLOW}AI Analysis results saved to {evidence_file}{colors.ENDC}')
            f.write(json.dumps(evidences, indent=2))
    from deployflow.core.deployment.ai_deployer import deploy_target
    deploy_target(repo, command, evidences)


if __name__ == "__main__":
    app()
