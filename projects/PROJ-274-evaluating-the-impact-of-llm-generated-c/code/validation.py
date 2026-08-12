import ast
import json
import os
import glob
import hashlib
import re
import sys
import logging
from typing import List, Dict, Any, Tuple, Optional

# Try to import yaml, but handle if not present (though requirements.txt should have it)
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not installed. Schema validation will be skipped or require manual schema loading.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Code Metrics Logic (Existing) ---

def calculate_loc(tree: ast.AST) -> int:
    """Calculate Lines of Code (logical) from an AST."""
    if not tree:
        return 0
    loc = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            loc += 1
        elif isinstance(node, ast.Assign):
            loc += 1
        elif isinstance(node, ast.AnnAssign):
            loc += 1
        elif isinstance(node, ast.AugAssign):
            loc += 1
        elif isinstance(node, ast.Return):
            loc += 1
        elif isinstance(node, ast.If):
            loc += 1
        elif isinstance(node, ast.For):
            loc += 1
        elif isinstance(node, ast.While):
            loc += 1
        elif isinstance(node, ast.With):
            loc += 1
        elif isinstance(node, ast.Try):
            loc += 1
    return loc

def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate Cyclomatic Complexity from an AST."""
    if not tree:
        return 1
    cc = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            cc += len(node.values) - 1
        elif isinstance(node, (ast.Assert, ast.comprehension)):
            cc += 1
    return cc

def analyze_file_metrics(file_path: str) -> Dict[str, Any]:
    """Analyze a single Python file for metrics."""
    result = {
        "file_path": file_path,
        "loc": 0,
        "cc": 0,
        "error": None
    }
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        result["loc"] = calculate_loc(tree)
        result["cc"] = calculate_cyclomatic_complexity(tree)
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {e}"
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Error processing {file_path}: {e}")
    return result

def scan_repository_for_metrics(repo_path: str) -> List[Dict[str, Any]]:
    """Scan a repository for Python files and collect metrics."""
    metrics = []
    py_files = glob.glob(os.path.join(repo_path, '**', '*.py'), recursive=True)
    # Limit to 500 files as per spec
    py_files = py_files[:500]
    for f in py_files:
        metrics.append(analyze_file_metrics(f))
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
        return "file_not_found"

def update_checksums(checksum_file: str, file_path: str, checksum: str) -> None:
    """Update the checksums file with a new entry."""
    if not os.path.exists(checksum_file):
        with open(checksum_file, 'w') as f:
            f.write("")
    
    with open(checksum_file, 'r') as f:
        lines = f.readlines()
    
    # Remove existing entry for this file if present
    lines = [line for line in lines if not line.strip().startswith(os.path.basename(file_path))]
    
    # Add new entry
    with open(checksum_file, 'a') as f:
        f.write(f"{os.path.basename(file_path)}:{checksum}\n")

# --- Repository Rubric Logic (Existing) ---

def check_documentation_criteria(repo_path: str) -> Dict[str, bool]:
    """Check for presence of standard documentation files."""
    criteria = {
        "setup_instructions": False,
        "api_ref": False,
        "architecture": False
    }
    
    files = os.listdir(repo_path)
    readme_found = any('readme' in f.lower() for f in files)
    docs_folder = os.path.join(repo_path, 'docs')
    docs_exists = os.path.isdir(docs_folder)
    
    criteria["setup_instructions"] = readme_found
    criteria["api_ref"] = any('api' in f.lower() or 'reference' in f.lower() for f in files) or (docs_exists and any('api' in f.lower() for f in os.listdir(docs_folder)))
    criteria["architecture"] = any('arch' in f.lower() or 'design' in f.lower() for f in files) or (docs_exists and any('arch' in f.lower() for f in os.listdir(docs_folder)))
    
    return criteria

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """Evaluate a repository against the selection rubric."""
    metrics = scan_repository_for_metrics(repo_path)
    total_loc = sum(m.get('loc', 0) for m in metrics)
    total_cc = sum(m.get('cc', 0) for m in metrics)
    doc_criteria = check_documentation_criteria(repo_path)
    
    score = 0
    if doc_criteria["setup_instructions"]: score += 1
    if doc_criteria["api_ref"]: score += 1
    if doc_criteria["architecture"]: score += 1
    
    # Heuristic: High complexity or low LOC might be excluded depending on criteria
    # For now, just return the data
    return {
        "repo_path": repo_path,
        "total_loc": total_loc,
        "total_cc": total_cc,
        "doc_criteria": doc_criteria,
        "rubric_score": score,
        "passed": score >= 2 # Example threshold
    }

def run_rubric_on_candidates(candidates: List[str]) -> List[Dict[str, Any]]:
    """Run rubric on a list of candidate repo paths."""
    results = []
    for candidate in candidates:
        if os.path.isdir(candidate):
            results.append(evaluate_repository_rubric(candidate))
        else:
            results.append({"repo_path": candidate, "error": "Not a directory"})
    return results

# --- Covariate Collection (Existing) ---

def collect_covariates(repo_path: str) -> Dict[str, Any]:
    """Collect covariate metrics for a repository."""
    metrics = scan_repository_for_metrics(repo_path)
    loc_values = [m['loc'] for m in metrics if m.get('loc', 0) > 0]
    cc_values = [m['cc'] for m in metrics if m.get('cc', 0) > 0]
    
    return {
        "repo_path": repo_path,
        "total_loc": sum(loc_values),
        "avg_loc": sum(loc_values) / len(loc_values) if loc_values else 0,
        "total_cc": sum(cc_values),
        "avg_cc": sum(cc_values) / len(cc_values) if cc_values else 0,
        "file_count": len(metrics)
    }

def generate_covariates_json(repos: List[str], output_path: str) -> None:
    """Generate a JSON file with covariates for multiple repos."""
    covariates = []
    for repo in repos:
        if os.path.isdir(repo):
            covariates.append(collect_covariates(repo))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(covariates, f, indent=2)
    logger.info(f"Covariates saved to {output_path}")

# --- NEW: Schema Validation Logic ---

def run_schema_validation(data_path: str, schema_path: str, output_path: str) -> Dict[str, Any]:
    """
    Validates a JSON data file against a YAML schema.
    
    Args:
        data_path: Path to the JSON file to validate.
        schema_path: Path to the YAML schema file.
        output_path: Path to write the validation report.
    
    Returns:
        A dictionary containing the validation result and report data.
    """
    report = {
        "data_file": data_path,
        "schema_file": schema_path,
        "valid": False,
        "errors": [],
        "warnings": [],
        "timestamp": None
    }

    # Check input files exist
    if not os.path.exists(data_path):
        report["errors"].append(f"Data file not found: {data_path}")
        save_validation_report(report, output_path)
        return report

    if not os.path.exists(schema_path):
        report["errors"].append(f"Schema file not found: {schema_path}")
        save_validation_report(report, output_path)
        return report

    if not YAML_AVAILABLE:
        report["errors"].append("PyYAML is not installed. Cannot parse schema.")
        save_validation_report(report, output_path)
        return report

    try:
        # Load Schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Load Data
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Basic validation logic (since jsonschema might not be in requirements)
        # We implement a minimal validator based on the specific schema structure we control
        # to avoid adding heavy dependencies if not strictly necessary, 
        # but ideally we would use `jsonschema` library.
        # Given requirements.txt includes common libs, let's assume we can try importing jsonschema.
        
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            report["valid"] = True
            logger.info("Schema validation passed.")
        except ImportError:
            # Fallback to manual validation if jsonschema is not present
            # This is a simplified check for the specific structure defined in contracts/dataset.schema.yaml
            logger.warning("jsonschema library not found. Performing manual basic validation.")
            valid = True
            errors = []
            
            # Check top level keys
            if "metadata" not in data:
                valid = False
                errors.append("Missing required key: metadata")
            if "participants" not in data:
                valid = False
                errors.append("Missing required key: participants")
            
            if valid:
                # Check metadata structure
                meta = data["metadata"]
                if not isinstance(meta, dict):
                    valid = False
                    errors.append("metadata must be an object")
                else:
                    required_meta = ["version", "generated_at", "experiment_id"]
                    for key in required_meta:
                        if key not in meta:
                            valid = False
                            errors.append(f"metadata missing required key: {key}")
                
                # Check participants array
                if valid and isinstance(data["participants"], list):
                    for i, p in enumerate(data["participants"]):
                        if not isinstance(p, dict):
                            valid = False
                            errors.append(f"Participant {i} is not an object")
                            continue
                        
                        required_p = ["participant_id", "condition", "session_start", "session_end", "tasks"]
                        for key in required_p:
                            if key not in p:
                                valid = False
                                errors.append(f"Participant {i} missing required key: {key}")
                        
                        # Check condition enum
                        if "condition" in p and p["condition"] not in ["llm_docs", "human_docs", "no_docs"]:
                            valid = False
                            errors.append(f"Participant {i} has invalid condition: {p['condition']}")
                
                report["valid"] = valid
                report["errors"] = errors
                if valid:
                    logger.info("Manual schema validation passed.")
                else:
                    logger.error(f"Manual schema validation failed: {errors}")

        except jsonschema.ValidationError as e:
            report["valid"] = False
            report["errors"].append(f"Schema Validation Error: {e.message} (Path: {list(e.path)})")
            logger.error(f"Schema validation failed: {e.message}")
        except jsonschema.SchemaError as e:
            report["valid"] = False
            report["errors"].append(f"Schema Definition Error: {e.message}")
            logger.error(f"Schema definition error: {e.message}")

    except json.JSONDecodeError as e:
        report["errors"].append(f"Invalid JSON in data file: {e}")
    except yaml.YAMLError as e:
        report["errors"].append(f"Invalid YAML in schema file: {e}")
    except Exception as e:
        report["errors"].append(f"Unexpected error during validation: {str(e)}")

    save_validation_report(report, output_path)
    return report

def save_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """Saves the validation report to a JSON file."""
    import datetime
    report["timestamp"] = datetime.datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for running schema validation."""
    # Default paths based on project structure
    data_path = "data/raw/participant_logs.json"
    schema_path = "contracts/dataset.schema.yaml"
    output_path = "data/processed/validation_report.json"
    
    # Allow override via command line args
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        schema_path = sys.argv[2]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]

    logger.info(f"Running schema validation for {data_path}")
    result = run_schema_validation(data_path, schema_path, output_path)
    
    if not result["valid"]:
        logger.error("Validation failed. Pipeline must abort.")
        sys.exit(1)
    else:
        logger.info("Validation passed. Pipeline can proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
