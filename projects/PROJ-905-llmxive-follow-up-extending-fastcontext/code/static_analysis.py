import ast
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from config import get_config_dict

def calculate_dir_score(repo_path: str) -> float:
    """
    Calculate directory structure score.
    Checks for src/, tests/, docs/.
    1.0 if all present, 0.0 if none, linear interpolation for partial.
    """
    path = Path(repo_path)
    required_dirs = ['src', 'tests', 'docs']
    present = sum(1 for d in required_dirs if (path / d).exists())
    return present / len(required_dirs)

def calculate_test_score(repo_path: str) -> float:
    """
    Calculate test placement score.
    Normalized depth of tests/ directory.
    """
    path = Path(repo_path)
    tests_dirs = [p for p in path.rglob('tests') if p.is_dir()]
    if not tests_dirs:
        return 0.0
    
    min_depth = min(len(p.relative_to(path).parts) for p in tests_dirs)
    max_expected_depth = 3 # Assume max depth is 3
    return max(0.0, 1.0 - (min_depth / max_expected_depth))

def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Extract imports from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
    except Exception:
        pass
    return imports

def calculate_import_score(repo_path: str) -> float:
    """
    Calculate import graph score.
    Ratio of internal imports + graph density.
    """
    path = Path(repo_path)
    all_imports = set()
    internal_imports = 0
    total_imports = 0
    
    python_files = list(path.rglob('*.py'))
    if not python_files:
        return 0.0
    
    # Build a set of local module names
    local_modules = set()
    for f in python_files:
        local_modules.add(f.stem)
        # Also add parent dirs as potential modules
        for p in f.parents:
            if p != path:
                local_modules.add(p.name)
    
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        total_imports += len(imports)
        for imp in imports:
            if imp in local_modules:
                internal_imports += 1
    
    if total_imports == 0:
        return 0.0
    
    internal_ratio = internal_imports / total_imports
    
    # Graph density approximation: 1 - (unique_imports / total_possible)
    unique_imports = len(all_imports) if all_imports else 1
    density = unique_imports / max(total_imports, 1)
    
    return 0.5 * internal_ratio + 0.5 * (1 - density)

def calculate_regularity_score(repo_path: str) -> float:
    """
    Calculate the total regularity score.
    dir_score + w1 * test_score + w2 * import_score
    """
    config = get_config_dict()
    w1 = config['weights']['w1']
    w2 = config['weights']['w2']
    
    dir_score = calculate_dir_score(repo_path)
    test_score = calculate_test_score(repo_path)
    import_score = calculate_import_score(repo_path)
    
    return dir_score + w1 * test_score + w2 * import_score

def analyze_repository(repo_path: str) -> Dict:
    """Analyze a single repository."""
    score = calculate_regularity_score(repo_path)
    return {
        'repo_id': Path(repo_path).name,
        'regularity_score': score
    }

def main():
    # Demo
    import sys
    if len(sys.argv) < 2:
        print("Usage: python static_analysis.py <repo_path>")
        return
    repo = sys.argv[1]
    result = analyze_repository(repo)
    print(result)

if __name__ == '__main__':
    main()
