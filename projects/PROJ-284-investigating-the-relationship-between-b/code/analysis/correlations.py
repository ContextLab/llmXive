"""
Correlation analysis module for US2.
Implements PCA, metric merging, and output generation for full metrics preservation.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy import stats

from code.logging_config import get_logger

logger = get_logger(__name__)

# Paths
DATA_ANALYSIS_DIR = Path("data/analysis")
DATA_PROCESSED_DIR = Path("data/processed")

# Ensure output directories exist
DATA_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_metrics_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load aggregated metrics from the processed data directory.
    Expected input: data/processed/aggregated_metrics.csv
    """
    if input_path is None:
        input_path = DATA_PROCESSED_DIR / "aggregated_metrics.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Metrics data file not found at {input_path}. "
                                "Ensure T021/T022 have run and written aggregated_metrics.csv.")

    logger.log("load_metrics_data", path=str(input_path))
    df = pd.read_csv(input_path)
    return df


def perform_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """
    Perform PCA on network metrics.
    Input: DataFrame with columns [modularity, global_efficiency, participation_coef, within_module_degree]
    Output: PCA object, loadings DataFrame, factor scores DataFrame.
    """
    metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
    
    # Validate columns
    missing_cols = [col for col in metric_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required metric columns for PCA: {missing_cols}")

    subject_ids = df['subject_id']
    X = df[metric_cols].values

    # Handle NaNs if any (simple drop for now, or impute)
    if np.isnan(X).any():
        logger.log("pca_nan_handling", method="drop_rows_with_nan")
        valid_mask = ~np.isnan(X).any(axis=1)
        subject_ids = subject_ids[valid_mask]
        X = X[valid_mask]

    if len(X) < n_components:
        raise ValueError(f"Insufficient samples ({len(X)}) for PCA with {n_components} components.")

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(X)

    # Create Loadings DataFrame
    loadings_dict = {}
    for i in range(n_components):
        loadings_dict[f'component_{i+1}'] = pca.components_[i]
    loadings_df = pd.DataFrame(loadings_dict, index=metric_cols)

    # Create Factor Scores DataFrame
    scores_df = pd.DataFrame(scores, columns=[f'pca_factor_{i+1}' for i in range(n_components)])
    scores_df.insert(0, 'subject_id', subject_ids)

    logger.log("perform_pca", n_samples=len(X), n_components=n_components, explained_variance_ratio=str(pca.explained_variance_ratio_))
    return pca, loadings_df, scores_df


def save_pca_results(loadings_df: pd.DataFrame, scores_df: pd.DataFrame) -> None:
    """
    Save PCA loadings and factor scores to CSV files.
    Outputs:
      - data/analysis/pca_loadings.csv
      - data/analysis/factor_scores.csv
    """
    loadings_path = DATA_ANALYSIS_DIR / "pca_loadings.csv"
    scores_path = DATA_ANALYSIS_DIR / "factor_scores.csv"

    loadings_df.to_csv(loadings_path, index=True)
    scores_df.to_csv(scores_path, index=False)

    logger.log("save_pca_results", loadings_path=str(loadings_path), scores_path=str(scores_path))


def merge_metrics_with_pca_scores(metrics_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge individual metric columns with PCA factor scores into a single DataFrame.
    """
    # Ensure both are indexed by subject_id for merging
    if 'subject_id' not in metrics_df.columns:
        raise ValueError("metrics_df must contain 'subject_id' column.")
    
    merged_df = pd.merge(
        metrics_df,
        scores_df,
        on='subject_id',
        how='inner'
    )
    logger.log("merge_metrics_with_pca", rows_before=len(metrics_df), rows_after=len(merged_df))
    return merged_df


def generate_full_metrics_output(merged_df: pd.DataFrame) -> None:
    """
    Write the merged DataFrame to data/analysis/full_metrics.csv.
    This ensures FR-005 (FDR on individual metrics) and FR-004 (report generation)
    have access to all raw metrics AND PCA factors.
    """
    output_path = DATA_ANALYSIS_DIR / "full_metrics.csv"
    merged_df.to_csv(output_path, index=False)
    logger.log("generate_full_metrics_output", path=str(output_path), rows=len(merged_df))


def main() -> None:
    """
    Main entry point for T023b: File Output & Metric Preservation.
    1. Load aggregated metrics (T021/T022 output).
    2. Perform PCA (T023a logic).
    3. Save PCA results (pca_loadings.csv, factor_scores.csv).
    4. Merge metrics with PCA scores.
    5. Save full_metrics.csv.
    """
    try:
        logger.log("main_start", step="T023b_Metric_Preservation")
        
        # 1. Load Data
        metrics_df = load_metrics_data()
        logger.log("data_loaded", count=len(metrics_df))

        # 2. Perform PCA
        pca, loadings_df, scores_df = perform_pca_on_metrics(metrics_df)

        # 3. Save PCA Results
        save_pca_results(loadings_df, scores_df)

        # 4. Merge
        merged_df = merge_metrics_with_pca_scores(metrics_df, scores_df)

        # 5. Generate Full Output
        generate_full_metrics_output(merged_df)

        logger.log("main_success", output_files=["pca_loadings.csv", "factor_scores.csv", "full_metrics.csv"])

    except FileNotFoundError as e:
        logger.log("main_error", error=str(e))
        raise
    except Exception as e:
        logger.log("main_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
