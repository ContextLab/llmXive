import ast
import json
import os
import glob
import hashlib
import re
import sys
from typing import List, Dict, Any, Optional, Tuple
import yaml

# Constants for metrics
MAX_FILES = 500
MAX_TIME_SECONDS = 2700  # 45 minutes

def calculate_loc(file_path: str) -> int:
    """Calculate Lines of Code (LOC) for a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        # Count non-empty, non-comment lines
        loc = 0
        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_multiline_comment:
                    in_multiline_comment = False
                    continue
                else:
                    if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                        # Single line docstring, count it
                        pass
                    else:
                        in_multiline_comment = True
                        continue
            if in_multiline_comment:
                continue
            if stripped.startswith('#'):
                continue
            loc += 1
        return loc
    except Exception:
        return 0

def calculate_cyclomatic_complexity(file_path: str) -> int:
    """Calculate Cyclomatic Complexity (CC) for a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
        
        cc = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                cc += len(node.values) - 1
        return cc
    except SyntaxError:
        return 0
    except Exception:
        return 0

def analyze_file_metrics(file_path: str) -> Dict[str, Any]:
    """Analyze LOC and CC for a single file."""
    return {
        'file': file_path,
        'loc': calculate_loc(file_path),
        'cc': calculate_cyclomatic_complexity(file_path)
    }

def scan_repository_for_metrics(repo_path: str) -> Tuple[int, int, int]:
    """Scan a repository and return total LOC, total CC, and file count."""
    total_loc = 0
    total_cc = 0
    file_count = 0
    
    python_files = glob.glob(os.path.join(repo_path, '**', '*.py'), recursive=True)
    # Limit to MAX_FILES
    python_files = python_files[:MAX_FILES]
    
    for py_file in python_files:
        # Skip __pycache__ and hidden directories
        if '__pycache__' in py_file or '/.' in py_file:
            continue
        
        metrics = analyze_file_metrics(py_file)
        total_loc += metrics['loc']
        total_cc += metrics['cc']
        file_count += 1
        
        if file_count >= MAX_FILES:
            break
            
    return total_loc, total_cc, file_count

def check_documentation_criteria(repo_path: str) -> Dict[str, bool]:
    """Check for presence of key documentation criteria."""
    criteria = {
        'setup_instructions': False,
        'api_ref': False,
        'architecture': False
    }
    
    # Look for common documentation files
    doc_files = glob.glob(os.path.join(repo_path, '**', '*.{md,txt,rst}'), recursive=True)
    doc_content = ""
    for f in doc_files[:10]:  # Check first 10 docs
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                doc_content += file.read().lower()
        except Exception:
            continue
    
    # Heuristic checks
    if any(kw in doc_content for kw in ['install', 'setup', 'getting started', 'quickstart']):
        criteria['setup_instructions'] = True
    if any(kw in doc_content for kw in ['api', 'reference', 'function', 'method']):
        criteria['api_ref'] = True
    if any(kw in doc_content for kw in ['architecture', 'structure', 'design', 'overview']):
        criteria['architecture'] = True
        
    return criteria

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """Evaluate a repository against the documentation rubric."""
    criteria = check_documentation_criteria(repo_path)
    loc, cc, file_count = scan_repository_for_metrics(repo_path)
    
    # Simple scoring: 1 point per criteria met
    score = sum(1 for v in criteria.values() if v)
    max_score = len(criteria)
    
    return {
        'repo_path': repo_path,
        'criteria_met': criteria,
        'score': score,
        'max_score': max_score,
        'pass': score >= 2,  # Must meet at least 2 criteria
        'metrics': {
            'loc': loc,
            'cc': cc,
            'file_count': file_count
        }
    }

def run_rubric_on_candidates(candidate_repos: List[str]) -> List[Dict[str, Any]]:
    """Run rubric evaluation on a list of candidate repositories."""
    results = []
    for repo in candidate_repos:
        if os.path.isdir(repo):
            result = evaluate_repository_rubric(repo)
            results.append(result)
    return results

def collect_covariates(repo_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect covariate data from repository results."""
    covariates = []
    for res in repo_results:
        covariates.append({
            'repo_path': res['repo_path'],
            'loc': res['metrics']['loc'],
            'cc': res['metrics']['cc'],
            'human_doc_quality_score': res['score'] / res['max_score'] if res['max_score'] > 0 else 0
        })
    return covariates

def generate_covariates_json(repo_results: List[Dict[str, Any]], output_path: str) -> None:
    """Generate the covariates JSON file."""
    covariates = collect_covariates(repo_results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(covariates, f, indent=2)

def run_schema_validation(input_path: str, schema_path: str, output_path: str) -> bool:
    """
    Run schema validation on a JSON file against a YAML schema.
    Returns True if validation passes, False otherwise.
    Writes a validation report to output_path.
    """
    import jsonschema
    
    report = {
        'validated_file': input_path,
        'schema_file': schema_path,
        'valid': False,
        'errors': [],
        'checked_at': None
    }
    
    try:
        # Load schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Load data
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        report['checked_at'] = json.dumps({
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'error_count': len(errors)
        })
        
        if errors:
            report['errors'] = [
                {
                    'path': list(error.absolute_path),
                    'message': error.message,
                    'validator': error.validator
                }
                for error in errors
            ]
            report['valid'] = False
        else:
            report['valid'] = True
            report['errors'] = []
            
    except FileNotFoundError as e:
        report['errors'].append({
            'path': [],
            'message': f"File not found: {e.filename}",
            'validator': 'file_io'
        })
    except json.JSONDecodeError as e:
        report['errors'].append({
            'path': [],
            'message': f"Invalid JSON: {e.msg}",
            'validator': 'json_decode'
        })
    except yaml.YAMLError as e:
        report['errors'].append({
            'path': [],
            'message': f"Invalid YAML schema: {e}",
            'validator': 'yaml_parse'
        })
    except ImportError:
        # Fallback if jsonschema not installed, do basic checks
        # This should ideally not happen in a proper environment
        report['errors'].append({
            'path': [],
            'message': "jsonschema library not installed. Please install it.",
            'validator': 'import_error'
        })
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report['valid']

def main():
    """Main entry point for validation script."""
    # Default paths
    input_file = "data/raw/participant_logs.json"
    schema_file = "contracts/dataset.schema.yaml"
    output_file = "data/processed/validation_report.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        schema_file = sys.argv[2]
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
        
    print(f"Validating {input_file} against {schema_file}...")
    is_valid = run_schema_validation(input_file, schema_file, output_file)
    
    if is_valid:
        print(f"Validation PASSED. Report written to {output_file}")
        sys.exit(0)
    else:
        print(f"Validation FAILED. Report written to {output_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
