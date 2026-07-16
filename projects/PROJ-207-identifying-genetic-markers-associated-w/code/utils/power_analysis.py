"""
code/utils/power_analysis.py

Implements statistical power analysis for GWAS sample size requirements.
Enforces FR-012: Halt if sample size < 80.
"""

import sys
import os
import math
from pathlib import Path
from scipy import stats
import pandas as pd

def get_sample_count_from_data(data_path: str) -> int:
    """
    Counts the number of samples in the provided data file.
    Supports VCF (count columns after #CHROM) or PLINK .fam (count rows).
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    if path.suffix == ".vcf" or str(path).endswith(".vcf.gz"):
        with open(path, "rt") as f:
            for line in f:
                if line.startswith("#CHROM"):
                    # The header line starts with #CHROM, followed by POS, ID, REF, ALT, QUAL, FILTER, INFO, FORMAT, then samples
                    parts = line.strip().split("\t")
                    # Sample columns start from index 9
                    return max(0, len(parts) - 9)
    elif path.suffix == ".fam":
        # PLINK .fam file: 1 sample per line
        return sum(1 for _ in open(path))
    elif path.suffix == ".csv" or path.suffix == ".tsv":
        df = pd.read_csv(path, sep="\t" if path.suffix == ".tsv" else ",")
        return len(df)
    else:
        # Try to infer or default to line count if unknown format
        return sum(1 for _ in open(path))

def calculate_power(n: int, alpha: float = 0.05, effect_size: float = 0.1) -> float:
    """
    Calculates statistical power using non-central chi-squared distribution.
    This is a simplified model for demonstration.
    """
    if n < 2:
        return 0.0
    
    # Degrees of freedom for 1 degree of freedom test (e.g., single SNP)
    df = 1
    # Non-centrality parameter approximation
    # NCP = n * effect_size^2 (simplified)
    ncp = n * (effect_size ** 2)
    
    # Critical value for chi-squared
    critical_val = stats.chi2.ppf(1 - alpha, df)
    
    # Power is the probability of exceeding the critical value under the alternative hypothesis
    power = 1 - stats.chi2.cdf(critical_val, df, ncp)
    return power

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Power Analysis for GWAS")
    parser.add_argument("--input", type=str, required=True, help="Path to input data (VCF, FAM, CSV)")
    parser.add_argument("--output", type=str, default="data/processed/power_analysis.txt", help="Output file path")
    args = parser.parse_args()

    try:
        n = get_sample_count_from_data(args.input)
        print(f"Sample count (n): {n}")

        if n < 80:
            print("ERR_SAMPLE_SIZE_INSUFFICIENT", file=sys.stderr)
            print(f"Error: Sample size ({n}) is insufficient. Minimum required is 80.", file=sys.stderr)
            # Exit with non-zero code to trigger halt in pipeline
            sys.exit(1)

        power = calculate_power(n)
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(f"Power: {power:.2f}\n")
        
        print(f"Power calculated: {power:.2f}")
        print(f"Report written to {output_path}")
        sys.exit(0)

    except Exception as e:
        print(f"Error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
