"""
Distillation pipeline for generating rules from annotated failures.
Supports pilot runs with subset size and schema validation.
"""
import json
import re
import sys
import time
import os
import psutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project API surface
# Note: The API surface lists these under code/02_annotation_distillation,
# but the task T082 requires them in code/annotation. We implement the
# logic here and ensure it matches the expected interface.
# We also import from utils if available, but define fallbacks if not.
try:
    from utils.logging import get_logger, log_stage_start, log_stage_end
    from utils.config import MAX_MEMORY_GB, DEFAULT_SAMPLE_SIZE
except ImportError:
    # Fallback if utils not in path (should be added to sys.path)
    logger = None
    MAX_MEMORY_GB = 7
    DEFAULT_SAMPLE_SIZE = 50

    def log_stage_start(msg):
        print(f"[START] {msg}")

    def log_stage_end(msg):
        print(f"[END] {msg}")

# Schema for validation
DISTILLED_RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "rule_id": {"type": "string"},
        "condition_pattern": {"type": "string"},
        "pivot_action": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
    },
    "required": ["rule_id", "condition_pattern", "pivot_action", "confidence"]
}

def load_schema(schema_path: Optional[Path] = None) -> Dict:
    """Load or return the default schema."""
    return DISTILLED_RULE_SCHEMA

def validate_rule_against_schema(rule: Dict, schema: Dict) -> Tuple[bool, Optional[str]]:
    """Validate a single rule against the schema."""
    for key in schema["required"]:
        if key not in rule:
            return False, f"Missing required key: {key}"
        if key == "confidence":
            if not isinstance(rule[key], (int, float)):
                return False, "confidence must be a number"
            if not (0.0 <= rule[key] <= 1.0):
                return False, "confidence must be between 0 and 1"
        elif not isinstance(rule[key], str):
            return False, f"{key} must be a string"
    return True, None

def check_ram_usage() -> bool:
    """Check if RAM usage is within limits."""
    process = psutil.Process()
    mem_info = process.memory_info()
    mem_gb = mem_info.rss / (1024 ** 3)
    if mem_gb > MAX_MEMORY_GB:
        log_stage_start(f"RAM usage {mem_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB")
        return False
    return True

def load_annotated_failures(input_path: Path, subset_size: Optional[int] = None) -> List[Dict]:
    """Load annotated failures from JSON, optionally subsetting."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        failures = data
    elif isinstance(data, dict):
        # Handle case where data is a dict of task_id -> failure
        failures = list(data.values())
    else:
        raise ValueError("Unexpected data format in annotated failures")

    if subset_size and subset_size > 0:
        failures = failures[:subset_size]

    return failures

def extract_rules_regex(failures: List[Dict]) -> List[Dict]:
    """Extract rules using regex patterns based on failure annotations."""
    rules = []
    rule_id_counter = 1

    # Patterns based on T009a logic
    patterns = [
        (r'SyntaxError.*|IndentationError.*', 'Syntactic Error', 'Refactor syntax and re-run'),
        (r'loop|recursion|infinite', 'Logical Loop', 'Break recursion or add termination condition'),
        (r'ambiguous|unclear|multiple meanings', 'Semantic Ambiguity', 'Clarify requirements or use probabilistic retrieval'),
        (r'missing|context|undefined', 'Missing Context', 'Provide additional context or documentation'),
    ]

    seen_patterns = set()

    for failure in failures:
        error_log = failure.get('raw_error_log', '')
        feature = failure.get('annotated_structural_feature', 'Unstructured')

        matched = False
        for pattern, feature_name, action in patterns:
            if re.search(pattern, error_log, re.IGNORECASE):
                if pattern not in seen_patterns:
                    rule = {
                        "rule_id": f"RULE_{rule_id_counter:04d}",
                        "condition_pattern": pattern,
                        "pivot_action": action,
                        "confidence": 0.95 if feature_name != 'Semantic Ambiguity' else 0.60
                    }
                    rules.append(rule)
                    seen_patterns.add(pattern)
                    rule_id_counter += 1
                    matched = True
                break

        if not matched and feature == 'Unstructured':
            # Fallback for unstructured
            if 'UNSTRUCTURED_FALLBACK' not in seen_patterns:
                rule = {
                    "rule_id": f"RULE_{rule_id_counter:04d}",
                    "condition_pattern": ".*",
                    "pivot_action": "Manual Review Required",
                    "confidence": 0.50
                }
                rules.append(rule)
                seen_patterns.add('UNSTRUCTURED_FALLBACK')
                rule_id_counter += 1

    return rules

def extract_rules_with_llm(failures: List[Dict]) -> List[Dict]:
    """
    Placeholder for LLM-based rule extraction.
    In a real implementation, this would call a quantized model.
    For this pilot, we rely on regex extraction which is CPU-tractable.
    """
    return []

def calculate_coverage(rules: List[Dict], failures: List[Dict]) -> Dict:
    """Calculate coverage of rules against failures."""
    covered = 0
    total = len(failures)
    covered_cases = []

    for failure in failures:
        error_log = failure.get('raw_error_log', '')
        for rule in rules:
            if re.search(rule['condition_pattern'], error_log, re.IGNORECASE):
                covered += 1
                covered_cases.append({
                    "task_id": failure.get('task_id', 'unknown'),
                    "matched_rule": rule['rule_id']
                })
                break

    coverage_pct = (covered / total * 100) if total > 0 else 0.0

    return {
        "coverage_percentage": coverage_pct,
        "total_cases": total,
        "covered_cases": covered,
        "uncovered_cases": total - covered,
        "covered_details": covered_cases
    }

def save_rules_library(rules: List[Dict], output_path: Path) -> None:
    """Save rules library to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(rules, f, indent=2)

