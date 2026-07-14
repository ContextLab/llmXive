import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# Default weights for regularity score calculation
DEFAULT_DIR_WEIGHT = 0.4
DEFAULT_TEST_WEIGHT = 0.3
DEFAULT_IMPORT_WEIGHT = 0.3

# Default baseline score for edge cases
DEFAULT_BASELINE_SCORE = 0.0


def calculate_dir_score(repo_path: Path) -> float:
    """
    Calculate directory structure score.
    Returns a value between 0.0 and 1.0 based on presence of standard directories.
    
    Standard directories: src/, tests/, docs/
    Score is linear interpolation based on presence of these directories.
    """
    if not repo_path.exists() or not repo_path.is_dir():
        return 0.0
    
    required_dirs = {'src', 'tests', 'docs'}
    found_dirs = set()
    
    for dir_name in required_dirs:
        if (repo_path / dir_name).is_dir():
            found_dirs.add(dir_name)
    
    if len(required_dirs) == 0:
        return 1.0
    
    return len(found_dirs) / len(required_dirs)


def calculate_test_score(repo_path: Path) -> float:
    """
    Calculate test presence score.
    Returns 1.0 if tests/ directory exists, 0.0 otherwise.
    """
    if not repo_path.exists() or not repo_path.is_dir():
        return 0.0
    
    tests_dir = repo_path / 'tests'
    if tests_dir.is_dir():
        return 1.0
    
    return 0.0


def extract_imports_from_file(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    Extract absolute and relative imports from a Python file.
    
    Returns:
        Tuple of (absolute_imports, relative_imports)
    """
    absolute_imports = []
    relative_imports = []
    
    if not file_path.exists() or not file_path.is_file():
        return absolute_imports, relative_imports
    
    # Pattern to match import statements
    import_pattern = re.compile(
        r'^\s*(?:from\s+(\.?)(\w+(?:\.\w+)*)\s+import\s+.*'
        r'|import\s+(\w+(?:\.\w+)*))',
        re.MULTILINE
    )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return absolute_imports, relative_imports
    
    for match in import_pattern.finditer(content):
        from_part = match.group(1)  # dots for from imports
        from_module = match.group(2)  # module for from imports
        import_module = match.group(3)  # module for import statements
        
        if from_part:  # from import
            if from_part.startswith('.'):
                relative_imports.append(from_module or '')
            else:
                absolute_imports.append(from_module)
        elif import_module:  # import statement
            absolute_imports.append(import_module)
    
    return absolute_imports, relative_imports


def calculate_import_score(repo_path: Path) -> float:
    """
    Calculate import pattern score.
    Returns ratio of absolute imports to total imports.
    Returns 0.0 if no imports are found or directory doesn't exist.
    """
    if not repo_path.exists() or not repo_path.is_dir():
        return 0.0
    
    total_absolute = 0
    total_relative = 0
    
    # Find all Python files
    py_files = list(repo_path.rglob('*.py'))
    
    for py_file in py_files:
        abs_imports, rel_imports = extract_imports_from_file(py_file)
        total_absolute += len(abs_imports)
        total_relative += len(rel_imports)
    
    total_imports = total_absolute + total_relative
    
    if total_imports == 0:
        return 0.0
    
    return total_absolute / total_imports


def calculate_regularity_score(
    repo_path: Path,
    w_dir: float = DEFAULT_DIR_WEIGHT,
    w_test: float = DEFAULT_TEST_WEIGHT,
    w_import: float = DEFAULT_IMPORT_WEIGHT,
    baseline: float = DEFAULT_BASELINE_SCORE
) -> float:
    """
    Calculate overall regularity score for a repository.
    
    Formula: w_dir * dir_score + w_test * test_score + w_import * import_score
    
    Args:
        repo_path: Path to the repository
        w_dir: Weight for directory structure score
        w_test: Weight for test presence score
        w_import: Weight for import pattern score
        baseline: Default score to return for edge cases (missing files, etc.)
    
    Returns:
        Regularity score between 0.0 and 1.0, or baseline for edge cases
    """
    if not repo_path or not repo_path.exists():
        return baseline
    
    try:
        dir_score = calculate_dir_score(repo_path)
        test_score = calculate_test_score(repo_path)
        import_score = calculate_import_score(repo_path)
        
        # Handle extreme irregularity case
        # If all scores are 0, return baseline
        if dir_score == 0.0 and test_score == 0.0 and import_score == 0.0:
            return baseline
        
        # Calculate weighted sum
        regularity_score = (
            w_dir * dir_score +
            w_test * test_score +
            w_import * import_score
        )
        
        # Ensure score is within valid range [0.0, 1.0]
        return max(0.0, min(1.0, regularity_score))
    
    except Exception:
        # Fallback for any unexpected errors
        return baseline


def analyze_repository(
    repo_path: Path,
    weights: Optional[Dict[str, float]] = None,
    baseline: float = DEFAULT_BASELINE_SCORE
) -> Dict[str, float]:
    """
    Analyze a repository and return detailed scores.
    
    Args:
        repo_path: Path to the repository
        weights: Optional dictionary of weights (dir, test, import)
        baseline: Default score for edge cases
    
    Returns:
        Dictionary containing individual scores and overall regularity score
    """
    if weights is None:
        weights = {
            'dir': DEFAULT_DIR_WEIGHT,
            'test': DEFAULT_TEST_WEIGHT,
            'import': DEFAULT_IMPORT_WEIGHT
        }
    
    dir_score = calculate_dir_score(repo_path)
    test_score = calculate_test_score(repo_path)
    import_score = calculate_import_score(repo_path)
    
    regularity_score = calculate_regularity_score(
        repo_path,
        w_dir=weights['dir'],
        w_test=weights['test'],
        w_import=weights['import'],
        baseline=baseline
    )
    
    return {
        'dir_score': dir_score,
        'test_score': test_score,
        'import_score': import_score,
        'regularity_score': regularity_score
    }


def main():
    """
    Main entry point for command-line usage.
    Analyzes repositories and prints scores.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python static_analysis.py <repo_path> [baseline_score]")
        print("  repo_path: Path to the repository to analyze")
        print("  baseline_score: Optional default score for edge cases (default: 0.0)")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    baseline = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BASELINE_SCORE
    
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    scores = analyze_repository(repo_path, baseline=baseline)
    
    print(f"Analysis for: {repo_path}")
    print(f"  Directory Score: {scores['dir_score']:.3f}")
    print(f"  Test Score: {scores['test_score']:.3f}")
    print(f"  Import Score: {scores['import_score']:.3f}")
    print(f"  Regularity Score: {scores['regularity_score']:.3f}")


if __name__ == '__main__':
    main()