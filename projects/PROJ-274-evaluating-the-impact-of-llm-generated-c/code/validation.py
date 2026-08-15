"""
Validation and schema generation utilities.
Extends existing validation logic to include schema generation and validation.
"""
import ast
import json
import os
import glob
import hashlib
import re
import yaml
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

# --- Existing Functions (Preserved) ---

def calculate_loc(file_path: str) -> int:
    """Calculate Lines of Code (excluding comments/blank lines)."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        loc = 0
        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if '"""' in stripped or "'''" in stripped:
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    continue
                in_multiline_comment = not in_multiline_comment
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
    """Calculate Cyclomatic Complexity using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
        cc = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                cc += len(node.values) - 1
        return cc
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
    """Scan a repository for Python files and return metrics."""
    metrics = []
    py_files = glob.glob(os.path.join(repo_path, "**", "*.py"), recursive=True)
    for f in py_files:
        metrics.append(analyze_file_metrics(f))
    return metrics

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(checksums_file: str, filename: str, checksum: str):
    """Update checksums file."""
    checksums = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, 'r') as f:
            checksums = json.load(f)
    checksums[filename] = checksum
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def check_documentation_criteria(repo_path: str) -> Dict[str, bool]:
    """Check for presence of Setup, API, Architecture docs."""
    criteria = {
        "has_setup": False,
        "has_api": False,
        "has_architecture": False
    }
    # Look for common files
    files = os.listdir(repo_path)
    readme = None
    for f in files:
        if f.lower().startswith('readme'):
            readme = f
            break
    
    if readme:
        with open(os.path.join(repo_path, readme), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            if 'setup' in content or 'install' in content:
                criteria["has_setup"] = True
            if 'api' in content or 'reference' in content:
                criteria["has_api"] = True
            if 'architecture' in content or 'structure' in content:
                criteria["has_architecture"] = True
    
    return criteria

def calculate_doc_quality_score(criteria: Dict[str, bool]) -> int:
    """Calculate binary score for doc quality."""
    return sum(1 for v in criteria.values() if v)

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """Evaluate a repository against the documentation rubric."""
    metrics = scan_repository_for_metrics(repo_path)
    total_loc = sum(m['loc'] for m in metrics)
    total_cc = sum(m['cc'] for m in metrics)
    doc_criteria = check_documentation_criteria(repo_path)
    doc_score = calculate_doc_quality_score(doc_criteria)
    
    return {
        "repo_path": repo_path,
        "total_loc": total_loc,
        "total_cc": total_cc,
        "doc_criteria": doc_criteria,
        "doc_quality_score": doc_score,
        "passes_rubric": doc_score >= 2 # Example threshold
    }

def run_rubric_on_candidates(candidates: List[str]) -> List[Dict[str, Any]]:
    """Run rubric on a list of candidate repo paths."""
    return [evaluate_repository_rubric(c) for c in candidates]

def collect_metrics_for_covariates(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare metrics for covariate analysis."""
    return [
        {
            "repo": r["repo_path"],
            "loc": r["total_loc"],
            "cc": r["total_cc"]
        } for r in repos
    ]

