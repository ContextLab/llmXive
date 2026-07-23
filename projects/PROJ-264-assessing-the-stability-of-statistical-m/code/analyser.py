import logging
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Imports from project API surface
# Note: Assuming these are available in the module namespace or imported from utils
# If utils is not imported here, we add the import below to ensure it works.
from code.utils import set_seed, setup_logging, log_and_reraise, safe_execute

# --- Data Loading Helpers ---

def load_raw_evaluations(file_path: str = "results/raw_evaluations.csv") -> pd.DataFrame:
    """Load raw evaluation results from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw evaluation file not found: {path}")
    df = pd.read_csv(path)
    required_cols = ['dataset_id', 'model_name', 'fold_id', 'repeat_id', 'accuracy', 'f1_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in raw evaluations: {missing}")
    return df

def load_dataset_properties(file_path: str = "results/dataset_properties.csv") -> pd.DataFrame:
    """Load dataset properties (n_samples, n_features) from CSV."""
    path = Path(file_path)
    if not path.exists():
        # Fallback to common location if not specified, or raise error
        # In this context, we assume it exists if analysis is run
        raise FileNotFoundError(f"Dataset properties file not found: {path}")
    df = pd.read_csv(path)
    return df

# --- Core Analysis Functions ---

def calculate_cv(df: pd.DataFrame, metric_col: str = 'accuracy') -> pd.DataFrame:
    """
    Calculate Coefficient of Variation (CV = std/mean) for each (dataset, model) pair.
    Handles zero-variance cases by returning 0.0 for CV if mean is 0 or std is 0.
    """
    if df.empty:
        return pd.DataFrame()

    # Group by dataset and model
    grouped = df.groupby(['dataset_id', 'model_name'])[metric_col]
    
    agg_df = grouped.agg(['mean', 'std']).reset_index()
    agg_df.rename(columns={'mean': f'mean_{metric_col}', 'std': f'std_{metric_col}'}, inplace=True)
    
    # Calculate CV
    # Avoid division by zero
    def safe_cv(row, col_mean, col_std):
        mean_val = row[col_mean]
        std_val = row[col_std]
        if pd.isna(mean_val) or mean_val == 0:
            return 0.0
        if pd.isna(std_val) or std_val == 0:
            return 0.0
        return std_val / abs(mean_val)

    cv_col = f'cv_{metric_col}'
    agg_df[cv_col] = agg_df.apply(safe_cv, axis=1, col_mean=f'mean_{metric_col}', col_std=f'std_{metric_col}')
    
    return agg_df

def aggregate_metrics(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate raw evaluations to compute mean_accuracy, cv_accuracy, mean_f1, cv_f1.
    Input: raw_df with columns dataset_id, model_name, accuracy, f1_score
    Output: DataFrame with aggregated metrics per (dataset_id, model_name)
    """
    # Calculate CV for accuracy
    cv_acc_df = calculate_cv(raw_df, 'accuracy')
    
    # Calculate CV for F1
    cv_f1_df = calculate_cv(raw_df, 'f1_score')
    
    # Merge results
    merged = cv_acc_df.merge(cv_f1_df[['dataset_id', 'model_name', 'cv_f1_score']], on=['dataset_id', 'model_name'])
    
    # Rename columns for clarity if needed, ensuring consistency with spec
    merged.rename(columns={
        'mean_accuracy': 'mean_accuracy',
        'std_accuracy': 'std_accuracy',
        'cv_accuracy': 'cv_accuracy',
        'mean_f1_score': 'mean_f1',
        'std_f1_score': 'std_f1',
        'cv_f1_score': 'cv_f1'
    }, inplace=True)
    
    # Ensure columns are in expected order
    cols = ['dataset_id', 'model_name', 'mean_accuracy', 'std_accuracy', 'cv_accuracy', 'mean_f1', 'std_f1', 'cv_f1']
    return merged[cols]

