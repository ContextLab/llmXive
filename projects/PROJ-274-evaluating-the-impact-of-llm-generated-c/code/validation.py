import ast
import json
import os
import glob
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple

# --- Metric Calculation Helpers ---

def calculate_loc(tree: ast.AST) -> int:
    """Calculate Lines of Code (LOC) for an AST."""
    if not tree:
        return 0
    lines = set()
    for node in ast.walk(tree):
        if hasattr(node, 'lineno'):
            lines.add(node.lineno)
    return len(lines)

def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate Cyclomatic Complexity (CC) for an AST."""
    if not tree:
        return 1
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                             ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity

def analyze_file_metrics(file_path: str) -> Dict[str, Any]:
    """Analyze a single Python file for LOC and CC."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        return {
            'file': file_path,
            'loc': calculate_loc(tree),
            'cc': calculate_cyclomatic_complexity(tree)
        }
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        return {
            'file': file_path,
            'error': str(e),
            'loc': 0,
            'cc': 0
        }

def scan_repository_for_metrics(repo_path: str) -> Dict[str, Any]:
    """Scan a repository for Python files and aggregate metrics."""
    python_files = glob.glob(os.path.join(repo_path, '**', '*.py'), recursive=True)
    results = []
    total_loc = 0
    total_cc = 0
    for pf in python_files:
        metrics = analyze_file_metrics(pf)
        results.append(metrics)
        total_loc += metrics['loc']
        total_cc += metrics['cc']
    return {
        'files': results,
        'total_loc': total_loc,
        'total_cc': total_cc,
        'file_count': len(results)
    }

# --- Documentation Criteria & Rubric Logic (T021a) ---

def check_documentation_criteria(repo_path: str) -> Dict[str, Any]:
    """
    Check specific documentation criteria for a repository.
    Criteria: Setup Instructions, API Reference, Architecture.
    Returns a dict with scores (0-1) and details for each criterion.
    """
    readme_path = os.path.join(repo_path, 'README.md')
    if not os.path.exists(readme_path):
        return {
            'setup_instructions': {'score': 0, 'found': False, 'reason': 'No README.md'},
            'api_reference': {'score': 0, 'found': False, 'reason': 'No README.md'},
            'architecture': {'score': 0, 'found': False, 'reason': 'No README.md'}
        }

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    # 1. Setup Instructions
    setup_patterns = [r'install', r'setup', r'getting started', r'quickstart', r'installation']
    setup_found = any(re.search(p, content) for p in setup_patterns)
    setup_score = 1.0 if setup_found else 0.0

    # 2. API Reference
    api_patterns = [r'api', r'usage', r'example', r'function', r'class', r'method']
    api_found = any(re.search(p, content) for p in api_patterns)
    api_score = 1.0 if api_found else 0.0

    # 3. Architecture
    arch_patterns = [r'architecture', r'structure', r'components', r'design', r'overview']
    arch_found = any(re.search(p, content) for p in arch_patterns)
    arch_score = 1.0 if arch_found else 0.0

    return {
        'setup_instructions': {
            'score': setup_score,
            'found': setup_found,
            'reason': 'Setup instructions found' if setup_found else 'No setup instructions detected'
        },
        'api_reference': {
            'score': api_score,
            'found': api_found,
            'reason': 'API reference found' if api_found else 'No API reference detected'
        },
        'architecture': {
            'score': arch_score,
            'found': arch_found,
            'reason': 'Architecture description found' if arch_found else 'No architecture description detected'
        }
    }

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """
    Evaluate a repository against the full selection rubric.
    Combines documentation criteria and basic metrics (if available).
    Returns a summary dict with pass/fail status and breakdown.
    """
    doc_criteria = check_documentation_criteria(repo_path)
    
    # Calculate total score (max 3.0)
    total_score = (
        doc_criteria['setup_instructions']['score'] +
        doc_criteria['api_reference']['score'] +
        doc_criteria['architecture']['score']
    )
    
    # Threshold: Must have at least 2 out of 3 criteria met (score >= 2.0)
    threshold = 2.0
    passed = total_score >= threshold

    return {
        'repo_path': repo_path,
        'total_score': total_score,
        'threshold': threshold,
        'passed': passed,
        'criteria': doc_criteria
    }

