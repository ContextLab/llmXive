from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

from code.logging_config import get_logger

logger = get_logger(__name__)

# --------------------------------------------------------------------------
# Data Loading
# --------------------------------------------------------------------------

def load_metrics_data(file_path: str = "data/analysis/aggregated_metrics.csv") -> pd.DataFrame:
    """Load aggregated metrics from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    df = pd.read_csv(path)
    logger.log("load_metrics_data", file=str(path), rows=len(df))
    return df

# --------------------------------------------------------------------------
# PCA Analysis
# --------------------------------------------------------------------------

def run_pca_on_metrics(df: pd.DataFrame, n_components: int = 2) -> Tuple[PCA, pd.DataFrame, pd.DataFrame]:
    """Run PCA on numeric columns of the metrics dataframe."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("Need at least 2 numeric columns for PCA.")

    X = df[numeric_cols].fillna(0).values
    pca = PCA(n_components=min(n_components, len(numeric_cols)))
    scores = pca.fit_transform(X)

    scores_df = pd.DataFrame(scores, columns=[f"PC{i+1}" for i in range(scores.shape[1])])
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=[f"PC{i+1}" for i in range(pca.components_.shape[0])],
        index=numeric_cols
    )

    logger.log("run_pca_on_metrics", n_components=n_components, explained_variance_ratio=pca.explained_variance_ratio_.tolist())
    return pca, scores_df, loadings_df

def save_pca_outputs(scores_df: pd.DataFrame, loadings_df: pd.DataFrame, output_dir: str = "data/analysis") -> None:
    """Save PCA results to CSV."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    scores_path = output_path / "factor_scores.csv"
    loadings_path = output_path / "pca_loadings.csv"

    scores_df.to_csv(scores_path, index=False)
    loadings_df.to_csv(loadings_path)

    logger.log("save_pca_outputs", scores=str(scores_path), loadings=str(loadings_path))

# --------------------------------------------------------------------------
# Full Metrics Generation
# --------------------------------------------------------------------------

def generate_full_metrics(df: pd.DataFrame, pca_scores: pd.DataFrame) -> pd.DataFrame:
    """Merge original metrics with PCA factor scores."""
    if len(df) != len(pca_scores):
        raise ValueError("DataFrame and PCA scores length mismatch.")
    
    full_df = pd.concat([df.reset_index(drop=True), pca_scores.reset_index(drop=True)], axis=1)
    logger.log("generate_full_metrics", total_columns=full_df.shape[1])
    return full_df

def save_full_metrics(df: pd.DataFrame, output_path: str = "data/analysis/full_metrics.csv") -> None:
    """Save full metrics dataframe."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_full_metrics", path=output_path)

# --------------------------------------------------------------------------
# Correlation Analysis
# --------------------------------------------------------------------------

def run_simple_correlations(df: pd.DataFrame, target_col: str = "motor_score") -> List[Dict[str, Any]]:
    """Run Spearman correlations between all numeric cols and target."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col not in numeric_cols:
        raise ValueError(f"Target column {target_col} not in numeric columns.")
    
    results = []
    for col in numeric_cols:
        if col == target_col:
            continue
        
        x = df[col].dropna()
        y = df[target_col].loc[x.index]
        
        if len(x) < 3:
            continue

        r, p = stats.spearmanr(x, y)
        results.append({
            "metric": col,
            "r": r,
            "p": p,
            "n": len(x)
        })
    
    logger.log("run_simple_correlations", count=len(results))
    return results

def run_correlations_with_fd_covariate(df: pd.DataFrame, target_col: str = "motor_score", covariate: str = "fd") -> List[Dict[str, Any]]:
    """Run partial correlations controlling for FD."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col not in numeric_cols or covariate not in numeric_cols:
        raise ValueError("Target or covariate not found in numeric columns.")
    
    results = []
    for col in numeric_cols:
        if col == target_col or col == covariate:
            continue

        # Simple partial correlation approximation using residuals
        # Regress col ~ fd, motor ~ fd, correlate residuals
        try:
            x = df[col].dropna()
            y = df[target_col].loc[x.index]
            z = df[covariate].loc[x.index]

            if len(x) < 4:
                continue

            # Linear regression residuals
            # y = a + b*z + res_y
            # x = c + d*z + res_x
            # corr(res_x, res_y)
            
            # Using numpy for simple linear regression
            z_arr = z.values
            y_arr = y.values
            x_arr = x.values

            # Fit y ~ z
            slope_y, intercept_y = np.polyfit(z_arr, y_arr, 1)
            res_y = y_arr - (slope_y * z_arr + intercept_y)

            # Fit x ~ z
            slope_x, intercept_x = np.polyfit(z_arr, x_arr, 1)
            res_x = x_arr - (slope_x * z_arr + intercept_x)

            r, p = stats.spearmanr(res_x, res_y)
            
            results.append({
                "metric": col,
                "r": r,
                "p": p,
                "n": len(x),
                "covariate_controlled": True
            })
        except Exception as e:
            logger.log("correlation_error", metric=col, error=str(e))
            continue

    logger.log("run_correlations_with_fd_covariate", count=len(results))
    return results

