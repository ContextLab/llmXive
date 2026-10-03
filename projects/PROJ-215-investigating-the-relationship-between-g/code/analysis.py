import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from statsmodels.stats.multitest import multipletests
from pathlib import Path
from config import get_output_path, ensure_directories
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_partial_spearman(x, y, covariates_df, covariate_cols):
    """
    Calculate partial Spearman correlation between x and y, adjusting for covariates.
    Algorithm:
    1. Rank transform x and y.
    2. Regress ranks of x against covariates -> residuals_x
    3. Regress ranks of y against covariates -> residuals_y
    4. Calculate Spearman correlation on residuals.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    
    if covariate_cols and covariate_cols[0] in covariates_df.columns:
        # Rank transform
        rank_x = pd.Series(x).rank()
        rank_y = pd.Series(y).rank()
        
        # Prepare covariates
        X = covariates_df[covariate_cols].dropna()
        if len(X) == 0:
            logger.warning("No valid covariate data after dropping NaNs. Proceeding without adjustment.")
            return spearmanr(x, y)[0], spearmanr(x, y)[1]
        
        # Align ranks with covariates
        valid_idx = X.index
        rank_x_adj = rank_x.loc[valid_idx]
        rank_y_adj = rank_y.loc[valid_idx]
        
        # Regression for x
        model_x = LinearRegression()
        model_x.fit(X, rank_x_adj)
        res_x = rank_x_adj - model_x.predict(X)
        
        # Regression for y
        model_y = LinearRegression()
        model_y.fit(X, rank_y_adj)
        res_y = rank_y_adj - model_y.predict(X)
        
        corr, pval = spearmanr(res_x, res_y)
        return corr, pval
    else:
        # Fallback to standard Spearman if covariates missing
        logger.warning("Covariates not found or insufficient. Using standard Spearman.")
        return spearmanr(x, y)

def run_partial_spearman_analysis(alpha_metrics_path, metadata_path, output_path):
    """
    Run partial Spearman correlation between alpha diversity and mental health scores.
    Reads alpha_metrics.csv and metadata, calculates partial correlations for PHQ-9 and GAD-7.
    Outputs unadjusted p-values to data/interim/unadjusted_alpha_pvals.csv.
    """
    ensure_directories()
    alpha_df = pd.read_csv(alpha_metrics_path)
    meta_df = pd.read_csv(metadata_path)
    
    # Merge on sample_id
    merged = pd.merge(alpha_df, meta_df, on='sample_id', how='inner')
    
    results = []
    covariates = ['age', 'bmi']
    available_covariates = [c for c in covariates if c in merged.columns and merged[c].notna().sum() > 0]
    
    for metric in ['shannon', 'simpson']:
        for outcome in ['phq9', 'gad7']:
            if metric not in merged.columns or outcome not in merged.columns:
                continue
            
            valid_data = merged[[metric, outcome] + available_covariates].dropna()
            if len(valid_data) < 3:
                continue
                
            corr, pval = calculate_partial_spearman(
                valid_data[metric], 
                valid_data[outcome], 
                valid_data, 
                available_covariates
            )
            results.append({
                'feature': f'{metric}_{outcome}',
                'pval_raw': pval,
                'correlation': corr,
                'n_samples': len(valid_data)
            })
    
    res_df = pd.DataFrame(results)
    res_df.to_csv(output_path, index=False)
    logger.info(f"Saved unadjusted alpha p-values to {output_path}")
    return res_df

def run_maaslin2_style_taxa_analysis(cleaned_dataset_path, metadata_path, output_path):
    """
    Perform linear modeling for taxa abundance vs PHQ-9/GAD-7 with covariate adjustment.
    Reads cleaned_dataset.csv and metadata.
    Outputs unadjusted p-values to data/interim/unadjusted_taxa_pvals.csv.
    """
    ensure_directories()
    data_df = pd.read_csv(cleaned_dataset_path)
    meta_df = pd.read_csv(metadata_path)
    
    # Identify OTU columns (assume they start with 'otu_' or are numeric columns not in metadata)
    # For simplicity, assume columns other than sample_id, phq9, gad7, age, bmi are OTUs
    exclude_cols = ['sample_id', 'phq9', 'gad7', 'age', 'bmi']
    otu_cols = [c for c in data_df.columns if c not in exclude_cols]
    
    merged = pd.merge(data_df, meta_df, on='sample_id', how='inner')
    
    results = []
    covariates = ['age', 'bmi']
    available_covariates = [c for c in covariates if c in merged.columns and merged[c].notna().sum() > 0]
    
    for outcome in ['phq9', 'gad7']:
        if outcome not in merged.columns:
            continue
            
        for taxon in otu_cols:
            if taxon not in merged.columns:
                continue
                
            valid_data = merged[[taxon, outcome] + available_covariates].dropna()
            if len(valid_data) < 3:
                continue
            
            # Linear model: outcome ~ taxon + covariates
            # We want the p-value for the taxon coefficient
            X = valid_data[[taxon] + available_covariates]
            y = valid_data[outcome]
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate t-statistic and p-value for the taxon coefficient
            # Residuals
            residuals = y - model.predict(X)
            # Standard error of the coefficient
            # This is a simplified approximation; for full MaAsLin2 we'd use statsmodels
            # Using a basic t-test on the correlation as a proxy for significance in this context
            # Or use scipy.stats.ttest_ind if we bin, but linear regression is specified.
            # Let's use statsmodels for proper p-values if available, otherwise fallback to correlation p-value
            try:
                import statsmodels.api as sm
                X_sm = sm.add_constant(X)
                ols = sm.OLS(y, X_sm).fit()
                pval = ols.pvalues[taxon]
                coef = ols.params[taxon]
            except ImportError:
                # Fallback: correlation p-value (less accurate for multivariate but better than nothing)
                corr, pval = spearmanr(valid_data[taxon], valid_data[outcome])
                coef = corr
            
            results.append({
                'feature': f'{taxon}_{outcome}',
                'pval_raw': pval,
                'correlation': coef,
                'n_samples': len(valid_data)
            })
    
    res_df = pd.DataFrame(results)
    res_df.to_csv(output_path, index=False)
    logger.info(f"Saved unadjusted taxa p-values to {output_path}")
    return res_df

def run_taxa_partial_spearman_fallback(cleaned_dataset_path, metadata_path, output_path):
    """
    Fallback to partial Spearman if linear modeling fails or is not appropriate.
    """
    # Reuse the logic from run_maaslin2_style but with partial spearman
    data_df = pd.read_csv(cleaned_dataset_path)
    meta_df = pd.read_csv(metadata_path)
    
    exclude_cols = ['sample_id', 'phq9', 'gad7', 'age', 'bmi']
    otu_cols = [c for c in data_df.columns if c not in exclude_cols]
    
    merged = pd.merge(data_df, meta_df, on='sample_id', how='inner')
    
    results = []
    covariates = ['age', 'bmi']
    available_covariates = [c for c in covariates if c in merged.columns and merged[c].notna().sum() > 0]
    
    for outcome in ['phq9', 'gad7']:
        if outcome not in merged.columns:
            continue
            
        for taxon in otu_cols:
            if taxon not in merged.columns:
                continue
                
            valid_data = merged[[taxon, outcome] + available_covariates].dropna()
            if len(valid_data) < 3:
                continue
            
            corr, pval = calculate_partial_spearman(
                valid_data[taxon],
                valid_data[outcome],
                valid_data,
                available_covariates
            )
            results.append({
                'feature': f'{taxon}_{outcome}',
                'pval_raw': pval,
                'correlation': corr,
                'n_samples': len(valid_data)
            })
    
    res_df = pd.DataFrame(results)
    res_df.to_csv(output_path, index=False)
    logger.info(f"Saved fallback taxa p-values to {output_path}")
    return res_df

def run_permanova_unifrac(distance_matrix_path, metadata_path, group_col, output_path):
    """
    Run PERMANOVA on a distance matrix.
    """
    import skbio
    from skbio.stats.distance import permanova
    
    dist_data = np.load(distance_matrix_path)
    distances = skbio.DistanceMatrix(dist_data['distances'], ids=dist_data['sample_ids'])
    meta_df = pd.read_csv(metadata_path)
    
    # Ensure sample IDs match
    common_ids = list(set(distances.ids) & set(meta_df['sample_id']))
    distances = distances.subset(common_ids)
    meta_df = meta_df[meta_df['sample_id'].isin(common_ids)]
    meta_df = meta_df.set_index('sample_id')
    
    # Group by high/low
    if group_col not in meta_df.columns:
        logger.error(f"Group column {group_col} not found in metadata")
        return None
        
    design = meta_df[[group_col]]
    
    result = permanova(distances, design, column=group_col)
    
    res_df = pd.DataFrame([result])
    res_df.to_csv(output_path, index=False)
    logger.info(f"Saved PERMANOVA results to {output_path}")
    return res_df

def apply_bh_correction(input_paths, output_path):
    """
    Apply Benjamini-Hochberg correction to all taxa and alpha diversity p-values.
    Input: List of paths to CSVs containing 'pval_raw' (or similar) columns.
    Output: Single CSV with 'feature', 'pval_raw', 'pval_adj'.
    Requirement: Do NOT apply to PERMANOVA.
    """
    ensure_directories()
    all_results = []
    
    for path in input_paths:
        if not os.path.exists(path):
            logger.warning(f"Input file not found: {path}")
            continue
        df = pd.read_csv(path)
        if 'pval_raw' not in df.columns:
            logger.warning(f"File {path} missing 'pval_raw' column, skipping")
            continue
        
        # Extract feature and pval
        features = df['feature']
        pvals = df['pval_raw']
        
        # Apply BH correction
        # multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
        _, pvals_adj, _, _ = multipletests(pvals, method='fdr_bh')
        
        batch_results = pd.DataFrame({
            'feature': features,
            'pval_raw': pvals,
            'pval_adj': pvals_adj
        })
        all_results.append(batch_results)
    
    if not all_results:
        logger.error("No valid p-value data found to correct.")
        # Create empty file with headers to satisfy contract
        pd.DataFrame(columns=['feature', 'pval_raw', 'pval_adj']).to_csv(output_path, index=False)
        return
    
    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(output_path, index=False)
    logger.info(f"Saved adjusted p-values to {output_path}")

def main():
    """
    Main entry point for analysis tasks including BH correction.
    """
    ensure_directories()
    logger.info("Starting analysis module...")
    
    # Paths
    alpha_metrics_path = get_output_path('data/processed/alpha_metrics.csv')
    metadata_path = get_output_path('data/processed/metadata.csv') # Assuming metadata is available
    cleaned_dataset_path = get_output_path('data/processed/cleaned_dataset.csv')
    
    interim_dir = get_output_path('data/interim')
    processed_dir = get_output_path('data/processed')
    
    # 1. Alpha Diversity Analysis (if not already done)
    alpha_pvals_path = os.path.join(interim_dir, 'unadjusted_alpha_pvals.csv')
    if not os.path.exists(alpha_pvals_path) and os.path.exists(alpha_metrics_path):
        run_partial_spearman_analysis(alpha_metrics_path, metadata_path, alpha_pvals_path)
    
    # 2. Taxa Analysis (if not already done)
    taxa_pvals_path = os.path.join(interim_dir, 'unadjusted_taxa_pvals.csv')
    if not os.path.exists(taxa_pvals_path) and os.path.exists(cleaned_dataset_path):
        run_maaslin2_style_taxa_analysis(cleaned_dataset_path, metadata_path, taxa_pvals_path)
    
    # 3. Apply Benjamini-Hochberg Correction (T022a)
    input_files = [alpha_pvals_path, taxa_pvals_path]
    adjusted_pvals_path = os.path.join(interim_dir, 'adjusted_pvals.csv')
    apply_bh_correction(input_files, adjusted_pvals_path)
    
    logger.info("Analysis module completed.")

if __name__ == "__main__":
    main()
