"""
code/utils/power_analysis.py

Implements statistical power analysis for GWAS sample size requirements.
Enforces FR-012: Halt if sample size < 80.

This script calculates power using the non-central chi-squared distribution.
It accepts an input data file (VCF or PLINK .fam) to determine the sample count (n).
If n < 80, it exits with error code 1 and message ERR_SAMPLE_SIZE_INSUFFICIENT.
If n >= 80, it calculates power and writes a report to data/processed/power_analysis_report.json
and a summary to data/processed/power_analysis.txt.
"""

import sys
import os
import json
import math
from pathlib import Path
from scipy import stats
import pandas as pd

def get_sample_count_from_data(data_path: str) -> int:
    """
    Counts the number of samples in the provided data file.
    Supports VCF (count columns after #CHROM) or PLINK .fam (count rows).
    
    Args:
        data_path: Path to the input data file (VCF, FAM, or CSV/TSV).
        
    Returns:
        int: Number of samples detected.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or malformed.
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
                    # Sample columns start from index 9 (0-based: 0=#CHROM, 1=POS, 2=ID, 3=REF, 4=ALT, 5=QUAL, 6=FILTER, 7=INFO, 8=FORMAT)
                    # So samples are from index 9 onwards.
                    sample_count = max(0, len(parts) - 9)
                    if sample_count == 0:
                        raise ValueError(f"VCF file {data_path} has no sample columns detected.")
                    return sample_count
        raise ValueError(f"VCF file {data_path} is missing the #CHROM header line.")
    elif path.suffix == ".fam":
        # PLINK .fam file: 1 sample per line
        count = sum(1 for _ in open(path))
        if count == 0:
            raise ValueError(f"PLINK .fam file {data_path} is empty.")
        return count
    elif path.suffix == ".csv" or path.suffix == ".tsv":
        df = pd.read_csv(path, sep="\t" if path.suffix == ".tsv" else ",")
        if df.empty:
            raise ValueError(f"CSV/TSV file {data_path} is empty.")
        return len(df)
    else:
        # Try to infer or default to line count if unknown format
        # This is a fallback and might be inaccurate for binary formats, etc.
        try:
            count = sum(1 for _ in open(path))
            if count == 0:
                raise ValueError(f"Unknown format file {data_path} is empty.")
            return count
        except Exception as e:
            raise ValueError(f"Could not determine sample count from file {data_path}: {e}")

def calculate_power(n: int, alpha: float = 0.05, effect_size: float = 2.5) -> float:
    """
    Calculates statistical power using non-central chi-squared distribution.
    
    Parameters:
        n (int): Sample size.
        alpha (float): Significance level (default 0.05).
        effect_size (float): Expected effect size (Odds Ratio >= 2.5 as per task spec).
                             This is used to approximate the non-centrality parameter.
                             
    Returns:
        float: Calculated power value (0.0 to 1.0).
    """
    if n < 2:
        return 0.0
    
    # Degrees of freedom for 1 degree of freedom test (e.g., single SNP logistic regression)
    df = 1
    
    # Non-centrality parameter (NCP) approximation.
    # For a logistic regression GWAS, NCP is roughly n * (log(OR))^2 * p * (1-p) * variance_explained.
    # Using a simplified model: NCP = n * (effect_size / 10)^2 as a proxy for the task's "OR >= 2.5" requirement.
    # A more standard approximation for a 2-sample proportion test (simplified for binary phenotype)
    # is NCP = n * (delta^2) / (p*(1-p)).
    # Here we use a heuristic that scales with n and the square of the log(OR) to reflect the "OR >= 2.5" constraint.
    # log(2.5) ≈ 0.916. We'll use a simplified scaling: ncp = n * (log(effect_size))^2 * 0.1
    # This is a conservative estimate for demonstration purposes.
    log_or = math.log(effect_size)
    ncp = n * (log_or ** 2) * 0.1
    
    if ncp <= 0:
        return 0.0
    
    # Critical value for chi-squared distribution with df=1 at significance level alpha
    critical_val = stats.chi2.ppf(1 - alpha, df)
    
    # Power is the probability that the non-central chi-squared variable exceeds the critical value
    # under the alternative hypothesis (with the calculated NCP).
    power = 1 - stats.chi2.cdf(critical_val, df, ncp)
    
    return power

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Power Analysis for GWAS (FR-012)")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to input data file (VCF, PLINK .fam, or CSV/TSV) to determine sample count.")
    parser.add_argument("--output-dir", type=str, default="data/processed", 
                        help="Directory for output files (default: data/processed).")
    parser.add_argument("--alpha", type=float, default=0.05, 
                        help="Significance level (default: 0.05).")
    parser.add_argument("--effect-size", type=float, default=2.5, 
                        help="Expected effect size (Odds Ratio) for power calculation (default: 2.5).")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = output_dir / "power_analysis_report.json"
    summary_path = output_dir / "power_analysis.txt"

    try:
        n = get_sample_count_from_data(args.input)
        print(f"Sample count (n) detected from {args.input}: {n}")

        # FR-012: HALT ONLY IF n < 80
        if n < 80:
            error_msg = f"ERR_SAMPLE_SIZE_INSUFFICIENT: Sample size ({n}) is below the minimum threshold of 80."
            print(error_msg, file=sys.stderr)
            # Write a minimal failure report if needed, but primarily exit with error code
            # to ensure the pipeline halts.
            sys.exit(1)

        # Calculate power
        power_value = calculate_power(n, alpha=args.alpha, effect_size=args.effect_size)
        
        # Prepare report data
        report_data = {
            "n_samples": n,
            "power_value": round(power_value, 4),
            "alpha": args.alpha,
            "effect_size": args.effect_size,
            "status": "PASS",
            "message": f"Power analysis passed for n={n}. Calculated power: {power_value:.4f}."
        }

        # Write structured JSON report
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        # Write summary text file
        with open(summary_path, "w") as f:
            f.write(f"Power Analysis Report\n")
            f.write(f"=====================\n")
            f.write(f"Sample Size (n): {n}\n")
            f.write(f"Calculated Power: {power_value:.4f}\n")
            f.write(f"Alpha: {args.alpha}\n")
            f.write(f"Effect Size (OR): {args.effect_size}\n")
            f.write(f"Status: PASS\n")

        print(f"Power calculated: {power_value:.4f}")
        print(f"Status: PASS (n={n} >= 80)")
        print(f"Structured report written to: {report_path}")
        print(f"Summary written to: {summary_path}")
        
        # Verification step: ensure files exist
        if not report_path.exists() or not summary_path.exists():
            raise FileNotFoundError("Failed to write output files despite successful calculation.")

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"File Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Value Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()