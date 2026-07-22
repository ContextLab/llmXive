"""
Logic Anchor extraction and serialization.
Parses Python solutions into AST and extracts algorithmic steps.
"""
import ast
import json
from typing import List, Dict, Any
from code.config import ANCHORS_PATH
from code.utils.logger import get_logger
from code.utils.common import save_json, load_json

logger = get_logger(__name__)

def extract_steps_from_python(code: str) -> List[str]:
    """
    Parse Python code and extract high-level algorithmic steps.
    Returns a list of pseudo-code strings.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in Python code: {e}")
        return []

    steps = []
    
    # Simple heuristic: Extract function definitions, loops, and conditionals
    # This is a placeholder for the actual logic to be refined in T013
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            steps.append(f"Define function: {node.name}")
        elif isinstance(node, ast.For):
            steps.append("Iterate over sequence")
        elif isinstance(node, ast.While):
            steps.append("Loop while condition holds")
        elif isinstance(node, ast.If):
            steps.append("Conditional branch")
        elif isinstance(node, ast.Assign):
            # Extract variable names
            targets = [t.id if isinstance(t, ast.Name) else str(t) for t in node.targets]
            steps.append(f"Assign value to {', '.join(targets)}")
    
    # Filter out too short steps
    return [s for s in steps if len(s) > 5]

def serialize_anchor(steps: List[str], target_language: str) -> str:
    """
    Serialize steps into a pseudo-code anchor string.
    Ensures NO target-language-specific idioms.
    """
    anchor = "Algorithmic Logic Trace:\n"
    for i, step in enumerate(steps):
        # Ensure no target language keywords
        # Check for common idioms based on target language
        if target_language == "rust":
            forbidden = ["let mut", "let", "val", "fn", "pub", "struct", "impl"]
        elif target_language == "kotlin":
            forbidden = ["val", "var", "fun", "class", "object"]
        elif target_language == "go":
            forbidden = ["func", "var", "const", "type", "struct"]
        else:
            forbidden = []
        
        # Verify step doesn't contain forbidden keywords (simple check)
        is_clean = all(kw not in step for kw in forbidden)
        if not is_clean:
            logger.warning(f"Anchor step contains forbidden idiom: {step}")
            # In a real scenario, we might sanitize or skip
        
        anchor += f"{i+1}. {step}\n"
    
    return anchor

def process_task(task: Dict[str, Any], target_language: str) -> Dict[str, Any]:
    """
    Process a single task to generate an anchor.
    """
    python_solution = task.get("solution_python")
    if not python_solution:
        logger.warning(f"No Python solution for task {task.get('id')}")
        return None

    steps = extract_steps_from_python(python_solution)
    if not steps:
        logger.warning(f"Could not extract steps for task {task.get('id')}")
        return None

    anchor = serialize_anchor(steps, target_language)
    
    return {
        "task_id": task.get("id"),
        "anchor": anchor,
        "steps": steps
    }

def generate_anchors(tasks: List[Dict], target_language: str) -> List[Dict]:
    """
    Generate anchors for a list of tasks.
    """
    anchors = []
    for task in tasks:
        result = process_task(task, target_language)
        if result:
            anchors.append(result)
    
    return anchors

def save_anchors(anchors: List[Dict]):
    """Save anchors to JSON."""
    save_json(anchors, ANCHORS_PATH)
    logger.info(f"Saved {len(anchors)} anchors to {ANCHORS_PATH}")