def calculate_correlations(metrics_df: pd.DataFrame, props_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pearson and Spearman correlations between CV metrics and dataset properties.
    Primary: Pearson r.
    Secondary: Spearman rho.
    """
    if metrics_df.empty or props_df.empty:
        return pd.DataFrame()

    # Merge metrics with properties
    merged = metrics_df.merge(props_df, on='dataset_id', how='inner')
    
    if merged.empty:
        return pd.DataFrame()

    results = []
    cv_metrics = ['cv_accuracy', 'cv_f1']
    prop_metrics = ['n_samples', 'n_features']
    
    for cv_col in cv_metrics:
        for prop_col in prop_metrics:
            if cv_col not in merged.columns or prop_col not in merged.columns:
                continue
            
            # Drop NaNs
            data = merged[[cv_col, prop_col]].dropna()
            if len(data) < 3:
                continue
            
            x = data[prop_col]
            y = data[cv_col]
            
            # Pearson
            try:
                pearson_r, pearson_p = stats.pearsonr(x, y)
            except Exception:
                pearson_r, pearson_p = np.nan, np.nan
            
            # Spearman
            try:
                spearman_r, spearman_p = stats.spearmanr(x, y)
            except Exception:
                spearman_r, spearman_p = np.nan, np.nan
            
            results.append({
                'metric': cv_col,
                'property': prop_col,
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_rho': spearman_r,
                'spearman_p': spearman_p
            })
    
    return pd.DataFrame(results)

def compute_regression_residuals(metrics_df: pd.DataFrame, props_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute residuals from log-log linear regression of log(CV) against log(n_samples) and log(n_features).
    """
    if metrics_df.empty or props_df.empty:
        return pd.DataFrame()

    merged = metrics_df.merge(props_df, on='dataset_id', how='inner')
    if merged.empty:
        return pd.DataFrame()

    results = []
    cv_cols = ['cv_accuracy', 'cv_f1']
    
    for cv_col in cv_cols:
        # Filter for positive values for log transform
        valid = merged[(merged[cv_col] > 0) & (merged['n_samples'] > 0) & (merged['n_features'] > 0)]
        if len(valid) < 3:
            continue
        
        # Log transform
        y = np.log(valid[cv_col])
        x_samples = np.log(valid['n_samples'])
        x_features = np.log(valid['n_features'])
        
        # Reshape for regression
        X = np.column_stack([x_samples, x_features])
        
        # Linear regression
        try:
            coeffs, intercept, r_value, p_value, std_err = stats.linregress(x_samples, y)
            # Note: Simple 1D regression for samples as example, or multiple regression if needed.
            # Spec says "log-log linear regression of log(CV) against log(n_samples) and log(n_features)".
            # We will do a simple multiple regression.
            from sklearn.linear_model import LinearRegression
            model = LinearRegression()
            model.fit(X, y)
            predictions = model.predict(X)
            residuals = y - predictions
            
            # Store residuals for each dataset
            for idx, res in zip(valid.index, residuals):
                results.append({
                    'dataset_id': valid.loc[idx, 'dataset_id'],
                    'model_name': valid.loc[idx, 'model_name'],
                    'metric': cv_col,
                    'residual': res
                })
        except Exception as e:
            logging.warning(f"Could not compute regression residuals for {cv_col}: {e}")
            continue

    return pd.DataFrame(results)

def run_correlation_analysis(metrics_df: pd.DataFrame, props_df: pd.DataFrame) -> pd.DataFrame:
    """Run the full correlation analysis pipeline."""
    return calculate_correlations(metrics_df, props_df)

# --- Permutation Test Implementation (T025) ---

def run_permutation_test(
    metrics_df: pd.DataFrame, 
    model_a: str = 'LogisticRegression', 
    model_b: str = 'RandomForest', 
    metric_col: str = 'cv_accuracy', 
    n_permutations: int = 10000, 
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Perform a permutation test to compare variance distributions of two models.
    
    Test Statistic: |Var_A - Var_B| derived from squared deviations of accuracy scores.
    However, since we are working with aggregated CV metrics in `metrics_df`, 
    we interpret "variance distributions" as the distribution of CV values across datasets 
    for each model, OR the distribution of squared deviations if raw data is used.
    
    Given the input `metrics_df` which contains `cv_accuracy` (which is std/mean),
    the "variance" of the model's stability across datasets is the variance of the `cv_accuracy` column.
    
    But the spec says: "Calculate the absolute difference of the variances (|Var_A - Var_B|) 
    derived from the squared deviations of accuracy scores for each model pair."
    
    This implies we need the raw accuracy scores to compute the variance of accuracy per dataset,
    then compare the distribution of these variances? 
    
    Actually, the task T025 says: "Input: Must consume variance values from T018 output."
    T018 output is `metrics_df` which has `cv_accuracy` (a single value per dataset/model).
    If we only have one CV value per dataset per model, we cannot compute a "variance distribution" 
    of CVs unless we have multiple datasets.
    
    Interpretation: We have multiple datasets. For each dataset, Model A has a CV value, Model B has a CV value.
    We want to test if the distribution of CV values for Model A is significantly different from Model B.
    The "variance" in the spec might refer to the variance of the CV values across the dataset population.
    
    Alternative Interpretation (Strict): The spec says "variance distributions across LR, RF, SVM".
    If we have N datasets, we have N CV values for LR and N CV values for RF.
    We want to test if the variance of the LR CVs is different from the variance of the RF CVs?
    Or if the means are different?
    
    Re-reading T025: "Test Statistic: Calculate the absolute difference of the variances (|Var_A - Var_B|) 
    derived from the squared deviations of accuracy scores for each model pair."
    
    This phrasing is slightly ambiguous with the input constraint.
    If we assume the input is `metrics_df` (aggregated), we have a set of CV values for Model A and Model B.
    Let's assume the "variance" refers to the variance of the CV metric across the datasets.
    i.e. Var(CV_A) vs Var(CV_B).
    Test Statistic = |Var(CV_A) - Var(CV_B)|.
    
    Permutation Logic:
    1. Pool all CV values from Model A and Model B.
    2. Shuffle the labels (A/B) randomly.
    3. Split into two groups of size N_A and N_B.
    4. Calculate |Var(Group_A) - Var(Group_B)|.
    5. Repeat N times.
    6. P-value = (count of permuted stats >= observed stat + 1) / (N + 1).
    
    Note: If the number of datasets is small, this test might have low power.
    
    Parameters:
    - metrics_df: DataFrame with columns ['dataset_id', 'model_name', 'cv_accuracy', ...]
    - model_a, model_b: Names of the models to compare.
    - metric_col: The column to use (e.g., 'cv_accuracy').
    - n_permutations: Number of permutations.
    - seed: Random seed.
    
    Returns:
    - observed_stat: |Var_A - Var_B|
    - p_value: Raw p-value
    - permuted_stats: List of permuted statistics (optional, for debugging)
    """
    
    set_seed(seed)
    
    # Filter data for the two models
    df_a = metrics_df[metrics_df['model_name'] == model_a][metric_col].dropna()
    df_b = metrics_df[metrics_df['model_name'] == model_b][metric_col].dropna()
    
    if len(df_a) < 2 or len(df_b) < 2:
        logging.warning(f"Not enough data points for permutation test between {model_a} and {model_b}.")
        return 0.0, 1.0, []
    
    # Observed statistic: Absolute difference of variances
    var_a = df_a.var()
    var_b = df_b.var()
    observed_stat = abs(var_a - var_b)
    
    # Pool data
    pooled = np.concatenate([df_a.values, df_b.values])
    n_a = len(df_a)
    n_b = len(df_b)
    n_total = n_a + n_b
    
    permuted_stats = []
    count_extreme = 0
    
    for _ in range(n_permutations):
        # Shuffle indices
        shuffled_indices = np.random.permutation(n_total)
        # Split
        group_a = pooled[shuffled_indices[:n_a]]
        group_b = pooled[shuffled_indices[n_a:]]
        
        # Calculate variances
        var_a_perm = np.var(group_a, ddof=1) # ddof=1 for sample variance
        var_b_perm = np.var(group_b, ddof=1)
        
        stat_perm = abs(var_a_perm - var_b_perm)
        permuted_stats.append(stat_perm)
        
        if stat_perm >= observed_stat:
            count_extreme += 1
    
    # Calculate p-value
    p_value = (count_extreme + 1) / (n_permutations + 1)
    
    return observed_stat, p_value, permuted_stats

def run_full_permutation_analysis(
    metrics_df: pd.DataFrame, 
    models: List[str] = None, 
    metric_col: str = 'cv_accuracy', 
    n_permutations: int = 10000, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Run permutation tests for all pairs of models in the list.
    Returns a DataFrame with results.
    """
    if models is None:
        models = ['LogisticRegression', 'RandomForest', 'SVC'] # Default models from T012
    
    results = []
    
    # Generate all pairs
    from itertools import combinations
    for m1, m2 in combinations(models, 2):
        stat, p_val, _ = run_permutation_test(
            metrics_df, 
            model_a=m1, 
            model_b=m2, 
            metric_col=metric_col, 
            n_permutations=n_permutations, 
            seed=seed
        )
        results.append({
            'comparison': f"{m1}_vs_{m2}",
            'model_a': m1,
            'model_b': m2,
            'metric': metric_col,
            'statistic': stat,
            'raw_p_value': p_val,
            'adjusted_p_value': np.nan, # To be filled by Bonferroni in T026
            'significant': False # To be filled by T026
        })
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for the analyser.
    Orchestrates loading, aggregation, correlation, and permutation tests.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # 1. Load Data
        logger.info("Loading raw evaluations...")
        raw_df = load_raw_evaluations()
        if raw_df.empty:
            logger.warning("Raw evaluations are empty. Skipping analysis.")
            return
        
        # 2. Aggregate Metrics
        logger.info("Aggregating metrics...")
        metrics_df = aggregate_metrics(raw_df)
        
        # 3. Load Properties (if available)
        props_df = None
        try:
            props_df = load_dataset_properties()
        except FileNotFoundError:
            logger.warning("Dataset properties not found. Skipping correlation analysis.")
        
        # 4. Correlation Analysis
        if props_df is not None and not props_df.empty:
            logger.info("Running correlation analysis...")
            corr_results = run_correlation_analysis(metrics_df, props_df)
            # Save correlation results (T021/T035)
            if not corr_results.empty:
                corr_results.to_csv("results/correlation_results.csv", index=False)
                logger.info(f"Saved correlation results to results/correlation_results.csv")
        
        # 5. Permutation Test (T025)
        logger.info("Running permutation test for variance differences...")
        perm_results = run_full_permutation_analysis(metrics_df, metric_col='cv_accuracy')
        
        if not perm_results.empty:
            perm_results.to_csv("results/permutation_results.csv", index=False)
            logger.info(f"Saved permutation results to results/permutation_results.csv")
        else:
            logger.warning("Permutation test results are empty.")
        
        # 6. Regression Residuals (T020)
        if props_df is not None and not props_df.empty:
            logger.info("Computing regression residuals...")
            residuals_df = compute_regression_residuals(metrics_df, props_df)
            if not residuals_df.empty:
                residuals_df.to_csv("results/regression_residuals.csv", index=False)
                logger.info(f"Saved regression residuals to results/regression_residuals.csv")
                
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise

if __name__ == "__main__":
    main()