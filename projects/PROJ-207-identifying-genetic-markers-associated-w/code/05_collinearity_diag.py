"""
Collinearity Diagnostics for GWAS Covariates (FR-010).

This script performs collinearity diagnostics on the phenotype and covariate data
prior to GWAS execution. It calculates Variance Inflation Factors (VIF) and a
correlation matrix to detect multicollinearity among covariates (geographic region,
sampling year, Varroa mite count).

Input:
    data/processed/phenotypes_cleaned.pheno (PLINK .pheno format)
    data/processed/phenotypes_cleaned.fam (PLINK .fam format for sample IDs)

Output:
    data/processed/collinearity_report.json (VIF scores, correlation matrix)
    data/processed/collinearity_report.txt (Human-readable summary)

Failure Condition:
    If any covariate has VIF > 10, the script exits with code 1 and logs the error.
"""

import os
import sys
import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure we can import from the project root if run as a module,
# but primarily designed to be run as a script.
# We rely on standard library and pandas/numpy.

def load_phenotype_data(pheno_path: str, fam_path: str) -> pd.DataFrame:
    """
    Loads PLINK .pheno and .fam files and merges them into a single DataFrame
    containing only the numeric covariates required for collinearity checks.

    Expected .pheno columns (based on T016/T062 output):
        - Family ID (FID)
        - Individual ID (IID)
        - Phenotype (CCD status)
        - Covariate_1 (e.g., Year)
        - Covariate_2 (e.g., Varroa_Count)
        - Covariate_3 (e.g., Region_Encoded)

    Expected .fam columns:
        - FID, IID, Paternal ID, Maternal ID, Sex, Phenotype
    """
    if not os.path.exists(pheno_path):
        raise FileNotFoundError(f"Input phenotype file not found: {pheno_path}")
    if not os.path.exists(fam_path):
        raise FileNotFoundError(f"Input family file not found: {fam_path}")

    # Load .pheno (space/tab delimited, no header in standard PLINK, but we add one)
    # PLINK .pheno usually has: FID IID PHENO [covariates...]
    pheno_df = pd.read_csv(pheno_path, delim_whitespace=True, header=None)
    
    # Load .fam to ensure we have the correct sample list (though .pheno should match)
    fam_df = pd.read_csv(fam_path, delim_whitespace=True, header=None)

    if pheno_df.shape[0] != fam_df.shape[0]:
        raise ValueError(f"Sample count mismatch between .pheno ({pheno_df.shape[0]}) and .fam ({fam_df.shape[0]})")

    # Define expected column names based on T016/T062 logic
    # Assuming the pipeline outputs: FID, IID, Phenotype, Year, Varroa_Count, Region_Code
    # If the .pheno file has a header, pandas might misinterpret it. 
    # Standard PLINK .pheno has no header.
    col_names = ['FID', 'IID', 'Phenotype']
    # We assume the remaining columns are covariates added by T016/T062
    # We need to identify which are numeric for VIF calculation.
    num_cols = pheno_df.shape[1]
    for i in range(3, num_cols):
        col_names.append(f'COV_{i}')

    pheno_df.columns = col_names

    # Filter for numeric columns only (excluding FID, IID which are strings)
    numeric_cols = []
    for col in pheno_df.columns:
        if col in ['FID', 'IID']:
            continue
        try:
            # Try to convert to numeric; if fails, it's a categorical string not encoded yet
            pd.to_numeric(pheno_df[col], errors='raise')
            numeric_cols.append(col)
        except (ValueError, TypeError):
            # Skip non-numeric columns (e.g., unencoded regions)
            continue

    if len(numeric_cols) < 2:
        raise ValueError("Insufficient numeric covariates found in phenotype file for collinearity analysis.")

    # Select only the numeric columns
    covariate_df = pheno_df[numeric_cols].copy()

    # Handle missing values (PLINK often uses -9 or NaN)
    # Replace common missing value codes with NaN
    covariate_df = covariate_df.replace([-9, -9.0], np.nan)
    
    # Drop rows with any missing values for VIF calculation
    covariate_df = covariate_df.dropna()

    if covariate_df.shape[0] < 10:
        raise ValueError("Insufficient samples remaining after dropping missing values for VIF calculation.")

    return covariate_df

def calculate_vif(df: pd.DataFrame) -> pd.Series:
    """
    Calculates Variance Inflation Factor (VIF) for each column in the DataFrame.
    
    VIF is calculated as 1 / (1 - R^2) where R^2 is from regressing the variable
    against all other variables in the set.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant

    # Add constant for intercept
    X = add_constant(df)
    
    vif_data = pd.Series()
    for i, col in enumerate(df.columns):
        # statsmodels VIF expects the full matrix including constant
        # but we calculate VIF for the specific column
        try:
            vif = variance_inflation_factor(X.values, i+1) # +1 because index 0 is constant
            vif_data[col] = vif
        except Exception as e:
            # Handle singular matrices if perfect collinearity exists
            vif_data[col] = np.inf
    
    return vif_data

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates the Pearson correlation matrix for the covariates."""
    return df.corr(method='pearson')

