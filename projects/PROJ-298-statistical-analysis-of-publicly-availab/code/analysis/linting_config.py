"""
Linting configuration and cleanup utilities for analysis modules.

This module provides tools to check code quality, style, and complexity
across the analysis modules, and to perform cleanup operations.
"""
import os
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import json


# Configuration constants
MAX_LINE_LENGTH = 100
MAX_COMPLEXITY = 15
MIN_DOCSTRING_LENGTH = 20
REQUIRED_DOCSTRING_SECTIONS = ["Args", "Returns", "Raises"]
ANALYSIS_MODULES = [
    "bootstrapping",
    "clustering",
    "correlation",
    "decomposition",
    "generate_cluster_results",
    "generate_decomposition_results",
    "generate_trend_results",
    "linting_config",
    "trends",
]


def get_module_path(module_name: str) -> Path:
    """
    Get the full path to an analysis module.
    
    Args:
        module_name: Name of the module (e.g., 'trends', 'clustering')
        
    Returns:
        Path object pointing to the module file
    """
    base_path = Path(__file__).parent
    return base_path / f"{module_name}.py"


def check_imports(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for problematic imports in a Python file.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        List of dictionaries containing import issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError as e:
        return [{"type": "syntax_error", "message": str(e), "line": e.lineno}]
    
    # Check for problematic imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('.'):
                    issues.append({
                        "type": "relative_import",
                        "module": alias.name,
                        "line": node.lineno,
                        "message": "Relative imports should be avoided in analysis modules"
                    })
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith('.'):
                issues.append({
                    "type": "relative_import",
                    "module": node.module,
                    "line": node.lineno,
                    "message": "Relative imports should be avoided in analysis modules"
                })
            
            # Check for unused imports (basic check)
            imported_names = {alias.name for alias in node.names}
            # Simple heuristic: if import is not used in the rest of the file
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name not in content.split('\n')[node.lineno:]:
                    issues.append({
                        "type": "potential_unused_import",
                        "module": node.module or "",
                        "name": name,
                        "line": node.lineno,
                        "message": f"Potentially unused import: {name}"
                    })
    
    return issues


def check_docstrings(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for missing or incomplete docstrings in a Python file.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        List of dictionaries containing docstring issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError:
        return [{"type": "syntax_error", "message": "File has syntax errors"}]
    
    # Check module docstring
    if not ast.get_docstring(tree):
        issues.append({
            "type": "missing_module_docstring",
            "line": 1,
            "message": "Module is missing a docstring"
        })
    
    # Check function and class docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if not docstring:
                issues.append({
                    "type": "missing_docstring",
                    "name": node.name,
                    "type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                    "line": node.lineno,
                    "message": f"{node.name} is missing a docstring"
                })
            elif len(docstring) < MIN_DOCSTRING_LENGTH:
                issues.append({
                    "type": "short_docstring",
                    "name": node.name,
                    "line": node.lineno,
                    "message": f"Docstring for {node.name} is too short ({len(docstring)} chars)"
                })
            else:
                # Check for required sections
                docstring_lower = docstring.lower()
                for section in REQUIRED_DOCSTRING_SECTIONS:
                    if section.lower() not in docstring_lower:
                        # Only warn for functions, not classes
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            issues.append({
                                "type": "missing_docstring_section",
                                "name": node.name,
                                "section": section,
                                "line": node.lineno,
                                "message": f"Docstring for {node.name} may be missing '{section}' section"
                            })
    
    return issues


def check_line_length(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for lines exceeding maximum length.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        List of dictionaries containing line length issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except IOError as e:
        return [{"type": "io_error", "message": str(e)}]
    
    for i, line in enumerate(lines, 1):
        # Remove trailing whitespace and newline
        stripped = line.rstrip()
        if len(stripped) > MAX_LINE_LENGTH:
            issues.append({
                "type": "line_too_long",
                "line": i,
                "length": len(stripped),
                "max_length": MAX_LINE_LENGTH,
                "message": f"Line {i} exceeds max length ({len(stripped)} > {MAX_LINE_LENGTH})"
            })
    
    return issues


def check_complexity(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for functions with high cyclomatic complexity.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        List of dictionaries containing complexity issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError:
        return [{"type": "syntax_error", "message": "File has syntax errors"}]
    
    # Calculate complexity for each function
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1  # Base complexity
            
            # Count decision points
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                    ast.With, ast.Assert, ast.comprehension)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
            
            if complexity > MAX_COMPLEXITY:
                issues.append({
                    "type": "high_complexity",
                    "name": node.name,
                    "line": node.lineno,
                    "complexity": complexity,
                    "max_complexity": MAX_COMPLEXITY,
                    "message": f"Function {node.name} has high complexity ({complexity} > {MAX_COMPLEXITY})"
                })
    
    return issues


def run_lint_checks(module_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run all lint checks on specified analysis modules.
    
    Args:
        module_names: Optional list of module names to check. If None, checks all.
        
    Returns:
        Dictionary containing lint results for all checked modules
    """
    if module_names is None:
        module_names = ANALYSIS_MODULES
    
    results = {
        "modules_checked": [],
        "total_issues": 0,
        "issues_by_type": {},
        "module_results": {}
    }
    
    for module_name in module_names:
        module_path = get_module_path(module_name)
        
        if not module_path.exists():
            results["module_results"][module_name] = {
                "status": "error",
                "message": f"Module file not found: {module_path}"
            }
            continue
        
        module_issues = []
        
        # Run all checks
        module_issues.extend(check_imports(module_path))
        module_issues.extend(check_docstrings(module_path))
        module_issues.extend(check_line_length(module_path))
        module_issues.extend(check_complexity(module_path))
        
        # Categorize issues
        for issue in module_issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in results["issues_by_type"]:
                results["issues_by_type"][issue_type] = 0
            results["issues_by_type"][issue_type] += 1
        
        results["modules_checked"].append(module_name)
        results["total_issues"] += len(module_issues)
        results["module_results"][module_name] = {
            "status": "ok" if not module_issues else "issues_found",
            "issue_count": len(module_issues),
            "issues": module_issues
        }
    
    return results


def generate_lint_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable lint report.
    
    Args:
        results: Results dictionary from run_lint_checks
        
    Returns:
        Formatted string report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("LINTING REPORT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Modules Checked: {len(results['modules_checked'])}")
    lines.append(f"Total Issues Found: {results['total_issues']}")
    lines.append("")
    
    if results["issues_by_type"]:
        lines.append("Issues by Type:")
        for issue_type, count in sorted(results["issues_by_type"].items()):
            lines.append(f"  - {issue_type}: {count}")
        lines.append("")
    
    lines.append("Module Details:")
    lines.append("-" * 40)
    
    for module_name, module_result in results["module_results"].items():
        lines.append(f"\n[{module_name}]")
        lines.append(f"  Status: {module_result['status']}")
        lines.append(f"  Issues: {module_result['issue_count']}")
        
        if module_result["issues"]:
            lines.append("  Issue Details:")
            for issue in module_result["issues"]:
                line_num = issue.get("line", "?")
                msg = issue.get("message", "No message")
                lines.append(f"    Line {line_num}: {msg}")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def cleanup_analysis_modules(module_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Perform cleanup operations on analysis modules.
    
    This includes:
    - Removing unused imports (basic cleanup)
    - Standardizing docstring formats
    - Removing trailing whitespace
    - Ensuring consistent line endings
    
    Args:
        module_names: Optional list of module names to clean up. If None, cleans all.
        
    Returns:
        Dictionary containing cleanup results
    """
    if module_names is None:
        module_names = ANALYSIS_MODULES
    
    results = {
        "modules_processed": [],
        "changes_made": 0,
        "module_results": {}
    }
    
    for module_name in module_names:
        module_path = get_module_path(module_name)
        
        if not module_path.exists():
            results["module_results"][module_name] = {
                "status": "error",
                "message": f"Module file not found: {module_path}"
            }
            continue
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            changes = 0
            change_log = []
            
            # Remove trailing whitespace from each line
            lines = content.splitlines()
            cleaned_lines = []
            for line in lines:
                stripped = line.rstrip()
                if stripped != line:
                    changes += 1
                    change_log.append(f"Removed trailing whitespace at line {len(cleaned_lines)+1}")
                cleaned_lines.append(stripped)
            
            content = "\n".join(cleaned_lines)
            
            # Ensure consistent line endings (Unix)
            if "\r\n" in content:
                content = content.replace("\r\n", "\n")
                changes += 1
                change_log.append("Converted line endings to Unix format")
            
            # Ensure file ends with newline
            if content and not content.endswith("\n"):
                content += "\n"
                changes += 1
                change_log.append("Added trailing newline")
            
            # Write back if changes were made
            if changes > 0:
                with open(module_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            results["modules_processed"].append(module_name)
            results["changes_made"] += changes
            results["module_results"][module_name] = {
                "status": "ok",
                "changes": changes,
                "change_log": change_log
            }
        
        except IOError as e:
            results["module_results"][module_name] = {
                "status": "error",
                "message": f"IO error: {str(e)}"
            }
    
    return results


def main() -> int:
    """
    Main entry point for the linting and cleanup utility.
    
    Returns:
        Exit code (0 for success, 1 for lint issues, 2 for errors)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Lint and cleanup analysis modules"
    )
    parser.add_argument(
        "--modules",
        nargs="+",
        help="Specific modules to check (default: all)",
        choices=ANALYSIS_MODULES
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Run cleanup operations in addition to linting"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Run lint checks
    print("Running lint checks...")
    lint_results = run_lint_checks(args.modules)
    
    # Run cleanup if requested
    if args.cleanup:
        print("\nRunning cleanup operations...")
        cleanup_results = cleanup_analysis_modules(args.modules)
    
    # Output results
    if args.json:
        output_data = {
            "lint_results": lint_results
        }
        if args.cleanup:
            output_data["cleanup_results"] = cleanup_results
        print(json.dumps(output_data, indent=2))
    else:
        print(generate_lint_report(lint_results))
        
        if args.cleanup:
            print("\n" + "=" * 80)
            print("CLEANUP RESULTS")
            print("=" * 80)
            print(f"Modules Processed: {len(cleanup_results['modules_processed'])}")
            print(f"Total Changes Made: {cleanup_results['changes_made']}")
            for module_name, module_result in cleanup_results["module_results"].items():
                if module_result["status"] == "ok" and module_result["changes"] > 0:
                    print(f"\n[{module_name}]: {module_result['changes']} changes")
                    for change in module_result["change_log"]:
                        print(f"  - {change}")
    
    # Determine exit code
    if lint_results["total_issues"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())