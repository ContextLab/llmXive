"""
Manual Review Flagger for Token Delta Analysis (Task T019a).

Reads generated prompt variants from data/processed/prompt_variants.parquet.
For each problem_id, compares 'degenerate' vs 'very_complex' variants.
Flags samples where:
  1. abs(token_delta) < 100
  2. degenerate_token_count < very_complex_token_count
Writes flagged samples to data/results/manual_review_queue.csv.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def load_prompt_variants() -> pd.DataFrame:
    """Load prompt variants from the processed parquet file."""
    input_path = Paths.DATA_PROCESSED / "prompt_variants.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T018 (storage) has been executed successfully."
        )
    logger.info(f"Loading prompt variants from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} prompt variants")
    return df


def calculate_token_delta(
    degenerate_tokens: int, very_complex_tokens: int
) -> int:
    """Calculate absolute token delta between degenerate and very_complex variants."""
    return abs(degenerate_tokens - very_complex_tokens)


def flag_low_delta_samples(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identify samples that fail the token delta criteria.

    Criteria:
      1. abs(token_delta) < 100
      2. degenerate_token_count < very_complex_token_count

    Returns a list of dictionaries for the manual review queue.
    """
    flagged_samples = []

    # Group by problem_id
    grouped = df.groupby("problem_id")

    for problem_id, group in grouped:
        # Filter for specific labels
        degenerate_rows = group[group["variant_label"] == "degenerate"]
        very_complex_rows = group[group["variant_label"] == "very_complex"]

        if degenerate_rows.empty or very_complex_rows.empty:
            logger.debug(f"Skipping {problem_id}: missing degenerate or very_complex variant")
            continue

        # Assume single row per label per problem (as per design)
        deg_row = degenerate_rows.iloc[0]
        vc_row = very_complex_rows.iloc[0]

        deg_tokens = deg_row.get("token_count", 0)
        vc_tokens = vc_row.get("token_count", 0)

        token_delta = calculate_token_delta(deg_tokens, vc_tokens)

        reasons = []

        # Check condition 1: Delta too low
        if token_delta < 100:
            reasons.append("token_delta_low")

        # Check condition 2: Degenerate under complex
        if deg_tokens < vc_tokens:
            reasons.append("degenerate_under_complex")

        if reasons:
            for reason in reasons:
                flagged_samples.append({
                    "problem_id": str(problem_id),
                    "variant_label": "degenerate", # Flagging the degenerate variant's issue
                    "token_delta": token_delta,
                    "reason": reason
                })
            logger.warning(
                f"Flagged problem {problem_id}: "
                f"delta={token_delta}, deg={deg_tokens}, vc={vc_tokens}, reasons={reasons}"
            )

    return flagged_samples


def write_manual_review_queue(flagged_samples: List[Dict[str, Any]]) -> None:
    """Append flagged samples to the manual review queue CSV."""
    output_path = Paths.DATA_RESULTS / "manual_review_queue.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine if file exists to handle headers correctly
    file_exists = output_path.exists()

    if not flagged_samples:
        logger.info("No samples flagged for manual review.")
        # If file doesn't exist, create it with headers
        if not file_exists:
            with open(output_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["problem_id", "variant_label", "token_delta", "reason"])
                writer.writeheader()
        return

    fieldnames = ["problem_id", "variant_label", "token_delta", "reason"]

    mode = "a" if file_exists else "w"
    with open(output_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(flagged_samples)

    logger.info(f"Wrote {len(flagged_samples)} flagged samples to {output_path}")


def main() -> None:
    """Main entry point for the manual review flagger."""
    logger.info("Starting manual review flagging (T019a)...")

    try:
        df = load_prompt_variants()
        flagged = flag_low_delta_samples(df)
        write_manual_review_queue(flagged)
        logger.info("Manual review flagging completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during flagging: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()