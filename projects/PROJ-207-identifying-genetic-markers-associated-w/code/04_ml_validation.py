import os
import sys
import argparse
import warnings
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Ensure utils is in path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

# --------------------------------------------------------------------------
# Data Loading Helpers
# --------------------------------------------------------------------------

def load_gwas_results(gwas_path: str) -> pd.DataFrame:
    """Load GWAS results TSV."""
    path = Path(gwas_path)
    if not path.exists():
        raise FileNotFoundError(f"GWAS results file not found: {gwas_path}")
    # Handle potential header issues
    df = pd.read_csv(path, sep='\t')
    return df

def load_phenotypes(pheno_path: str) -> pd.DataFrame:
    """Load phenotype data (FAM/PHENO format combined)."""
    path = Path(pheno_path)
    if not path.exists():
        raise FileNotFoundError(f"Phenotype file not found: {pheno_path}")
    
    # Try to read as space-separated, handling potential headers
    try:
        df = pd.read_csv(path, sep='\s+', header=None)
        # FAM format: FID IID PAT MAT SEX PHENO
        # We assume columns 0,1 are IDs, 5 is phenotype (index 5)
        # If there are more columns (covariates), they follow
        if df.shape[1] >= 6:
            df.columns = ['FID', 'IID', 'PAT', 'MAT', 'SEX', 'PHENO'] + [f'COV_{i}' for i in range(df.shape[1]-6)]
        else:
            raise ValueError("Phenotype file must have at least 6 columns (FAM format + phenotype)")
    except Exception as e:
        # Fallback for labeled files
        df = pd.read_csv(path, sep='\s+')
        if 'PHENO' not in df.columns:
            raise ValueError("Phenotype file must contain a 'PHENO' column or be in FAM format")
    return df

