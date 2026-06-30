"""
Bonferroni correction utility for multiple hypothesis testing.

Applies the Bonferroni correction to a list of p-values to control the family-wise error rate.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path


def bonferroni_correct(p_values: List[float], total_tests: int) -> List[Tuple[float, float]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        total_tests: Total number of tests performed (n).
    
    Returns:
        List of tuples (original_p, corrected_p) for each test.
    """
    if total_tests <= 0:
        raise ValueError("total_tests must be greater than 0")
    
    corrected_results = []
    for p in p_values:
        # Cap corrected p-value at 1.0
        corrected_p = min(p * total_tests, 1.0)
        corrected_results.append((p, corrected_p))
    
    return corrected_results


def load_p_values_from_csv(
    file_path: str, 
    p_column: str = "p_value", 
    output_path: Optional[str] = None
) -> List[float]:
    """
    Load p-values from a CSV file.
    
    Args:
        file_path: Path to the input CSV file.
        p_column: Name of the column containing p-values.
        output_path: Optional path to save the extracted list as JSON (checkpoint).
    
    Returns:
        List of float p-values.
    """
    p_values = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if p_column not in reader.fieldnames:
            raise ValueError(f"Column '{p_column}' not found in {file_path}. Available: {reader.fieldnames}")
        
        for row in reader:
            try:
                val = float(row[p_column])
                if val < 0 or val > 1:
                    # Log warning but keep going, or raise? Spec says real data, assume valid range mostly
                    # But strictly p-values are [0,1]. Let's clamp or warn. For now, just append.
                    pass
                p_values.append(val)
            except ValueError:
                # Skip non-numeric entries if any
                continue
    
    if output_path:
        save_checkpoint({"p_values": p_values}, output_path)
    
    return p_values


def save_corrected_results(
    results: List[Tuple[float, float]], 
    input_file: str, 
    output_file: str, 
    p_column: str = "p_value"
) -> None:
    """
    Save corrected p-values to a new CSV file, preserving original columns.
    
    Args:
        results: List of (original_p, corrected_p) tuples.
        input_file: Path to the source CSV (to preserve other columns).
        output_file: Path to save the result CSV.
        p_column: Name of the original p-value column.
    """
    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)
        
        # Add new column if not present
        corrected_col = f"{p_column}_bonferroni"
        if corrected_col not in fieldnames:
            fieldnames.append(corrected_col)
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row, (_, corrected_p) in zip(reader, results):
            row[corrected_col] = f"{corrected_p:.6f}"
            writer.writerow(row)


def main():
    """
    CLI entry point for Bonferroni correction.
    
    Usage:
    python -m scripts.utils.bonferroni \
        --input data/processed/distribution_fits.csv \
        --p-column KS_pvalue \
        --total-tests 50 \
        --output data/processed/distribution_fits_corrected.csv
    """
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to p-values in a CSV.")
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument("--p-column", default="p_value", help="Name of the column containing p-values.")
    parser.add_argument("--total-tests", type=int, required=True, help="Total number of hypothesis tests performed (N).")
    parser.add_argument("--output", required=True, help="Path to save the output CSV with corrected p-values.")
    parser.add_argument("--checkpoint-dir", default="data/checkpoints", help="Directory for intermediate checkpoints.")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load p-values
        p_values = load_p_values_from_csv(str(input_path), p_column=args.p_column)
        
        if not p_values:
            print(f"Warning: No valid p-values found in column '{args.p_column}'.", file=sys.stderr)
            sys.exit(0)
        
        # Apply correction
        corrected = bonferroni_correct(p_values, args.total_tests)
        
        # Save results
        save_corrected_results(corrected, str(input_path), args.output, p_column=args.p_column)
        
        print(f"Successfully applied Bonferroni correction to {len(p_values)} values.")
        print(f"Output saved to: {args.output}")
        
        # Optional: Save a summary checkpoint
        ensure_checkpoint_dir(args.checkpoint_dir)
        checkpoint_path = get_checkpoint_path(args.checkpoint_dir, "bonferroni_summary")
        save_checkpoint({
            "input_file": str(input_path),
            "total_tests": args.total_tests,
            "n_values_processed": len(p_values),
            "output_file": args.output
        }, checkpoint_path)
        
    except Exception as e:
        print(f"Error during correction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()