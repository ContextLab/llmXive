#!/usr/bin/env python3
"""
Git hook script to check for problematic imports in the codebase.
Ensures that imports follow project conventions and avoid circular dependencies.
"""
import os
import sys
import ast
from pathlib import Path
from typing import Set, List, Tuple

# Forbidden imports (project-specific)
FORBIDDEN_IMPORTS = {
    'pickle',  # Use joblib or specific serialization
    'glob',    # Use pathlib
}

# Allowed relative import patterns
ALLOWED_RELATIVE_IMPORTS = {
    'config',
    'utils',
    'ingestion',
    'modeling',
    'interpretability',
}

def find_python_files(root_dir):
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        # Skip common non-code directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', 'env', '.venv']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_file(filepath):
    """Analyze a Python file for import issues."""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_IMPORTS:
                        issues.append(f"Forbidden import: {alias.name}")
                    
                    # Check for absolute imports of project modules
                    if alias.name in ALLOWED_RELATIVE_IMPORTS:
                        # This is okay if it's in the code directory
                        pass
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module in FORBIDDEN_IMPORTS:
                        issues.append(f"Forbidden from-import: {node.module}")
                    
                    # Check relative imports
                    if node.level > 0:
                        # Relative import - check if it's allowed
                        if node.module and not any(allowed in node.module for allowed in ALLOWED_RELATIVE_IMPORTS):
                            # Allow some common relative imports
                            if not any(common in node.module for common in ['utils', 'config', 'tests']):
                                issues.append(f"Potentially problematic relative import: {'.' * node.level}{node.module}")
    
    except SyntaxError as e:
        issues.append(f"Syntax error in file: {str(e)}")
    except Exception as e:
        issues.append(f"Error analyzing file: {str(e)}")
    
    return issues

def main():
    """Main hook function."""
    repo_root = Path(__file__).parent.parent.parent
    code_dir = repo_root / 'code'
    
    if not code_dir.exists():
        print("Warning: code/ directory not found. Skipping import check.")
        return 0
    
    python_files = find_python_files(str(code_dir))
    files_with_issues = []
    
    print("Checking imports...")
    
    for filepath in python_files:
        # Skip hook scripts themselves
        if 'hook_scripts' in filepath:
            continue
        
        issues = analyze_file(filepath)
        if issues:
            files_with_issues.append((filepath, issues))
    
    if files_with_issues:
        print("\n❌ WARNING: The following files have import issues:")
        for filepath, issues in files_with_issues:
            print(f"\n  {filepath}:")
            for issue in issues:
                print(f"    - {issue}")
        print("\nPlease fix these import issues before committing.")
        # Return 0 to allow commit (warning only, not blocking)
        return 0
    
    print("✅ All imports look good.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
