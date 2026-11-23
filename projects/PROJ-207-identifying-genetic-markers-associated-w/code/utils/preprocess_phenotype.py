"""
Preprocess phenotype data for GWAS analysis.

This module handles:
1. LD pruning of genotype data (r² < 0.2)
2. Covariate encoding (geographic region, sampling year, Varroa mite count)
3. Generation of cleaned .fam and .pheno files for PLINK

Dependencies:
- PLINK must be installed and available in PATH
- Input genotype data must be in PLINK binary format (bed/bim/fam)
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess
from typing import Tuple, Optional

class CovariateCollinearityError(Exception):
    """Raised when covariates exhibit high collinearity (VIF >= 5)."""
    pass


def calculate_vif(df: pd.DataFrame, exclude: list = None) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each column.

    Args:
        df: DataFrame with numeric columns
        exclude: List of column names to exclude from calculation

    Returns:
        Series with VIF values for each column
    """
    if exclude is None:
        exclude = []

    from statsmodels.stats.outliers_influence import variance_inflation_factor

    # Select numeric columns excluding specified ones
    cols = [c for c in df.columns if c not in exclude and df[c].dtype in [np.float64, np.int64, np.float32, np.int32]]

    if len(cols) < 2:
        return pd.Series(index=[], dtype=float)

    X = df[cols].values

    # Add constant for intercept
    X_const = np.column_stack([np.ones(X.shape[0]), X])

    vif_data = []
    for i in range(len(cols)):
        try:
            vif = variance_inflation_factor(X_const, i + 1)
            vif_data.append((cols[i], vif))
        except Exception:
            vif_data.append((cols[i], np.nan))

    return pd.Series([v for _, v in vif_data], index=[c for c, _ in vif_data])


def ld_pruning_r2(
    plink_prefix: str,
    out_prefix: str,
    window_size: int = 50,
    step_size: int = 5,
    r2_threshold: float = 0.2
) -> Tuple[str, str]:
    """
    Perform LD pruning on genotype data using PLINK.

    Args:
        plink_prefix: Path prefix for PLINK binary files (bed/bim/fam)
        out_prefix: Output prefix for pruned SNP list
        window_size: Window size in SNPs for LD calculation
        step_size: Step size in SNPs for sliding window
        r2_threshold: R² threshold for pruning (default 0.2)

    Returns:
        Tuple of (pruned_snp_list_path, pruned_genotype_prefix)
    """
    plink_cmd = [
        'plink',
        '--bfile', plink_prefix,
        '--indep-pairwise', str(window_size), str(step_size), str(r2_threshold),
        '--out', out_prefix
    ]

    try:
        result = subprocess.run(
            plink_cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"PLINK LD pruning failed: {e.stderr}")
        raise

    # PLINK outputs two files: .prune.in and .prune.out
    prune_in_path = f"{out_prefix}.prune.in"
    prune_out_path = f"{out_prefix}.prune.out"

    if not os.path.exists(prune_in_path):
        raise FileNotFoundError(f"PLINK did not produce expected output: {prune_in_path}")

    # Extract pruned SNPs
    with open(prune_in_path, 'r') as f:
        pruned_snps = [line.strip() for line in f if line.strip()]

    print(f"LD pruning complete: {len(pruned_snps)} SNPs retained out of initial set")

    return prune_in_path, f"{out_prefix}_pruned"


