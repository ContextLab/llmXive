"""
Manual Review Flagging for Prompt Complexity Evaluation.

This module implements logic to flag samples where the 'degenerate' prompt
token delta is less than 100 tokens compared to the 'very_complex' prompt.
Such cases indicate a potential failure in the prompt generation logic to
create sufficient complexity separation, requiring manual review.

The flagged sample IDs are appended to `data/results/manual_review_queue.csv`.
"""

import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
MANUAL_REVIEW_QUEUE_PATH = DATA_RESULTS_DIR / "manual_review_queue.csv"

# Threshold for flagging
TOKEN_DELTA_THRESHOLD = 100

def load_variants_from_parquet(parquet_path: Path) -> List[Dict[str, Any]]:
    """
    Load prompt variants from a Parquet file.
    
    Args:
        parquet_path: Path to the parquet file containing prompt variants.
        
    Returns:
        List of dictionaries representing the variants.
    """
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        return df.to_dict(orient='records')
    except ImportError:
        print("Error: pandas and pyarrow are required to read parquet files.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Parquet file not found at {parquet_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading parquet file: {e}")
        sys.exit(1)

def group_variants_by_problem(variants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group variants by problem_id.
    
    Args:
        variants: List of variant dictionaries.
        
    Returns:
        Dictionary mapping problem_id to list of variants.
    """
    groups = {}
    for variant in variants:
        problem_id = variant.get('problem_id')
        if not problem_id:
            continue
        if problem_id not in groups:
            groups[problem_id] = []
        groups[problem_id].append(variant)
    return groups

def find_token_delta_for_degenerate_vs_very_complex(
    variants_for_problem: List[Dict[str, Any]]
) -> Optional[int]:
    """
    Calculate the token count delta between 'degenerate' and 'very_complex' variants
    for a specific problem.
    
    Args:
        variants_for_problem: List of variants for a single problem.
        
    Returns:
        The token delta (degenerate_tokens - very_complex_tokens), or None if
        either variant is missing.
    """
    degenerate_variant = None
    very_complex_variant = None
    
    for variant in variants_for_problem:
        complexity_label = variant.get('complexity_label')
        token_count = variant.get('token_count')
        
        if complexity_label == 'degenerate' and token_count is not None:
            degenerate_variant = variant
        elif complexity_label == 'very_complex' and token_count is not None:
            very_complex_variant = variant
    
    if degenerate_variant is None or very_complex_variant is None:
        return None
        
    return degenerate_variant.get('token_count', 0) - very_complex_variant.get('token_count', 0)

def flag_low_delta_samples(
    variants: List[Dict[str, Any]],
    threshold: int = TOKEN_DELTA_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Identify samples where the 'degenerate' prompt token delta is less than
    the specified threshold compared to 'very_complex'.
    
    Args:
        variants: List of all prompt variants.
        threshold: Minimum expected token delta.
        
    Returns:
        List of flagged variant dictionaries.
    """
    groups = group_variants_by_problem(variants)
    flagged_samples = []
    
    for problem_id, problem_variants in groups.items():
        delta = find_token_delta_for_degenerate_vs_very_complex(problem_variants)
        
        if delta is not None and delta < threshold:
            # Find the specific degenerate and very_complex variants to flag
            for variant in problem_variants:
                if variant.get('complexity_label') in ['degenerate', 'very_complex']:
                    flagged_record = {
                        'problem_id': problem_id,
                        'complexity_label': variant.get('complexity_label'),
                        'token_count': variant.get('token_count'),
                        'delta': delta,
                        'reason': f"Token delta ({delta}) < threshold ({threshold})"
                    }
                    flagged_samples.append(flagged_record)
                    
    return flagged_samples

def append_to_manual_review_queue(flagged_samples: List[Dict[str, Any]]) -> None:
    """
    Append flagged samples to the manual review queue CSV.
    
    Args:
        flagged_samples: List of dictionaries containing flagged sample info.
    """
    if not flagged_samples:
        print("No samples flagged for manual review.")
        return
        
    # Ensure directory exists
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['problem_id', 'complexity_label', 'token_count', 'delta', 'reason']
    
    # Check if file exists to determine if we need to write headers
    file_exists = MANUAL_REVIEW_QUEUE_PATH.exists()
    
    with open(MANUAL_REVIEW_QUEUE_PATH, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        for sample in flagged_samples:
            writer.writerow(sample)
            
    print(f"Flagged {len(flagged_samples)} samples appended to {MANUAL_REVIEW_QUEUE_PATH}")

def main():
    """
    Main entry point for the manual review flagging process.
    
    Reads variants from data/processed/prompt_variants.parquet,
    flags low-delta samples, and appends them to data/results/manual_review_queue.csv.
    """
    parquet_path = PROJECT_ROOT / "data" / "processed" / "prompt_variants.parquet"
    
    if not parquet_path.exists():
        print(f"Error: Input file not found: {parquet_path}")
        print("Please ensure prompt_variants.parquet has been generated by previous steps.")
        sys.exit(1)
        
    print(f"Loading variants from {parquet_path}...")
    variants = load_variants_from_parquet(parquet_path)
    print(f"Loaded {len(variants)} variants.")
    
    print(f"Checking for degenerate vs very_complex token delta < {TOKEN_DELTA_THRESHOLD}...")
    flagged_samples = flag_low_delta_samples(variants, TOKEN_DELTA_THRESHOLD)
    
    if flagged_samples:
        print(f"Found {len(flagged_samples)} samples requiring manual review.")
        append_to_manual_review_queue(flagged_samples)
    else:
        print("No samples require manual review based on the token delta threshold.")
        
    print("Manual review flagging complete.")

if __name__ == "__main__":
    main()