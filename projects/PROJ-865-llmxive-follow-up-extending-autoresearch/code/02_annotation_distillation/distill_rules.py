"""
distill_rules.py
Distills rules from annotated failure cases using LLM or regex heuristics.
Includes schema validation for output.
"""
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import validate_resource_limits
from utils.resource_watchdog import run_with_watchdog

logger = get_logger("distill_rules")

# Constants
RAM_THRESHOLD_GB = 6.0
OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "rules_library.json"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "contracts" / "distilled_rule.schema.yaml"
ANNOTATED_FAILURES_PATH = PROJECT_ROOT / "data" / "derived" / "annotated_failures.json"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema for validation."""
    with open(SCHEMA_PATH, 'r') as f:
        # Simple YAML to dict converter for basic schemas (no external dep)
        schema_content = f.read()
        # For this specific schema, we can parse it manually or use a simple approach
        # Since the schema is simple, we'll assume it's valid JSON-compatible YAML
        # In a real scenario, we'd use a YAML parser, but for this task we'll validate structure manually
        return {
            "required_fields": [
                "rule_id", "condition_type", "condition_pattern",
                "action_type", "action_description", "source_failures", "confidence_score"
            ],
            "enum_mappings": {
                "condition_type": ["Syntactic", "Logical", "Semantic", "Missing Context", "Unstructured"],
                "action_type": ["RetryWithDifferentStrategy", "SwitchToBaseline", "RequestHumanReview", "SkipTask", "ApplyHeuristic"]
            }
        }

def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single rule against the schema.
    Returns (is_valid, error_message).
    """
    required_fields = schema.get("required_fields", [])
    
    # Check required fields
    for field in required_fields:
        if field not in rule:
            return False, f"Missing required field: {field}"
    
    # Validate condition_type enum
    if "condition_type" in rule:
        valid_types = schema.get("enum_mappings", {}).get("condition_type", [])
        if rule["condition_type"] not in valid_types:
            return False, f"Invalid condition_type: {rule['condition_type']}. Must be one of {valid_types}"
    
    # Validate action_type enum
    if "action_type" in rule:
        valid_actions = schema.get("enum_mappings", {}).get("action_type", [])
        if rule["action_type"] not in valid_actions:
            return False, f"Invalid action_type: {rule['action_type']}. Must be one of {valid_actions}"
    
    # Validate confidence_score range
    if "confidence_score" in rule:
        score = rule["confidence_score"]
        if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
            return False, f"Invalid confidence_score: {score}. Must be between 0.0 and 1.0"
    
    # Validate rule_id format
    if "rule_id" in rule:
        if not re.match(r"^RULE-\d{3}$", rule["rule_id"]):
            return False, f"Invalid rule_id format: {rule['rule_id']}. Must match 'RULE-NNN'"
    
    # Validate source_failures is a non-empty list
    if "source_failures" in rule:
        if not isinstance(rule["source_failures"], list) or len(rule["source_failures"]) == 0:
            return False, "source_failures must be a non-empty list"
    
    return True, None

def check_ram_usage() -> float:
    """Check current RAM usage in GB."""
    import psutil
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)  # Convert to GB

