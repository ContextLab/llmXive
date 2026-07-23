"""
Logic Anchor Module for llmXive Multi-LCB Extension.

This module handles the extraction of algorithmic steps from Python ground-truth solutions
and their serialization into language-agnostic pseudo-code/Python anchor strings.

Key Constraints:
- Output MUST be free of target-language-specific idioms (e.g., Rust 'let mut', Kotlin 'val').
- Steps are derived from the AST of the Python solution.
- Handles edge cases where solutions are too short or malformed.
"""

import ast
import json
from typing import List, Dict, Any, Optional, Set

from code.config import ANCHORS_PATH, get_path
from code.utils.logger import get_logger
from code.utils.common import save_json, load_json

logger = get_logger(__name__)

# Keywords to explicitly forbid in anchor serialization to ensure language neutrality
FORBIDDEN_IDIOMS: Set[str] = {
    "let mut", "let mut", "val", "var", "fun", "fn", "impl", "struct", "trait",
    "match", "if let", "while let", "loop", "break", "continue", "return",
    "mut", "ref", "box", "move", "dyn", "async", "await", "yield",
    "lambda", "def", "class", "import", "from", "pass", "elif", "else",
    "try", "except", "finally", "raise", "with", "as", "global", "nonlocal",
    "assert", "del", "print", "input", "range", "len", "str", "int", "float",
    "list", "dict", "set", "tuple", "bool", "None", "True", "False",
    "and", "or", "not", "in", "is", "for", "while", "if",
    "case", "switch", "default", "do", "goto", "sizeof", "typedef", "enum",
    "union", "const", "volatile", "static", "extern", "inline", "register",
    "signed", "unsigned", "short", "long", "double", "char", "void",
    "nullptr", "NULL", "true", "false", "nil", "nil!", "Some", "None", "Ok", "Err"
}

# Specific target language patterns to filter out during serialization
TARGET_LANGUAGE_PATTERNS = {
    "rust": [r"let\s+mut", r"let\s+\w+\s*:", r"fn\s+\w+", r"impl\s+\w+", r"struct\s+\w+", r"match\s+", r"\.unwrap\(\)", r"\.expect\("],
    "kotlin": [r"val\s+", r"var\s+", r"fun\s+", r"object\s+", r"class\s+\w+.*\{", r"interface\s+"],
    "go": [r"func\s+", r"var\s+", r"const\s+", r"type\s+", r"package\s+"],
    "cpp": [r"int\s+", r"void\s+", r"std::", r"cout", r"cin", r"new\s+", r"delete\s+"]
}

def _is_valid_step_node(node: ast.AST) -> bool:
    """
    Determines if an AST node represents a meaningful algorithmic step.
    Excludes trivial imports, docstrings, or empty passes.
    """
    if isinstance(node, ast.Expr):
        # Skip docstrings or simple expressions that don't drive logic
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return False
        if isinstance(node.value, ast.Constant):
            return False
    if isinstance(node, ast.Pass):
        return False
    if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
        return False
    return True

