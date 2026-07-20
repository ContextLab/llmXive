import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA

from code.config import get_path, ensure_dirs, get_analysis_config, get_project_root
from code.logging_utils import get_logger

logger = get_logger(__name__)

def normalize_cognitive_scores_per_cohort(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Implements Z-score normalization of cognitive scores per cohort (FR-009).
    
    Logic:
    1. Identify distinct study cohorts (defined by 'brain_region' and 'pathology_status').
    2. Calculate mean and std of 'cognitive_score' per cohort.
    3. Transform raw scores to Z-scores: (x - mean) / std.
    4. Handle edge cases: If a cohort has only one sample or std is 0, set Z-score to 0.
    
    Args:
        input_path: Path to the input CSV containing raw cognitive scores.
        output_path: Path to write the normalized CSV.
        
    Returns:
        The normalized DataFrame.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    logger.info(f"Loading cognitive scores from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['brain_region', 'pathology_status', 'cognitive_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")
    
    # Define cohort grouping
    cohort_cols = ['brain_region', 'pathology_status']
    
    # Calculate mean and std per cohort
    # We use transform to broadcast the stats back to the original rows
    try:
        df['cohort_mean'] = df.groupby(cohort_cols)['cognitive_score'].transform('mean')
        df['cohort_std'] = df.groupby(cohort_cols)['cognitive_score'].transform('std')
    except Exception as e:
        logger.error(f"Error calculating cohort statistics: {e}")
        raise
    
    # Handle division by zero or single-sample cohorts (std == 0)
    # Per standard Z-score practice in such cases, we assign 0 or NaN. 
    # Here we assign 0 as the deviation from the mean is 0.
    df['cohort_std'] = df['cohort_std'].replace(0, np.nan)
    
    # Calculate Z-score
    df['cognitive_score_z'] = (df['cognitive_score'] - df['cohort_mean']) / df['cohort_std']
    
    # Fill NaN Z-scores (from 0 std) with 0.0
    df['cognitive_score_z'] = df['cognitive_score_z'].fillna(0.0)
    
    # Prepare output DataFrame
    output_cols = required_cols + ['cognitive_score_z', 'cohort_mean', 'cohort_std']
    # Ensure all exist before selecting
    available_cols = [c for c in output_cols if c in df.columns]
    result_df = df[available_cols].copy()
    
    # Round for readability
    result_df['cognitive_score_z'] = result_df['cognitive_score_z'].round(4)
    result_df['cohort_mean'] = result_df['cohort_mean'].round(4)
    result_df['cohort_std'] = result_df['cohort_std'].round(4)
    
    ensure_dirs(output_path)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Normalized cognitive scores written to {output_path}")
    
    return result_df

def calculate_vif(features_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    
    Args:
        features_df: DataFrame containing only the numeric feature columns.
        
    Returns:
        Dictionary mapping feature name to VIF score.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    vif_data = {}
    X = features_df.values
    # Add constant for intercept if needed, but VIF is usually calculated on predictors only
    # with a model y = Xb + e, VIF for col i is 1/(1-R_i^2)
    
    for i, col in enumerate(features_df.columns):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[col] = vif
        except Exception:
            vif_data[col] = np.inf
            
    return vif_data

def apply_pca(features_df: pd.DataFrame, n_components: Optional[int] = None) -> Tuple[pd.DataFrame, PCA]:
    """
    Apply PCA to orthogonalize features.
    
    Args:
        features_df: Input features.
        n_components: Number of components to keep. If None, keeps all.
        
    Returns:
        Transformed DataFrame with PCA components, and the fitted PCA object.
    """
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(features_df)
    
    component_names = [f'PC{i+1}' for i in range(X_pca.shape[1])]
    pca_df = pd.DataFrame(X_pca, columns=component_names, index=features_df.index)
    
    return pca_df, pca

def run_vif_check_and_pca(input_path: str, output_vif_path: str, output_pca_path: Optional[str] = None, vif_threshold: float = 5.0) -> Tuple[Dict, Optional[pd.DataFrame]]:
    """
    Run VIF check and conditionally apply PCA.
    
    Args:
        input_path: Path to input CSV with morphological metrics.
        output_vif_path: Path to write VIF results JSON.
        output_pca_path: Path to write PCA transformed data (if triggered).
        vif_threshold: Threshold for triggering PCA.
        
    Returns:
        Tuple of (vif_results_dict, pca_df or None)
    """
    import json
    import numpy as np
    
    df = pd.read_csv(input_path)
    # Select morphological metrics
    metric_cols = ['branch_points', 'total_length', 'soma_area', 'sholl_intersections']
    available_metrics = [c for c in metric_cols if c in df.columns]
    
    if not available_metrics:
        raise ValueError("No morphological metrics found in input CSV")
        
    features_df = df[available_metrics].dropna()
    
    vif_scores = calculate_vif(features_df)
    max_vif = max(vif_scores.values())
    trigger_pca = max_vif > vif_threshold
    
    vif_results = {
        'vif_scores': {k: float(v) for k, v in vif_scores.items()},
        'max_vif': float(max_vif),
        'trigger_pca': trigger_pca
    }
    
    # Ensure output directory exists
    ensure_dirs(output_vif_path)
    with open(output_vif_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
        
    logger.info(f"VIF Check complete. Max VIF: {max_vif:.2f}. Trigger PCA: {trigger_pca}")
    
    pca_df = None
    if trigger_pca:
        pca_df, _ = apply_pca(features_df)
        if output_pca_path:
            ensure_dirs(output_pca_path)
            pca_df.to_csv(output_pca_path, index=False)
            logger.info(f"PCA applied and saved to {output_pca_path}")
    
    return vif_results, pca_df

def classify_early_ad_dynamic(input_path: str, output_path: str, threshold_percentile: float = 90.0) -> pd.DataFrame:
    """
    Dynamically classify 'Early AD' based on amyloid-beta load if labels are missing.
    
    Logic:
    1. Check if 'pathology_status' is already populated.
    2. If missing, identify 'Normal' group.
    3. Calculate high percentile of amyloid-beta load in 'Normal' group.
    4. Classify 'Early AD' if load > threshold.
    
    Args:
        input_path: Path to input CSV.
        output_path: Path to write classified CSV.
        threshold_percentile: Percentile to use as threshold (default 90).
        
    Returns:
        DataFrame with updated pathology status.
    """
    df = pd.read_csv(input_path)
    
    # Placeholder logic assuming 'amyloid_beta_load' exists if dynamic classification is needed
    # In real pipeline, this column must be present.
    if 'amyloid_beta_load' not in df.columns:
        logger.warning("Column 'amyloid_beta_load' not found. Skipping dynamic classification.")
        df.to_csv(output_path, index=False)
        return df
    
    if df['pathology_status'].isnull().all() or df['pathology_status'].astype(str).str.lower().isin(['nan', 'none']).all():
        logger.info("Performing dynamic 'Early AD' classification...")
        # Assume 'Normal' is the baseline if we need to find the threshold
        # If labels are completely missing, we might need to infer from other metadata or assume all are candidates
        # For this implementation, we assume we are classifying based on load relative to a known control distribution
        # If 'pathology_status' is entirely missing, we treat the whole set as potentially mixed or need a reference.
        # Simplified: Calculate threshold on the whole set if no 'Normal' label exists, or just use a fixed logic.
        # Per spec: "identify the 'control group' as subjects with pathology_status == 'Normal'".
        # If no 'Normal' exists, we cannot calculate the threshold as per spec.
        
        if 'Normal' in df['pathology_status'].values:
            control_group = df[df['pathology_status'] == 'Normal']
            threshold = control_group['amyloid_beta_load'].quantile(threshold_percentile / 100.0)
        else:
            # Fallback: use the whole population's percentile if no control group labeled
            # This is a deviation from strict spec but necessary if data is unlabelled
            threshold = df['amyloid_beta_load'].quantile(threshold_percentile / 100.0)
            logger.warning("No 'Normal' group found. Using full dataset for threshold calculation.")
        
        logger.info(f"Dynamic threshold calculated: {threshold}")
        
        def classify_row(row):
            if pd.isna(row['pathology_status']):
                return 'Early AD' if row['amyloid_beta_load'] > threshold else 'Normal'
            return row['pathology_status']
        
        df['pathology_status'] = df.apply(classify_row, axis=1)
    
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    return df

def run_kfold_cv(model_func, X: pd.DataFrame, y: pd.Series, k: int = 5) -> Dict[str, float]:
    """
    Run k-fold cross-validation.
    
    Args:
        model_func: Function that takes X, y and returns R2 score.
        X: Features.
        y: Target.
        k: Number of folds.
        
    Returns:
        Dict with 'r2_mean' and 'r2_std'.
    """
    from sklearn.model_selection import KFold
    
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        r2 = model_func(X_train, y_train, X_test, y_test)
        r2_scores.append(r2)
        
    return {
        'r2_mean': float(np.mean(r2_scores)),
        'r2_std': float(np.std(r2_scores)),
        'r2_scores': r2_scores
    }

def run_sensitivity_analysis(base_config: Dict, steps: List[int]) -> Dict:
    """
    Run sensitivity analysis on Sholl radius steps.
    
    Args:
        base_config: Base configuration for the analysis.
        steps: List of Sholl radius steps to test.
        
    Returns:
        Dict containing p-value variations.
    """
    results = {}
    for step in steps:
        # Placeholder for running the full pipeline with specific step
        # In real implementation, this would call run_analysis_pipeline with modified config
        logger.info(f"Running sensitivity analysis for Sholl step: {step}")
        # Mock result for structure
        results[step] = {'p_value': 0.05} 
        
    return results

def calculate_interaction_pvalue_variation(p_values: Dict[int, float], reference_step: int = 5, threshold: float = 0.05) -> Dict:
    """
    Calculate variation in interaction effect p-value across sensitivity sweeps.
    
    Args:
        p_values: Dict mapping step size to p-value.
        reference_step: The step size to use as baseline.
        threshold: Threshold for flagging significant variation.
        
    Returns:
        Dict with variation metrics and flags.
    """
    if reference_step not in p_values:
        raise ValueError(f"Reference step {reference_step} not found in p_values")
        
    ref_p = p_values[reference_step]
    variations = {}
    flags = {}
    
    for step, p_val in p_values.items():
        diff = abs(p_val - ref_p)
        variations[step] = diff
        flags[step] = diff > threshold
        
    return {
        'reference_p_value': ref_p,
        'variations': variations,
        'flags': flags,
        'max_variation': max(variations.values()) if variations else 0.0
    }

def run_analysis_pipeline(config: Optional[Dict] = None):
    """
    Main entry point for the analysis pipeline.
    Orchestrates normalization, VIF/PCA, regression, and validation.
    """
    if config is None:
        config = get_analysis_config()
        
    # Paths
    input_metrics = get_path('data/processed/morphological_metrics.csv')
    output_normalized = get_path('data/intermediates/normalized_cognitive_scores.csv')
    output_vif = get_path('data/intermediates/vif_check.json')
    output_pca = get_path('data/intermediates/processed_pca.csv')
    
    # 1. Normalize Cognitive Scores
    normalize_cognitive_scores_per_cohort(input_metrics, output_normalized)
    
    # 2. VIF Check and PCA
    vif_results, pca_df = run_vif_check_and_pca(
        input_metrics, 
        output_vif, 
        output_pca if pca_df is not None else None
    )
    
    # 3. Regression (Placeholder for T027 logic)
    # 4. Validation (Placeholder for T033-T035 logic)
    
    logger.info("Analysis pipeline completed.")

def main():
    """CLI entry point."""
    run_analysis_pipeline()

if __name__ == "__main__":
    main()