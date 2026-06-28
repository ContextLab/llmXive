"""
Outcome-type detection heuristics for A/B test summaries.

Detects whether an A/B test summary represents a binary outcome (proportions,
conversion rates) vs continuous outcome (means, averages).

This module is used by the reconstructor (T023) to determine which statistical
test to apply for reconstruction.
"""

import logging
from typing import Dict, Any, Optional, Tuple, Literal

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import safe_float

# Outcome type constants
OUTCOME_BINARY = "binary"
OUTCOME_CONTINUOUS = "continuous"
OUTCOME_UNKNOWN = "unknown"

# Field name patterns that indicate binary outcomes
BINARY_FIELD_PATTERNS = [
    "conversion_rate",
    "baseline_rate",
    "treatment_rate",
    "control_rate",
    "success_rate",
    "click_rate",
    "click_through_rate",
    "ctr",
    "conversion",
    "baseline_conversion",
    "treatment_conversion",
    "control_conversion",
    "proportion",
    "baseline_proportion",
    "treatment_proportion",
    "control_proportion",
    "rate",
    "baseline_rate_numerator",
    "baseline_rate_denominator",
    "treatment_rate_numerator",
    "treatment_rate_denominator",
]

# Field name patterns that indicate continuous outcomes
CONTINUOUS_FIELD_PATTERNS = [
    "mean",
    "average",
    "baseline_mean",
    "treatment_mean",
    "control_mean",
    "avg",
    "baseline_avg",
    "treatment_avg",
    "control_avg",
    "value",
    "baseline_value",
    "treatment_value",
    "control_value",
    "metric_value",
    "revenue",
    "baseline_revenue",
    "treatment_revenue",
    "time",
    "baseline_time",
    "treatment_time",
    "duration",
    "baseline_duration",
    "treatment_duration",
    "latency",
    "baseline_latency",
    "treatment_latency",
]

# Metric description keywords indicating binary outcomes
BINARY_KEYWORDS = [
    "conversion",
    "click",
    "signup",
    "purchase",
    "install",
    "click-through",
    "ctr",
    "rate",
    "proportion",
    "percentage",
    "binary",
    "success",
    "failure",
    "yes/no",
    "converted",
    "clicked",
    "bought",
    "subscribed",
]

# Metric description keywords indicating continuous outcomes
CONTINUOUS_KEYWORDS = [
    "mean",
    "average",
    "value",
    "amount",
    "revenue",
    "time",
    "duration",
    "latency",
    "response",
    "wait",
    "load",
    "score",
    "rating",
    "continuous",
    "quantitative",
    "dollars",
    "seconds",
    "minutes",
    "hours",
    "bytes",
    "kilobytes",
    "megabytes",
]


def _normalize_field_name(field_name: str) -> str:
    """
    Normalize a field name for pattern matching.

    Args:
        field_name: The field name to normalize.

    Returns:
        Lowercase, underscore-normalized field name.
    """
    if not field_name:
        return ""
    return field_name.lower().replace("-", "_").replace(".", "_")


def _check_binary_fields(summary_data: Dict[str, Any]) -> bool:
    """
    Check if summary data contains fields indicative of binary outcomes.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if binary-indicative fields are present.
    """
    for key in summary_data.keys():
        normalized = _normalize_field_name(key)
        for pattern in BINARY_FIELD_PATTERNS:
            if pattern in normalized:
                return True
    return False


def _check_continuous_fields(summary_data: Dict[str, Any]) -> bool:
    """
    Check if summary data contains fields indicative of continuous outcomes.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if continuous-indicative fields are present.
    """
    for key in summary_data.keys():
        normalized = _normalize_field_name(key)
        for pattern in CONTINUOUS_FIELD_PATTERNS:
            if pattern in normalized:
                return True
    return False


def _check_binary_keywords(summary_data: Dict[str, Any]) -> bool:
    """
    Check if summary data contains keywords indicative of binary outcomes.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if binary-indicative keywords are present.
    """
    # Check metric_name or description fields
    text_fields = [
        summary_data.get("metric_name", ""),
        summary_data.get("metric_description", ""),
        summary_data.get("description", ""),
        summary_data.get("title", ""),
        summary_data.get("metric", ""),
    ]

    for text in text_fields:
        if text:
            text_lower = text.lower()
            for keyword in BINARY_KEYWORDS:
                if keyword in text_lower:
                    return True
    return False


