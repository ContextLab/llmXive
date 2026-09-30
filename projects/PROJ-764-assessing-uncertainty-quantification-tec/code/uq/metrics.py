import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
import logging

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def expected_calibration_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    uncertainty: np.ndarray,
    num_bins: int = 10
) -> float:
    """
    Calculate Expected Calibration Error (ECE) using quantile binning.
    
    Args:
        y_true: True values.
        y_pred: Predicted mean values.
        uncertainty: Predicted uncertainty (standard deviation or variance).
        num_bins: Number of bins for calibration.
        
    Returns:
        ECE value.
    """
    # Calculate residuals
    residuals = np.abs(y_true - y_pred)
    
    # Sort by predicted uncertainty
    sorted_indices = np.argsort(uncertainty)
    sorted_residuals = residuals[sorted_indices]
    sorted_uncertainty = uncertainty[sorted_indices]
    
    # Bin the data
    bin_edges = np.linspace(0, sorted_uncertainty.max(), num_bins + 1)
    ece = 0.0
    
    for i in range(num_bins):
        lower, upper = bin_edges[i], bin_edges[i+1]
        mask = (sorted_uncertainty >= lower) & (sorted_uncertainty < upper)
        if i == num_bins - 1:
            mask = (sorted_uncertainty >= lower) & (sorted_uncertainty <= upper)
        
        if np.sum(mask) == 0:
            continue
        
        avg_residual = np.mean(sorted_residuals[mask])
        avg_uncertainty = np.mean(sorted_uncertainty[mask])
        
        ece += np.sum(mask) * np.abs(avg_residual - avg_uncertainty)
    
    return ece / len(y_true)

def interval_score(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    alpha: float = 0.1
) -> float:
    """
    Calculate the Interval Score for a given confidence level (1-alpha).
    
    Args:
        y_true: True values.
        lower: Lower bound of the prediction interval.
        upper: Upper bound of the prediction interval.
        alpha: Significance level (e.g., 0.1 for 90% interval).
        
    Returns:
        Mean Interval Score.
    """
    width = upper - lower
    penalty = np.maximum(0, (lower - y_true) * (2 / alpha) + (y_true - upper) * (2 / alpha))
    scores = width + penalty
    return np.mean(scores)

def sharpness(
    lower: np.ndarray,
    upper: np.ndarray
) -> float:
    """
    Calculate Sharpness (average width of prediction intervals).
    
    Args:
        lower: Lower bound of the prediction interval.
        upper: Upper bound of the prediction interval.
        
    Returns:
        Mean sharpness.
    """
    return np.mean(upper - lower)

