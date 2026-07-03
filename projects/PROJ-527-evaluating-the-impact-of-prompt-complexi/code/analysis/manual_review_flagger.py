"""
T019: Flag samples where 'degenerate' prompt token delta < 100 tokens vs 'very complex'.

This module implements the logic to identify prompt variants that fail to exhibit
the expected token count separation between 'degenerate' and 'very_complex' complexity levels.
According to the specification, if the delta is less than 100 tokens, the sample is flagged
for manual review and appended to data/results/manual_review_queue.csv.

This is a diagnostic check to ensure prompt generation logic is working as intended
(i.e., degenerate prompts should be significantly longer/more redundant than very complex ones).
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import Paths
from data.storage import load_variants_from_parquet
from models.data_models import ComplexityLabel


def calculate_token_delta(variants: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate the token count difference between 'degenerate' and 'very_complex' variants.

    Args:
        variants: List of prompt variant dictionaries containing 'complexity_label' and 'token_count'.

    Returns:
        The token delta (degenerate - very_complex) if both exist, otherwise None.
    """
    degenerate_token_count = None
    very_complex_token_count = None

    for variant in variants:
        label = variant.get('complexity_label')
        token_count = variant.get('token_count')

        if label == 'degenerate' and token_count is not None:
            degenerate_token_count = token_count
        elif label == 'very_complex' and token_count is not None:
            very_complex_token_count = token_count

    if degenerate_token_count is not None and very_complex_token_count is not None:
        return degenerate_token_count - very_complex_token_count

    return None


def flag_low_delta_samples(
    variants_df: pd.DataFrame,
    threshold: float = 100.0,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Identify samples where the token delta between degenerate and very_complex is below threshold.

    Args:
        variants_df: DataFrame containing prompt variants with columns:
            - problem_id
            - complexity_label
            - token_count
        threshold: Minimum expected token difference (default 100).
        output_path: Path to write the manual review CSV. Defaults to data/results/manual_review_queue.csv.

    Returns:
        DataFrame of flagged samples with columns: problem_id, degenerate_tokens, very_complex_tokens, delta.
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Group by problem_id to compare variants
    flagged_samples = []

    for problem_id, group in variants_df.groupby('problem_id'):
        # Get token counts for specific complexity labels
        degenerate_row = group[group['complexity_label'] == 'degenerate']
        very_complex_row = group[group['complexity_label'] == 'very_complex']

        if degenerate_row.empty or very_complex_row.empty:
            continue

        degenerate_tokens = degenerate_row['token_count'].iloc[0]
        very_complex_tokens = very_complex_row['token_count'].iloc[0]
        delta = degenerate_tokens - very_complex_tokens

        # Flag if delta is below threshold
        if delta < threshold:
            flagged_samples.append({
                'problem_id': problem_id,
                'degenerate_token_count': degenerate_tokens,
                'very_complex_token_count': very_complex_tokens,
                'delta': delta,
                'reason': 'Degenerate prompt token delta < 100 vs very complex'
            })

    flagged_df = pd.DataFrame(flagged_samples)

    # Write to CSV
    if not flagged_df.empty:
        # Check if file exists to determine append mode
        file_exists = output_path.exists() and output_path.stat().st_size > 0
        mode = 'a' if file_exists else 'w'
        header = mode == 'w'

        flagged_df.to_csv(
            output_path,
            mode=mode,
            index=False,
            header=header
        )

    return flagged_df


def main():
    """
    Main entry point for T019 implementation.
    Loads generated variants, flags low-delta samples, and writes to manual review queue.
    """
    print("Starting T019: Manual Review Flagging for Low Token Delta")

    # Load variants from parquet
    variants_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if not variants_path.exists():
        print(f"ERROR: Variants file not found at {variants_path}")
        print("Please ensure T018 (storage) has been completed first.")
        return

    print(f"Loading variants from {variants_path}...")
    variants_df = load_variants_from_parquet(variants_path)

    if variants_df is None or variants_df.empty:
        print("WARNING: No variants found in the dataset.")
        return

    print(f"Loaded {len(variants_df)} variants")

    # Perform flagging
    output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"
    flagged_df = flag_low_delta_samples(variants_df, threshold=100.0, output_path=output_path)

    if flagged_df.empty:
        print(f"No samples flagged for manual review. All degenerate prompts have delta >= 100.")
    else:
        print(f"Flagged {len(flagged_df)} samples for manual review.")
        print(f"Results written to: {output_path}")
        print("\nFlagged samples summary:")
        print(flagged_df[['problem_id', 'degenerate_token_count', 'very_complex_token_count', 'delta']].to_string())

    return flagged_df


if __name__ == "__main__":
    main()