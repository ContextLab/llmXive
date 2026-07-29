"""
Manual Review Flagging Module for T019.

Implements logic to flag samples where the 'degenerate' prompt token delta
is less than 100 tokens compared to the 'very_complex' prompt.
This is a diagnostic flag for manual review, not a fatal error.
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
    variants_df: pd.DataFrame,
    problem_id: str,
    degenerate_label: str = 'degenerate',
    very_complex_label: str = 'very_complex'
) -> Optional[int]:
    """
    Calculate the token count difference between the 'degenerate' and 'very_complex'
    variants for a specific problem_id.

    Args:
        variants_df: DataFrame containing prompt variants with columns:
                     'problem_id', 'complexity_label', 'token_count'.
        problem_id: The ID of the HumanEval problem.
        degenerate_label: The label for the degenerate variant.
        very_complex_label: The label for the very complex variant.

    Returns:
        The token count difference (degenerate - very_complex), or None if
        either variant is missing.
    """
    problem_variants = variants_df[variants_df['problem_id'] == problem_id]

    degenerate_row = problem_variants[
        problem_variants['complexity_label'] == degenerate_label
    ]
    very_complex_row = problem_variants[
        problem_variants['complexity_label'] == very_complex_label
    ]

    if degenerate_row.empty or very_complex_row.empty:
        logger.warning(
            f"Missing variant for problem {problem_id}: "
            f"degenerate={degenerate_row.empty}, very_complex={very_complex_row.empty}"
        )
        return None

    degenerate_tokens = degenerate_row['token_count'].iloc[0]
    very_complex_tokens = very_complex_row['token_count'].iloc[0]

    return int(degenerate_tokens - very_complex_tokens)

def flag_low_delta_samples(
    variants_df: pd.DataFrame,
    threshold: int = 100
) -> List[Dict[str, Any]]:
    """
    Identify all samples where the 'degenerate' prompt token delta is less than
    the specified threshold compared to 'very_complex'.

    Args:
        variants_df: DataFrame of prompt variants.
        threshold: The minimum expected delta (default 100).

    Returns:
        List of dictionaries containing flagged sample details.
    """
    flagged_samples = []
    problem_ids = variants_df['problem_id'].unique()

    for pid in problem_ids:
        delta = calculate_token_delta(variants_df, pid)
        if delta is not None and delta < threshold:
            flagged_samples.append({
                'problem_id': pid,
                'degenerate_tokens': int(
                    variants_df[
                        (variants_df['problem_id'] == pid) &
                        (variants_df['complexity_label'] == 'degenerate')
                    ]['token_count'].iloc[0]
                ),
                'very_complex_tokens': int(
                    variants_df[
                        (variants_df['problem_id'] == pid) &
                        (variants_df['complexity_label'] == 'very_complex')
                    ]['token_count'].iloc[0]
                ),
                'delta': delta,
                'reason': f"Token delta ({delta}) < threshold ({threshold})"
            })

    logger.info(f"Flagged {len(flagged_samples)} samples for manual review.")
    return flagged_samples

def write_manual_review_queue(
    flagged_samples: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Write the flagged samples to the manual review queue CSV.

    Args:
        flagged_samples: List of flagged sample dictionaries.
        output_path: Path to the output CSV file.
    """
    if not flagged_samples:
        logger.info("No samples flagged. Creating empty queue file.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['problem_id', 'degenerate_tokens', 'very_complex_tokens', 'delta', 'reason'])
            writer.writeheader()
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['problem_id', 'degenerate_tokens', 'very_complex_tokens', 'delta', 'reason']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flagged_samples)

    logger.info(f"Wrote {len(flagged_samples)} flagged samples to {output_path}")

def main() -> None:
    """
    Main entry point to run the manual review flagging logic.
    Reads from data/processed/prompt_variants.parquet and writes to
    data/results/manual_review_queue.csv.
    """
    input_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T018 (storage) has been run successfully."
        )

    logger.info(f"Loading variants from {input_path}")
    df = pd.read_parquet(input_path)

    # Ensure required columns exist
    required_cols = ['problem_id', 'complexity_label', 'token_count']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")

    flagged = flag_low_delta_samples(df, threshold=100)
    write_manual_review_queue(flagged, output_path)

    if not flagged:
        logger.info("All degenerate prompts have sufficient token delta (>100) vs very_complex.")
    else:
        logger.warning(
            f"Found {len(flagged)} samples with low token delta. "
            f"Review queue written to {output_path}"
        )

if __name__ == "__main__":
    main()