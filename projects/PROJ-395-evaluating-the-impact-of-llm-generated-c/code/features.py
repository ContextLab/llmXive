"""
Code feature extraction module.

This module extracts static code features for correlation analysis with
memory usage. Features include:
    - Lines of Code (LOC)
    - Cyclomatic Complexity
    - Library import counts
    - Normalized code text

Key Functions:
    - extract_loc: Count lines of code
    - calculate_cyclomatic_complexity: Compute complexity using AST
    - count_library_imports: Count import statements
    - normalize_code_text: Standardize code for comparison
    - extract_feature_vector: Combine all features

Usage:
    from features import extract_feature_vector
    features = extract_feature_vector(code_text)
    print(f"LOC: {features['loc']}, Complexity: {features['complexity']}")
"""

import re
import string
from pathlib import Path
from typing import List, Dict, Any, Optional

import ast
import networkx as nx

from config import DATASET_MANIFEST_PATH


def normalize_code_text(code: str) -> str:
    """
    Normalize code text by removing whitespace and comments.

    Args:
        code: Raw code string.

    Returns:
        str: Normalized code without extra whitespace or comments.
    """
    # Remove comments
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    # Remove docstrings
    code = re.sub(r'"""[\s\S]*?"""', '', code)
    code = re.sub(r"'''[\s\S]*?'''", '', code)
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    return code.strip()


def extract_loc(code: str) -> int:
    """
    Extract Lines of Code (LOC) from a code string.

    Counts non-empty, non-comment lines.

    Args:
        code: Code string to analyze.

    Returns:
        int: Number of lines of code.
    """
    lines = code.split('\n')
    loc = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            loc += 1
    return loc


def calculate_cyclomatic_complexity(code: str) -> int:
    """
    Calculate cyclomatic complexity using AST and NetworkX.

    Cyclomatic complexity measures the number of linearly independent paths
    through the code. Higher complexity indicates more complex control flow.

    Args:
        code: Code string to analyze.

    Returns:
        int: Cyclomatic complexity score.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0  # Return 0 for invalid code

    # Count decision points
    complexity = 1  # Base complexity
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1
            if node.ifs:
                complexity += len(node.ifs)

    return complexity


def count_library_imports(code: str) -> int:
    """
    Count the number of library import statements.

    Args:
        code: Code string to analyze.

    Returns:
        int: Number of import statements.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            count += 1

    return count


def get_manifest_version() -> Optional[str]:
    """
    Get the version of the dataset manifest.

    Returns:
        str or None: Version string if manifest exists, None otherwise.
    """
    manifest_path = Path(DATASET_MANIFEST_PATH)
    if not manifest_path.exists():
        return None

    import yaml
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    if manifest and 'datasets' in manifest:
        # Return version of first dataset
        for dataset_info in manifest['datasets'].values():
            return dataset_info.get('version')
    return None


def extract_feature_vector(code: str) -> Dict[str, Any]:
    """
    Extract all features from a code string.

    Args:
        code: Code string to analyze.

    Returns:
        Dict[str, Any]: Dictionary of feature values.
    """
    return {
        'loc': extract_loc(code),
        'complexity': calculate_cyclomatic_complexity(code),
        'imports': count_library_imports(code),
        'normalized': normalize_code_text(code)
    }


def calculate_memory_per_loc(memory_bytes: float, loc: int) -> float:
    """
    Calculate memory per line of code (DESCRIPTIVE ONLY).

    WARNING: This is a descriptive metric only. Do NOT use in regression
    analysis as it creates spurious correlations (memory/LOC vs LOC).

    Args:
        memory_bytes: Peak memory in bytes.
        loc: Lines of code.

    Returns:
        float: Memory per LOC, or 0.0 if LOC is 0.
    """
    if loc <= 0:
        return 0.0
    return memory_bytes / loc


if __name__ == '__main__':
    # Simple test
    test_code = """
    import os
    import sys

    def hello():
        if True:
            print("Hello")
        else:
            print("World")
    """

    features = extract_feature_vector(test_code)
    print(f"LOC: {features['loc']}")
    print(f"Complexity: {features['complexity']}")
    print(f"Imports: {features['imports']}")