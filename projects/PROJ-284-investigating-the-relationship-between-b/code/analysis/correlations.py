import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA
from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_batch_size(total_memory_gb=7.0, matrix_size=400):
    """
    Calculate optimal batch size for matrix computations to respect memory limits.
    Assumes float64 matrices (8 bytes per element).
    """
    # Estimate memory per subject: 400x400 matrix * 8 bytes = 1.28 MB
    # Add overhead for PCA intermediate structures (approx 3x)
    memory_per_subject_mb = (matrix_size ** 2 * 8) / (1024 * 1024) * 3.5
    max_subjects = int((total_memory_gb * 1024) / memory_per_subject_mb)
    return max(1, max_subjects)

def load_metrics_data(input_path=None):
    """
    Load the aggregated network metrics from the processed data.
    Expects a CSV with columns: subject_id, modularity, global_efficiency,
    participation_coef, within_module_degree.
    """
    if input_path is None:
        # Default path based on project structure
        input_path = Path("data/analysis/full_metrics.csv")
        if not input_path.exists():
            # Fallback to raw metrics if full_metrics doesn't exist yet
            input_path = Path("data/analysis/aggregated_metrics.csv")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Metrics file not found at {input_path}. "
                                "Please run T021/T022 to generate metrics first.")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['subject_id', 'modularity', 'global_efficiency', 
                     'participation_coef', 'within_module_degree']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in metrics file: {missing_cols}")
    
    return df

def run_pca_analysis(metrics_df=None, n_components=2, output_dir="data/analysis"):
    """
    Perform PCA on network metrics.
    
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]
    Output: 
      - data/analysis/pca_loadings.csv (columns: component_1, component_2)
      - data/analysis/factor_scores.csv (columns: subject_id, pca_factor_1)
    
    Note: Per task spec, factor_scores only includes pca_factor_1, not pca_factor_2.
    """
    if metrics_df is None:
        metrics_df = load_metrics_data()
    
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = metrics_df[metric_cols].values
    subject_ids = metrics_df['subject_id'].values
    
    # Standardize features before PCA
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_standardized = (X - X_mean) / X_std
    
    # Run PCA
    pca = PCA(n_components=n_components)
    pca.fit(X_standardized)
    
    # Extract loadings (correlations between original variables and components)
    # Loadings matrix shape: (n_features, n_components)
    loadings = pca.components_.T  # Transpose to get (n_components, n_features)
    
    # Create loadings DataFrame
    # Columns: component_1, component_2
    # Rows: modularity, global_efficiency, participation_coef, within_module_degree
    loading_df = pd.DataFrame({
        'component_1': loadings[0],
        'component_2': loadings[1]
    }, index=metric_cols)
    
    # Save loadings
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    loadings_path = output_dir_path / "pca_loadings.csv"
    loading_df.to_csv(loadings_path)
    logger.info(f"PCA loadings saved to {loadings_path}")
    
    # Calculate factor scores (projected data)
    # Factor scores shape: (n_subjects, n_components)
    factor_scores = pca.transform(X_standardized)
    
    # Create factor scores DataFrame
    # Per task spec: columns: subject_id, pca_factor_1
    # We only include pca_factor_1, not pca_factor_2
    factor_scores_df = pd.DataFrame({
        'subject_id': subject_ids,
        'pca_factor_1': factor_scores[:, 0]
    })
    
    # Save factor scores
    scores_path = output_dir_path / "factor_scores.csv"
    factor_scores_df.to_csv(scores_path)
    logger.info(f"PCA factor scores saved to {scores_path}")
    
    return loading_df, factor_scores_df

def merge_metrics_and_pca_scores(metrics_df=None, factor_scores_df=None, output_dir="data/analysis"):
    """
    Merge individual metric columns with PCA factor scores into a single output DataFrame.
    Output: data/analysis/full_metrics.csv containing all raw metrics AND PCA factors.
    """
    if metrics_df is None:
        metrics_df = load_metrics_data()
    
    if factor_scores_df is None:
        # Run PCA if scores not provided
        _, factor_scores_df = run_pca_analysis(metrics_df, output_dir=output_dir)
    
    # Merge on subject_id
    merged_df = pd.merge(metrics_df, factor_scores_df, on='subject_id', how='left')
    
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    full_metrics_path = output_dir_path / "full_metrics.csv"
    merged_df.to_csv(full_metrics_path, index=False)
    logger.info(f"Full metrics with PCA scores saved to {full_metrics_path}")
    
    return merged_df

def run_correlation_analysis(data_df=None, covariate='fd'):
    """
    Run correlation analysis between network metrics and sensorimotor performance.
    Applies partial correlation if covariate is provided.
    """
    if data_df is None:
        # Load from full_metrics if available
        full_path = Path("data/analysis/full_metrics.csv")
        if full_path.exists():
            data_df = pd.read_csv(full_path)
        else:
            data_df = load_metrics_data()
    
    # This is a placeholder for the actual correlation logic which would be
    # implemented in T024. For T023a, we focus on PCA.
    logger.info("Correlation analysis placeholder - T024 implementation required")
    return None

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    Returns adjusted p-values and boolean mask for significance.
    """
    # This is a placeholder for T025 implementation
    logger.info("FDR correction placeholder - T025 implementation required")
    return None

def log_correlation_threshold(r_threshold=0.3):
    """
    Log correlation threshold for significant relationships.
    """
    logger.info(f"Correlation threshold set to |r| > {r_threshold}")
    return r_threshold

def main():
    """
    Main entry point for running PCA analysis on network metrics.
    """
    try:
        # Load metrics
        metrics_df = load_metrics_data()
        logger.info(f"Loaded {len(metrics_df)} subject records with network metrics")
        
        # Run PCA
        loading_df, factor_scores_df = run_pca_analysis(metrics_df)
        
        # Merge and save full metrics
        merged_df = merge_metrics_and_pca_scores(metrics_df, factor_scores_df)
        
        logger.info("PCA analysis completed successfully")
        logger.info(f"Loadings shape: {loading_df.shape}")
        logger.info(f"Factor scores shape: {factor_scores_df.shape}")
        
        return True
    except Exception as e:
        logger.error(f"PCA analysis failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
