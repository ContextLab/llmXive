"""
Distillation pipeline for generating rules from annotated failure cases.
Includes strict schema validation against distilled_rule.schema.yaml.
"""
import json
import re
import sys
import time
import os
import psutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

# Import logging utilities from the project's utils
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import EXPECTED_EFFECT_SIZE, DEFAULT_SAMPLE_SIZE

logger = get_logger(__name__)

SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml")
RULES_OUTPUT_PATH = Path("data/derived/rules_library.json")
COVERAGE_OUTPUT_PATH = Path("data/derived/rule_coverage_report.json")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema definition from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single rule against the schema.
    Returns (is_valid, list_of_errors).
    This implements strict validation before writing to the library.
    """
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: {field}")

    # Check field types
    if "rule_id" in rule and not isinstance(rule["rule_id"], str):
        errors.append("Field 'rule_id' must be a string")
    if "condition_pattern" in rule and not isinstance(rule["condition_pattern"], str):
        errors.append("Field 'condition_pattern' must be a string")
    if "pivot_action" in rule and not isinstance(rule["pivot_action"], str):
        errors.append("Field 'pivot_action' must be a string")
    if "confidence" in rule:
        if not isinstance(rule["confidence"], (int, float)):
            errors.append("Field 'confidence' must be a number")
        elif not (0.0 <= rule["confidence"] <= 1.0):
            errors.append("Field 'confidence' must be between 0.0 and 1.0")

    # Check for unexpected fields (optional strictness)
    allowed_keys = set(properties.keys())
    for key in rule.keys():
        if key not in allowed_keys:
            errors.append(f"Unexpected field in rule: {key}")

    return len(errors) == 0, errors

def check_ram_usage(threshold_gb: float = 7.0) -> bool:
    """Check if current RAM usage is below threshold."""
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    if available_gb < threshold_gb:
        logger.warning(f"Low RAM available: {available_gb:.2f} GB < {threshold_gb} GB")
        return False
    return True

def load_annotated_failures(input_path: Path) -> List[Dict[str, Any]]:
    """Load the consensus failure cases."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_rules_regex(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract deterministic rules based on regex patterns for syntactic errors.
    """
    rules = []
    # Simple heuristic: if error log contains specific keywords, generate a rule
    patterns = [
        (r"SyntaxError|IndentationError|NameError", "Syntactic Error", "Fix syntax and retry"),
        (r"TimeoutError|timed out", "Timeout", "Reduce complexity or increase timeout"),
        (r"KeyError|IndexError", "Data Access", "Validate data structure before access"),
    ]

    for pattern, feature, action in patterns:
        count = sum(1 for f in failures if re.search(pattern, f.get("raw_error_log", ""), re.IGNORECASE))
        if count > 0:
            confidence = min(0.9, 0.5 + (count / len(failures)) * 0.4) if failures else 0.5
            rules.append({
                "rule_id": f"rule_{feature.replace(' ', '_').lower()}",
                "condition_pattern": pattern,
                "pivot_action": action,
                "confidence": confidence,
                "source_feature": feature
            })
    return rules

def extract_rules_with_llm(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Placeholder for LLM-based rule extraction.
    In a real implementation, this would call an LLM to analyze semantic failures.
    For now, returns a fallback rule for unstructured cases.
    """
    # Check for semantic ambiguity
    semantic_count = sum(1 for f in failures if "Semantic Ambiguity" in f.get("annotated_structural_feature", ""))
    if semantic_count > 0:
        return [{
            "rule_id": "rule_semantic_fallback",
            "condition_pattern": "Semantic Ambiguity detected",
            "pivot_action": "Request clarification or switch to probabilistic retrieval",
            "confidence": 0.8,
            "source_feature": "Semantic Ambiguity"
        }]
    return []

