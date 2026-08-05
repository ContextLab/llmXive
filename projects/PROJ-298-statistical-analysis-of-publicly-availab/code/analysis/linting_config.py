"""
Linting configuration and cleanup utilities for code/analysis modules.

This module provides standardized linting rules and cleanup functions
to ensure code quality across all analysis modules.
"""
import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import re


# Standard linting rules based on project requirements
LINTING_RULES = {
    "max_line_length": 100,
    "max_complexity": 15,
    "max_function_length": 50,
    "max_imports_per_module": 20,
    "required_docstring_style": "google",
    "enforce_type_hints": True,
    "enforce_pep8": True,
}

# Files that should be cleaned up
ANALYSIS_MODULES = [
    "trends.py",
    "decomposition.py",
    "clustering.py",
    "correlation.py",
    "bootstrapping.py",
    "generate_trend_results.py",
    "generate_decomposition_results.py",
    "generate_cluster_results.py",
]

def get_module_path(module_name: str, project_root: Optional[Path] = None) -> Path:
    """
    Get the full path to an analysis module.
    
    Args:
        module_name: Name of the module (e.g., 'trends.py')
        project_root: Root directory of the project. Defaults to parent of this file.
        
    Returns:
        Path to the module file
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent
    return project_root / "analysis" / module_name


def check_imports(module_path: Path) -> List[str]:
    """
    Check for problematic imports in a module.
    
    Args:
        module_path: Path to the Python module
        
    Returns:
        List of import-related issues found
    """
    issues = []
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError as e:
        issues.append(f"Syntax error in {module_path.name}: {e}")
        return issues
    except FileNotFoundError:
        issues.append(f"File not found: {module_path}")
        return issues
    
    # Check for wildcard imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.names and node.names[0].name == '*':
                issues.append(f"Wildcard import in {module_path.name}: {node.module}")
    
    # Check for unused imports (basic check)
    imported_names = set()
    defined_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
    
    # Report potentially unused imports (simple heuristic)
    # Note: This is a basic check and may have false positives
    for name in imported_names:
        if name not in defined_names and not name.startswith('_'):
            # Check if it's used in the code (simple string search)
            if content.count(name) < 2:  # Import line + at least one usage
                issues.append(f"Potentially unused import in {module_path.name}: {name}")
    
    return issues


def check_docstrings(module_path: Path) -> List[str]:
    """
    Check for missing or malformed docstrings.
    
    Args:
        module_path: Path to the Python module
        
    Returns:
        List of docstring-related issues found
    """
    issues = []
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except (SyntaxError, FileNotFoundError):
        return issues
    
    # Check module docstring
    if not ast.get_docstring(tree):
        issues.append(f"Missing module docstring in {module_path.name}")
    
    # Check function and class docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                # Skip private methods (starting with underscore)
                if not node.name.startswith('_') or node.name == '__init__':
                    issues.append(
                        f"Missing docstring in {node.name} in {module_path.name}"
                    )
    
    return issues


def check_line_length(module_path: Path, max_length: int = 100) -> List[str]:
    """
    Check for lines exceeding maximum length.
    
    Args:
        module_path: Path to the Python module
        max_length: Maximum allowed line length
        
    Returns:
        List of line length violations
    """
    issues = []
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Remove trailing whitespace and newline
                stripped = line.rstrip()
                if len(stripped) > max_length:
                    issues.append(
                        f"Line {line_num} in {module_path.name} exceeds {max_length} characters: {len(stripped)}"
                    )
    except FileNotFoundError:
        pass
    
    return issues


def check_complexity(module_path: Path, max_complexity: int = 15) -> List[str]:
    """
    Check for functions with high cyclomatic complexity.
    
    Args:
        module_path: Path to the Python module
        max_complexity: Maximum allowed complexity
        
    Returns:
        List of complexity violations
    """
    issues = []
    
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except (SyntaxError, FileNotFoundError):
        return issues
    
    # Simple complexity calculation (number of decision points + 1)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                                    ast.With, ast.Assert, ast.comprehension)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
            
            if complexity > max_complexity:
                issues.append(
                    f"Function {node.name} in {module_path.name} has complexity {complexity} (max: {max_complexity})"
                )
    
    return issues


def run_lint_checks(project_root: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Run all linting checks on analysis modules.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary mapping module names to lists of issues
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    results = {}
    
    for module_name in ANALYSIS_MODULES:
        module_path = get_module_path(module_name, project_root)
        if not module_path.exists():
            results[module_name] = [f"Module not found: {module_path}"]
            continue
        
        issues = []
        issues.extend(check_imports(module_path))
        issues.extend(check_docstrings(module_path))
        issues.extend(check_line_length(module_path, LINTING_RULES["max_line_length"]))
        issues.extend(check_complexity(module_path, LINTING_RULES["max_complexity"]))
        
        results[module_name] = issues if issues else []
    
    return results


def generate_lint_report(results: Dict[str, List[str]]) -> str:
    """
    Generate a formatted linting report.
    
    Args:
        results: Dictionary from run_lint_checks()
        
    Returns:
        Formatted report string
    """
    report_lines = ["Linting Report for Analysis Modules", "=" * 40, ""]
    
    total_issues = 0
    modules_with_issues = 0
    
    for module_name, issues in results.items():
        if issues:
            modules_with_issues += 1
            total_issues += len(issues)
            report_lines.append(f"[{module_name}] ({len(issues)} issues):")
            for issue in issues:
                report_lines.append(f"  - {issue}")
            report_lines.append("")
        else:
            report_lines.append(f"[{module_name}] ✓ No issues")
    
    report_lines.append("")
    report_lines.append("-" * 40)
    report_lines.append(f"Total modules checked: {len(results)}")
    report_lines.append(f"Modules with issues: {modules_with_issues}")
    report_lines.append(f"Total issues found: {total_issues}")
    
    if total_issues == 0:
        report_lines.append("\n✓ All modules pass linting checks!")
    
    return "\n".join(report_lines)


def cleanup_analysis_modules(project_root: Optional[Path] = None) -> str:
    """
    Main function to run linting checks and cleanup on analysis modules.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Summary report of linting results
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    print("Running linting checks on analysis modules...")
    results = run_lint_checks(project_root)
    report = generate_lint_report(results)
    
    # Save report to file
    report_path = project_root / "analysis" / "linting_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    print("\n" + report)
    
    return report


def main():
    """Entry point for linting cleanup."""
    cleanup_analysis_modules()


if __name__ == "__main__":
    main()