def run_rubric_on_candidates(candidates: List[str]) -> List[Dict[str, Any]]:
    """
    Run the rubric on a list of candidate repository paths.
    Returns a list of evaluation results.
    """
    results = []
    for candidate in candidates:
        if not os.path.isdir(candidate):
            results.append({
                'repo_path': candidate,
                'error': 'Directory not found',
                'passed': False
            })
            continue
        evaluation = evaluate_repository_rubric(candidate)
        results.append(evaluation)
    return results

# --- Schema Validation Helpers ---

def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Basic JSON schema validation without external libraries.
    Checks for required fields and basic types.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be boolean, got {type(value).__name__}")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{field}' must be array, got {type(value).__name__}")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be object, got {type(value).__name__}")
    
    return len(errors) == 0, errors

def validate_data_file(data_path: str, schema_path: str) -> Dict[str, Any]:
    """Validate a data file against a schema."""
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        schema = load_schema_from_file(schema_path)
        is_valid, errors = validate_json_schema(data, schema)
        return {
            'valid': is_valid,
            'errors': errors,
            'data_path': data_path,
            'schema_path': schema_path
        }
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'errors': [f"JSON Decode Error: {str(e)}"],
            'data_path': data_path,
            'schema_path': schema_path
        }
    except FileNotFoundError as e:
        return {
            'valid': False,
            'errors': [f"File not found: {str(e)}"],
            'data_path': data_path,
            'schema_path': schema_path
        }

# --- Covariate Collection Helpers ---

def collect_covariates(repo_path: str) -> Dict[str, Any]:
    """Collect covariates (LOC, CC, Doc Score) for a repository."""
    metrics = scan_repository_for_metrics(repo_path)
    doc_eval = evaluate_repository_rubric(repo_path)
    return {
        'repo_path': repo_path,
        'loc': metrics['total_loc'],
        'cc': metrics['total_cc'],
        'doc_score': doc_eval['total_score'],
        'doc_details': doc_eval['criteria']
    }

def generate_covariates_json(repos: List[str], output_path: str) -> None:
    """Generate a JSON file with covariates for a list of repositories."""
    covariates = [collect_covariates(repo) for repo in repos]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(covariates, f, indent=2)

# --- Main Entry Point ---

def main():
    """Main entry point for validation script."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python code/validation.py <command> [args...]")
        print("Commands: rubric, metrics, covariates, validate")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'rubric':
        if len(sys.argv) < 3:
            print("Usage: python code/validation.py rubric <repo_path>")
            sys.exit(1)
        repo_path = sys.argv[2]
        result = evaluate_repository_rubric(repo_path)
        print(json.dumps(result, indent=2))

    elif command == 'metrics':
        if len(sys.argv) < 3:
            print("Usage: python code/validation.py metrics <repo_path>")
            sys.exit(1)
        repo_path = sys.argv[2]
        result = scan_repository_for_metrics(repo_path)
        print(json.dumps(result, indent=2))

    elif command == 'covariates':
        if len(sys.argv) < 4:
            print("Usage: python code/validation.py covariates <repo1> <repo2> ... <output_path>")
            sys.exit(1)
        output_path = sys.argv[-1]
        repos = sys.argv[2:-1]
        generate_covariates_json(repos, output_path)
        print(f"Covariates written to {output_path}")

    elif command == 'validate':
        if len(sys.argv) != 4:
            print("Usage: python code/validation.py validate <data_path> <schema_path>")
            sys.exit(1)
        data_path = sys.argv[2]
        schema_path = sys.argv[3]
        result = validate_data_file(data_path, schema_path)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['valid'] else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