def encode_covariates(
    phenotype_df: pd.DataFrame,
    covariate_columns: list,
    output_dir: str
) -> pd.DataFrame:
    """
    Encode covariates for PLINK analysis.

    Args:
        phenotype_df: DataFrame with raw phenotype and covariate data
        covariate_columns: List of covariate column names to encode
        output_dir: Directory to write encoded files

    Returns:
        DataFrame with encoded covariates
    """
    df = phenotype_df.copy()

    # Ensure required columns exist
    missing_cols = [c for c in covariate_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required covariate columns: {missing_cols}")

    # Handle Varroa mite count (numeric)
    if 'Varroa_mite_count' in df.columns:
        # Replace NaN with median or 0 if all NaN
        if df['Varroa_mite_count'].isna().all():
            df['Varroa_mite_count'] = 0
            print("Warning: Varroa_mite_count was all NaN, replaced with 0")
        else:
            df['Varroa_mite_count'] = df['Varroa_mite_count'].fillna(df['Varroa_mite_count'].median())

    # Handle sampling year (numeric)
    if 'sampling_year' in df.columns:
        if df['sampling_year'].isna().all():
            df['sampling_year'] = 2020  # Default year
            print("Warning: sampling_year was all NaN, replaced with 2020")
        else:
            df['sampling_year'] = df['sampling_year'].fillna(df['sampling_year'].median())

    # Handle geographic region (categorical -> numeric encoding)
    if 'geographic_region' in df.columns:
        if df['geographic_region'].isna().all():
            df['geographic_region'] = 'Unknown'
            print("Warning: geographic_region was all NaN, replaced with 'Unknown'")
        else:
            df['geographic_region'] = df['geographic_region'].fillna('Unknown')

        # Create dummy variables for categorical encoding
        region_dummies = pd.get_dummies(df['geographic_region'], prefix='region')
        df = pd.concat([df.drop('geographic_region', axis=1), region_dummies], axis=1)

    # Write .pheno file (PLINK format: FID IID PHENO [COVARIATES...])
    pheno_path = os.path.join(output_dir, 'phenotypes_cleaned.pheno')

    # PLINK .pheno format requires: FID, IID, PHENO (1=control, 2=case, -9=missing)
    # We assume 'CCD_diagnosis' is the phenotype column (1=control, 2=case)
    if 'CCD_diagnosis' in df.columns:
        pheno_col = 'CCD_diagnosis'
    elif 'case_control' in df.columns:
        pheno_col = 'case_control'
    else:
        # Default to first numeric column if not found
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            pheno_col = numeric_cols[0]
            print(f"Warning: No standard phenotype column found, using {pheno_col}")
        else:
            raise ValueError("No phenotype column found in data")

    # Prepare output dataframe
    output_df = pd.DataFrame()
    if 'FID' in df.columns and 'IID' in df.columns:
        output_df['FID'] = df['FID']
        output_df['IID'] = df['IID']
    else:
        # Create default FID/IID from index
        output_df['FID'] = df.index
        output_df['IID'] = df.index

    output_df['PHENO'] = df[pheno_col].apply(lambda x: 2 if x == 1 else (1 if x == 0 else -9))

    # Add covariates (numeric only)
    for col in df.columns:
        if col not in ['FID', 'IID', pheno_col, 'CCD_diagnosis', 'case_control']:
            if df[col].dtype in [np.float64, np.int64, np.float32, np.int32]:
                output_df[col] = df[col].fillna(-9)  # PLINK missing value

    # Write .pheno file
    output_df.to_csv(pheno_path, sep='\t', index=False)
    print(f"Wrote phenotype file: {pheno_path}")

    # Write .fam file (PLINK format: FID IID PAT MAT SEX PHENO)
    fam_path = os.path.join(output_dir, 'phenotypes_cleaned.fam')

    fam_df = pd.DataFrame()
    fam_df['FID'] = output_df['FID']
    fam_df['IID'] = output_df['IID']
    fam_df['PAT'] = 0  # No paternal ID
    fam_df['MAT'] = 0  # No maternal ID
    fam_df['SEX'] = 0  # Unknown sex
    fam_df['PHENO'] = output_df['PHENO']

    fam_df.to_csv(fam_path, sep='\t', index=False)
    print(f"Wrote family file: {fam_path}")

    return output_df


def main():
    """Main entry point for phenotype preprocessing."""
    parser = argparse.ArgumentParser(
        description='Preprocess phenotype data for GWAS analysis'
    )
    parser.add_argument(
        '--geno',
        type=str,
        required=True,
        help='Path prefix for PLINK binary genotype files (bed/bim/fam)'
    )
    parser.add_argument(
        '--pheno',
        type=str,
        required=True,
        help='Path to phenotype data file (CSV or TSV)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed',
        help='Output directory for cleaned files'
    )
    parser.add_argument(
        '--covariates',
        type=str,
        nargs='+',
        default=['geographic_region', 'sampling_year', 'Varroa_mite_count'],
        help='Covariate columns to encode'
    )
    parser.add_argument(
        '--ld-window',
        type=int,
        default=50,
        help='LD pruning window size in SNPs'
    )
    parser.add_argument(
        '--ld-step',
        type=int,
        default=5,
        help='LD pruning step size in SNPs'
    )
    parser.add_argument(
        '--ld-r2',
        type=float,
        default=0.2,
        help='LD pruning R² threshold'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load phenotype data
    print(f"Loading phenotype data from: {args.pheno}")
    try:
        if args.pheno.endswith('.csv'):
            phenotype_df = pd.read_csv(args.pheno)
        elif args.pheno.endswith('.tsv'):
            phenotype_df = pd.read_csv(args.pheno, sep='\t')
        else:
            # Try both
            try:
                phenotype_df = pd.read_csv(args.pheno)
            except:
                phenotype_df = pd.read_csv(args.pheno, sep='\t')
    except Exception as e:
        print(f"Error loading phenotype file: {e}")
        sys.exit(1)

    print(f"Loaded {len(phenotype_df)} samples")

    # Perform LD pruning on genotype data
    print(f"Performing LD pruning on genotype data: {args.geno}")
    try:
        prune_list_path, pruned_geno_prefix = ld_pruning_r2(
            plink_prefix=args.geno,
            out_prefix=str(output_dir / 'ld_pruned'),
            window_size=args.ld_window,
            step_size=args.ld_step,
            r2_threshold=args.ld_r2
        )
        print(f"LD pruning complete. Pruned SNP list: {prune_list_path}")
    except Exception as e:
        print(f"Error during LD pruning: {e}")
        sys.exit(1)

    # Extract pruned SNPs
    with open(prune_list_path, 'r') as f:
        pruned_snps = [line.strip() for line in f if line.strip()]

    # Create pruned genotype files
    pruned_cmd = [
        'plink',
        '--bfile', args.geno,
        '--extract', prune_list_path,
        '--make-bed',
        '--out', str(output_dir / 'pruned_genotypes')
    ]

    try:
        result = subprocess.run(
            pruned_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Created pruned genotype files: {output_dir / 'pruned_genotypes'}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating pruned genotype files: {e.stderr}")
        sys.exit(1)

    # Encode covariates and write output files
    print("Encoding covariates and writing output files...")
    try:
        encoded_df = encode_covariates(
            phenotype_df=phenotype_df,
            covariate_columns=args.covariates,
            output_dir=str(output_dir)
        )
    except Exception as e:
        print(f"Error encoding covariates: {e}")
        sys.exit(1)

    # Verify outputs
    fam_path = output_dir / 'phenotypes_cleaned.fam'
    pheno_path = output_dir / 'phenotypes_cleaned.pheno'

    if not fam_path.exists():
        print(f"Error: Family file not created: {fam_path}")
        sys.exit(1)

    if not pheno_path.exists():
        print(f"Error: Phenotype file not created: {pheno_path}")
        sys.exit(1)

    # Verify required columns in .pheno file
    pheno_df = pd.read_csv(pheno_path, sep='\t')
    expected_cols = ['FID', 'IID', 'PHENO']
    missing = [c for c in expected_cols if c not in pheno_df.columns]
    if missing:
        print(f"Error: Missing required columns in .pheno file: {missing}")
        sys.exit(1)

    print(f"\nPreprocessing complete!")
    print(f"  - Pruned genotype files: {output_dir / 'pruned_genotypes'}")
    print(f"  - Family file: {fam_path}")
    print(f"  - Phenotype file: {pheno_path}")
    print(f"  - Samples processed: {len(encoded_df)}")
    print(f"  - SNPs retained after LD pruning: {len(pruned_snps)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())