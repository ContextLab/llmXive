"""
Manual Review Flagger for Prompt Complexity Evaluation.

This module implements logic to flag samples where the token delta between
'degenerate' and 'very_complex' prompt variants is less than 100 tokens.
Such samples may indicate a failure in the prompt generation logic to
create sufficient complexity differentiation and require manual review.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_token_delta(
    variants: List[Dict[str, Any]],
    problem_id: str
) -> Optional[Dict[str, Any]]:
    """
    Calculate the token delta between 'degenerate' and 'very_complex' variants
    for a specific problem.

    Args:
        variants: List of prompt variant dictionaries containing complexity_label
                 and token_count fields.
        problem_id: The HumanEval problem identifier.

    Returns:
        A dictionary with problem_id, degenerate_token_count, very_complex_token_count,
        and delta if both variants exist. Returns None if either variant is missing.
    """
    degenerate_variant = None
    very_complex_variant = None

    for variant in variants:
        label = variant.get("complexity_label")
        if label == "degenerate":
            degenerate_variant = variant
        elif label == "very_complex":
            very_complex_variant = variant

    if degenerate_variant is None or very_complex_variant is None:
        logger.warning(
            f"Missing variant for problem {problem_id}. "
            f"Found degenerate: {degenerate_variant is not None}, "
            f"very_complex: {very_complex_variant is not None}"
        )
        return None

    degenerate_tokens = degenerate_variant.get("token_count", 0)
    very_complex_tokens = very_complex_variant.get("token_count", 0)
    delta = very_complex_tokens - degenerate_tokens

    return {
        "problem_id": problem_id,
        "degenerate_token_count": degenerate_tokens,
        "very_complex_token_count": very_complex_tokens,
        "delta": delta
    }


def flag_low_delta_samples(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    delta_threshold: int = 100
) -> List[Dict[str, Any]]:
    """
    Load prompt variants from parquet, calculate token deltas, and flag
    samples where the delta is below the threshold.

    Args:
        input_path: Path to the input parquet file. Defaults to
                   Paths.PROCESSED_DIR / "prompt_variants.parquet".
        output_path: Path to write the manual review queue CSV. Defaults to
                    Paths.RESULTS_DIR / "manual_review_queue.csv".
        delta_threshold: The minimum required delta between very_complex and
                        degenerate tokens. Samples below this are flagged.

    Returns:
        List of flagged sample dictionaries.
    """
    if input_path is None:
        input_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"

    if output_path is None:
        output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure prompt variants have been generated and stored."
        )

    logger.info(f"Loading prompt variants from {input_path}")
    df = pd.read_parquet(input_path)

    # Group by problem_id to analyze variants per problem
    flagged_samples = []

    # Ensure required columns exist
    required_cols = ["problem_id", "complexity_label", "token_count"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in input data: {missing_cols}"
        )

    for problem_id, group in df.groupby("problem_id"):
        variants = group.to_dict(orient="records")
        delta_info = calculate_token_delta(variants, problem_id)

        if delta_info is not None:
            if delta_info["delta"] < delta_threshold:
                flagged_samples.append({
                    "problem_id": problem_id,
                    "degenerate_token_count": delta_info["degenerate_token_count"],
                    "very_complex_token_count": delta_info["very_complex_token_count"],
                    "delta": delta_info["delta"],
                    "flag_reason": f"Token delta ({delta_info['delta']}) < threshold ({delta_threshold})"
                })
                logger.info(
                    f"Flagged problem {problem_id}: delta={delta_info['delta']} "
                    f"(degenerate={delta_info['degenerate_token_count']}, "
                    f"very_complex={delta_info['very_complex_token_count']})"
                )

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if flagged_samples:
        logger.info(f"Writing {len(flagged_samples)} flagged samples to {output_path}")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "problem_id",
                "degenerate_token_count",
                "very_complex_token_count",
                "delta",
                "flag_reason"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flagged_samples)
    else:
        logger.info("No samples flagged for manual review.")
        # Write empty file with headers
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "problem_id",
                "degenerate_token_count",
                "very_complex_token_count",
                "delta",
                "flag_reason"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    return flagged_samples


def main() -> None:
    """
    Entry point for the manual review flagger script.
    Reads prompt variants from data/processed/prompt_variants.parquet,
    flags samples with low token delta between degenerate and very_complex,
    and writes results to data/results/manual_review_queue.csv.
    """
    logger.info("Starting manual review flagger")
    try:
        flagged = flag_low_delta_samples()
        logger.info(f"Manual review flagger completed. {len(flagged)} samples flagged.")
    except Exception as e:
        logger.error(f"Manual review flagger failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()