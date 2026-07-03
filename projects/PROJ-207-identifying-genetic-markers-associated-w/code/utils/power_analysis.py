"""
Power analysis module for FR-012.

Calculates statistical power for GWAS using a non-central chi-squared distribution.
Enforces minimum sample size requirements (n >= 80).
"""
import sys
import os
import math
from pathlib import Path
from scipy import stats
import pandas as pd
import numpy as np

# Error codes
ERR_SAMPLE_SIZE_INSUFFICIENT = "ERR_SAMPLE_SIZE_INSUFFICIENT"

def get_sample_count_from_data(input_path: str) -> int:
    """
    Determine the total sample size (n) from the input data file.
    
    Attempts to read a phenotype file or a PLINK .fam file to count samples.
    If the file is a .fam file, it counts the number of rows.
    If it's a CSV/TSV with a 'sample_id' or similar column, it counts rows.
    
    Args:
        input_path: Path to the data file (e.g., .fam, .csv, .tsv)
        
    Returns:
        int: The number of samples (n)
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file format is unrecognized or cannot be parsed
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    suffix = path.suffix.lower()
    
    # Handle PLINK .fam files (6 columns, no header)
    if suffix == '.fam':
        with open(path, 'r') as f:
            lines = f.readlines()
        return len([l for l in lines if l.strip()])
    
    # Handle CSV/TSV
    try:
        # Try to detect separator
        with open(path, 'r') as f:
            first_line = f.readline()
            if '\t' in first_line:
                sep = '\t'
            else:
                sep = ','
        
        df = pd.read_csv(path, sep=sep)
        return len(df)
    except Exception as e:
        raise ValueError(f"Could not parse input file {input_path}: {e}")

def calculate_power(n: int, alpha: float = 0.05, effect_size: float = 0.15) -> float:
    """
    Calculate statistical power using the non-central chi-squared distribution.
    
    This approximates the power of a chi-squared test (e.g., for a 2x2 contingency
    table or a single SNP association test with 1 degree of freedom) given:
    - n: Total sample size
    - alpha: Significance threshold (default 0.05)
    - effect_size: Cohen's w (effect size for chi-squared), default 0.15 (small)
    
    Args:
        n: Total sample size
        alpha: Significance level
        effect_size: Cohen's w effect size
        
    Returns:
        float: Calculated power (0.0 to 1.0)
    """
    df = 1  # Degrees of freedom for a single SNP test
    
    # Critical value for chi-squared distribution
    critical_value = stats.chi2.ppf(1 - alpha, df)
    
    # Non-centrality parameter (NCP)
    # For a chi-squared test, NCP = n * effect_size^2
    ncp = n * (effect_size ** 2)
    
    # Power is the probability of exceeding the critical value under the alternative
    # distribution (non-central chi-squared)
    power = 1 - stats.ncx2.cdf(critical_value, df, ncp)
    
    return power

def main():
    """
    Main entry point for power analysis.
    
    Reads sample count from data, checks minimum size, calculates power,
    and writes result to data/processed/power_analysis.txt.
    """
    # Determine input data path. 
    # Priority: 
    # 1. Command line argument
    # 2. data/processed/phenotypes_cleaned.fam (output of T016)
    # 3. data/interim/synthetic.fam (converted by T015)
    # 4. data/raw/ (try to find .fam or .csv)
    
    input_file = None
    
    # Check for CLI arg
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default paths based on pipeline flow
        candidate_paths = [
            "data/processed/phenotypes_cleaned.fam",
            "data/processed/phenotypes_cleaned.pheno",
            "data/interim/synthetic.fam",
            "data/raw/phenotypes.csv",
            "data/raw/phenotypes.tsv"
        ]
        
        for p in candidate_paths:
            if Path(p).exists():
                input_file = p
                break
    
    if not input_file:
        print("ERROR: No input data file found. Please provide a path as argument or ensure data is in the expected location.", file=sys.stderr)
        sys.exit(1)
    
    try:
        n = get_sample_count_from_data(input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: Failed to determine sample size: {e}", file=sys.stderr)
        sys.exit(1)
    
    # FR-012: Check sample size
    if n < 80:
        print(f"ERROR: Sample size (n={n}) is below the minimum threshold of 80.", file=sys.stderr)
        print(f"HALTING with error code: {ERR_SAMPLE_SIZE_INSUFFICIENT}", file=sys.stderr)
        sys.exit(1)
    
    # Calculate power
    power = calculate_power(n)
    
    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "power_analysis.txt"
    
    # Write result
    with open(output_file, 'w') as f:
        f.write(f"Power: {power:.2f}\n")
    
    print(f"Power analysis complete. Sample size: {n}, Power: {power:.2f}")
    print(f"Result written to: {output_file}")

if __name__ == "__main__":
    main()