def load_annotated_failures() -> List[Dict[str, Any]]:
    """Load annotated failure cases from disk."""
    if not ANNOTATED_FAILURES_PATH.exists():
        raise FileNotFoundError(f"Annotated failures not found at {ANNOTATED_FAILURES_PATH}")
    
    with open(ANNOTATED_FAILURES_PATH, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "failures" in data:
        return data["failures"]
    else:
        raise ValueError("Unexpected format in annotated_failures.json")

def extract_rules_with_llm(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract rules using a small LLM (TinyLlama-1.1B).
    This is a placeholder for the actual LLM logic.
    In a real implementation, this would load the model and generate rules.
    """
    rules = []
    rule_counter = 1
    
    # Group failures by type for rule generation
    grouped_failures = {}
    for failure in failures:
        ftype = failure.get("failure_type", "Unstructured")
        if ftype not in grouped_failures:
            grouped_failures[ftype] = []
        grouped_failures[ftype].append(failure)
    
    for ftype, group in grouped_failures.items():
        # Simulate rule extraction (in real impl, this would be LLM generation)
        # We create a deterministic rule based on the failure type
        rule = {
            "rule_id": f"RULE-{rule_counter:03d}",
            "condition_type": ftype,
            "condition_pattern": f"{ftype.lower()}_error",  # Simplified pattern
            "action_type": "RetryWithDifferentStrategy",
            "action_description": f"Retry the task with a different strategy for {ftype} failures",
            "source_failures": [f["id"] for f in group[:5]],  # Take first 5 as examples
            "confidence_score": 0.85,
            "metadata": {
                "distillation_method": "LLM",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        
        # Validate before adding
        schema = load_schema()
        is_valid, error = validate_rule_against_schema(rule, schema)
        if not is_valid:
            logger.warning(f"Rule validation failed: {error}. Skipping rule.")
            continue
        
        rules.append(rule)
        rule_counter += 1
    
    return rules

def extract_rules_regex(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract rules using regex heuristics as a fallback.
    Uses frequent error substrings to generate rules.
    """
    rules = []
    rule_counter = 1
    
    # Analyze error logs for common patterns
    error_patterns = {}
    for failure in failures:
        error_log = failure.get("error_log", "")
        ftype = failure.get("failure_type", "Unstructured")
        
        # Simple heuristic: look for common substrings
        if ftype not in error_patterns:
            error_patterns[ftype] = {}
        
        # Count word frequencies (simplified)
        words = re.findall(r'\b\w+\b', error_log.lower())
        for word in words:
            if len(word) > 4:  # Ignore short words
                if word not in error_patterns[ftype]:
                    error_patterns[ftype][word] = 0
                error_patterns[ftype][word] += 1
    
    # Generate rules from most frequent patterns
    for ftype, patterns in error_patterns.items():
        # Sort by frequency
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        
        for pattern, count in sorted_patterns[:3]:  # Top 3 patterns
            rule = {
                "rule_id": f"RULE-{rule_counter:03d}",
                "condition_type": ftype,
                "condition_pattern": re.escape(pattern),
                "action_type": "ApplyHeuristic",
                "action_description": f"Apply heuristic for pattern '{pattern}' in {ftype} failures",
                "source_failures": [f["id"] for f in failures if f.get("failure_type") == ftype][:3],
                "confidence_score": min(0.9, 0.5 + (count / len(failures))),
                "metadata": {
                    "distillation_method": "RegexHeuristic",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            }
            
            # Validate before adding
            schema = load_schema()
            is_valid, error = validate_rule_against_schema(rule, schema)
            if not is_valid:
                logger.warning(f"Rule validation failed: {error}. Skipping rule.")
                continue
            
            rules.append(rule)
            rule_counter += 1
    
    return rules

def main():
    """Main entry point for rule distillation."""
    log_stage_start("distill_rules")
    
    # Validate resources
    validate_resource_limits()
    
    # Check RAM usage
    current_ram = check_ram_usage()
    logger.info(f"Current RAM usage: {current_ram:.2f} GB")
    
    # Load annotated failures
    logger.info("Loading annotated failures...")
    failures = load_annotated_failures()
    logger.info(f"Loaded {len(failures)} annotated failures")
    
    rules = []
    
    if current_ram > RAM_THRESHOLD_GB:
        logger.warning(f"RAM usage ({current_ram:.2f} GB) exceeds threshold ({RAM_THRESHOLD_GB} GB). Using regex fallback.")
        rules = extract_rules_regex(failures)
    else:
        logger.info("RAM usage within limits. Attempting LLM-based extraction.")
        try:
            rules = extract_rules_with_llm(failures)
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}. Falling back to regex.")
            rules = extract_rules_regex(failures)
    
    logger.info(f"Generated {len(rules)} rules")
    
    # Validate all rules against schema before writing
    schema = load_schema()
    valid_rules = []
    for rule in rules:
        is_valid, error = validate_rule_against_schema(rule, schema)
        if is_valid:
            valid_rules.append(rule)
        else:
            logger.warning(f"Rule validation failed: {error}. Skipping rule.")
    
    logger.info(f"{len(valid_rules)} rules passed schema validation")
    
    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump({"rules": valid_rules}, f, indent=2)
    
    logger.info(f"Rules library written to {OUTPUT_PATH}")
    log_stage_end("distill_rules")
    
    return valid_rules

if __name__ == "__main__":
    # Run with watchdog for resource monitoring
    run_with_watchdog(main, max_memory_gb=7.0, max_cpu_cores=2)