def extract_steps_from_python(source_code: str) -> List[str]:
    """
    Parses Python source code and extracts high-level algorithmic steps.

    Args:
        source_code: The Python ground-truth solution.

    Returns:
        A list of string descriptions representing the algorithmic flow.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.warning(f"Syntax error in source code: {e}")
        return []

    steps = []
    # Traverse top-level nodes and function definitions
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign,
                             ast.If, ast.For, ast.While, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef, ast.Return,
                             ast.Call, ast.BinOp, ast.BoolOp, ast.Compare)):
            # Convert node to a string representation
            step_str = ast.unparse(node)
            
            # Sanitize the step string to remove target-language idioms
            sanitized = sanitize_for_language(step_str)
            
            if sanitized and _is_valid_step_node(node):
                # Only add if it looks like a meaningful logic step
                if len(sanitized) > 5: 
                    steps.append(sanitized)
    
    # Deduplicate while preserving order
    seen = set()
    unique_steps = []
    for step in steps:
        if step not in seen:
            seen.add(step)
            unique_steps.append(step)
    
    return unique_steps[:10]  # Limit to first 10 significant steps to avoid noise

def sanitize_for_language(code_snippet: str) -> str:
    """
    Ensures the code snippet contains NO target-language-specific idioms.
    Replaces or strips forbidden patterns to maintain language neutrality.

    Args:
        code_snippet: A string of code (derived from Python AST).

    Returns:
        A sanitized string safe for use as a logic anchor.
    """
    if not code_snippet:
        return code_snippet

    # Basic cleanup: ensure it's just standard Python-like logic
    # Since the source is Python, we primarily need to ensure we don't accidentally
    # introduce or preserve fragments that look like other languages if we were
    # doing cross-language translation, but here the source is Python.
    # The main risk is if the user provided code contains comments or strings
    # with target language idioms, or if we are reconstructing from a mixed source.
    
    # Check for forbidden idioms in the snippet
    cleaned = code_snippet
    for idiom in FORBIDDEN_IDIOMS:
        # Simple substring check for forbidden idioms in the snippet
        # This is a strict filter as per requirements
        if idiom in cleaned:
            # If a forbidden idiom is found, we must strip or replace it.
            # However, since the source is Python, 'let mut' shouldn't exist unless
            # it's in a string/comment. If it is, we strip the whole snippet if it's
            # purely noise, or replace the specific token.
            # For strict compliance: if a forbidden idiom is present, we assume
            # the snippet is compromised for a language-agnostic anchor.
            # We will remove the snippet if it contains forbidden idioms.
            logger.debug(f"Removing snippet due to forbidden idiom '{idiom}': {code_snippet}")
            return ""

    # Additional check: ensure no target language patterns exist
    for lang, patterns in TARGET_LANGUAGE_PATTERNS.items():
        import re
        for pattern in patterns:
            if re.search(pattern, cleaned):
                logger.debug(f"Removing snippet due to {lang} pattern '{pattern}': {code_snippet}")
                return ""

    return cleaned

def serialize_anchor(steps: List[str], task_id: str) -> str:
    """
    Serializes a list of algorithmic steps into a single anchor string.

    Args:
        steps: List of sanitized step strings.
        task_id: The ID of the task (for logging/context).

    Returns:
        A formatted pseudo-code anchor string.
    """
    if not steps:
        return ""
    
    lines = [f"// Logic Anchor for Task: {task_id}", "// Partial Logic Trace (Language Agnostic):"]
    for i, step in enumerate(steps, 1):
        lines.append(f"  {i}. {step}")
    return "\n".join(lines)

def process_task(task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Processes a single task to generate its logic anchor.

    Args:
        task: A dictionary containing task data (id, python_solution, etc.).

    Returns:
        A dictionary with task_id and anchor, or None if extraction fails.
    """
    task_id = task.get("id")
    python_solution = task.get("python_solution")
    
    if not python_solution:
        logger.warning(f"Task {task_id} has no python_solution. Skipping.")
        return None

    try:
        steps = extract_steps_from_python(python_solution)
        if not steps:
            logger.warning(f"Task {task_id}: No valid steps extracted. Skipping.")
            return None
        
        anchor = serialize_anchor(steps, task_id)
        if not anchor:
            logger.warning(f"Task {task_id}: Anchor serialization resulted in empty string. Skipping.")
            return None

        return {
            "id": task_id,
            "anchor": anchor,
            "step_count": len(steps),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        return None

def generate_anchors(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates anchors for a list of tasks.

    Args:
        tasks: List of task dictionaries.

    Returns:
        List of anchor records.
    """
    anchors = []
    for task in tasks:
        result = process_task(task)
        if result:
            anchors.append(result)
        else:
            logger.info(f"Skipped task {task.get('id')} during anchor generation.")
    return anchors

def save_anchors(anchors: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Saves the generated anchors to a JSON file.

    Args:
        anchors: List of anchor records.
        output_path: Path to save the file. Defaults to ANCHORS_PATH.
    """
    if output_path is None:
        output_path = ANCHORS_PATH
    
    path = get_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    save_json(anchors, path)
    logger.info(f"Saved {len(anchors)} anchors to {path}")

def load_anchors(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads anchors from a JSON file.

    Args:
        input_path: Path to the file. Defaults to ANCHORS_PATH.

    Returns:
        List of anchor records.
    """
    if input_path is None:
        input_path = ANCHORS_PATH
    
    path = get_path(input_path)
    if not path.exists():
        logger.warning(f"Anchor file not found at {path}. Returning empty list.")
        return []
    
    return load_json(path)

def main():
    """
    Main entry point for the logic anchor generation pipeline.
    Reads from the filtered tasks dataset and writes anchors.
    """
    from code.dataset import load_filtered_tasks
    
    # Dependency: T018 produces data/final_tasks_enriched.json
    # We need to load the tasks that passed the filter
    # Since dataset.py might not have a direct loader for 'final_tasks_enriched.json' 
    # as a generic function, we construct the path manually or use config.
    
    from code.config import get_path
    import json
    
    input_path = get_path("data/final_tasks_enriched.json")
    output_path = get_path(ANCHORS_PATH)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Ensure T018 has completed.")
        return

    logger.info(f"Loading tasks from {input_path}")
    with open(input_path, 'r') as f:
        tasks = json.load(f)
    
    if not isinstance(tasks, list):
        # Handle case where file is a dict with a 'tasks' key or similar
        if isinstance(tasks, dict) and 'tasks' in tasks:
            tasks = tasks['tasks']
        else:
            logger.error("Input data is not a list of tasks.")
            return

    logger.info(f"Processing {len(tasks)} tasks for logic anchors.")
    anchors = generate_anchors(tasks)
    
    logger.info(f"Successfully generated {len(anchors)} anchors.")
    save_anchors(anchors)

    # Log summary
    logger.info(f"Anchor generation complete. Output: {output_path}")

if __name__ == "__main__":
    main()