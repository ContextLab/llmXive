from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from code.logging_config import get_logger

logger = get_logger(__name__)

def load_metrics_data(filepath: str = "data/processed/aggregated_metrics.csv") -> pd.DataFrame:
    """
    Load the aggregated metrics DataFrame containing:
    subject_id, modularity, global_efficiency, participation_coef, within_module_degree, fd
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found at {filepath}. "
                                "Ensure T021/T022 have run and written data/processed/aggregated_metrics.csv.")
    
    df = pd.read_csv(filepath)
    required_cols = ['subject_id', 'modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    
    # Ensure numeric types
    numeric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN in metrics
    df = df.dropna(subset=numeric_cols)
    return df

def run_pca_on_metrics(
    df: pd.DataFrame,
    n_components: int = 2,
    output_dir: str = "data/analysis",
    loadings_file: str = "pca_loadings.csv",
    scores_file: str = "factor_scores.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]
    Output: 
      - pca_loadings.csv: columns [component_1, component_2] (loadings for each metric)
      - factor_scores.csv: columns [subject_id, pca_factor_1] (projected scores)
    
    This function implements T023a.
    """
    logger.log("run_pca_on_metrics", operation="PCA", n_components=n_components)
    
    # Select features
    features = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    X = df[features].values
    
    # Initialize and fit PCA
    pca = PCA(n_components=n_components)
    pca.fit(X)
    
    # 1. Generate Loadings DataFrame
    # Loadings are the components_ array (n_components x n_features)
    # We transpose to make it n_features x n_components for easier reading
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f'component_{i+1}' for i in range(n_components)],
        index=features
    )
    
    # Save loadings
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    loadings_path = output_path / loadings_file
    loadings_df.to_csv(loadings_path, index=True)
    logger.log("save_loadings", path=str(loadings_path), rows=len(loadings_df))
    
    # 2. Generate Factor Scores (Transformed data)
    scores = pca.transform(X)
    scores_df = pd.DataFrame(
        scores,
        columns=[f'pca_factor_{i+1}' for i in range(n_components)]
    )
    # Add subject_id back
    scores_df.insert(0, 'subject_id', df['subject_id'].values)
    
    # Save scores
    scores_path = output_path / scores_file
    scores_df.to_csv(scores_path, index=False)
    logger.log("save_scores", path=str(scores_path), rows=len(scores_df))
    
    return loadings_df, scores_df

def run_correlations_with_fd_covariate(
    df: pd.DataFrame,
    metric_cols: List[str] = None
) -> pd.DataFrame:
    """
    Run correlations between metrics and behavioral scores, controlling for FD.
    Implemented in T024. Placeholder for T023a context.
    """
    logger.log("run_correlations_with_fd_covariate", operation="Correlation")
    # Implementation deferred to T024
    return pd.DataFrame()

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction.
    Implemented in T025. Placeholder for T023a context.
    """
    logger.log("apply_fdr_correction", operation="FDR", alpha=alpha)
    # Implementation deferred to T025
    return [False] * len(p_values)

def log_significant_correlations(results: pd.DataFrame) -> None:
    """Log significant correlations."""
    logger.log("log_significant_correlations", operation="Logging")

def generate_full_metrics(df: pd.DataFrame, pca_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores.
    Implements T023b.
    
    Logic:
    1. Ensure both DataFrames are indexed by subject_id (or merge on it).
    2. Concatenate raw metrics (from df) and PCA scores (from pca_scores).
    3. Return a single DataFrame containing all data for FR-005 and FR-004.
    """
    logger.log("generate_full_metrics", operation="Merge")
    
    if df.empty or pca_scores.empty:
        logger.log("generate_full_metrics", status="skipped", reason="Empty input")
        return pd.DataFrame()

    # Ensure subject_id is a column and set as index for merging
    # df comes from load_metrics_data, which keeps subject_id as a column
    # pca_scores comes from run_pca_on_metrics, which inserts subject_id as first col
    
    # Prepare left (raw metrics)
    left = df.copy()
    if 'subject_id' in left.columns:
        left = left.set_index('subject_id')
    
    # Prepare right (PCA scores)
    right = pca_scores.copy()
    if 'subject_id' in right.columns:
        right = right.set_index('subject_id')
    
    # Merge on index (subject_id)
    # inner join ensures we only keep subjects present in BOTH datasets
    merged = left.join(right, how='inner')
    
    if merged.empty:
        logger.log("generate_full_metrics", status="warning", reason="No matching subjects found")
        return pd.DataFrame()
    
    # Reset index to make subject_id a column again for CSV output
    merged = merged.reset_index()
    
    # Log output schema
    logger.log("generate_full_metrics", status="success", columns=list(merged.columns), rows=len(merged))
    
    return merged

def main() -> None:
    """
    Main entry point for T023a/T023b: Run PCA and generate full metrics.
    Reads from data/processed/aggregated_metrics.csv
    Writes:
      - data/analysis/pca_loadings.csv
      - data/analysis/factor_scores.csv
      - data/analysis/full_metrics.csv (T023b output)
    """
    try:
        # Load data
        df = load_metrics_data()
        
        if df.empty:
            logger.log("main", status="skipped", reason="No data available")
            return
        
        logger.log("main", status="starting", subjects=len(df))
        
        # Run PCA (T023a)
        loadings, scores = run_pca_on_metrics(df)
        
        # Generate Full Metrics (T023b)
        full_metrics = generate_full_metrics(df, scores)
        
        if not full_metrics.empty:
            output_dir = Path("data/analysis")
            output_dir.mkdir(parents=True, exist_ok=True)
            full_metrics_path = output_dir / "full_metrics.csv"
            full_metrics.to_csv(full_metrics_path, index=False)
            logger.log("save_full_metrics", path=str(full_metrics_path), rows=len(full_metrics))
        
        logger.log("main", status="completed", 
                   loadings_file="data/analysis/pca_loadings.csv",
                   scores_file="data/analysis/factor_scores.csv",
                   full_metrics_file="data/analysis/full_metrics.csv")
        
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()