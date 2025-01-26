from typing import Dict, List

from deployflow.core.analysis.ai_analyzer import ai_analysis
from deployflow.core.analysis.fs import init_target


def analyze_repository(target: str, task: str = "") -> Dict[str, List[str] | str]:
    """
    Analyze a repository to extract deployment details.

    Might include other analysis tools in the future, right now it only uses AI.

    Args:
        target (str): Path to the repository (zip, Git repo, or directory).
        task (str): The task provided by the user.

    Returns:
        Dict[str, List[str]]: A dictionary of evidences.
    """
    evidences = {}
    ls, cat, close = init_target(target)
    evidences = ai_analysis(evidences, ls, cat, task)
    close()
    return evidences