def _check_continuous_keywords(summary_data: Dict[str, Any]) -> bool:
    """
    Check if summary data contains keywords indicative of continuous outcomes.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if continuous-indicative keywords are present.
    """
    # Check metric_name or description fields
    text_fields = [
        summary_data.get("metric_name", ""),
        summary_data.get("metric_description", ""),
        summary_data.get("description", ""),
        summary_data.get("title", ""),
        summary_data.get("metric", ""),
    ]

    for text in text_fields:
        if text:
            text_lower = text.lower()
            for keyword in CONTINUOUS_KEYWORDS:
                if keyword in text_lower:
                    return True
    return False


def _check_numeric_patterns(summary_data: Dict[str, Any]) -> Tuple[bool, bool]:
    """
    Check numeric field patterns to infer outcome type.

    Binary outcomes typically have:
    - baseline_rate/treatment_rate with numerators and denominators
    - Values between 0 and 1 for rates

    Continuous outcomes typically have:
    - baseline_mean/treatment_mean with standard deviations
    - Values that can exceed 1

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        Tuple of (has_binary_pattern, has_continuous_pattern).
    """
    has_binary_pattern = False
    has_continuous_pattern = False

    # Check for rate-based patterns (binary)
    rate_fields = ["baseline_rate", "treatment_rate", "control_rate"]
    for field in rate_fields:
        if field in summary_data:
            value = safe_float(summary_data.get(field))
            if value is not None and 0 <= value <= 1:
                has_binary_pattern = True

    # Check for mean-based patterns with standard deviation (continuous)
    mean_fields = ["baseline_mean", "treatment_mean", "control_mean"]
    std_fields = ["baseline_std", "treatment_std", "control_std",
                 "baseline_std_dev", "treatment_std_dev", "control_std_dev"]

    for mean_field in mean_fields:
        if mean_field in summary_data:
            # Check if there's a corresponding std field
            for std_field in std_fields:
                if std_field in summary_data:
                    has_continuous_pattern = True
                    break
            if has_continuous_pattern:
                break

    return has_binary_pattern, has_continuous_pattern


def detect_outcome_type(
    summary_data: Dict[str, Any],
    logger: Optional[AuditLogger] = None
) -> Tuple[str, Dict[str, bool]]:
    """
    Detect the outcome type (binary vs continuous) for an A/B test summary.

    This function uses multiple heuristics to determine whether the summary
    represents a binary outcome (e.g., conversion rate, click-through rate)
    or a continuous outcome (e.g., mean revenue, average latency).

    The detection follows this priority:
    1. Explicit field type indicators (most reliable)
    2. Field name patterns (high reliability)
    3. Keyword analysis in descriptions (medium reliability)
    4. Numeric pattern analysis (supporting evidence)

    Args:
        summary_data: The extracted summary data as a dictionary.
        logger: Optional AuditLogger for logging detection decisions.

    Returns:
        Tuple of (outcome_type, evidence_dict) where:
        - outcome_type: One of "binary", "continuous", or "unknown"
        - evidence_dict: Dictionary with detection evidence for each heuristic
    """
    if logger is None:
        logger = get_default_logger()

    evidence = {
        "binary_fields": False,
        "continuous_fields": False,
        "binary_keywords": False,
        "continuous_keywords": False,
        "binary_numeric_pattern": False,
        "continuous_numeric_pattern": False,
    }

    # Heuristic 1: Check field name patterns
    evidence["binary_fields"] = _check_binary_fields(summary_data)
    evidence["continuous_fields"] = _check_continuous_fields(summary_data)

    # Heuristic 2: Check keyword patterns in text fields
    evidence["binary_keywords"] = _check_binary_keywords(summary_data)
    evidence["continuous_keywords"] = _check_continuous_keywords(summary_data)

    # Heuristic 3: Check numeric patterns
    evidence["binary_numeric_pattern"], evidence["continuous_numeric_pattern"] = \
        _check_numeric_patterns(summary_data)

    # Decision logic with priority
    binary_score = sum([
        evidence["binary_fields"],
        evidence["binary_keywords"],
        evidence["binary_numeric_pattern"],
    ])

    continuous_score = sum([
        evidence["continuous_fields"],
        evidence["continuous_keywords"],
        evidence["continuous_numeric_pattern"],
    ])

    # If there's a clear winner, return that type
    if binary_score > continuous_score and binary_score >= 1:
        outcome_type = OUTCOME_BINARY
    elif continuous_score > binary_score and continuous_score >= 1:
        outcome_type = OUTCOME_CONTINUOUS
    elif binary_score > 0 and continuous_score == 0:
        outcome_type = OUTCOME_BINARY
    elif continuous_score > 0 and binary_score == 0:
        outcome_type = OUTCOME_CONTINUOUS
    else:
        outcome_type = OUTCOME_UNKNOWN

    # Log detection decision
    if logger:
        logger.info(
            f"Outcome type detection: {outcome_type} (binary_score={binary_score}, "
            f"continuous_score={continuous_score})"
        )

    return outcome_type, evidence