def decompose_uncertainty(
    df: pd.DataFrame,
    method_col: str = 'method',
    prediction_col: str = 'prediction',
    variance_col: str = 'variance'
) -> pd.DataFrame:
    """
    Decompose total uncertainty into aleatoric and epistemic components.
    
    Logic:
    - Epistemic variance = variance of predictions across ensemble members for a single sample.
    - Aleatoric variance = mean of predicted variances (model's internal uncertainty).
    - For Sparse GP: set aleatoric and epistemic to null, total = variance.
    
    Args:
        df: DataFrame containing predictions from multiple seeds/methods.
        method_col: Name of the column containing the method name.
        prediction_col: Name of the column containing the predicted mean.
        variance_col: Name of the column containing the predicted variance.
        
    Returns:
        DataFrame with added columns: aleatoric, epistemic, total, uncertainty_type.
    """
    logger.info(f"Decomposing uncertainty for {len(df)} rows...")
    
    # Initialize new columns
    df['aleatoric'] = np.nan
    df['epistemic'] = np.nan
    df['total'] = np.nan
    df['uncertainty_type'] = ''
    
    # Identify ensemble methods that allow decomposition
    ensemble_methods = ['Deep Ensemble', 'MC Dropout']
    gp_methods = ['Sparse GP']
    
    # Process each method separately
    for method in df[method_col].unique():
        mask = df[method_col] == method
        subset = df.loc[mask]
        
        if method in ensemble_methods:
            # For ensemble methods:
            # We need to calculate epistemic as the variance of predictions across seeds
            # and aleatoric as the mean of predicted variances.
            
            # Group by sample_id to aggregate across seeds
            # Assuming the input df has a 'sample_id' column
            if 'sample_id' not in subset.columns:
                logger.warning(f"sample_id column missing for method {method}, skipping decomposition.")
                continue
                
            # Calculate epistemic: variance of predictions for each sample_id
            epistemic_series = subset.groupby('sample_id')[prediction_col].var()
            
            # Calculate aleatoric: mean of predicted variances for each sample_id
            aleatoric_series = subset.groupby('sample_id')[variance_col].mean()
            
            # Map back to the original dataframe
            # We assume the input df has one row per sample per seed, but we need to aggregate
            # However, the task requires outputting a decomposed file.
            # If the input `aggregated` file is already aggregated by sample_id (one row per sample),
            # then we cannot calculate epistemic (variance across seeds) from a single row.
            # 
            # RE-READING TASK: "This task MUST read the aggregated file... and apply the decomposition"
            # "Epistemic variance = variance of predictions across ensemble members for a single sample"
            #
            # If `results/uq_predictions_aggregated.csv` contains rows for *each seed* (e.g., 3 seeds),
            # then we can group by sample_id and calculate variance.
            # If it contains *one row per sample* (already aggregated mean), we cannot calculate variance.
            #
            # Given T025a says "aggregate them into a single intermediate file", it likely contains
            # all rows from all seeds. So we group by sample_id.
            
            df.loc[mask, 'epistemic'] = df.loc[mask, 'sample_id'].map(epistemic_series)
            df.loc[mask, 'aleatoric'] = df.loc[mask, 'sample_id'].map(aleatoric_series)
            df.loc[mask, 'total'] = df.loc[mask, 'aleatoric'] + df.loc[mask, 'epistemic']
            df.loc[mask, 'uncertainty_type'] = 'Mixed'
            
        elif method in gp_methods:
            # For Sparse GP: set aleatoric and epistemic to null
            df.loc[mask, 'aleatoric'] = None
            df.loc[mask, 'epistemic'] = None
            df.loc[mask, 'total'] = df.loc[mask, variance_col]
            df.loc[mask, 'uncertainty_type'] = 'Total'
        else:
            logger.warning(f"Unknown method {method}, skipping decomposition.")
            df.loc[mask, 'total'] = df.loc[mask, variance_col]
            df.loc[mask, 'uncertainty_type'] = 'Unknown'

    # Fill NaN in total for ensemble methods if calculation failed for some reason
    df['total'] = df['total'].fillna(df[variance_col])
    
    return df

def calculate_all_metrics(
    df: pd.DataFrame,
    y_true_col: str = 'y_true',
    method_col: str = 'method'
) -> Dict[str, float]:
    """
    Calculate all UQ metrics (ECE, Interval Score, Sharpness) for each method.
    
    Args:
        df: DataFrame with predictions and true values.
        y_true_col: Column name for true values.
        method_col: Column name for method identifier.
        
    Returns:
        Dictionary of metrics per method.
    """
    metrics = {}
    
    for method in df[method_col].unique():
        subset = df[df[method_col] == method]
        
        if len(subset) == 0:
            continue
        
        ece = expected_calibration_error(
            subset['y_true'].values,
            subset['prediction'].values,
            np.sqrt(subset['variance']).values # Assuming variance is stored, use std for ECE
        )
        
        interval_score_val = interval_score(
            subset['y_true'].values,
            subset['lower_90'].values,
            subset['upper_90'].values,
            alpha=0.1
        )
        
        sharpness_val = sharpness(
            subset['lower_90'].values,
            subset['upper_90'].values
        )
        
        metrics[method] = {
            'ece': ece,
            'interval_score': interval_score_val,
            'sharpness': sharpness_val
        }
        
    return metrics

def main():
    """
    Main entry point to load aggregated predictions, decompose uncertainty,
    and save the decomposed file.
    """
    input_path = 'results/uq_predictions_aggregated.csv'
    output_path = 'results/uq_predictions_decomposed.csv'
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Ensure T025a has completed.")
        return 1
    
    logger.info(f"Loading aggregated predictions from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['sample_id', 'method', 'prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input: {missing_cols}")
        return 1
    
    logger.info("Applying uncertainty decomposition...")
    df_decomposed = decompose_uncertainty(df)
    
    logger.info(f"Saving decomposed predictions to {output_path}")
    df_decomposed.to_csv(output_path, index=False)
    
    logger.info("Decomposition complete.")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())