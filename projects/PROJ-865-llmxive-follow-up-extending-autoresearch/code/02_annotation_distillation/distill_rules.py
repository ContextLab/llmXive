"""
Distill rules from annotated failure cases.
Implements T080: Strict schema validation for every generated rule before writing.
"""

import json
import re
import sys
import time
import os
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import DEFAULT_SAMPLE_SIZE

logger = get_logger(__name__)

# Paths
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "contracts" / "distilled_rule.schema.yaml"
INPUT_FAILURE_CASES = PROJECT_ROOT / "data" / "derived" / "failure_cases_train.json"
OUTPUT_RULES_LIBRARY = PROJECT_ROOT / "data" / "derived" / "rules_library.json"
OUTPUT_COVERAGE_REPORT = PROJECT_ROOT / "data" / "derived" / "rule_coverage_report.json"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single rule against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Check types and constraints based on schema properties
    properties = schema.get('properties', {})

    # Check rule_id
    if 'rule_id' in rule:
        if not isinstance(rule['rule_id'], str):
            errors.append("rule_id must be a string")

    # Check condition_pattern
    if 'condition_pattern' in rule:
        if not isinstance(rule['condition_pattern'], str):
            errors.append("condition_pattern must be a string")
        else:
            # Validate regex compilation
            try:
                re.compile(rule['condition_pattern'])
            except re.error as e:
                errors.append(f"Invalid regex in condition_pattern: {e}")

    # Check pivot_action
    if 'pivot_action' in rule:
        if not isinstance(rule['pivot_action'], str):
            errors.append("pivot_action must be a string")

    # Check confidence
    if 'confidence' in rule:
        if not isinstance(rule['confidence'], (int, float)):
            errors.append("confidence must be a number")
        elif not (0.0 <= rule['confidence'] <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")

    # Check failure_type enum
    if 'failure_type' in rule:
        enum_values = properties.get('failure_type', {}).get('enum', [])
        if rule['failure_type'] not in enum_values:
            errors.append(f"failure_type must be one of {enum_values}, got: {rule['failure_type']}")

    return len(errors) == 0, errors

def check_ram_usage() -> bool:
    """Check if RAM usage is within limits (simple check)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024
        if mem_mb > 6000: # Warn if > 6GB
            logger.warning(f"High RAM usage detected: {mem_mb:.2f} MB")
        return True
    except ImportError:
        logger.warning("psutil not installed, skipping RAM check")
        return True

def load_annotated_failures(input_path: Path) -> List[Dict[str, Any]]:
    """Load annotated failure cases from JSON."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_rules_regex(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract rules using deterministic regex patterns based on structural features.
    T072: Differentiate strategies for Syntactic vs Semantic.
    """
    rules = []
    rule_counter = 1

    # Define deterministic patterns for specific failure types
    # Syntactic: Look for specific error keywords
    syntactic_patterns = [
        (r"SyntaxError.*", "Syntactic Error", "Refactor syntax"),
        (r"IndentationError.*", "Syntactic Error", "Fix indentation"),
        (r"NameError.*", "Syntactic Error", "Check variable scope"),
    ]

    # Semantic: Flag for retrieval/unstructured (T072)
    semantic_patterns = [
        (r"ambiguity|unclear|vague", "Semantic Ambiguity", "Retrieve context"),
        (r"missing.*context", "Missing Context", "Fetch documentation"),
    ]

    # Logical: Loops
    logical_patterns = [
        (r"infinite.*loop|recursion.*limit", "Logical Loop", "Add termination condition"),
    ]

    # Unstructured: Catch-all
    unstructured_pattern = r"error|exception|failed"

    processed_ids = set()

    for failure in failures:
        task_id = failure.get('task_id')
        raw_log = failure.get('raw_error_log', '')
        failure_type = failure.get('annotated_structural_feature', 'Unstructured')

        if not raw_log or task_id in processed_ids:
            continue

        rule_found = False
        matched_rule = None

        # Apply specific strategies based on failure_type
        if failure_type == "Syntactic Error":
            for pattern, f_type, action in syntactic_patterns:
                if re.search(pattern, raw_log, re.IGNORECASE):
                    matched_rule = {
                        "rule_id": f"RULE_SYNTAX_{rule_counter}",
                        "condition_pattern": pattern,
                        "pivot_action": action,
                        "confidence": 0.95,
                        "failure_type": f_type
                    }
                    rule_found = True
                    break

        elif failure_type == "Semantic Ambiguity":
            for pattern, f_type, action in semantic_patterns:
                if re.search(pattern, raw_log, re.IGNORECASE):
                    matched_rule = {
                        "rule_id": f"RULE_SEMANTIC_{rule_counter}",
                        "condition_pattern": pattern,
                        "pivot_action": action,
                        "confidence": 0.80,
                        "failure_type": f_type
                    }
                    rule_found = True
                    break
            # Fallback for semantic if no specific match: Unstructured
            if not rule_found:
                matched_rule = {
                    "rule_id": f"RULE_SEMANTIC_FALLBACK_{rule_counter}",
                    "condition_pattern": r".*",
                    "pivot_action": "Manual Review",
                    "confidence": 0.50,
                    "failure_type": "Semantic Ambiguity"
                }
                rule_found = True

        elif failure_type == "Logical Loop":
            for pattern, f_type, action in logical_patterns:
                if re.search(pattern, raw_log, re.IGNORECASE):
                    matched_rule = {
                        "rule_id": f"RULE_LOGIC_{rule_counter}",
                        "condition_pattern": pattern,
                        "pivot_action": action,
                        "confidence": 0.90,
                        "failure_type": f_type
                    }
                    rule_found = True
                    break

        # Default fallback for Unstructured or unmatched
        if not rule_found:
            matched_rule = {
                "rule_id": f"RULE_UNSTRUCTURED_{rule_counter}",
                "condition_pattern": unstructured_pattern,
                "pivot_action": "Manual Review",
                "confidence": 0.60,
                "failure_type": "Unstructured"
            }
            rule_found = True

        if matched_rule:
            rules.append(matched_rule)
            processed_ids.add(task_id)
            rule_counter += 1

    return rules

def extract_rules_with_llm(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder for LLM-based rule extraction.
    Currently returns empty as we rely on regex for determinism in this phase.
    """
    return []

def calculate_coverage(rules: List[Dict[str, Any]], failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate rule coverage over the dataset."""
    total = len(failures)
    covered = 0
    covered_ids = set()

    for rule in rules:
        pattern = re.compile(rule['condition_pattern'], re.IGNORECASE)
        for failure in failures:
            if failure['task_id'] not in covered_ids:
                if pattern.search(failure.get('raw_error_log', '')):
                    covered += 1
                    covered_ids.add(failure['task_id'])

    return {
        "total_cases": total,
        "covered_cases": covered,
        "coverage_percentage": (covered / total * 100) if total > 0 else 0.0
    }

def save_rules_library(rules: List[Dict[str, Any]], output_path: Path):
    """Save the validated rules library to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2)
    logger.info(f"Saved {len(rules)} rules to {output_path}")

def save_coverage_report(coverage: Dict[str, Any], output_path: Path):
    """Save the coverage report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2)
    logger.info(f"Saved coverage report to {output_path}")

def log_distillation_thresholds(rules: List[Dict[str, Any]]):
    """Log thresholds and pruning info."""
    logger.info(f"Distillation complete. Total rules: {len(rules)}")
    for rule in rules:
        logger.info(f"Rule {rule['rule_id']}: Confidence={rule['confidence']}, Type={rule['failure_type']}")

def run_distill_pipeline(input_path: Path, output_path: Path, schema_path: Path):
    """
    Main pipeline: Load, Extract, Validate, Save.
    T080: Strict validation for every rule.
    """
    logger.info(f"Starting distillation pipeline. Input: {input_path}")

    # 1. Load Schema
    schema = load_schema(schema_path)

    # 2. Load Data
    failures = load_annotated_failures(input_path)
    logger.info(f"Loaded {len(failures)} failure cases")

    # 3. Extract Rules
    rules = extract_rules_regex(failures)
    # Note: LLM extraction skipped for determinism in this phase

    # 4. STRICT VALIDATION (T080)
    valid_rules = []
    invalid_count = 0

    for i, rule in enumerate(rules):
        is_valid, errors = validate_rule_against_schema(rule, schema)
        if is_valid:
            valid_rules.append(rule)
        else:
            invalid_count += 1
            logger.error(f"Rule validation FAILED for rule {rule.get('rule_id', 'UNKNOWN')}: {errors}")
            # In a strict pipeline, we might abort here, but we log and continue to save valid ones
            # or raise an error if ANY rule is invalid. Per T080, we prevent malformed rules.
            # We will raise to ensure the pipeline fails if the logic is broken.
            raise ValueError(f"Schema validation failed for rule {rule.get('rule_id')}: {errors}")

    if invalid_count > 0:
        raise RuntimeError(f"Pipeline failed: {invalid_count} rules failed schema validation.")

    logger.info(f"Validation passed for {len(valid_rules)} rules.")

    # 5. Calculate Coverage
    coverage = calculate_coverage(valid_rules, failures)
    logger.info(f"Coverage: {coverage['coverage_percentage']:.2f}%")

    # 6. Save Outputs
    save_rules_library(valid_rules, output_path)
    save_coverage_report(coverage, OUTPUT_COVERAGE_REPORT)
    log_distillation_thresholds(valid_rules)

    return valid_rules, coverage

def main():
    """Entry point for the script."""
    log_stage_start("distill_rules")

    try:
        # Ensure directories exist
        OUTPUT_RULES_LIBRARY.parent.mkdir(parents=True, exist_ok=True)

        # Run pipeline
        rules, coverage = run_distill_pipeline(
            input_path=INPUT_FAILURE_CASES,
            output_path=OUTPUT_RULES_LIBRARY,
            schema_path=SCHEMA_PATH
        )

        log_stage_end("distill_rules", status="success")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end("distill_rules", status="failed", error=str(e))
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_stage_end("distill_rules", status="failed", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())