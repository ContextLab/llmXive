"""
Structural Redundancy Check (Task T019b).

Reads generated prompt variants from T018 (data/processed/prompt_variants.parquet).
For each problem_id, compares the 'degenerate' and 'very_complex' variants.
Flags samples where the 'degenerate' variant has FEWER structural elements than
the 'very_complex' variant (indicating a generation logic failure).
Appends flagged samples to data/results/manual_review_queue.csv.
"""
import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

def load_prompt_variants() -> pd.DataFrame:
    """
    Load the prompt variants from the processed Parquet file.
    """
    input_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T018 (storage.py) has been executed successfully."
        )

    logger.info(f"Loading prompt variants from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} variants")
    return df

def verify_redundancy(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identify samples where degenerate structural count < very_complex structural count.

    Args:
        df: DataFrame containing prompt variants with columns:
            - problem_id
            - variant_label (e.g., 'degenerate', 'very_complex')
            - structural_element_count (dict with keys: 'examples', 'constraints', 'steps')

    Returns:
        List of dicts representing flagged samples.
    """
    flagged_samples = []

    # Group by problem_id
    grouped = df.groupby('problem_id')

    for problem_id, group in grouped:
        # Filter for specific labels
        degenerate_rows = group[group['variant_label'] == 'degenerate']
        very_complex_rows = group[group['variant_label'] == 'very_complex']

        if degenerate_rows.empty or very_complex_rows.empty:
            # Skip if either variant is missing for this problem
            continue

        # Take the first occurrence if multiple exist (should be unique per problem/label)
        deg_row = degenerate_rows.iloc[0]
        vc_row = very_complex_rows.iloc[0]

        # Extract structural counts
        deg_struct = deg_row.get('structural_element_count', {})
        vc_struct = vc_row.get('structural_element_count', {})

        # Calculate total structural count (sum of examples, constraints, steps)
        deg_total = sum(deg_struct.values()) if deg_struct else 0
        vc_total = sum(vc_struct.values()) if vc_struct else 0

        # Check condition: degenerate < very_complex indicates failure
        if deg_total < vc_total:
            flagged_samples.append({
                'problem_id': str(problem_id),
                'variant_label': 'degenerate',
                'token_delta': None, # Not applicable for this check
                'reason': 'structural_redundancy_failure',
                'degenerate_structural_count': deg_total,
                'very_complex_structural_count': vc_total
            })
            logger.warning(
                f"Flagged problem {problem_id}: degenerate ({deg_total}) < very_complex ({vc_total})"
            )

    return flagged_samples

def write_manual_review_flags(flags: List[Dict[str, Any]]) -> None:
    """
    Append flagged samples to the manual review queue CSV.
    """
    output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define columns to ensure consistency
    # Note: We append to existing file if it exists, so we handle headers carefully.
    fieldnames = ['problem_id', 'variant_label', 'token_delta', 'reason',
                  'degenerate_structural_count', 'very_complex_structural_count']

    file_exists = output_path.exists() and output_path.stat().st_size > 0

    logger.info(f"Writing {len(flags)} flags to {output_path}")

    with open(output_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for flag in flags:
            # Only write the columns that are relevant for this check
            # but include all defined fieldnames for consistency
            row = {key: flag.get(key, '') for key in fieldnames}
            writer.writerow(row)

def run_structural_redundancy_check() -> int:
    """
    Main entry point for the structural redundancy check.
    Returns 0 on success, non-zero on failure.
    """
    try:
        df = load_prompt_variants()
        flags = verify_redundancy(df)
        write_manual_review_flags(flags)
        
        if flags:
            logger.warning(f"Structural redundancy check found {len(flags)} failures.")
        else:
            logger.info("Structural redundancy check passed: no failures found.")
        
        return 0
    except Exception as e:
        logger.error(f"Structural redundancy check failed: {e}", exc_info=True)
        return 1

def main():
    """
    CLI entry point.
    """
    import sys
    sys.exit(run_structural_redundancy_check())

if __name__ == "__main__":
    main()