def collect_covariates(metrics: List[Dict[str, Any]], matching_report: Optional[Dict] = None, doc_scores: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Aggregate covariates."""
    # This is a simplified aggregation logic
    covariates = []
    for m in metrics:
        entry = {
            "repo": m["repo"],
            "loc": m["loc"],
            "cc": m["cc"]
        }
        if doc_scores and m["repo"] in doc_scores:
            entry["doc_quality"] = doc_scores[m["repo"]]
        covariates.append(entry)
    return covariates

def generate_covariates_json(covariates: List[Dict[str, Any]], output_path: str):
    """Save covariates to JSON."""
    with open(output_path, 'w') as f:
        json.dump(covariates, f, indent=2)

# --- New Functions for T030a and T033 ---

def generate_dataset_schema(output_path: str) -> Dict[str, Any]:
    """
    Generate the JSON Schema for participant_logs.json (T030a).
    Defines the expected structure for validation.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Participant Logs",
        "description": "Schema for raw participant onboarding study logs",
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "participant_id",
                "condition",
                "start_time",
                "end_time",
                "help_request_count",
                "cognitive_load_proxy",
                "subjective_rating",
                "status"
            ],
            "properties": {
                "participant_id": {
                    "type": "string",
                    "description": "UUID v4 identifier for the participant",
                    "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
                },
                "condition": {
                    "type": "string",
                    "enum": ["LLM", "Human", "None"],
                    "description": "Documentation condition assigned"
                },
                "start_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO 8601 timestamp of session start"
                },
                "end_time": {
                    "type": ["string", "null"],
                    "format": "date-time",
                    "description": "ISO 8601 timestamp of session end (null if incomplete)"
                },
                "help_request_count": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Number of clarification questions asked"
                },
                "cognitive_load_proxy": {
                    "type": "number",
                    "description": "Composite score of cognitive load"
                },
                "subjective_rating": {
                    "type": ["number", "null"],
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Subjective helpfulness rating (1-5)"
                },
                "status": {
                    "type": "string",
                    "enum": ["complete", "incomplete"],
                    "description": "Session completion status"
                },
                "intervention_flag": {
                    "type": "boolean",
                    "default": false,
                    "description": "True if stop-loss intervention was triggered"
                },
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp": {"type": "string", "format": "date-time"},
                            "content": {"type": "string"},
                            "moderator_tagged": {"type": "boolean"}
                        }
                    },
                    "description": "Detailed log of help requests"
                }
            },
            "additionalProperties": True
        }
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)
    
    return schema

def run_schema_validation(data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against the provided JSON Schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Basic type check
    if not isinstance(data, list):
        errors.append("Root element must be an array.")
        return False, errors

    # Validate each item
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i} is not an object.")
            continue
        
        # Check required fields
        required = schema["items"].get("required", [])
        for field in required:
            if field not in item:
                errors.append(f"Item {i} missing required field: {field}")
        
        # Type checks for specific fields
        if "participant_id" in item:
            if not isinstance(item["participant_id"], str):
                errors.append(f"Item {i}: participant_id must be string")
            # Pattern check
            if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", item["participant_id"]) is None:
                errors.append(f"Item {i}: participant_id invalid UUID format")
        
        if "condition" in item:
            if item["condition"] not in ["LLM", "Human", "None"]:
                errors.append(f"Item {i}: condition must be LLM, Human, or None")
        
        if "help_request_count" in item:
            if not isinstance(item["help_request_count"], int) or item["help_request_count"] < 0:
                errors.append(f"Item {i}: help_request_count must be non-negative integer")
        
        if "status" in item:
            if item["status"] not in ["complete", "incomplete"]:
                errors.append(f"Item {i}: status must be complete or incomplete")

    return len(errors) == 0, errors

def save_validation_report(report: Dict[str, Any], output_path: str):
    """Save the validation report to JSON."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def load_json_file(path: str) -> Any:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def main():
    """Main entry point for validation script."""
    # Default paths
    schema_path = "contracts/dataset.schema.yaml"
    data_path = "data/raw/participant_logs.json"
    report_path = "data/processed/validation_report.json"

    # Check if schema exists, if not generate it
    if not os.path.exists(schema_path):
        print(f"Schema not found at {schema_path}. Generating schema...")
        generate_dataset_schema(schema_path)
        print(f"Schema generated at {schema_path}")

    # Load schema
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    # Load data
    if not os.path.exists(data_path):
        print(f"Data file not found at {data_path}.")
        sys.exit(1)
    
    data = load_json_file(data_path)

    # Validate
    is_valid, errors = run_schema_validation(data, schema)

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "schema_file": schema_path,
        "data_file": data_path,
        "status": "valid" if is_valid else "invalid",
        "valid": is_valid,
        "errors": errors
    }

    save_validation_report(report, report_path)
    print(f"Validation report saved to {report_path}")

    if not is_valid:
        print("Validation failed.")
        sys.exit(1)
    else:
        print("Validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
