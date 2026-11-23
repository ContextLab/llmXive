"""
Pre-commit hook to check for inefficient imports in Python files.
Flags:
- 'import pandas' without 'as pd' (encourages standard alias)
- 'import numpy' without 'as np'
- 'from numpy import *', 'from pandas import *' (star imports)
- 'import tensorflow' or 'import torch' (heavy ML libs, warn if not in data/analysis)
- 'import sklearn' (should be 'import sklearn' or 'from sklearn import ...')
"""
import ast
import sys
from pathlib import Path

HEAVY_LIBS = {'tensorflow', 'torch', 'keras', 'scikit-learn', 'sklearn'}
REQUIRED_ALIASES = {
    'pandas': 'pd',
    'numpy': 'np',
    'matplotlib.pyplot': 'plt',
}

def check_file(filepath):
    """
    Analyze a single Python file for inefficient import patterns.
    Returns a list of warning messages.
    """
    warnings = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"Syntax error in {filepath}: {e}"]
    except Exception as e:
        return [f"Error reading {filepath}: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in REQUIRED_ALIASES:
                    expected_alias = REQUIRED_ALIASES[name]
                    if not alias.asname or alias.asname != expected_alias:
                        warnings.append(
                            f"{filepath}: Line {node.lineno}: "
                            f"Import '{name}' should use alias 'as {expected_alias}'."
                        )
                if name in HEAVY_LIBS:
                    warnings.append(
                        f"{filepath}: Line {node.lineno}: "
                        f"Import of heavy library '{name}' detected. "
                        f"Ensure this is necessary for the current task."
                    )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in HEAVY_LIBS:
                warnings.append(
                    f"{filepath}: Line {node.lineno}: "
                    f"Import from heavy library '{module}' detected."
                )
            
            # Check for star imports
            for alias in node.names:
                if alias.name == "*":
                    warnings.append(
                        f"{filepath}: Line {node.lineno}: "
                        f"Star import ('from {module} import *') is discouraged."
                    )

    return warnings

def check_inefficient_imports(filenames):
    """
    Check all provided Python files.
    Returns 0 if no warnings found (or only warnings), 1 if syntax errors found.
    Note: This hook currently acts as a linter/warning system. 
    To make it strict, we could return 1 on any warning.
    For now, we return 1 only on syntax errors or if we want to enforce strictness.
    Let's enforce strictness: return 1 if any warning found.
    """
    issues_found = False
    for filename in filenames:
        path = Path(filename)
        if path.suffix != '.py':
            continue
        
        warnings = check_file(path)
        if warnings:
            issues_found = True
            for w in warnings:
                print(w)
    
    if issues_found:
        print("Fix the import issues above before committing.")
        return 1
    return 0

def main():
    if len(sys.argv) < 2:
        print("No Python files to check.")
        return 0
    return check_inefficient_imports(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())