from typing import Dict, Any
from code.utils.common import load_json
from code.config import ANCHORS_PATH, get_path
from code.utils.logger import get_logger
import json

logger = get_logger(__name__)

def build_blind_prompt(task: Dict[str, Any]) -> str:
    """
    Builds a blind prompt for the task.
    The blind prompt contains ONLY the problem statement, asking the model to solve it
    in the target language without any logic hints.
    """
    problem_statement = task.get("problem_statement", "")
    target_language = task.get("target_language", "python")
    
    # Construct a simple prompt
    prompt = f"Please solve the following programming problem in {target_language}:\n\n"
    prompt += f"{problem_statement}\n\n"
    prompt += "Write your solution in the target language."
    
    return prompt

def build_guided_prompt(task: Dict[str, Any], anchor: str) -> str:
    """
    Builds a guided prompt including the logic anchor.
    This prompt provides the problem statement, the failed output (if any),
    and the Partial Logic Trace (anchor) to guide the model.
    """
    problem_statement = task.get("problem_statement", "")
    target_language = task.get("target_language", "python")
    failed_output = task.get("failed_output", "")
    
    prompt = f"Please solve the following programming problem in {target_language}:\n\n"
    prompt += f"{problem_statement}\n\n"
    
    if failed_output:
        prompt += "Previous attempt failed with the following output:\n"
        prompt += f"{failed_output}\n\n"
    
    prompt += "Use the following Partial Logic Trace to guide your solution:\n"
    prompt += f"Logic Steps:\n{anchor}\n\n"
    prompt += "Write your solution in the target language, following the logic steps provided."
    
    return prompt

def load_anchor_for_task(task_id: str, anchors_path: str = None) -> str:
    """
    Loads the anchor for a specific task_id from the anchors.json file.
    """
    if anchors_path is None:
        anchors_path = get_path(ANCHORS_PATH)
    
    try:
        with open(anchors_path, 'r') as f:
            anchors_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Anchor file not found: {anchors_path}")
        raise
    
    for entry in anchors_data:
        if entry.get("task_id") == task_id:
            return entry.get("anchor", "")
    
    logger.warning(f"No anchor found for task_id: {task_id}")
    return ""

def build_prompt_for_task(task: Dict[str, Any], guided: bool = False) -> str:
    """
    Convenience function to build a prompt for a task.
    If guided=True, it loads the corresponding anchor and builds a guided prompt.
    If guided=False, it builds a blind prompt.
    """
    if guided:
        task_id = task.get("task_id")
        if not task_id:
            raise ValueError("Task must have a 'task_id' to build a guided prompt.")
        
        anchor = load_anchor_for_task(task_id)
        if not anchor:
            logger.warning(f"Anchor missing for task {task_id}, falling back to blind prompt.")
            return build_blind_prompt(task)
        
        return build_guided_prompt(task, anchor)
    else:
        return build_blind_prompt(task)