def detect_outcome_type_from_ab_summary(
    ab_summary: Any,
    logger: Optional[AuditLogger] = None
) -> Tuple[str, Dict[str, bool]]:
    """
    Detect outcome type from an ABTestSummary object.

    This is a wrapper around detect_outcome_type that accepts a Pydantic
    ABTestSummary object and extracts its dictionary representation.

    Args:
        ab_summary: An ABTestSummary object from src.models.data_models.
        logger: Optional AuditLogger for logging detection decisions.

    Returns:
        Tuple of (outcome_type, evidence_dict).
    """
    if logger is None:
        logger = get_default_logger()

    # Convert Pydantic model to dict if needed
    if hasattr(ab_summary, "model_dump"):
        summary_data = ab_summary.model_dump()
    elif hasattr(ab_summary, "dict"):
        summary_data = ab_summary.dict()
    elif isinstance(ab_summary, dict):
        summary_data = ab_summary
    else:
        logger.error("ERR-099", "Invalid ABTestSummary type for outcome detection")
        return OUTCOME_UNKNOWN, {}

    return detect_outcome_type(summary_data, logger)


def is_binary_outcome(summary_data: Dict[str, Any]) -> bool:
    """
    Convenience function to check if summary represents a binary outcome.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if the outcome type is binary.
    """
    outcome_type, _ = detect_outcome_type(summary_data)
    return outcome_type == OUTCOME_BINARY


def is_continuous_outcome(summary_data: Dict[str, Any]) -> bool:
    """
    Convenience function to check if summary represents a continuous outcome.

    Args:
        summary_data: The extracted summary data as a dictionary.

    Returns:
        True if the outcome type is continuous.
    """
    outcome_type, _ = detect_outcome_type(summary_data)
    return outcome_type == OUTCOME_CONTINUOUS


def main():
    """
    Main entry point for standalone testing of the outcome type detector.
    """
    logger = get_default_logger()
    logger.info("Starting outcome type detector test")

    # Test cases
    test_cases = [
        {
            "name": "Binary - Conversion Rate",
            "data": {
                "metric_name": "Conversion Rate",
                "baseline_rate": 0.05,
                "treatment_rate": 0.07,
                "baseline_n": 1000,
                "treatment_n": 1000,
            },
            "expected": OUTCOME_BINARY,
        },
        {
            "name": "Binary - Click-Through Rate",
            "data": {
                "metric_name": "CTR",
                "baseline_ctr": 0.02,
                "treatment_ctr": 0.025,
            },
            "expected": OUTCOME_BINARY,
        },
        {
            "name": "Continuous - Mean Revenue",
            "data": {
                "metric_name": "Average Revenue",
                "baseline_mean": 50.0,
                "treatment_mean": 55.0,
                "baseline_std": 10.0,
                "treatment_std": 12.0,
            },
            "expected": OUTCOME_CONTINUOUS,
        },
        {
            "name": "Continuous - Mean Latency",
            "data": {
                "metric_name": "Response Time",
                "baseline_mean": 200,
                "treatment_mean": 180,
                "baseline_std": 50,
                "treatment_std": 45,
            },
            "expected": OUTCOME_CONTINUOUS,
        },
        {
            "name": "Unknown - Insufficient Data",
            "data": {
                "metric_name": "Unknown Metric",
                "sample_size": 100,
            },
            "expected": OUTCOME_UNKNOWN,
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        outcome_type, evidence = detect_outcome_type(test_case["data"], logger)
        expected = test_case["expected"]

        if outcome_type == expected:
            passed += 1
            logger.info(f"✓ PASSED: {test_case['name']} -> {outcome_type}")
        else:
            failed += 1
            logger.error(
                f"✗ FAILED: {test_case['name']} -> got {outcome_type}, "
                f"expected {expected}"
            )
            logger.info(f"  Evidence: {evidence}")

    logger.info(f"Test summary: {passed} passed, {failed} failed")

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
