import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from utils.logging import get_logger
from evaluation.validators import validate_task

logger = get_logger(__name__)


def calculate_hallucination_rate(
    output_text: str,
    context: Optional[str] = None,
    task_type: Optional[str] = None
) -> Tuple[int, int]:
    """
    Calculate hallucination rate for a single output.

    Logic:
    1. Regex extraction of entity-value pairs.
    2. Multi-hop reasoning check (simplified for this task).
    3. Compare extracted facts against context.

    Returns:
        Tuple (hallucinated_count, total_facts_count)
    """
    if not output_text:
        return 0, 0

    # 1. Extract entity-value pairs
    pattern = r'\b(\w+): (\w+)\b'
    matches = re.findall(pattern, output_text)
    if not matches:
        return 0, 0

    total_facts = len(matches)
    hallucinated_count = 0

    context_lower = context.lower() if context else ""

    for key, value in matches:
        # Simple check: is the fact present in the context?
        # In a real multi-hop scenario, we would use a solver or graph traversal.
        # Here we check if the specific key-value pair appears in context.
        fact_string = f"{key}: {value}"
        if fact_string.lower() not in context_lower:
            # Check if it's a derived fact (multi-hop) - simplified heuristic
            # If the key is not in context at all, it's likely a hallucination
            if key.lower() not in context_lower:
                hallucinated_count += 1
            else:
                # Key exists but value might be wrong or derived
                # For this task, we assume if it's not explicitly in context, it's a hallucination
                # unless we have a solver to verify derivation.
                hallucinated_count += 1

    return hallucinated_count, total_facts


def batch_calculate_hallucination_rate(
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate hallucination rate for a batch of records.
    """
    results = []
    for record in records:
        output_text = record.get("output", "")
        context = record.get("context", "")
        task_type = record.get("task_type", "")

        hallucinated, total = calculate_hallucination_rate(output_text, context, task_type)
        rate = hallucinated / total if total > 0 else 0.0

        record["hallucination_rate"] = rate
        record["hallucinated_facts"] = hallucinated
        record["total_facts"] = total
        results.append(record)

    return results


def calculate_style_consistency(
    output_text: str,
    profile: Dict[str, Any],
    task_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate Style Consistency for a single output based on a profile.

    Logic:
    1. Count occurrences of behavior track keywords (from profile) in output.
    2. Calculate frequency ratio (keywords found / total keywords defined).
    3. Match against structure rules (e.g., "must start with greeting").

    Args:
        output_text: The generated text.
        profile: The expert profile dict containing 'behavior_keywords' and 'capability_rules'.
        task_type: Optional task type for specific rule checks.

    Returns:
        Dict containing:
            - 'consistency_score': float (0.0 to 1.0)
            - 'keywords_found': List[str]
            - 'keywords_total': int
            - 'structure_rules_passed': bool
            - 'structure_rules_details': Dict[str, Any]
    """
    if not output_text or not profile:
        return {
            "consistency_score": 0.0,
            "keywords_found": [],
            "keywords_total": 0,
            "structure_rules_passed": False,
            "structure_rules_details": {"reason": "Missing input"}
        }

    # 1. Extract behavior keywords from profile
    behavior_keywords = profile.get("behavior_keywords", [])
    if not behavior_keywords:
        return {
            "consistency_score": 0.0,
            "keywords_found": [],
            "keywords_total": 0,
            "structure_rules_passed": False,
            "structure_rules_details": {"reason": "No behavior keywords in profile"}
        }

    keywords_total = len(behavior_keywords)
    keywords_found = []
    output_lower = output_text.lower()

    # Count occurrences (case-insensitive)
    for keyword in behavior_keywords:
        if keyword.lower() in output_lower:
            keywords_found.append(keyword)

    # 2. Calculate frequency ratio
    # Using presence ratio (1 if found, 0 if not) rather than raw count to avoid bias towards long texts
    found_count = len(keywords_found)
    consistency_score = found_count / keywords_total if keywords_total > 0 else 0.0

    # 3. Match against structure rules
    # Extract rules from capability_rules string
    capability_rules = profile.get("capability_rules", "")
    structure_rules_passed = True
    structure_details = {}

    # Rule: "must start with greeting"
    if "must start with greeting" in capability_rules.lower() or "greeting" in capability_rules.lower():
        # Heuristic: Check if output starts with common greeting words
        greeting_patterns = [
            r"^\s*(hello|hi|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening)\b",
            r"^\s*(welcome|nice\s+to\s+meet\s+you)\b"
        ]
        starts_with_greeting = False
        for pattern in greeting_patterns:
            if re.search(pattern, output_lower):
                starts_with_greeting = True
                break

        structure_details["greeting_check"] = starts_with_greeting
        if not starts_with_greeting:
            structure_rules_passed = False

    # Rule: "must end with summary"
    if "must end with summary" in capability_rules.lower() or "summary" in capability_rules.lower():
        # Heuristic: Check if output ends with summary-like phrases
        summary_patterns = [
            r"\b(in\s+summary|to\s+summarize|in\s+conclusion|therefore|thus)\b\s*$",
            r"\b(summary:|conclusion:)\b\s*$"
        ]
        ends_with_summary = False
        for pattern in summary_patterns:
            if re.search(pattern, output_lower, re.MULTILINE):
                ends_with_summary = True
                break

        structure_details["summary_check"] = ends_with_summary
        if not ends_with_summary:
            structure_rules_passed = False

    # Add other potential rule checks here if needed

    return {
        "consistency_score": consistency_score,
        "keywords_found": keywords_found,
        "keywords_total": keywords_total,
        "structure_rules_passed": structure_rules_passed,
        "structure_rules_details": structure_details
    }


def batch_calculate_style_consistency(
    records: List[Dict[str, Any]],
    profiles_map: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate style consistency for a batch of records.

    Args:
        records: List of inference output records.
        profiles_map: Dict mapping profile_id to profile dict.

    Returns:
        List of records with added style consistency metrics.
    """
    results = []
    for record in records:
        profile_id = record.get("profile_id")
        output_text = record.get("output", "")

        if profile_id not in profiles_map:
            logger.warning(f"Profile {profile_id} not found for record {record.get('task_id')}")
            record["style_consistency_score"] = 0.0
            record["style_consistency_details"] = {"error": "Profile not found"}
            results.append(record)
            continue

        profile = profiles_map[profile_id]
        task_type = record.get("task_type")

        style_metrics = calculate_style_consistency(output_text, profile, task_type)

        record["style_consistency_score"] = style_metrics["consistency_score"]
        record["style_keywords_found"] = style_metrics["keywords_found"]
        record["style_keywords_total"] = style_metrics["keywords_total"]
        record["style_structure_passed"] = style_metrics["structure_rules_passed"]
        record["style_structure_details"] = style_metrics["structure_rules_details"]
        results.append(record)

    return results


def main():
    """
    Main function to demonstrate style consistency calculation.
    This is primarily for testing and can be run as a script.
    """
    # Example usage
    sample_profile = {
        "id": "prof_001",
        "domain": "coding",
        "capability_rules": "must start with greeting",
        "behavior_keywords": ["efficient", "clean", "pythonic", "optimized", "readable"]
    }

    sample_output = """
    Hello! Here is an efficient and clean pythonic solution for your problem.
    The code is optimized for readability and performance.
    """

    metrics = calculate_style_consistency(sample_output, sample_profile)
    print(f"Style Consistency Score: {metrics['consistency_score']}")
    print(f"Keywords Found: {metrics['keywords_found']}")
    print(f"Structure Rules Passed: {metrics['structure_rules_passed']}")


if __name__ == "__main__":
    main()