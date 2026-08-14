"""
Validation module for repository selection, metrics, and data schema validation.
Extends existing API surface with schema validation logic.
"""

import ast
import json
import os
import glob
import hashlib
import re
import yaml
from typing import List, Dict, Any, Tuple, Optional

# --- Existing API Surface (Preserved) ---
# These functions are already implemented by previous tasks (T021a, T021c, T021d, T030a)
# and must remain exactly as they are.

def calculate_loc(file_path: str) -> int:
    """Calculate Lines of Code for a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        # Simple LOC: non-empty, non-comment lines
        loc = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        return loc
    except Exception:
        return 0

def calculate_cyclomatic_complexity(file_path: str) -> int:
    """Calculate Cyclomatic Complexity using a basic AST approach."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
        
        complexity = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    except Exception:
        return 0

def analyze_file_metrics(file_path: str) -> Dict[str, Any]:
    """Analyze a single file for LOC and CC."""
    return {
        "path": file_path,
        "loc": calculate_loc(file_path),
        "cc": calculate_cyclomatic_complexity(file_path)
    }

def scan_repository_for_metrics(repo_path: str) -> List[Dict[str, Any]]:
    """Scan a repository for Python files and collect metrics."""
    metrics = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                metrics.append(analyze_file_metrics(file_path))
    return metrics

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return ""

def update_checksums(checksums_file: str, new_entries: Dict[str, str]):
    """Update the checksums file with new entries."""
    existing = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, 'r') as f:
            for line in f:
                if ':' in line:
                    key, val = line.strip().split(':', 1)
                    existing[key] = val
    existing.update(new_entries)
    with open(checksums_file, 'w') as f:
        for k, v in existing.items():
            f.write(f"{k}:{v}\n")

def check_documentation_criteria(repo_path: str) -> Dict[str, Any]:
    """Check if repo has required documentation files."""
    files = os.listdir(repo_path)
    has_readme = any('readme' in f.lower() for f in files)
    has_setup = any('setup' in f.lower() for f in files) or any('install' in f.lower() for f in files)
    has_api_ref = any('api' in f.lower() and ('ref' in f.lower() or 'doc' in f.lower()) for f in files)
    return {
        "has_readme": has_readme,
        "has_setup": has_setup,
        "has_api_ref": has_api_ref,
        "score": (1 if has_readme else 0) + (1 if has_setup else 0) + (1 if has_api_ref else 0)
    }

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """Evaluate a repository against the selection rubric."""
    metrics = scan_repository_for_metrics(repo_path)
    doc_check = check_documentation_criteria(repo_path)
    
    total_loc = sum(m['loc'] for m in metrics)
    total_cc = sum(m['cc'] for m in metrics)
    
    return {
        "repo_path": repo_path,
        "metrics": metrics,
        "total_loc": total_loc,
        "total_cc": total_cc,
        "documentation": doc_check,
        "rubric_score": doc_check['score'],
        "passed": doc_check['score'] >= 2  # At least 2/3 criteria
    }

def run_rubric_on_candidates(candidates: List[str]) -> Dict[str, Any]:
    """Run the rubric on a list of candidate repositories."""
    results = []
    for candidate in candidates:
        if os.path.exists(candidate):
            res = evaluate_repository_rubric(candidate)
            results.append(res)
    return {"candidates": results}

def collect_metrics_for_covariates(repo_metrics_path: str) -> List[Dict[str, Any]]:
    """Collect metrics for covariate adjustment."""
    # This reads from the metrics generated by T021c
    if os.path.exists(repo_metrics_path):
        with open(repo_metrics_path, 'r') as f:
            return json.load(f)
    return []

def collect_covariates(repo_metrics: List[Dict[str, Any]], matching_report: Dict[str, Any]) -> Dict[str, Any]:
    """Combine metrics and matching report into covariates."""
    return {
        "metrics": repo_metrics,
        "matching_quality": matching_report.get("quality_score", 0),
        "total_loc": sum(m.get("total_loc", 0) for m in repo_metrics),
        "total_cc": sum(m.get("total_cc", 0) for m in repo_metrics)
    }

def generate_covariates_json(covariates: Dict[str, Any], output_path: str):
    """Save covariates to JSON."""
    with open(output_path, 'w') as f:
        json.dump(covariates, f, indent=2)

# --- NEW API: Schema Validation (Task T033) ---

def run_schema_validation(data: Any, schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate data against a YAML schema.
    
    Args:
        data: The JSON data to validate (list of participant logs).
        schema: The schema definition loaded from YAML.
    
    Returns:
        Tuple of (is_valid: bool, report: Dict)
    """
    errors = []
    warnings = []
    
    if not isinstance(data, list):
        errors.append("Root element must be a list of records.")
        return False, {"errors": errors, "warnings": warnings, "valid": False}

    required_fields = schema.get("required_fields", [])
    field_types = schema.get("field_types", {})
    optional_fields = schema.get("optional_fields", [])

    for i, record in enumerate(data):
        if not isinstance(record, dict):
            errors.append(f"Record {i} is not a dictionary.")
            continue

        # Check required fields
        for field in required_fields:
            if field not in record:
                errors.append(f"Record {i}: Missing required field '{field}'.")

        # Check types
        for field, expected_type in field_types.items():
            if field in record:
                value = record[field]
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Record {i}: Field '{field}' must be string, got {type(value).__name__}.")
                elif expected_type == "integer" and not isinstance(value, int):
                    errors.append(f"Record {i}: Field '{field}' must be integer, got {type(value).__name__}.")
                elif expected_type == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Record {i}: Field '{field}' must be float, got {type(value).__name__}.")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Record {i}: Field '{field}' must be boolean, got {type(value).__name__}.")
                elif expected_type == "list" and not isinstance(value, list):
                    errors.append(f"Record {i}: Field '{field}' must be list, got {type(value).__name__}.")

        # Check optional fields exist (just logging, not error)
        for field in optional_fields:
            if field not in record:
                warnings.append(f"Record {i}: Optional field '{field}' missing.")

    is_valid = len(errors) == 0
    report = {
        "valid": is_valid,
        "record_count": len(data),
        "errors": errors,
        "warnings": warnings
    }
    return is_valid, report

def save_validation_report(report: Dict[str, Any], output_path: str):
    """Save the validation report to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def main():
    """CLI entry point for validation."""
    import sys
    if len(sys.argv) < 3:
        print("Usage: python validation.py <data_json> <schema_yaml> <output_json>")
        sys.exit(1)
    
    data_path = sys.argv[1]
    schema_path = sys.argv[2]
    output_path = sys.argv[3]

    with open(data_path, 'r') as f:
        data = json.load(f)
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    is_valid, report = run_schema_validation(data, schema)
    save_validation_report(report, output_path)
    
    if is_valid:
        print("Validation passed.")
        sys.exit(0)
    else:
        print("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
