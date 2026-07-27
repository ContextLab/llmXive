import json
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

# Paths
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/failure_case.schema.yaml")
OUTPUT_DIR = Path("data/derived")
ARTIFACTS_DIR = Path("data/artifacts")
LOG_FILE = ARTIFACTS_DIR / "annotation.log"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("annotate_failures")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data: List[Dict], schema: Dict) -> Tuple[bool, Optional[str]]:
    """
    Validate data against the schema.
    Returns (is_valid, error_message).
    """
    required_keys = {"task_id", "raw_error_log", "ground_truth_resolution", "annotated_structural_feature"}
    valid_features = {"Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"}
    
    for i, item in enumerate(data):
        if not required_keys.issubset(item.keys()):
            missing = required_keys - set(item.keys())
            return False, f"Item {i} missing keys: {missing}"
        
        feat = item.get("annotated_structural_feature")
        if feat not in valid_features:
            return False, f"Item {i} has invalid feature: {feat}. Expected one of {valid_features}"
        
        if not isinstance(item.get("task_id"), str):
            return False, f"Item {i} task_id must be string"
        if not isinstance(item.get("raw_error_log"), str):
            return False, f"Item {i} raw_error_log must be string"
        if not isinstance(item.get("ground_truth_resolution"), str):
            return False, f"Item {i} ground_truth_resolution must be string"
        
    return True, None

def load_parsed_traces(input_path: Path) -> List[Dict]:
    """Load the raw failure cases from JSON."""
    if not input_path.exists():
        raise FileNotFoundError(f"Parsed traces not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def classify_failure_heuristic(entry: Dict) -> str:
    """
    Classify a failure case into a structural feature using deterministic heuristics.
    This is the annotation logic required by the task.
    """
    error_log = entry.get("raw_error_log", "").lower()
    resolution = entry.get("ground_truth_resolution", "").lower()
    
    # Priority 1: Syntactic Error
    if any(kw in error_log for kw in ["syntax", "indentation", "invalid syntax", "parse error", "unexpected token"]):
        return "Syntactic Error"
    
    # Priority 2: Logical Loop
    if any(kw in error_log for kw in ["infinite loop", "recursion", "loop", "timeout", "max retries", "stack overflow"]):
        return "Logical Loop"
    
    # Priority 3: Semantic Ambiguity
    if any(kw in error_log for kw in ["ambiguous", "unclear", "confusing", "multiple meanings", "interpretation"]):
        return "Semantic Ambiguity"
    
    # Priority 4: Missing Context
    if any(kw in error_log for kw in ["missing", "undefined", "not found", "context", "variable not defined"]):
        return "Missing Context"
    
    # Default: Unstructured
    return "Unstructured"

def annotate_single_entry(entry: Dict) -> Dict:
    """Annotate a single entry with a structural feature."""
    annotated = entry.copy()
    annotated["annotated_structural_feature"] = classify_failure_heuristic(entry)
    return annotated

def main():
    set_seed(42) # Use seed from config for reproducibility
    log_stage_start(logger, "annotate_failures")
    
    # Input path: T036 produces this file
    input_path = OUTPUT_DIR / "failure_cases_raw.json"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Ensure T036 has completed successfully.")
        sys.exit(1)

    try:
        traces = load_parsed_traces(input_path)
        logger.info(f"Loaded {len(traces)} raw failure cases from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # Annotate all cases
    annotated_cases = []
    for trace in traces:
        annotated_cases.append(annotate_single_entry(trace))

    # Load schema and validate
    try:
        schema = load_schema(SCHEMA_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    is_valid, error_msg = validate_against_schema(annotated_cases, schema)
    if not is_valid:
        logger.error(f"Schema validation failed: {error_msg}")
        sys.exit(1)
    
    logger.info("Schema validation passed.")

    # Split data: 70% train, 15% val, 15% test
    total = len(annotated_cases)
    if total == 0:
        logger.warning("No cases to split. Creating empty files.")
    else:
        # Use fixed seed for reproducibility
        import random
        random.seed(42)
        random.shuffle(annotated_cases) # Shuffle before splitting

        train_end = int(total * 0.7)
        val_end = int(total * 0.85)
        
        train_set = annotated_cases[:train_end]
        val_set = annotated_cases[train_end:val_end]
        test_set = annotated_cases[val_end:]

        logger.info(f"Split: Train={len(train_set)}, Val={len(val_set)}, Test={len(test_set)}")

        # Save splits
        train_path = OUTPUT_DIR / "failure_cases_train.json"
        val_path = OUTPUT_DIR / "failure_cases_val.json"
        test_path = OUTPUT_DIR / "failure_cases_test.json"
        full_path = OUTPUT_DIR / "failure_cases.json"

        for path, data in [(full_path, annotated_cases), (train_path, train_set), (val_path, val_set), (test_path, test_set)]:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} cases to {path}")

    # --- T016: Logging Metrics ---
    counts = {
        "Syntactic Error": 0,
        "Logical Loop": 0,
        "Semantic Ambiguity": 0,
        "Missing Context": 0,
        "Unstructured": 0
    }
    for case in annotated_cases:
        feat = case.get("annotated_structural_feature")
        if feat in counts:
            counts[feat] += 1

    log_entry = {
        "total_cases": total,
        "syntactic_count": counts["Syntactic Error"],
        "semantic_count": counts["Semantic Ambiguity"],
        "logical_count": counts["Logical Loop"],
        "missing_count": counts["Missing Context"],
        "unstructured_count": counts["Unstructured"]
    }

    # Append to log file
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Annotation metrics logged to {LOG_FILE}")
    logger.info(f"Total: {total}, Syntactic: {counts['Syntactic Error']}, Semantic: {counts['Semantic Ambiguity']}, Logical: {counts['Logical Loop']}, Missing: {counts['Missing Context']}, Unstructured: {counts['Unstructured']}")

    log_stage_end(logger, "annotate_failures")

if __name__ == "__main__":
    main()