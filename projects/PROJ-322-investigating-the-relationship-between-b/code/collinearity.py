import numpy as np
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_config, is_synthetic
from entities import GraphMetrics

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, exclude_intercept: bool = True) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor in a DataFrame.
    
    Args:
        df: DataFrame containing predictor variables.
        exclude_intercept: If True, removes the intercept column from calculation.
        
    Returns:
        Dictionary mapping column names to their VIF values.
    """
    if exclude_intercept and 'intercept' in df.columns:
        df = df.drop(columns=['intercept'])
    
    vif_data = {}
    for col in df.columns:
        other_cols = [c for c in df.columns if c != col]
        if len(other_cols) == 0:
            vif_data[col] = 0.0
            continue
        
        # Fit linear model: col ~ other_cols
        try:
            X = sm.add_constant(df[other_cols])
            y = df[col]
            model = sm.OLS(y, X).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
    
    return vif_data

def run_pca_on_metrics(df: pd.DataFrame, target_cols: List[str], variance_threshold: float = 0.60) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Run PCA on selected metrics to handle collinearity.
    
    Args:
        df: DataFrame containing the metrics.
        target_cols: List of column names to apply PCA on.
        variance_threshold: Minimum cumulative variance explained required.
        
    Returns:
        Tuple of (PCA object or None, dict with variance info)
    """
    if len(target_cols) == 0:
        return None, {"variance_explained": 0.0, "success": False}
    
    X = df[target_cols].dropna()
    if X.shape[0] < 2:
        logger.warning("Not enough samples for PCA")
        return None, {"variance_explained": 0.0, "success": False}
        
    try:
        from sklearn.decomposition import PCA
        pca = PCA()
        pca.fit(X)
        
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        total_variance_explained = cumulative_variance[-1]
        
        if total_variance_explained >= variance_threshold:
            logger.info(f"PCA successful: cumulative variance = {total_variance_explained:.4f}")
            return pca, {
                "variance_explained": float(total_variance_explained),
                "components": int(pca.n_components_),
                "success": True
            }
        else:
            logger.warning(f"PCA failed: cumulative variance = {total_variance_explained:.4f} < {variance_threshold}")
            return None, {
                "variance_explained": float(total_variance_explained),
                "components": int(pca.n_components_),
                "success": False
            }
    except Exception as e:
        logger.error(f"PCA failed with error: {e}")
        return None, {"variance_explained": 0.0, "success": False}

def generate_descriptive_vif_report(df: pd.DataFrame, target_cols: List[str], output_path: Path) -> Dict[str, Any]:
    """
    Generate a descriptive VIF report when PCA fails.
    Contains correlation matrix and variance decomposition.
    
    Args:
        df: DataFrame with predictor variables.
        target_cols: List of column names to include in the report.
        output_path: Path to save the JSON report.
        
    Returns:
        Dictionary containing the report data.
    """
    if len(target_cols) == 0:
        logger.warning("No target columns provided for VIF report")
        return {}
        
    X = df[target_cols].dropna()
    if X.shape[0] < 2:
        logger.warning("Not enough samples for VIF report")
        return {}
    
    # Calculate correlation matrix
    corr_matrix = X.corr()
    
    # Calculate VIFs
    vif_dict = calculate_vif(X)
    
    # Variance decomposition (proportion of variance explained by each component)
    # We'll use a simple decomposition based on correlation structure
    variance_decomposition = {}
    for col in X.columns:
        # Sum of squared correlations with other variables (simplified measure)
        other_cols = [c for c in X.columns if c != col]
        if len(other_cols) > 0:
            sq_corr_sum = sum(corr_matrix.loc[col, other_col]**2 for other_col in other_cols)
            variance_decomposition[col] = float(sq_corr_sum)
        else:
            variance_decomposition[col] = 0.0
    
    report = {
        "correlation_matrix": corr_matrix.to_dict(),
        "vif_values": vif_dict,
        "variance_decomposition": variance_decomposition,
        "sample_size": int(X.shape[0]),
        "num_predictors": len(target_cols),
        "description": "Descriptive VIF report generated because PCA failed (singular matrix or insufficient variance explained). This report characterizes the joint relationships among predictors."
    }
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Descriptive VIF report saved to {output_path}")
    return report

def check_and_handle_collinearity(df: pd.DataFrame, target_cols: List[str], vif_threshold: float = 5.0, variance_threshold: float = 0.60) -> Dict[str, Any]:
    """
    Check for multicollinearity and handle it by attempting PCA or generating a report.
    
    Args:
        df: DataFrame containing the data.
        target_cols: List of column names to check.
        vif_threshold: VIF value above which collinearity is considered problematic.
        variance_threshold: Minimum cumulative variance for PCA to be considered successful.
        
    Returns:
        Dictionary with the outcome of the collinearity check and handling.
    """
    if len(target_cols) == 0:
        return {"status": "no_columns", "message": "No target columns provided."}
    
    X = df[target_cols].dropna()
    if X.shape[0] < 2:
        return {"status": "insufficient_data", "message": "Not enough samples for collinearity check."}
    
    vif_dict = calculate_vif(X)
    max_vif = max(vif_dict.values()) if vif_dict else 0.0
    
    logger.info(f"Maximum VIF: {max_vif:.2f}")
    
    if max_vif <= vif_threshold:
        logger.info("No significant multicollinearity detected.")
        return {
            "status": "ok",
            "vif_values": vif_dict,
            "message": "VIF values are within acceptable limits."
        }
    
    logger.warning(f"High multicollinearity detected (Max VIF: {max_vif:.2f}). Attempting PCA...")
    
    pca, pca_info = run_pca_on_metrics(X, target_cols, variance_threshold)
    
    if pca_info["success"]:
        return {
            "status": "pca_success",
            "vif_values": vif_dict,
            "pca_info": pca_info,
            "message": "PCA successfully reduced dimensionality while explaining sufficient variance."
        }
    
    logger.warning("PCA failed. Generating descriptive VIF report...")
    
    # Generate the descriptive report as per FR-006
    report_path = Path("data/results/descriptive_vif_report.json")
    report_data = generate_descriptive_vif_report(X, target_cols, report_path)
    
    return {
        "status": "pca_failed_report_generated",
        "vif_values": vif_dict,
        "pca_info": pca_info,
        "report_path": str(report_path),
        "report_data": report_data,
        "message": "PCA failed. Descriptive VIF report generated to characterize joint relationships."
    }

def main():
    """
    Main entry point for collinearity analysis.
    Loads preprocessed data and checks for multicollinearity.
    """
    logger.info("Starting collinearity analysis...")
    
    # Load preprocessed data (assuming it's in data/processed/)
    # This is a placeholder; actual implementation would load from the correct path
    preprocessed_path = Path("data/processed/preprocessed_data.csv")
    
    if not preprocessed_path.exists():
        logger.error(f"Preprocessed data not found at {preprocessed_path}")
        return
    
    df = pd.read_csv(preprocessed_path)
    
    # Define target columns for collinearity check
    # These should match the predictors used in the statistical model
    target_cols = ["global_efficiency", "modularity"]  # Example columns
    
    # Check and handle collinearity
    result = check_and_handle_collinearity(df, target_cols)
    
    logger.info(f"Collinearity analysis result: {result['status']}")
    if "report_path" in result:
        logger.info(f"Report saved to: {result['report_path']}")

if __name__ == "__main__":
    main()
