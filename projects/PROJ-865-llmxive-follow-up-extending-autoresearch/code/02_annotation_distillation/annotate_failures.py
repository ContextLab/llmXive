import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed

# Import schema paths from contracts if they were defined in T006a, 
# but we assume the schema file exists at the expected location based on T006a
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/failure_case.schema.yaml")
OUTPUT_DIR = Path("data/derived")
ARTIFACTS_DIR = Path("data/artifacts")
LOG_FILE = ARTIFACTS_DIR / "annotation.log"

# Ensure log directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("annotate_failures")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data: List[Dict], schema: Dict) -> bool:
    # Simple validation: check keys and enum values
    required_keys = {"task_id", "raw_error_log", "ground_truth_resolution", "annotated_structural_feature"}
    valid_features = {"Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"}
    
    for item in data:
        if not required_keys.issubset(item.keys()):
            return False
        if item.get("annotated_structural_feature") not in valid_features:
            return False
    return True

def load_parsed_traces(input_path: Path) -> List[Dict]:
    if not input_path.exists():
        raise FileNotFoundError(f"Parsed traces not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def classify_failure_heuristic(entry: Dict) -> str:
    error_log = entry.get("raw_error_log", "").lower()
    resolution = entry.get("ground_truth_resolution", "").lower()
    
    # Heuristic rules for classification
    if any(kw in error_log for kw in ["syntax", "indentation", "invalid syntax", "parse error"]):
        return "Syntactic Error"
    elif any(kw in error_log for kw in ["infinite loop", "recursion", "loop", "timeout"]):
        return "Logical Loop"
    elif any(kw in error_log for kw in ["ambiguous", "unclear", "confusing", "multiple meanings"]):
        return "Semantic Ambiguity"
    elif any(kw in error_log for kw in ["missing", "undefined", "not found", "context"]):
        return "Missing Context"
    else:
        return "Unstructured"

def annotate_single_entry(entry: Dict) -> Dict:
    annotated = entry.copy()
    annotated["annotated_structural_feature"] = classify_failure_heuristic(entry)
    return annotated

def main():
    set_seed(42) # Use seed from config
    log_stage_start(logger, "annotate_failures")
    
    input_path = OUTPUT_DIR / "parsed_traces.json"
    
    try:
        traces = load_parsed_traces(input_path)
        logger.info(f"Loaded {len(traces)} parsed traces from {input_path}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    annotated_cases = []
    for trace in traces:
        annotated_cases.append(annotate_single_entry(trace))

    if not validate_against_schema(annotated_cases, load_schema(SCHEMA_PATH)):
        logger.error("Schema validation failed for annotated cases.")
        sys.exit(1)

    # Split data
    total = len(annotated_cases)
    # Simple split: 70% train, 15% val, 15% test
    train_end = int(total * 0.7)
    val_end = int(total * 0.85)
    
    train_set = annotated_cases[:train_end]
    val_set = annotated_cases[train_end:val_end]
    test_set = annotated_cases[val_end:]

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
