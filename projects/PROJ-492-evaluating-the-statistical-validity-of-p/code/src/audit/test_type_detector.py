"""
Outcome-type detection heuristics for A/B test summaries.

This module determines whether an A/B test summary represents a binary outcome
(e.g., conversion rate, click-through rate) or a continuous outcome
(e.g., average order value, time on site).

Detection is based on field names and value characteristics in the ABTestSummary.
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from pathlib import Path

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

OutcomeType = Literal["binary", "continuous", "unknown"]

logger = get_default_logger()


def detect_outcome_type(summary: ABTestSummary) -> OutcomeType:
    """
    Detect whether the A/B test summary represents a binary or continuous outcome.

    Heuristics:
    1. If 'baseline_conversion_rate' or 'treatment_conversion_rate' is present,
       it is likely a binary outcome.
    2. If 'baseline_mean' or 'treatment_mean' is present, it is likely continuous.
    3. If 'sample_size' and 'baseline_conversion_rate' are present, assume binary.
    4. If 'baseline_mean' and 'baseline_std' are present, assume continuous.
    5. Check field names for keywords like 'rate', 'conversion', 'click' -> binary.
    6. Check field names for keywords like 'mean', 'avg', 'value', 'time' -> continuous.

    Args:
        summary: An ABTestSummary object containing extracted metrics.

    Returns:
        "binary", "continuous", or "unknown" if insufficient evidence.
    """
    data = summary.model_dump(exclude_none=True)

    # Heuristic 1: Check for conversion rate fields
    conversion_fields = ["baseline_conversion_rate", "treatment_conversion_rate",
                         "baseline_cr", "treatment_cr", "conversion_rate"]
    if any(field in data for field in conversion_fields):
        logger.debug(f"Detected binary outcome via conversion rate fields for {summary.url}")
        return "binary"

    # Heuristic 2: Check for mean/std fields
    mean_fields = ["baseline_mean", "treatment_mean", "baseline_avg", "treatment_avg"]
    std_fields = ["baseline_std", "treatment_std", "baseline_sd", "treatment_sd"]
    
    has_mean = any(field in data for field in mean_fields)
    has_std = any(field in data for field in std_fields)

    if has_mean and has_std:
        logger.debug(f"Detected continuous outcome via mean/std fields for {summary.url}")
        return "continuous"
    
    if has_mean:
        # If only mean is present, check for other continuous indicators
        continuous_keywords = ["value", "time", "duration", "revenue", "amount", "price"]
        # Check keys for keywords
        key_str = " ".join(data.keys()).lower()
        if any(kw in key_str for kw in continuous_keywords):
            logger.debug(f"Detected continuous outcome via keyword match for {summary.url}")
            return "continuous"

    # Heuristic 3: Check for sample size with conversion indicators
    if "sample_size" in data or "n_control" in data or "n_treatment" in data:
        # If we have sample sizes but no mean/std, and no explicit conversion fields,
        # check if the metric looks like a proportion (0-1 range)
        for key, val in data.items():
            if isinstance(val, (int, float)) and 0.0 <= val <= 1.0:
                # Could be a rate/proportion
                if "rate" in key.lower() or "conversion" in key.lower():
                    logger.debug(f"Detected binary outcome via proportion range for {summary.url}")
                    return "binary"

    # Heuristic 4: Fallback based on raw metric presence
    # If we have 'metric' field, check its name
    if "metric_name" in data:
        metric_name = str(data["metric_name"]).lower()
        if any(kw in metric_name for kw in ["conversion", "rate", "click", "signup", "purchase"]):
            logger.debug(f"Detected binary outcome via metric name for {summary.url}")
            return "binary"
        if any(kw in metric_name for kw in ["mean", "avg", "value", "time", "duration", "revenue"]):
            logger.debug(f"Detected continuous outcome via metric name for {summary.url}")
            return "continuous"

    logger.warning(f"Could not determine outcome type for {summary.url}; defaulting to unknown")
    return "unknown"


def detect_outcome_types_batch(summaries: List[ABTestSummary]) -> List[Dict[str, Any]]:
    """
    Detect outcome types for a batch of ABTestSummary objects.

    Args:
        summaries: List of ABTestSummary objects.

    Returns:
        List of dictionaries containing 'url', 'outcome_type', and 'detected_by'.
    """
    results = []
    for summary in summaries:
        outcome_type = detect_outcome_type(summary)
        results.append({
            "url": summary.url,
            "outcome_type": outcome_type,
            "detection_status": "success" if outcome_type != "unknown" else "unknown"
        })
    return results


def main() -> int:
    """
    Main entry point for running the test type detector on extracted summaries.
    
    This script loads extracted summaries from data/extracted_summaries.json,
    runs the detector, and writes results to data/outcome_types.json.
    """
    import json
    from pathlib import Path

    input_path = Path("data/extracted_summaries.json")
    output_path = Path("data/outcome_types.json")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    logger.info(f"Loading summaries from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        summaries_data = json.load(f)

    # Convert to ABTestSummary objects
    summaries = [ABTestSummary(**item) for item in summaries_data]

    logger.info(f"Detected outcome types for {len(summaries)} summaries")
    results = detect_outcome_types_batch(summaries)

    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Wrote outcome type detection results to {output_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
