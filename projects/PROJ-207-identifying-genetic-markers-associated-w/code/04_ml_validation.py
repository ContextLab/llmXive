"""
Machine Learning Validation and Polygenic Risk Scoring for Honeybee CCD.

This module implements:
1. LASSO logistic regression with k-fold cross-validation (FR-006).
2. Polygenic Risk Score (PRS) calculation (FR-007).
3. Likelihood-ratio test for PRS improvement (FR-007).
4. AUC threshold logic with permutation testing (FR-006).
5. Collinearity diagnostics (VIF) for covariates (FR-010, US-3 AC4).
"""

import os
import sys
import argparse
import warnings
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score
from scipy import stats
import statsmodels.api as sm

# Set seed for reproducibility
def set_seed(seed=42):
    np.random.seed(seed)

def load_gwas_results(gwas_path):
    """Load GWAS results from TSV file."""
    if not os.path.exists(gwas_path):
        raise FileNotFoundError(f"GWAS results file not found: {gwas_path}")
    return pd.read_csv(gwas_path, sep='\t')

def load_phenotypes(pheno_path):
    """Load phenotype data from FAM/PHENO files."""
    # Assuming the phenotype file contains the necessary covariates and target
    # The .fam file structure is: Family ID, Individual ID, Paternal ID, Maternal ID, Sex, Phenotype
    # We expect a combined file or a specific format from T016
    df = pd.read_csv(pheno_path, sep='\s+', header=None)
    # Rename columns for clarity based on T016 output expectation
    # T016 produces phenotypes_cleaned.fam and phenotypes_cleaned.pheno
    # We assume the input here is the .pheno file or a combined file
    # For robustness, we check if the file has headers or not
    if df.shape[1] == 6:
        df.columns = ['FID', 'IID', 'PAT', 'MAT', 'SEX', 'PHENO']
    else:
        # Try to load as a generic table with headers if 6 cols doesn't match
        df = pd.read_csv(pheno_path, sep='\s+')
    return df

def load_genotype_plink_prefix(geno_prefix):
    """
    Load genotype data from PLINK binary files (.bed, .bim, .fam).
    For simplicity in this context, we assume the .fam file is the phenotype source
    and the .bim file provides the SNP list. The actual matrix loading is handled
    via PLINK or a library if available. Here we simulate the load for the ML part
    by assuming the PRS is pre-calculated or we use the GWAS betas.
    """
    # In a real scenario, we would load the .bed file using pandas-plink or similar.
    # For this task, we assume the PRS is calculated from the GWAS results and phenotype.
    return geno_prefix

def run_lasso_cv(geno_matrix, y, cv=5):
    """
    Run LASSO logistic regression with k-fold cross-validation.
    Returns the best model and the cross-validated AUC.
    """
    # Add intercept
    X = sm.add_constant(geno_matrix)
    
    # Split data
    kf = KFold(n_splits=cv, shuffle=True, random_state=42)
    auc_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # LASSO Logistic Regression
        # Using sklearn's LogisticRegressionCV with l1 penalty
        # solver='liblinear' supports l1 penalty
        model = LogisticRegressionCV(
            penalty='l1', 
            solver='liblinear', 
            cv=3, 
            max_iter=1000,
            random_state=42
        )
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_pred)
            auc_scores.append(auc)
        except Exception as e:
            warnings.warn(f"Cross-validation fold failed: {e}")
            continue

    if not auc_scores:
        return None, 0.0
    
    return model, np.mean(auc_scores)

def calculate_prs(gwas_df, geno_matrix, snp_col='SNP', beta_col='Odds_Ratio'):
    """
    Calculate Polygenic Risk Score.
    PRS = sum(beta_i * genotype_i)
    """
    # Map SNPs to columns in geno_matrix
    # This assumes geno_matrix columns match SNP IDs
    prs_values = []
    
    for idx in range(geno_matrix.shape[0]):
        score = 0
        for snp in gwas_df[snp_col]:
            if snp in geno_matrix.columns:
                # Use log(Odds_Ratio) as beta for additive model
                beta = np.log(gwas_df[gwas_df[snp_col] == snp][beta_col].values[0])
                score += beta * geno_matrix.loc[idx, snp]
        prs_values.append(score)
    
    return pd.Series(prs_values, index=geno_matrix.index)

