import numpy as np
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import is_synthetic, get_config

logger = logging.getLogger(__name__)

def calculate_vif(dataframe: pd.DataFrame, exclude_intercept: bool = True) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor in the dataframe.
    
    Args:
        dataframe: DataFrame containing predictor variables.
        exclude_intercept: If True, excludes the intercept column from calculation.
        
    Returns:
        Series of VIF values indexed by column name.
    """
    vif_data = {}
    columns = dataframe.columns
    
    if exclude_intercept and 'intercept' in columns:
        columns = columns.drop('intercept')
        
    for col in columns:
        if col == 'intercept':
            continue
            
        # Create a dataframe with the current column and all other columns
        y = dataframe[col]
        X = dataframe.drop(columns=[col])
        
        # Add constant for intercept if not present
        if 'intercept' not in X.columns:
            X = pd.concat([pd.Series(np.ones(len(X)), name='intercept'), X], axis=1)
        
        try:
            # Fit OLS regression
            model = pd.ols(y=y, x=X)
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if (1.0 - r_squared) > 1e-10 else float('inf')
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
            
    return pd.Series(vif_data)

def run_pca_on_metrics(metrics_df: pd.DataFrame, min_variance_threshold: float = 0.60) -> Tuple[bool, Dict[str, Any]]:
    """
    Attempt PCA on graph metrics to resolve collinearity.
    
    Args:
        metrics_df: DataFrame containing graph metrics (predictors).
        min_variance_threshold: Minimum cumulative variance required (default 0.60).
        
    Returns:
        Tuple of (success: bool, result: Dict).
        If successful, result contains PCA components and variance explained.
        If failed, result contains failure reason.
    """
    from sklearn.decomposition import PCA
    
    # Drop non-numeric columns if any
    numeric_df = metrics_df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 2:
        return False, {"reason": "Insufficient columns for PCA", "cumulative_variance": 0.0}
        
    try:
        pca = PCA()
        pca.fit(numeric_df)
        
        eigenvalues = pca.explained_variance_
        if np.any(eigenvalues <= 0):
            return False, {"reason": "Non-positive eigenvalues detected (singular matrix)", "eigenvalues": eigenvalues.tolist()}
            
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        max_cumulative = float(cumulative_variance[-1])
        
        if max_cumulative < min_variance_threshold:
            return False, {
                "reason": f"Cumulative variance {max_cumulative:.4f} < threshold {min_variance_threshold}",
                "cumulative_variance": max_cumulative,
                "explained_variance_ratio": pca.explained_variance_ratio_.tolist()
            }
            
        return True, {
            "cumulative_variance": float(max_cumulative),
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "components_shape": list(pca.components_.shape),
            "n_components_retained": int(np.sum(cumulative_variance >= min_variance_threshold))
        }
        
    except np.linalg.LinAlgError as e:
        return False, {"reason": f"LinAlgError during PCA: {str(e)}", "error_type": "singular_matrix"}
    except Exception as e:
        return False, {"reason": f"PCA failed: {str(e)}", "error_type": type(e).__name__}

def check_and_handle_collinearity(metrics_df: pd.DataFrame, vif_threshold: float = 5.0, 
                                  results_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Check for multicollinearity using VIF. If VIF > threshold, attempt PCA.
    If PCA fails, generate descriptive VIF report.
    
    Args:
        metrics_df: DataFrame with graph metrics.
        vif_threshold: VIF threshold above which to attempt PCA.
        results_dir: Directory to save output JSON files.
        
    Returns:
        Dictionary with collinearity status and actions taken.
    """
    if results_dir is None:
        config = get_config()
        results_dir = Path(config.get('results_dir', 'data/results'))
        
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate VIF
    vif_series = calculate_vif(metrics_df)
    max_vif = vif_series.max()
    high_vif_cols = vif_series[vif_series > vif_threshold].index.tolist()
    
    result = {
        "vif_calculated": True,
        "max_vif": float(max_vif),
        "high_vif_columns": high_vif_cols,
        "vif_threshold_used": vif_threshold,
        "action_taken": None,
        "pca_result": None,
        "descriptive_report_generated": False
    }
    
    if max_vif <= vif_threshold:
        result["action_taken"] = "no_action_needed"
        logger.info(f"Max VIF ({max_vif:.2f}) is below threshold ({vif_threshold}). No collinearity handling needed.")
        return result
        
    logger.warning(f"Max VIF ({max_vif:.2f}) exceeds threshold ({vif_threshold}). Attempting PCA.")
    
    # Attempt PCA
    pca_success, pca_info = run_pca_on_metrics(metrics_df)
    result["pca_result"] = pca_info
    
    if pca_success:
        result["action_taken"] = "pca_successful"
        logger.info(f"PCA successful. Cumulative variance: {pca_info['cumulative_variance']:.4f}")
    else:
        # PCA failed - generate descriptive report
        result["action_taken"] = "pca_failed_generating_report"
        result["descriptive_report_generated"] = True
        
        # Generate correlation matrix
        correlation_matrix = metrics_df.corr()
        
        # Prepare descriptive report
        descriptive_report = {
            "status": "pca_failed",
            "reason": pca_info.get("reason", "Unknown"),
            "vif_summary": {
                "max_vif": float(max_vif),
                "threshold": vif_threshold,
                "problematic_columns": high_vif_cols
            },
            "correlation_matrix": {
                col: correlation_matrix[col].to_dict() for col in correlation_matrix.columns
            },
            "variance_decomposition": {
                col: float(vif_series[col]) for col in vif_series.index
            },
            "recommendation": "Use descriptive report for joint relationship analysis. Consider removing highly correlated predictors manually or using regularization techniques."
        }
        
        # Save report
        report_path = results_dir / "descriptive_vif_report.json"
        with open(report_path, 'w') as f:
            json.dump(descriptive_report, f, indent=2, default=str)
        
        logger.info(f"Generated descriptive VIF report at {report_path}")
        
    return result

def main():
    """
    Main entry point for collinearity checking and handling.
    Reads preprocessed data, checks VIF, attempts PCA, and generates reports.
    """
    logging.basicConfig(level=logging.INFO)
    
    config = get_config()
    results_dir = Path(config.get('results_dir', 'data/results'))
    data_dir = Path(config.get('processed_dir', 'data/processed'))
    
    # Load metrics data (assuming it's generated by previous steps)
    metrics_path = data_dir / "graph_metrics.csv"
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}. Run graph_metrics.py first.")
        return
        
    metrics_df = pd.read_csv(metrics_path)
    
    # Ensure numeric columns are numeric
    numeric_cols = metrics_df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        logger.error("Insufficient numeric columns for collinearity analysis.")
        return
        
    # Check and handle collinearity
    result = check_and_handle_collinearity(metrics_df, results_dir=results_dir)
    
    # Save summary
    summary_path = results_dir / "collinearity_check.json"
    with open(summary_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
        
    logger.info(f"Collinearity check complete. Results saved to {summary_path}")
    
    return result

if __name__ == "__main__":
    main()