def run_collinearity_diagnostics(covariate_df: pd.DataFrame, output_dir: Path):
    """
    Runs the full diagnostics suite: VIF and Correlation Matrix.
    Writes results to JSON and a human-readable text file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    vif_results = calculate_vif(covariate_df)
    corr_matrix = calculate_correlation_matrix(covariate_df)

    # Check for high collinearity (Threshold: VIF > 10)
    high_vif_cols = vif_results[vif_results > 10.0]
    
    report_data = {
        "vif_scores": vif_results.to_dict(),
        "correlation_matrix": corr_matrix.round(4).to_dict(),
        "high_collinearity_detected": len(high_vif_cols) > 0,
        "problematic_variables": list(high_vif_cols.index),
        "max_vif": float(vif_results.max()),
        "sample_count": len(covariate_df)
    }

    # Write JSON report
    json_path = output_dir / "collinearity_report.json"
    with open(json_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    # Write Text Report
    txt_path = output_dir / "collinearity_report.txt"
    with open(txt_path, 'w') as f:
        f.write("=== Collinearity Diagnostics Report (FR-010) ===\n\n")
        f.write(f"Sample Count: {report_data['sample_count']}\n")
        f.write(f"Max VIF: {report_data['max_vif']:.4f}\n")
        f.write(f"High Collinearity Detected: {report_data['high_collinearity_detected']}\n\n")
        
        f.write("Variance Inflation Factors (VIF):\n")
        f.write("-" * 40 + "\n")
        for var, vif_val in vif_results.items():
            status = " [WARNING]" if vif_val > 10.0 else ""
            f.write(f"{var:20s}: {vif_val:10.4f}{status}\n")
        
        f.write("\nCorrelation Matrix:\n")
        f.write("-" * 40 + "\n")
        # Simple text representation of the matrix
        headers = "\t".join([f"{c[:8]}" for c in corr_matrix.columns])
        f.write(f"{'':10s}\t{headers}\n")
        for idx, row in corr_matrix.iterrows():
            row_str = "\t".join([f"{v:.2f}" for v in row.values])
            f.write(f"{idx[:10]:10s}\t{row_str}\n")

        if high_vif_cols.any():
            f.write("\n!!! ALERT: High Collinearity Detected !!!\n")
            f.write("The following variables have VIF > 10:\n")
            for var in high_vif_cols.index:
                f.write(f"  - {var} (VIF: {high_vif_cols[var]:.4f})\n")
            f.write("\nRecommendation: Remove or combine highly correlated covariates\n")
            f.write("before proceeding to GWAS regression to avoid unstable estimates.\n")

    return report_data

def main():
    parser = argparse.ArgumentParser(
        description="Perform collinearity diagnostics on GWAS covariates (FR-010)."
    )
    parser.add_argument(
        "--input-pheno",
        type=str,
        required=True,
        help="Path to the cleaned phenotype file (PLINK .pheno format). "
             "Default: data/processed/phenotypes_cleaned.pheno"
    )
    parser.add_argument(
        "--input-fam",
        type=str,
        required=False,
        help="Path to the family file (PLINK .fam format). "
             "Default: data/processed/phenotypes_cleaned.fam"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write reports. Default: data/processed"
    )

    args = parser.parse_args()

    # Default paths if not provided
    pheno_path = args.input_pheno
    if args.input_fam:
        fam_path = args.input_fam
    else:
        # Infer .fam path from .pheno path
        fam_path = pheno_path.replace('.pheno', '.fam')

    output_dir = Path(args.output_dir)

    try:
        # 1. Load Data
        # The execution error log indicated: "Error: Input file not found: data/processed/phenotypes_cleaned.pheno"
        # We ensure we look there if no arg provided, but the arg is required here.
        # If the run-book didn't pass it, the argparse will fail (rc=2), 
        # but the task is to implement the script logic correctly.
        # We assume the run-book will be fixed to pass the correct input.
        
        covariate_df = load_phenotype_data(pheno_path, fam_path)

        # 2. Run Diagnostics
        report = run_collinearity_diagnostics(covariate_df, output_dir)

        # 3. Exit with error if high collinearity found (FR-010 Gate)
        if report['high_collinearity_detected']:
            print(f"CRITICAL: Collinearity detected. Max VIF = {report['max_vif']:.4f} (>10.0)")
            print(f"Details written to {output_dir}/collinearity_report.txt")
            sys.exit(1)
        
        print("Collinearity diagnostics passed. No high VIF detected.")
        print(f"Report written to {output_dir}/collinearity_report.txt")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Ensure the phenotype file exists. If running from quickstart, ensure T016/T062 completed successfully.")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Data validation failed - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during diagnostics - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()