def likelihood_ratio_test(y, prs, covariates):
    """
    Perform likelihood-ratio test for PRS improvement over covariates-only model.
    Full model: y ~ PRS + covariates
    Reduced model: y ~ covariates
    """
    # Prepare data
    X_cov = covariates.copy()
    X_full = X_cov.copy()
    X_full['PRS'] = prs
    
    # Add constant
    X_cov = sm.add_constant(X_cov)
    X_full = sm.add_constant(X_full)
    
    # Fit reduced model
    try:
        model_reduced = sm.Logit(y, X_cov).fit(disp=0)
    except Exception:
        return None, None, None # Fail gracefully
        
    # Fit full model
    try:
        model_full = sm.Logit(y, X_full).fit(disp=0)
    except Exception:
        return None, None, None
        
    # Likelihood ratio test
    lr_stat = 2 * (model_full.llf - model_reduced.llf)
    df_diff = model_full.df_model - model_reduced.df_model
    p_value = 1 - stats.chi2.cdf(lr_stat, df_diff)
    
    return lr_stat, df_diff, p_value

def permutation_test(y, prs, covariates, n_permutations=1000, seed=42):
    """
    Generate null distribution via phenotype permutation.
    """
    set_seed(seed)
    null_aucs = []
    
    # Calculate observed AUC for baseline
    X_base = sm.add_constant(covariates)
    try:
        model_base = sm.Logit(y, X_base).fit(disp=0)
        # We need a baseline model with PRS to compare against
        X_full_obs = sm.add_constant(pd.concat([covariates, prs], axis=1))
        model_full_obs = sm.Logit(y, X_full_obs).fit(disp=0)
        obs_auc = roc_auc_score(y, model_full_obs.predict())
    except:
        obs_auc = 0.5
    
    for _ in range(n_permutations):
        y_perm = y.sample(frac=1, random_state=np.random.randint(0, 10000)).reset_index(drop=True)
        X_full_perm = sm.add_constant(pd.concat([covariates, prs], axis=1))
        try:
            model_perm = sm.Logit(y_perm, X_full_perm).fit(disp=0)
            auc = roc_auc_score(y_perm, model_perm.predict())
            null_aucs.append(auc)
        except:
            continue
    
    return null_aucs, obs_auc

def check_auc_threshold(obs_auc, null_aucs, threshold=0.75):
    """
    Check if observed AUC is significantly better than null and meets threshold.
    """
    if not null_aucs:
        return "insufficient_data", obs_auc, threshold
    
    null_mean = np.mean(null_aucs)
    null_std = np.std(null_aucs)
    z_score = (obs_auc - null_mean) / null_std if null_std > 0 else 0
    p_val = 1 - stats.norm.cdf(z_score)
    
    status = "low predictive power"
    if obs_auc >= threshold:
        status = "high predictive power"
    elif p_val < 0.05:
        status = "statistically significant but low power"
        
    return status, obs_auc, threshold

def calculate_vif_series(df):
    """
    Calculate Variance Inflation Factor (VIF) for each column in a DataFrame.
    """
    vif_data = pd.DataFrame()
    vif_data["Feature"] = df.columns
    vif_data["VIF"] = [
        stats.inflation_factor(df.values, i) 
        for i in range(len(df.columns))
    ]
    return vif_data

def write_collinearity_report(vif_df, r2_matrix, output_path):
    """
    Write collinearity diagnostics to a TSV file.
    Flags relationships where r² > 0.8.
    """
    # Prepare VIF data
    vif_report = vif_df.copy()
    vif_report.columns = ['Covariate', 'VIF']
    
    # Identify high correlation pairs
    high_corr_pairs = []
    cols = r2_matrix.columns
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            r2_val = r2_matrix.iloc[i, j]
            if r2_val > 0.8:
                high_corr_pairs.append({
                    'Covariate_1': cols[i],
                    'Covariate_2': cols[j],
                    'R_squared': r2_val,
                    'Status': 'HIGH_COLLINEARITY'
                })
    
    # Create report DataFrame
    report_rows = []
    for _, row in vif_report.iterrows():
        report_rows.append({
            'Covariate': row['Covariate'],
            'VIF': row['VIF'],
            'Status': 'HIGH' if row['VIF'] >= 5 else 'OK'
        })
    
    report_df = pd.DataFrame(report_rows)
    
    # Save to TSV
    report_df.to_csv(output_path, sep='\t', index=False)
    
    # Also save correlation details if needed, but task asks for TSV report
    # We append the high correlation pairs to the same file or a separate note?
    # The task says "output artifact data/processed/collinearity_report.tsv"
    # We will include the high correlation info in the report if possible, 
    # or just the VIFs as per standard VIF reports. 
    # The requirement says "flag relationships where r² > 0.8".
    # Let's append the high correlation pairs as additional rows or a separate section?
    # Standard TSV: one row per covariate. 
    # We will add a column 'High_Correlation_Pairs' if any exist for that covariate.
    
    # Re-doing the report to include pairs
    final_report = []
    for _, row in vif_report.iterrows():
        cov = row['Covariate']
        pairs = [f"{p['Covariate_2']} (r²={p['R_squared']:.3f})" 
                 for p in high_corr_pairs 
                 if p['Covariate_1'] == cov or p['Covariate_2'] == cov]
        final_report.append({
            'Covariate': cov,
            'VIF': row['VIF'],
            'High_Correlation_Pairs': '; '.join(pairs) if pairs else 'None',
            'Status': 'HIGH' if row['VIF'] >= 5 else 'OK'
        })
    
    final_df = pd.DataFrame(final_report)
    final_df.to_csv(output_path, sep='\t', index=False)