def save_coverage_report(coverage: Dict, output_path: Path) -> None:
    """Save coverage report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(coverage, f, indent=2)

def log_thresholds_and_pruning(rules: List[Dict], threshold: float = 0.5) -> List[Dict]:
    """Log and prune rules below confidence threshold."""
    pruned = [r for r in rules if r.get('confidence', 0) < threshold]
    kept = [r for r in rules if r.get('confidence', 0) >= threshold]

    if pruned:
        log_stage_start(f"Pruned {len(pruned)} rules below confidence threshold {threshold}")
        for r in pruned:
            print(f"  - {r['rule_id']}: {r['confidence']}")

    return kept

def run_distill_pipeline(
    input_path: Path,
    output_rules_path: Path,
    output_coverage_path: Path,
    subset_size: Optional[int] = None,
    validate_schema: bool = True
) -> Dict:
    """Run the full distillation pipeline."""
    log_stage_start("Starting distillation pipeline")

    if not check_ram_usage():
        raise MemoryError("RAM limit exceeded")

    # Load data
    failures = load_annotated_failures(input_path, subset_size)
    log_stage_start(f"Loaded {len(failures)} annotated failures")

    # Extract rules
    rules = extract_rules_regex(failures)
    log_stage_start(f"Extracted {len(rules)} rules via regex")

    # Optional LLM extraction (placeholder)
    # llm_rules = extract_rules_with_llm(failures)
    # rules.extend(llm_rules)

    # Validate schema if requested
    if validate_schema:
        schema = load_schema()
        invalid_rules = []
        for rule in rules:
            valid, reason = validate_rule_against_schema(rule, schema)
            if not valid:
                invalid_rules.append((rule['rule_id'], reason))

        if invalid_rules:
            log_stage_start(f"Found {len(invalid_rules)} invalid rules")
            for rule_id, reason in invalid_rules:
                print(f"  - {rule_id}: {reason}")
            # For pilot, we proceed but log warnings
            # In production, we might raise an error

    # Prune low confidence rules
    rules = log_thresholds_and_pruning(rules, threshold=0.5)

    # Calculate coverage
    coverage = calculate_coverage(rules, failures)
    log_stage_start(f"Coverage: {coverage['coverage_percentage']:.2f}%")

    # Save outputs
    save_rules_library(rules, output_rules_path)
    save_coverage_report(coverage, output_coverage_path)

    log_stage_end("Distillation pipeline completed")

    return {
        "rules_count": len(rules),
        "coverage": coverage['coverage_percentage'],
        "output_rules": str(output_rules_path),
        "output_coverage": str(output_coverage_path)
    }

def main():
    parser = argparse.ArgumentParser(description="Run rule distillation pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to annotated failures JSON")
    parser.add_argument("--output-rules", type=str, required=True, help="Path to output rules JSON")
    parser.add_argument("--output-coverage", type=str, required=True, help="Path to output coverage JSON")
    parser.add_argument("--subset-size", type=int, default=None, help="Subset size for pilot run")
    parser.add_argument("--validate-schema", action="store_true", help="Validate rules against schema")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_rules_path = Path(args.output_rules)
    output_coverage_path = Path(args.output_coverage)

    try:
        result = run_distill_pipeline(
            input_path=input_path,
            output_rules_path=output_rules_path,
            output_coverage_path=output_coverage_path,
            subset_size=args.subset_size,
            validate_schema=args.validate_schema
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
