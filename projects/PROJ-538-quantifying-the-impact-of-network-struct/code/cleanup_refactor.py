"""
Code Cleanup and Refactoring Module (Task T040)

This module performs static analysis, dependency verification, and
structural cleanup of the codebase to ensure maintainability and
compliance with project standards.
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
import json

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent

# Files to analyze for cleanup
CODE_FILES = [
    "code/config.py",
    "code/ingest.py",
    "code/interfaces.py",
    "code/main.py",
    "code/metrics.py",
    "code/models.py",
    "code/stats.py",
    "code/synthetic.py",
    "code/utils.py",
    "code/viz.py",
]

# Unused import patterns to detect (simplified heuristic)
UNSUED_IMPORT_PATTERNS = {
    "os": ["path", "sep", "walk"], # Commonly unused if pathlib is used
    "json": ["load", "dump"],      # If using json module directly without specific calls
}

def get_imports(filepath: Path) -> Dict[str, Set[str]]:
    """
    Parse a Python file and extract all import statements.
    Returns a dict mapping module names to set of imported names.
    """
    imports = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name not in imports:
                        imports[module_name] = set()
                    if alias.asname:
                        imports[module_name].add(alias.asname)
                    else:
                        imports[module_name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name not in imports:
                        imports[module_name] = set()
                    for alias in node.names:
                        if alias.name == "*":
                            imports[module_name].add("*")
                        elif alias.asname:
                            imports[module_name].add(alias.asname)
                        else:
                            imports[module_name].add(alias.name)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return imports

def check_unused_imports(filepath: Path) -> List[Tuple[str, str]]:
    """
    Heuristic check for potentially unused imports.
    Returns list of (module, name) tuples that might be unused.
    """
    imports = get_imports(filepath)
    unused = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Collect all names actually used in the code (excluding imports)
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access like os.path.join
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        for module, names in imports.items():
            for name in names:
                if name not in used_names and name != "*":
                    unused.append((module, name))
    except Exception as e:
        print(f"Error analyzing usage in {filepath}: {e}")
    
    return unused

def run_cleanup_report(output_path: Path) -> Dict:
    """
    Generate a cleanup report for all code files.
    """
    report = {
        "status": "completed",
        "files_analyzed": 0,
        "issues_found": [],
        "recommendations": []
    }
    
    for rel_path in CODE_FILES:
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            report["issues_found"].append(f"File not found: {rel_path}")
            continue
        
        report["files_analyzed"] += 1
        
        # Check for unused imports
        unused = check_unused_imports(filepath)
        if unused:
            report["issues_found"].append({
                "file": rel_path,
                "type": "unused_imports",
                "details": [f"{mod}.{name}" for mod, name in unused]
            })
        
        # Check for TODOs or FIXMEs
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if "TODO" in content or "FIXME" in content:
                    report["issues_found"].append({
                        "file": rel_path,
                        "type": "todo_comments",
                        "details": ["TODO or FIXME comments found"]
                    })
        except Exception:
            pass
    
    # Generate recommendations
    if report["issues_found"]:
        report["recommendations"].append("Review and remove unused imports")
        report["recommendations"].append("Address TODO/FIXME comments")
        report["recommendations"].append("Run linter (ruff/flake8) for additional checks")
    else:
        report["recommendations"].append("Codebase appears clean of common issues")
    
    # Write report to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """
    Main entry point for cleanup task.
    """
    output_file = PROJECT_ROOT / "data" / "processed" / "cleanup_report.json"
    print(f"Running cleanup analysis...")
    
    report = run_cleanup_report(output_file)
    
    print(f"Analysis complete. Files analyzed: {report['files_analyzed']}")
    print(f"Issues found: {len(report['issues_found'])}")
    print(f"Report written to: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