def main():
    parser = argparse.ArgumentParser(description="ML Validation and Collinearity Diagnostics")
    parser.add_argument("--gwas", required=True, help="Path to GWAS results TSV")
    parser.add_argument("--pheno", required=True, help="Path to phenotype file")
    parser.add_argument("--geno", required=True, help="Path to genotype PLINK prefix")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    print("Loading GWAS results...")
    gwas_df = load_gwas_results(args.gwas)
    
    print("Loading phenotypes...")
    pheno_df = load_phenotypes(args.pheno)
    
    # For collinearity, we need the covariates. 
    # Assuming pheno_df contains the covariates: geographic_region, sampling_year, Varroa_mite_count
    # We need to encode categorical variables if any.
    covariates = pheno_df.copy()
    
    # Check for required columns or assume specific names from T016
    # T016 output: phenotypes_cleaned.fam (6 cols) and phenotypes_cleaned.pheno
    # Let's assume the input --pheno is the .pheno file which has the covariates
    # If it's the .fam file, we need to merge with .pheno
    # For this implementation, we assume the passed file has the covariates.
    
    # 2. Collinearity Diagnostics (T031)
    print("Running collinearity diagnostics...")
    
    # Select numeric columns for VIF calculation
    # Exclude FID, IID, PAT, MAT, SEX, PHENO if present
    numeric_cols = covariates.select_dtypes(include=[np.number]).columns
    # Remove standard PLINK ID columns if they are numeric
    cols_to_check = [c for c in numeric_cols if c not in ['FID', 'IID', 'PAT', 'MAT', 'SEX', 'PHENO']]
    
    if len(cols_to_check) < 2:
        print("Not enough covariates for VIF calculation.")
        # Create empty report
        pd.DataFrame(columns=['Covariate', 'VIF', 'High_Correlation_Pairs', 'Status']).to_csv(
            output_dir / "collinearity_report.tsv", sep='\t', index=False
        )
    else:
        covariate_matrix = covariates[cols_to_check].dropna()
        if covariate_matrix.shape[0] > 1:
            # Calculate VIF
            # We need a function to calculate VIF properly
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            
            vif_data = []
            for i, col in enumerate(covariate_matrix.columns):
                try:
                    vif = variance_inflation_factor(covariate_matrix.values, i)
                    vif_data.append({'Feature': col, 'VIF': vif})
                except Exception as e:
                    print(f"Error calculating VIF for {col}: {e}")
            
            vif_df = pd.DataFrame(vif_data)
            
            # Calculate Correlation Matrix
            corr_matrix = covariate_matrix.corr()
            r2_matrix = corr_matrix ** 2
            
            # Write Report
            write_collinearity_report(vif_df, r2_matrix, output_dir / "collinearity_report.tsv")
            print(f"Collinearity report written to {output_dir / 'collinearity_report.tsv'}")
        else:
            print("Insufficient data for collinearity diagnostics.")

    # 3. LASSO and PRS (Remaining US3 tasks)
    # Note: Real genotype matrix loading is complex without .bed reader.
    # We will simulate the ML part with the available data or skip if not possible.
    # However, the task T031 is specifically about collinearity, which we have done.
    # The other parts (LASSO, PRS) are in the same file but T031 is the focus.
    # We will ensure the script runs and produces the collinearity report.
    
    print("ML Validation pipeline completed (Collinearity Diagnostics only for T031).")

if __name__ == "__main__":
    main()