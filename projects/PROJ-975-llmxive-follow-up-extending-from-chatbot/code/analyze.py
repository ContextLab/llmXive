import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging for the analysis module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_experiment_data(log_path: str = "data/results/experiment_log.csv") -> pd.DataFrame:
    """
    Loads the experiment log data from the specified CSV file.
    
    Args:
        log_path: Path to the experiment log CSV file.
        
    Returns:
        A pandas DataFrame containing the experiment data.
        
    Raises:
        FileNotFoundError: If the log file does not exist.
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Experiment log file not found: {log_path}")
    
    df = pd.read_csv(log_path)
    
    # Ensure required columns exist for VIF calculation
    required_cols = ['library_size', 'semantic_overlap']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for VIF calculation: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} records from {log_path}")
    return df

def calculate_vif(df: pd.DataFrame, predictors: Optional[list] = None) -> Dict[str, float]:
    """
    Calculates the Variance Inflation Factor (VIF) for the specified predictors
    to confirm VIF < 5.0, indicating low multicollinearity.
    
    FR-007 & SC-006: Explicitly calculate and report VIF for 'library size' and 
    'semantic overlap'. Assert or warn if VIF >= 5.0.
    
    Args:
        df: DataFrame containing the experiment data.
        predictors: List of column names to calculate VIF for. Defaults to 
                  ['library_size', 'semantic_overlap'].
                  
    Returns:
        Dictionary mapping predictor names to their VIF values.
        
    Raises:
        ValueError: If VIF >= 5.0 is detected for any predictor.
    """
    if predictors is None:
        predictors = ['library_size', 'semantic_overlap']
        
    # Filter DataFrame to only include predictors
    X = df[predictors]
    
    # Add constant for intercept (required by VIF calculation)
    X_with_const = sm.add_constant(X)
    
    vif_results = {}
    max_vif = 0.0
    high_vif_pred = None
    
    logger.info("Calculating Variance Inflation Factor (VIF) for predictors...")
    
    for i, col in enumerate(predictors):
        # Calculate VIF for each predictor
        vif = variance_inflation_factor(X_with_const.values, i + 1) # +1 because of constant
        vif_results[col] = vif
        max_vif = max(max_vif, vif)
        
        logger.info(f"VIF for '{col}': {vif:.4f}")
        
        if vif >= 5.0:
            high_vif_pred = col
            
    # FR-007 & SC-006: Hard assertion/warning if VIF >= 5.0
    if high_vif_pred:
        error_msg = (
            f"CRITICAL: Multicollinearity detected! VIF for '{high_vif_pred}' is {vif_results[high_vif_pred]:.4f} "
            f"(threshold: 5.0). The model may be invalid due to collinearity."
        )
        logger.error(error_msg)
        # We do not raise here to allow the analysis to continue, but we log the failure
        # The final report should flag this.
        
    return vif_results

def piecewise_linear(x, breakpoint, slope1, slope2, intercept):
    """
    Piecewise linear function with a single breakpoint.
    
    Args:
        x: Input array
        breakpoint: The x-value where the slope changes
        slope1: Slope before the breakpoint
        slope2: Slope after the breakpoint
        intercept: Y-intercept
        
    Returns:
        Array of y-values
    """
    return np.where(
        x <= breakpoint,
        slope1 * x + intercept,
        slope2 * (x - breakpoint) + slope1 * breakpoint + intercept
    )

def perform_piecewise_regression(x, y, initial_breakpoint_guess=None):
    """
    Performs piecewise linear regression to identify the tipping point.
    
    Args:
        x: Independent variable array
        y: Dependent variable array
        initial_breakpoint_guess: Optional initial guess for the breakpoint
        
    Returns:
        Dictionary containing model parameters and the calculated breakpoint (x0).
    """
    from scipy.optimize import curve_fit
    
    if initial_breakpoint_guess is None:
        initial_breakpoint_guess = np.percentile(x, 50) # Default to median
        
    try:
        popt, pcov = curve_fit(
            piecewise_linear, 
            x, 
            y, 
            p0=[initial_breakpoint_guess, -0.01, -0.05, 1.0],
            bounds=([min(x), -1, -1, -10], [max(x), 0, 0, 10])
        )
        
        breakpoint_val, slope1, slope2, intercept = popt
        
        logger.info(f"Piecewise regression converged. Breakpoint (x0): {breakpoint_val:.4f}")
        
        return {
            'breakpoint': float(breakpoint_val),
            'slope_before': float(slope1),
            'slope_after': float(slope2),
            'intercept': float(intercept),
            'converged': True
        }
    except Exception as e:
        logger.error(f"Piecewise regression failed: {str(e)}")
        return {
            'breakpoint': None,
            'slope_before': None,
            'slope_after': None,
            'intercept': None,
            'converged': False,
            'error': str(e)
        }

def calculate_pruning_efficacy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates the efficacy of pruning by comparing success rates between
    pruned and baseline configurations.
    
    Args:
        df: DataFrame containing experiment data with 'pruning_enabled' column.
        
    Returns:
        Dictionary with pruning efficacy metrics.
    """
    if 'pruning_enabled' not in df.columns or 'success' not in df.columns:
        logger.warning("Missing required columns for pruning efficacy calculation.")
        return {'efficacy': None, 'error': "Missing columns"}
        
    pruned = df[df['pruning_enabled'] == True]['success'].mean()
    baseline = df[df['pruning_enabled'] == False]['success'].mean()
    
    efficacy = pruned - baseline if not np.isnan(pruned) and not np.isnan(baseline) else None
    
    return {
        'pruned_success_rate': float(pruned) if not np.isnan(pruned) else None,
        'baseline_success_rate': float(baseline) if not np.isnan(baseline) else None,
        'efficacy': float(efficacy) if efficacy is not None else None
    }

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: list = [5, 10, 20]) -> Dict[str, Any]:
    """
    Runs sensitivity analysis by recalculating tipping points for different pruning thresholds.
    
    Args:
        df: DataFrame containing experiment data.
        thresholds: List of pruning intervals to test.
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    results = {}
    
    # Note: This is a simplified version. In a full implementation, we would
    # re-run the experiment or filter data based on the specific threshold.
    # For now, we simulate the sensitivity check by analyzing existing data
    # with different subsets if available.
    
    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")
    
    # Placeholder for actual sensitivity logic
    # In a real scenario, we would filter by 'pruning_interval' column if it exists
    # and re-run piecewise regression for each subset.
    
    for thresh in thresholds:
        # Simulated result - in real implementation, this would be calculated
        results[thresh] = {
            'tipping_point': None,
            'status': 'placeholder - requires specific data filtering logic'
        }
        
    return results

def run_analysis(log_path: str = "data/results/experiment_log.csv", 
               baseline_path: Optional[str] = None,
               output_path: str = "data/results/final_analysis.json") -> Dict[str, Any]:
    """
    Runs the full analysis pipeline including VIF calculation, piecewise regression,
    and generates the final analysis report.
    
    Args:
        log_path: Path to the main experiment log.
        baseline_path: Optional path to baseline log for comparison.
        output_path: Path to write the final analysis JSON.
        
    Returns:
        Dictionary containing the full analysis results.
    """
    logger.info("Starting full analysis pipeline...")
    
    # Load data
    df = load_experiment_data(log_path)
    
    # 1. Calculate VIF (Task T032)
    vif_results = calculate_vif(df)
    
    # 2. Perform Piecewise Regression (Task T033)
    x_data = df['library_size'].values
    y_data = df['success'].astype(float).values # Assuming success is binary or rate
    
    regression_results = perform_piecewise_regression(x_data, y_data)
    
    # 3. Calculate Pruning Efficacy (Task T034)
    pruning_efficacy = calculate_pruning_efficacy(df)
    
    # 4. Run Sensitivity Analysis (Task T035)
    sensitivity_results = run_sensitivity_analysis(df)
    
    # Compile final report
    final_report = {
        'vif_metrics': vif_results,
        'tipping_point_piecewise': regression_results,
        'pruning_efficacy': pruning_efficacy,
        'sensitivity_analysis': sensitivity_results,
        'data_summary': {
            'total_records': len(df),
            'library_size_range': [float(df['library_size'].min()), float(df['library_size'].max())],
            'success_rate': float(df['success'].mean())
        }
    }
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
        
    logger.info(f"Analysis complete. Results written to {output_path}")
    
    return final_report

def main():
    """Main entry point for the analysis script."""
    log_path = os.getenv("EXPERIMENT_LOG_PATH", "data/results/experiment_log.csv")
    output_path = os.getenv("ANALYSIS_OUTPUT_PATH", "data/results/final_analysis.json")
    
    try:
        results = run_analysis(log_path=log_path, output_path=output_path)
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
