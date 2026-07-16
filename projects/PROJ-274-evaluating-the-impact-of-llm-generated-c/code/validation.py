import ast
import json
import os
import glob
import hashlib
import re
from typing import List, Dict, Any, Optional

def calculate_loc(file_path: str) -> int:
    """Calculate Lines of Code (LOC) for a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Filter out empty lines and comments
        code_lines = [
            line for line in lines 
            if line.strip() and not line.strip().startswith('#')
        ]
        return len(code_lines)
    except Exception:
        return 0

def calculate_cyclomatic_complexity(file_path: str) -> int:
    """Calculate Cyclomatic Complexity (CC) for a Python file using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        
        cc = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                                 ast.With, ast.Assert, ast.comprehension)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                # Each 'and' or 'or' adds to complexity
                cc += len(node.values) - 1
        return cc
    except SyntaxError:
        return 0
    except Exception:
        return 0

def analyze_file_metrics(repo_path: str) -> List[Dict[str, Any]]:
    """Scan a repository and return metrics for each Python file."""
    metrics = []
    py_files = glob.glob(os.path.join(repo_path, "**", "*.py"), recursive=True)
    
    # Exclude common non-source directories
    exclude_dirs = {'__pycache__', '.git', 'venv', 'env', '.tox', 'node_modules'}
    
    for file_path in py_files:
        # Check if file is in an excluded directory
        parts = file_path.replace(repo_path, '').split(os.sep)
        if any(p in exclude_dirs for p in parts):
            continue
        
        loc = calculate_loc(file_path)
        cc = calculate_cyclomatic_complexity(file_path)
        
        metrics.append({
            "file": file_path,
            "loc": loc,
            "cyclomatic_complexity": cc
        })
    
    return metrics

def scan_repository_for_metrics(repo_path: str) -> Dict[str, Any]:
    """Aggregate metrics for an entire repository."""
    file_metrics = analyze_file_metrics(repo_path)
    total_loc = sum(m['loc'] for m in file_metrics)
    total_cc = sum(m['cyclomatic_complexity'] for m in file_metrics)
    
    return {
        "total_loc": total_loc,
        "total_cyclomatic_complexity": total_cc,
        "file_count": len(file_metrics),
        "average_cc": total_cc / len(file_metrics) if file_metrics else 0
    }

def check_documentation_criteria(repo_path: str) -> Dict[str, Any]:
    """
    Check if a repository meets basic documentation criteria:
    - Has a README (README.md, README.rst, README.txt)
    - Has a setup file (setup.py, pyproject.toml, setup.cfg)
    - Has API documentation (docs/ folder or similar)
    """
    criteria = {
        "has_readme": False,
        "has_setup_file": False,
        "has_api_docs": False,
        "details": {}
    }
    
    # Check for README
    readme_patterns = ['README.md', 'README.rst', 'README.txt', 'readme.md']
    for pattern in readme_patterns:
        if os.path.exists(os.path.join(repo_path, pattern)):
            criteria["has_readme"] = True
            criteria["details"]["readme_file"] = pattern
            break
    
    # Check for setup files
    setup_files = ['setup.py', 'pyproject.toml', 'setup.cfg']
    for sf in setup_files:
        if os.path.exists(os.path.join(repo_path, sf)):
            criteria["has_setup_file"] = True
            criteria["details"]["setup_file"] = sf
            break
    
    # Check for docs folder
    if os.path.isdir(os.path.join(repo_path, 'docs')):
        criteria["has_api_docs"] = True
        criteria["details"]["docs_folder"] = "docs/"
    
    return criteria

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """
    Evaluate a repository against the selection rubric.
    Returns a score and pass/fail status.
    Criteria: Setup instructions, API ref, Architecture docs.
    """
    doc_check = check_documentation_criteria(repo_path)
    
    # Scoring logic (simple weighted sum)
    score = 0
    details = {}
    
    if doc_check["has_readme"]:
        score += 40
        details["readme"] = "Present"
    else:
        details["readme"] = "Missing"
        
    if doc_check["has_setup_file"]:
        score += 30
        details["setup"] = "Present"
    else:
        details["setup"] = "Missing"
        
    if doc_check["has_api_docs"]:
        score += 30
        details["api_docs"] = "Present"
    else:
        details["api_docs"] = "Missing"
    
    # Threshold: Must have at least README and Setup file to pass
    passed = doc_check["has_readme"] and doc_check["has_setup_file"]
    
    return {
        "score": score,
        "passed": passed,
        "details": details
    }

def run_rubric_on_candidates(repos: List[str]) -> List[Dict[str, Any]]:
    """Run the rubric on a list of repository paths."""
    results = []
    for repo in repos:
        if os.path.exists(repo):
            result = evaluate_repository_rubric(repo)
            result["repo_path"] = repo
            results.append(result)
    return results

def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Basic validation of data against a schema (simplified)."""
    # In a real implementation, use jsonschema library
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            return False
    return True

def validate_data_file(file_path: str, schema_path: str) -> bool:
    """Validate a data file against a schema."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        schema = load_schema_from_file(schema_path)
        return validate_json_schema(data, schema)
    except Exception:
        return False

def collect_covariates(repo_path: str) -> Dict[str, Any]:
    """Collect covariates for a repository (LOC, CC, etc.)."""
    metrics = scan_repository_for_metrics(repo_path)
    return {
        "repo": repo_path,
        "loc": metrics["total_loc"],
        "cyclomatic_complexity": metrics["total_cyclomatic_complexity"],
        "average_cc": metrics["average_cc"]
    }

def generate_covariates_json(repos: List[str], output_path: str):
    """Generate a JSON file with covariates for multiple repositories."""
    covariates = []
    for repo in repos:
        if os.path.exists(repo):
            covariates.append(collect_covariates(repo))
    
    with open(output_path, 'w') as f:
        json.dump(covariates, f, indent=2)

def main():
    """Entry point for validation module tests."""
    print("Validation module loaded successfully.")

if __name__ == "__main__":
    main()
