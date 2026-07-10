"""
Outcome-type detection heuristics for A/B test summaries.

This module implements logic to distinguish between binary (proportion-based)
and continuous (mean-based) outcomes based on the fields present in an ABTestSummary.
"""

import logging
from typing import List, Optional, Tuple

from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

OUTCOME_TYPE_BINARY = "binary"
OUTCOME_TYPE_CONTINUOUS = "continuous"
OUTCOME_TYPE_UNKNOWN = "unknown"


def detect_outcome_type(summary: ABTestSummary) -> str:
    """
    Detect whether an A/B test summary represents a binary or continuous outcome.

    Heuristics:
    1. If 'conversions_control' or 'conversions_treatment' are present and non-null,
       it is treated as a binary outcome (proportions).
    2. If 'mean_control' or 'mean_treatment' are present and non-null, it is
       treated as a continuous outcome (means).
    3. If both are present, binary takes precedence (as conversions are more
       specific to proportion tests).
    4. If neither is present, return 'unknown'.

    Args:
        summary: An ABTestSummary object containing extracted metrics.

    Returns:
        One of 'binary', 'continuous', or 'unknown'.
    """
    has_conversions = (
        summary.conversions_control is not None
        or summary.conversions_treatment is not None
    )
    has_means = (
        summary.mean_control is not None
        or summary.mean_treatment is not None
    )

    if has_conversions:
        logger.debug(
            f"Detected binary outcome for source {summary.source_url or 'unknown'} "
            "(conversions fields present)"
        )
        return OUTCOME_TYPE_BINARY

    if has_means:
        logger.debug(
            f"Detected continuous outcome for source {summary.source_url or 'unknown'} "
            "(mean fields present)"
        )
        return OUTCOME_TYPE_CONTINUOUS

    logger.warning(
        f"Could not determine outcome type for source {summary.source_url or 'unknown'}; "
        "neither conversion nor mean fields found."
    )
    return OUTCOME_TYPE_UNKNOWN


def detect_outcome_types_for_batch(
    summaries: List[ABTestSummary],
) -> List[Tuple[ABTestSummary, str]]:
    """
    Detect outcome types for a list of summaries.

    Args:
        summaries: List of ABTestSummary objects.

    Returns:
        List of tuples (summary, detected_type).
    """
    results = []
    for summary in summaries:
        detected_type = detect_outcome_type(summary)
        results.append((summary, detected_type))
    return results


def main() -> None:
    """
    CLI entry point for testing the detector on a provided JSON file.
    Usage: python -m src.audit.test_type_detector --input data/extracted/summaries.json
    """
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Detect outcome types for A/B test summaries."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to JSON file containing list of ABTestSummary objects.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=False,
        help="Path to write results JSON (optional).",
    )
    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Convert raw dicts to ABTestSummary objects if needed
    summaries = []
    for item in raw_data:
        try:
            summary = ABTestSummary(**item)
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Failed to parse summary item: {e}")
            continue

    results = detect_outcome_types_for_batch(summaries)

    output_data = []
    for summary, detected_type in results:
        output_data.append({
            "source_url": summary.source_url,
            "detected_type": detected_type,
        })

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()
