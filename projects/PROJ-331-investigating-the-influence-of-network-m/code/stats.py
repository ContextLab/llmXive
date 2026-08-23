import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import existing utilities from the project
# Note: We assume utils.py provides safe file operations and logging setup
# If specific imports are missing, they should be added to utils.py in a separate task
# For now, we use standard library and numpy/pandas directly

def load_subject_metrics_data(metrics_path="data/processed/subject_metrics.csv"):
    """Load subject metrics from CSV file."""
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    return pd.read_csv(metrics_path)

def compute_vif(df, predictor_var, control_var):
    """
    Compute Variance Inflation Factor (VIF) for a predictor variable.
    
    VIF = 1 / (1 - R^2) where R^2 is from regressing predictor on controls.
    """
    if predictor_var not in df.columns or control_var not in df.columns:
        raise ValueError(f"Columns {predictor_var} or {control_var} not found in dataframe")
    
    # Simple VIF calculation: regress predictor on control
    # Using numpy for linear regression
    X = df[control_var].values
    y = df[predictor_var].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    try:
        # Solve least squares
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        
        if len(residuals) == 0:
            # Perfect fit, R^2 = 1, VIF = infinity
            return float('inf')
        
        # Calculate R^2
        y_pred = X_with_intercept @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        
        if ss_tot == 0:
            return float('inf')
        
        r_squared = 1 - (ss_res / ss_tot)
        
        if r_squared >= 1.0:
            return float('inf')
        
        vif = 1 / (1 - r_squared)
        return vif
    except Exception as e:
        logging.error(f"Error computing VIF: {e}")
        return float('inf')

def check_vif_and_select_method(metrics, predictor_var='z_score', control_var='global_node_degree', threshold=5.0):
    """
    Check VIF for predictor variable and select analysis method.
    
    Args:
        metrics: DataFrame with subject metrics
        predictor_var: Name of the predictor variable (e.g., 'z_score')
        control_var: Name of the control variable (default: 'global_node_degree')
        threshold: VIF threshold above which to switch to permutation-only method
    
    Returns:
        dict with quality flags and selected method
    """
    # Check for zero variance in predictor
    if predictor_var not in metrics.columns:
        raise ValueError(f"Predictor variable '{predictor_var}' not found in metrics")
    
    unique_values = metrics[predictor_var].nunique()
    zero_variance = unique_values <= 1
    
    # Compute VIF if not zero variance
    if not zero_variance:
        vif_value = compute_vif(metrics, predictor_var, control_var)
    else:
        vif_value = float('inf')
    
    # Select method based on VIF
    if vif_value > threshold:
        method_selected = "permutation_only"
    else:
        method_selected = "partial_correlation_and_permutation"
    
    # Prepare result
    result = {
        "zero_variance": zero_variance,
        "vif_value": vif_value if not np.isinf(vif_value) else None,
        "method_selected": method_selected
    }
    
    # Save quality flags
    output_path = "data/processed/quality_flags.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logging.info(f"VIF check completed: zero_variance={zero_variance}, vif={vif_value}, method={method_selected}")
    return result

def report_insufficient_variance(motif_id):
    """
    Generate a report entry for motifs with insufficient variance.
    
    This function creates a structured entry that can be included in the PDF report
    to explicitly state that a motif has insufficient variance for statistical testing.
    
    Args:
        motif_id: The identifier of the motif with insufficient variance
    
    Returns:
        dict with report entry information
    """
    entry = {
        "motif_id": motif_id,
        "status": "insufficient_variance",
        "message": f"Insufficient variance for motif {motif_id}. Statistical testing skipped.",
        "reason": "The motif z-scores have zero or near-zero variance across subjects, making correlation analysis impossible.",
        "recommendation": "Consider aggregating with similar motifs or increasing sample size.",
        "pdf_entry_type": "insufficient_variance_report",
        "display_text": f"Motif {motif_id}: Insufficient Variance"
    }
    
    logging.info(f"Report generated for insufficient variance motif: {motif_id}")
    return entry

def main():
    """Main execution function for stats module."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example usage
    try:
        # Load metrics (if available)
        if os.path.exists("data/processed/subject_metrics.csv"):
            metrics = load_subject_metrics_data()
            
            # Check VIF and select method
            result = check_vif_and_select_method(metrics)
            logging.info(f"Method selection result: {result}")
            
            # Example of reporting insufficient variance (if needed)
            if result.get("zero_variance"):
                entry = report_insufficient_variance("example_motif")
                logging.info(f"Insufficient variance report: {entry}")
        else:
            logging.warning("subject_metrics.csv not found. Skipping analysis.")
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()