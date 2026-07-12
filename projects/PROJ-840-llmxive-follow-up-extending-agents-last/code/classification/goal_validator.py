"""
Task Goal Validator Module.

Uses a deterministic regex-based template matcher to extract static constraints
(file paths, variable names) from task descriptions.

This module explicitly overrides the 'local LLM' approach from Plan.md to satisfy
FR-007 by using deterministic regex matching.
"""
import re
from typing import List, Dict, Any

# Regex patterns for static constraints
# Matches quoted or unquoted file paths with extensions (e.g., "data.csv", /tmp/log.txt)
FILE_PATH_PATTERN = re.compile(r'["\']?([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)["\']?')

# Matches variable declarations with common type hints (var, let, const, int, float, str)
# Captures the variable name
VARIABLE_PATTERN = re.compile(r'\b(?:var|let|const|int|float|str)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b')

# Matches Python function definitions
FUNCTION_PATTERN = re.compile(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')

def validate_static_constraints(task_description: str) -> Dict[str, List[str]]:
    """
    Extracts static constraints from the task description using deterministic regex.
    
    This function scans the input `task_description` for:
    1. File paths (strings ending in common extensions)
    2. Variable names (following standard declaration keywords)
    3. Function names (Python `def` statements)
    
    Args:
        task_description (str): The natural language or code-like description of the task.
    
    Returns:
        Dict[str, List[str]]: A dictionary with keys 'files', 'variables', 'functions',
                              each containing a list of unique extracted strings.
    """
    if not task_description or not isinstance(task_description, str):
        return {
            "files": [],
            "variables": [],
            "functions": []
        }

    constraints = {
        "files": [],
        "variables": [],
        "functions": []
    }
    
    # Extract files
    # findall returns all non-overlapping matches
    files = FILE_PATH_PATTERN.findall(task_description)
    # Filter out false positives like single letters or common non-path words if necessary,
    # but for now we rely on the extension requirement in the regex.
    # Deduplicate while preserving order (though order doesn't matter for sets)
    constraints["files"] = list(dict.fromkeys(files))
    
    # Extract variables
    variables = VARIABLE_PATTERN.findall(task_description)
    constraints["variables"] = list(dict.fromkeys(variables))
    
    # Extract functions
    functions = FUNCTION_PATTERN.findall(task_description)
    constraints["functions"] = list(dict.fromkeys(functions))
    
    return constraints

def main():
    """
    CLI entry point for testing the validator on a provided description string.
    Usage: python -m code.classification.goal_validator "Your task description here"
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.classification.goal_validator \"<task_description>\"")
        sys.exit(1)
    
    description = " ".join(sys.argv[1:])
    result = validate_static_constraints(description)
    
    print("Extracted Static Constraints:")
    print(f"  Files: {result['files']}")
    print(f"  Variables: {result['variables']}")
    print(f"  Functions: {result['functions']}")

if __name__ == "__main__":
    main()