def load_genotype_plink_prefix(geno_prefix: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load genotype matrix and phenotype vector from PLINK binary files.
    Returns (genotypes, phenotypes) where genotypes is (n_samples, n_snps).
    Note: This is a simplified loader assuming .bed/.bim/.fam exist.
    In a real pipeline, we'd use pandas-plink or pybedtools.
    For this task, we simulate loading from the processed files.
    """
    bed_path = Path(f"{geno_prefix}.bed")
    fam_path = Path(f"{geno_prefix}.fam")
    
    if not bed_path.exists() or not fam_path.exists():
        # Fallback: Try to derive from GWAS results if available
        # This is a hack for the synthetic pipeline where we might not have raw bed files
        raise FileNotFoundError(f"PLINK binary files not found: {geno_prefix}.bed, {geno_prefix}.fam")
    
    # Placeholder for actual PLINK loading logic
    # In a real scenario, we would parse .bed files
    # For now, we assume we can load from a processed matrix if available
    # or raise an error if strictly required
    raise NotImplementedError("Direct .bed parsing not implemented. Use PLINK to export to .txt for this demo.")

# --------------------------------------------------------------------------
# ML Validation Logic (LASSO, PRS, Likelihood Ratio, Permutation)
# --------------------------------------------------------------------------

def run_lasso_cv(X: np.ndarray, y: np.ndarray, cv: int = 5) -> Tuple[float, Any]:
    """Run LASSO logistic regression with k-fold cross-validation."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    model = LogisticRegression(penalty='l1', solver='liblinear', random_state=42)
    
    scores = cross_val_score(model, X_scaled, y, cv=skf, scoring='roc_auc')
    auc = np.mean(scores)
    
    # Fit final model on full data
    model.fit(X_scaled, y)
    return auc, model

def calculate_prs(gwas_df: pd.DataFrame, geno_matrix: np.ndarray, snp_map: List[str]) -> np.ndarray:
    """
    Calculate Polygenic Risk Score.
    Sum of (beta * genotype) for significant SNPs.
    """
    # Filter significant SNPs (e.g., p < 0.05 before FDR for PRS construction, or use FDR q < 0.05)
    # Here we use a threshold from the GWAS results
    sig_snps = gwas_df[gwas_df['P'] < 0.05]
    
    # Map SNPs to columns in geno_matrix
    # This assumes snp_map aligns with geno_matrix columns
    indices = []
    betas = []
    
    for _, row in sig_snps.iterrows():
        snp_id = row['SNP']
        if snp_id in snp_map:
            idx = snp_map.index(snp_id)
            indices.append(idx)
            betas.append(row['BETA'])
    
    if not indices:
        return np.zeros(geno_matrix.shape[0])
    
    prs = np.dot(geno_matrix[:, indices], betas)
    return prs

def likelihood_ratio_test(full_model, reduced_model, df_diff: int) -> float:
    """Perform likelihood ratio test."""
    # Extract log-likelihoods
    ll_full = full_model.llf
    ll_reduced = reduced_model.llf
    
    lr_stat = -2 * (ll_reduced - ll_full)
    p_val = 1 - stats.chi2.cdf(lr_stat, df_diff)
    return p_val

def permutation_test(y: np.ndarray, X: np.ndarray, model_func, n_perm: int = 1000, seed: int = 42) -> np.ndarray:
    """Generate null distribution via phenotype permutation."""
    np.random.seed(seed)
    null_aucs = []
    
    for _ in range(n_perm):
        y_perm = np.random.permutation(y)
        auc, _ = model_func(X, y_perm)
        null_aucs.append(auc)
    
    return np.array(null_aucs)

def check_auc_threshold(observed_auc: float, null_dist: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """Compare AUC against null distribution."""
    threshold = np.quantile(null_dist, 1 - alpha)
    is_significant = observed_auc > threshold
    
    return {
        "observed_auc": observed_auc,
        "null_threshold": threshold,
        "is_significant": is_significant,
        "p_value": (null_dist >= observed_auc).mean()
    }

# --------------------------------------------------------------------------
# T031: Collinearity Diagnostics (VIF)
# --------------------------------------------------------------------------

def calculate_vif_series(df: pd.DataFrame, exclude_cols: List[str] = None) -> pd.Series:
    """
    Calculate Variance Inflation Factor for numeric columns in a DataFrame.
    """
    if exclude_cols is None:
        exclude_cols = []
    
    # Select numeric columns excluding specified ones
    cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    if len(cols) < 2:
        return pd.Series(dtype=float)
    
    X = df[cols].values
    # Add constant for intercept
    X_with_const = np.column_stack([np.ones(X.shape[0]), X])
    
    vif_data = []
    for i, col in enumerate(cols):
        try:
            # VIF for feature i is 1 / (1 - R^2_i)
            # R^2_i is from regressing feature i on all other features
            vif = variance_inflation_factor(X_with_const, i+1) # +1 because of intercept column
            vif_data.append((col, vif))
        except LinAlgError:
            vif_data.append((col, np.nan))
    
    return pd.Series([v for _, v in vif_data], index=cols)

def write_collinearity_report(vif_series: pd.Series, correlation_matrix: pd.DataFrame, output_path: str):
    """
    Write collinearity diagnostics to TSV.
    Includes VIF values and flags r² > 0.8 pairs.
    """
    report_rows = []
    
    # 1. VIF Section
    report_rows.append("# VARIANCE INFLATION FACTOR (VIF) ANALYSIS")
    report_rows.append("# Description: VIF > 5 indicates high multicollinearity.")
    report_rows.append("feature\tvif\tstatus")
    
    for feature, vif_val in vif_series.items():
        status = "OK"
        if not np.isnan(vif_val):
            if vif_val > 5:
                status = "HIGH_VIF"
            elif vif_val > 2.5:
                status = "MODERATE_VIF"
        report_rows.append(f"{feature}\t{vif_val:.4f}\t{status}")
    
    report_rows.append("")
    report_rows.append("# CORRELATION MATRIX (r² > 0.8 FLAGGED)")
    report_rows.append("# Description: Joint relationships between covariates.")
    report_rows.append("feature_1\tfeature_2\tr_squared\tstatus")
    
    # Check pairwise correlations
    flagged_pairs = []
    for i, col1 in enumerate(correlation_matrix.columns):
        for j, col2 in enumerate(correlation_matrix.columns):
            if i < j:
                r = correlation_matrix.loc[col1, col2]
                r_sq = r ** 2
                status = "OK"
                if r_sq > 0.8:
                    status = "HIGH_CORR"
                    flagged_pairs.append((col1, col2, r_sq, status))
                report_rows.append(f"{col1}\t{col2}\t{r_sq:.4f}\t{status}")
    
    # Write to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_rows))
    
    return flagged_pairs

def run_collinearity_diagnostics(pheno_df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Main entry for T031: Run VIF and correlation analysis on covariates.
    Mandatory: Document findings descriptively.
    """
    # Select covariates: Geographic region (encoded), Sampling year, Varroa load
    # Assume columns are named or encoded as numeric for VIF calculation
    # If categorical, we assume they are already one-hot encoded or ordinal in the input
    numeric_cols = pheno_df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude ID columns and phenotype
    covariate_cols = [c for c in numeric_cols if c not in ['PHENO', 'FID', 'IID', 'PAT', 'MAT', 'SEX']]
    
    if len(covariate_cols) < 2:
        # Not enough covariates for VIF
        with open(output_path, 'w') as f:
            f.write("# Insufficient covariates for VIF calculation.\n")
        return {"vif": {}, "high_corr_pairs": []}
    
    # Calculate VIF
    vif_series = calculate_vif_series(pheno_df[covariate_cols])
    
    # Calculate Correlation Matrix
    corr_matrix = pheno_df[covariate_cols].corr()
    
    # Write Report
    flagged_pairs = write_collinearity_report(vif_series, corr_matrix, output_path)
    
    # Descriptive Summary
    summary = {
        "vif": vif_series.to_dict(),
        "high_corr_pairs": [{"f1": p[0], "f2": p[1], "r2": p[2]} for p in flagged_pairs],
        "interpretation": "Joint relationships identified where r² > 0.8. These covariates should be treated as a group rather than independent effects in the model."
    }
    
    return summary

# --------------------------------------------------------------------------
# Main Entry Point
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ML Validation and Collinearity Diagnostics")
    parser.add_argument("--gwas", required=True, help="Path to GWAS results TSV")
    parser.add_argument("--pheno", required=True, help="Path to phenotype file")
    parser.add_argument("--geno", required=True, help="Prefix for PLINK genotype files")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    print("Loading GWAS results...")
    gwas_df = load_gwas_results(args.gwas)
    
    print("Loading phenotypes...")
    pheno_df = load_phenotypes(args.pheno)
    
    # 2. T031: Collinearity Diagnostics
    print("Running collinearity diagnostics (T031)...")
    collinearity_report_path = output_dir / "collinearity_report.tsv"
    collinearity_results = run_collinearity_diagnostics(pheno_df, str(collinearity_report_path))
    print(f"Collinearity report written to {collinearity_report_path}")
    
    # Print summary
    high_vif = [k for k, v in collinearity_results['vif'].items() if v > 5]
    if high_vif:
        print(f"WARNING: High VIF detected for: {high_vif}")
    
    high_corr = collinearity_results['high_corr_pairs']
    if high_corr:
        print(f"WARNING: High correlation (r² > 0.8) detected between: {high_corr}")
    
    # 3. Placeholder for other T027-T030 logic (LASSO, PRS, etc.)
    # Since we cannot run full ML without real .bed files, we stop here for T031
    # ensuring the collinearity report is written.
    
    print("T031 Collinearity Diagnostics Complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())