def calculate_coverage(rules: List[Dict[str, Any]], failures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate how many failures are covered by the generated rules."""
    total = len(failures)
    if total == 0:
        return {"total": 0, "covered": 0, "coverage_rate": 0.0}

    covered = 0
    for failure in failures:
        log = failure.get("raw_error_log", "")
        for rule in rules:
            if re.search(rule["condition_pattern"], log, re.IGNORECASE):
                covered += 1
                break

    return {
        "total": total,
        "covered": covered,
        "coverage_rate": covered / total if total > 0 else 0.0
    }

def save_rules_library(rules: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the validated rules to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)
    logger.info(f"Saved {len(rules)} rules to {output_path}")

def save_coverage_report(coverage: Dict[str, Any], output_path: Path) -> None:
    """Save the coverage report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(coverage, f, indent=2)
    logger.info(f"Saved coverage report to {output_path}")

def log_thresholds_and_pruning(rules: List[Dict[str, Any]], threshold: float) -> None:
    """Log the rules that passed the confidence threshold."""
    for rule in rules:
        logger.info(f"Rule {rule['rule_id']}: confidence={rule['confidence']:.2f}, action={rule['pivot_action']}")

def run_distill_pipeline(
    input_path: Path = Path("data/derived/failure_cases_consensus.json"),
    output_path: Path = RULES_OUTPUT_PATH,
    coverage_path: Path = COVERAGE_OUTPUT_PATH,
    min_confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Main pipeline to distill rules from failures.
    1. Load failures.
    2. Extract rules (regex + heuristic).
    3. **Validate every rule against the schema** before adding to library.
    4. Filter by confidence.
    5. Save validated rules.
    """
    logger.info("Starting rule distillation pipeline...")

    # 1. Load data
    failures = load_annotated_failures(input_path)
    logger.info(f"Loaded {len(failures)} failure cases.")

    # 2. Extract rules
    regex_rules = extract_rules_regex(failures)
    llm_rules = extract_rules_with_llm(failures)
    all_candidates = regex_rules + llm_rules

    # 3. Load Schema and Validate STRICTLY
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file missing: {SCHEMA_PATH}. Cannot validate rules.")
    schema = load_schema(SCHEMA_PATH)
    logger.info(f"Loaded schema from {SCHEMA_PATH}")

    validated_rules = []
    validation_errors = []

    for i, candidate in enumerate(all_candidates):
        is_valid, errors = validate_rule_against_schema(candidate, schema)
        if is_valid:
            # Filter by confidence
            if candidate.get("confidence", 0.0) >= min_confidence:
                validated_rules.append(candidate)
            else:
                logger.debug(f"Rule {candidate.get('rule_id', 'unknown')} filtered out: confidence {candidate.get('confidence')} < {min_confidence}")
        else:
            error_msg = f"Validation failed for candidate {i}: {errors}"
            logger.error(error_msg)
            validation_errors.append({"candidate_index": i, "candidate": candidate, "errors": errors})

    if validation_errors:
        logger.error(f"Found {len(validation_errors)} invalid rules. Aborting write to prevent malformed library.")
        # In a strict pipeline, we might raise here, but for now we log and proceed with valid ones if any
        # However, if the task requires *every* generated rule to be valid, we should ensure we don't write garbage.
        # We will write only the validated ones, but log the failure.
        raise ValueError(f"Rule validation failed for {len(validation_errors)} candidates. Check logs for details.")

    # 4. Save
    save_rules_library(validated_rules, output_path)

    # 5. Calculate and save coverage
    coverage = calculate_coverage(validated_rules, failures)
    save_coverage_report(coverage, coverage_path)

    logger.info(f"Distillation complete. {len(validated_rules)} valid rules saved.")
    return validated_rules

def main():
    """Entry point for the distillation script."""
    log_stage_start("distill_rules")
    try:
        # Check RAM before proceeding
        if not check_ram_usage():
            logger.error("Insufficient RAM. Aborting.")
            sys.exit(1)

        # Run the pipeline
        run_distill_pipeline()
        log_stage_end("distill_rules", status="success")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        log_stage_end("distill_rules", status="failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())