# --------------------------------------------------------------------------
# FDR Correction
# --------------------------------------------------------------------------

def apply_fdr_correction(results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Apply Benjamini-Hochberg FDR correction to a list of correlation results."""
    if not results:
        return []

    # Extract p-values and sort
    p_values = [r["p"] for r in results]
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])

    # BH Procedure
    ranks = np.arange(1, n + 1)
    thresholds = (ranks / n) * alpha
    q_values = sorted_p * n / ranks
    
    # Ensure q-values are monotonic (cumulative min from largest to smallest)
    # Actually, standard BH: q_i = p_i * n / i. 
    # To be conservative and monotonic, we take min(q_j) for j >= i
    monotonic_q = np.minimum.accumulate(q_values[::-1])[::-1]
    
    # Map back to original order
    final_q = np.zeros(n)
    final_q[sorted_indices] = monotonic_q
    
    # Determine significance
    significant = final_q < alpha

    # Update results
    for i, res in enumerate(results):
        res["q"] = float(final_q[i])
        res["significant"] = bool(significant[i])

    logger.log("apply_fdr_correction", alpha=alpha, significant_count=int(sum(significant)))
    return results

# --------------------------------------------------------------------------
# Output & Logging
# --------------------------------------------------------------------------

def save_correlations_to_csv(results: List[Dict[str, Any]], output_path: str = "data/analysis/correlation_results.csv") -> None:
    """Save correlation results to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.log("save_correlations_to_csv", path=output_path, count=len(results))

def log_significant_correlations(results: List[Dict[str, Any]], threshold_r: float = 0.3) -> None:
    """
    Log correlation threshold (r > 0.3) and significant findings.
    Task T027: Implement correlation threshold logging.
    """
    significant_results = [r for r in results if r.get("significant", False)]
    
    logger.log(
        "correlation_threshold_check",
        threshold_r=threshold_r,
        total_results=len(results),
        significant_count=len(significant_results)
    )

    strong_significant = [r for r in significant_results if abs(r.get("r", 0)) > threshold_r]
    
    logger.log(
        "strong_significant_correlations",
        count=len(strong_significant),
        threshold_r=threshold_r
    )

    for r in strong_significant:
        logger.log(
            "significant_correlation_found",
            metric=r.get("metric", "unknown"),
            r=r.get("r"),
            p=r.get("p"),
            q=r.get("q"),
            exceeds_threshold=abs(r.get("r", 0)) > threshold_r
        )

def process_metrics_with_batching(df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
    """Process metrics in batches if memory is constrained."""
    # Placeholder for batching logic if needed for very large datasets
    return df

# --------------------------------------------------------------------------
# Main Entry Point
# --------------------------------------------------------------------------

def main():
    """Main execution for correlation analysis."""
    logger.log("main_correlation_analysis", status="starting")

    try:
        # 1. Load Data
        metrics_df = load_metrics_data()
        logger.log("data_loaded", rows=len(metrics_df))

        # 2. Run PCA
        pca, scores_df, loadings_df = run_pca_on_metrics(metrics_df)
        save_pca_outputs(scores_df, loadings_df)

        # 3. Generate Full Metrics
        full_df = generate_full_metrics(metrics_df, scores_df)
        save_full_metrics(full_df)

        # 4. Run Correlations (Simple + FD Covariate)
        # Combine results
        simple_results = run_simple_correlations(full_df)
        fd_results = run_correlations_with_fd_covariate(full_df)
        
        # Merge results (prefer FD results if available, else simple)
        # For simplicity in this runner, we'll run simple and then re-run with FD for key metrics
        # Or just run FD for all if data permits.
        # Let's assume we want FD controlled results for the final output.
        final_results = fd_results if fd_results else simple_results

        # 5. FDR Correction
        corrected_results = apply_fdr_correction(final_results)

        # 6. Save Results
        save_correlations_to_csv(corrected_results)

        # 7. Task T027: Log Thresholds
        log_significant_correlations(corrected_results, threshold_r=0.3)

        logger.log("main_correlation_analysis", status="completed")

    except Exception as e:
        logger.log("main_correlation_analysis", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()