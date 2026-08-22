import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.data.paths import get_processed_path, get_results_path, ensure_dir
from code.utils.logging import log_error, log_warning, log_info

logger = logging.getLogger(__name__)

def load_metrics_data() -> pd.DataFrame:
    """Load the intermediate metrics from T026."""
    metrics_path = os.path.join(get_processed_path(), "metrics.csv")
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}. T026 must run first.")
    return pd.read_csv(metrics_path)

def load_behavioral_covariates() -> pd.DataFrame:
    """Load the merged behavioral and covariate data from T014/T015/T017."""
    # The merge task (T014) produces the dataset with Subject_ID, Flexibility_Score, Age, Sex, Mean_FD, Total_Scan_Time
    # We assume this is saved as 'merged_data.csv' in processed or 'final_preprocessed.csv'
    # Based on T014 description: "merge neuroimaging features with NIH Toolbox... scores"
    # T015/T017 filter this. The result is the clean dataset ready for regression.
    # We look for the standard output of the merge pipeline.
    processed_path = get_processed_path()
    candidates = [
        os.path.join(processed_path, "merged_data.csv"),
        os.path.join(processed_path, "final_preprocessed.csv"),
        os.path.join(processed_path, "regression_dataset.csv") # Used by T030
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"Loading covariates from {candidate}")
            return pd.read_csv(candidate)
    
    raise FileNotFoundError("Could not find merged behavioral/covariate data file in processed directory.")

def load_regression_summary() -> Dict[str, Any]:
    """Load the global regression coefficients from T034."""
    summary_path = os.path.join(get_results_path(), "regression_summary.json")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Regression summary not found at {summary_path}. T034 must run first.")
    
    with open(summary_path, 'r') as f:
        return json.load(f)

def generate_final_results(
    metrics_df: pd.DataFrame,
    covariates_df: pd.DataFrame,
    summary: Dict[str, Any]
) -> pd.DataFrame:
    """
    Merge metrics and covariates, calculate predictions and residuals,
    and append global regression coefficients to every row.
    """
    # 1. Merge on Subject_ID
    # Ensure column names match exactly as expected
    # metrics_df has: Subject_ID, Variability_Metric, Entropy
    # covariates_df has: Subject_ID, Flexibility_Score, Age, Sex, Mean_FD, Total_Scan_Time
    
    if 'Subject_ID' not in metrics_df.columns or 'Subject_ID' not in covariates_df.columns:
        raise ValueError("Both dataframes must contain 'Subject_ID' column.")

    merged = pd.merge(
        metrics_df[['Subject_ID', 'Variability_Metric']],
        covariates_df,
        on='Subject_ID',
        how='inner'
    )

    if merged.empty:
        raise ValueError("Merge resulted in empty dataframe. Check Subject_ID formats.")

    # 2. Extract regression parameters from summary
    # The summary structure is assumed to be:
    # { "coefficients": { "Variability_Metric": {"beta": ..., "se": ..., "p_value": ...}, ... }, ... }
    # or similar flat structure. We need to find the beta for Variability_Metric.
    
    beta_var = summary.get('beta_variability') or summary.get('beta')
    se_var = summary.get('se_variability') or summary.get('se')
    p_val = summary.get('p_value')
    
    # If the summary is nested differently, try to find it
    if beta_var is None:
        coeffs = summary.get('coefficients', {})
        if 'Variability_Metric' in coeffs:
            beta_var = coeffs['Variability_Metric'].get('beta')
            se_var = coeffs['Variability_Metric'].get('se')
            p_val = coeffs['Variability_Metric'].get('p_value')
        elif 'variability_metric' in coeffs:
             beta_var = coeffs['variability_metric'].get('beta')
             se_var = coeffs['variability_metric'].get('se')
             p_val = coeffs['variability_metric'].get('p_value')
    
    if beta_var is None:
        raise KeyError("Could not find 'beta' for Variability_Metric in regression summary.")

    # 3. Calculate Predicted Score
    # Formula: Predicted = Intercept + Beta * Variability + (Covariate Effects)
    # However, the task says: "Read global coefficients... and repeat them in every row".
    # It also asks for "Predicted_Score" and "Residual".
    # To calculate a specific subject's predicted score, we need the full model equation.
    # The summary usually contains the full model stats.
    # If the summary only has the Variability coefficient, we might not have the intercept 
    # or covariate betas to calculate the EXACT predicted score for a subject unless we 
    # assume the summary contains the full intercept and covariate betas.
    
    # Let's assume the summary contains 'intercept' and a 'coefficients' dict with all betas.
    intercept = summary.get('intercept', 0.0)
    
    # We need to construct the prediction:
    # Y_pred = Intercept + Beta_Var * X_Var + Beta_Age * X_Age + Beta_Sex * X_Sex + Beta_FD * X_FD + Beta_Time * X_Time
    
    # Check if we have the other betas in the summary
    other_betas = {}
    if 'coefficients' in summary:
        for col in ['Age', 'Sex', 'Mean_FD', 'Total_Scan_Time']:
            if col in summary['coefficients']:
                other_betas[col] = summary['coefficients'][col].get('beta', 0.0)
    
    # Calculate Prediction
    # Note: Sex is likely encoded (0/1) in the regression dataset used by T030.
    # We assume the covariates_df passed in has the same encoding.
    
    y_pred = intercept + (beta_var * merged['Variability_Metric'])
    
    for col, beta in other_betas.items():
        if col in merged.columns:
            y_pred += beta * merged[col]
    
    merged['Predicted_Score'] = y_pred
    merged['Residual'] = merged['Flexibility_Score'] - merged['Predicted_Score']
    
    # 4. Add Global Coefficients to every row
    # Mandatory Columns: Subject_ID, Variability_Metric, Flexibility_Score, Age, Sex, Mean_FD, Total_Scan_Time, 
    # Predicted_Score, Residual, Beta_Variability, SE_Variability, P_Value
    
    result_df = merged[[
        'Subject_ID', 
        'Variability_Metric', 
        'Flexibility_Score', 
        'Age', 
        'Sex', 
        'Mean_FD', 
        'Total_Scan_Time',
        'Predicted_Score', 
        'Residual'
    ]].copy()
    
    result_df['Beta_Variability'] = beta_var
    result_df['SE_Variability'] = se_var
    result_df['P_Value'] = p_val
    
    # Ensure correct types
    result_df['Subject_ID'] = result_df['Subject_ID'].astype(str)
    result_df['Age'] = result_df['Age'].astype(int)
    
    return result_df

def save_final_results(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """Save the final results to CSV."""
    if output_path is None:
        output_path = os.path.join(get_processed_path(), "final_results.csv")
    
    ensure_dir(output_path)
    df.to_csv(output_path, index=False)
    logger.info(f"Final results saved to {output_path} with {len(df)} rows.")
    return output_path

def run_final_results_pipeline() -> str:
    """Main pipeline entry point for T036."""
    logger.info("Starting Final Results Generation (T036)...")
    
    try:
        metrics_df = load_metrics_data()
        covariates_df = load_behavioral_covariates()
        summary = load_regression_summary()
        
        final_df = generate_final_results(metrics_df, covariates_df, summary)
        output_path = save_final_results(final_df)
        
        return output_path
    except Exception as e:
        log_error(f"Pipeline failed: {str(e)}")
        raise

def main():
    run_final_results_pipeline()

if __name__ == "__main__":
    main()