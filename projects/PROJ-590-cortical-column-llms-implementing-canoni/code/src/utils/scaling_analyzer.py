import os
import json
import logging
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from scipy import stats

logger = logging.getLogger(__name__)

def load_scaling_data(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load scaling data from CSV file.
    
    Expects CSV with columns: columns, params, mae, time_sec
    
    Returns:
        Tuple of (params_array, mae_array)
    """
    import pandas as pd
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Scaling data file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    required_cols = ['params', 'mae']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {csv_path}")
    
    params = df['params'].values.astype(float)
    mae = df['mae'].values.astype(float)
    
    # Filter out zero or negative values for log-log regression
    valid_mask = (params > 0) & (mae > 0)
    if not np.all(valid_mask):
        logger.warning(f"Filtered {np.sum(~valid_mask)} rows with non-positive params or mae")
        params = params[valid_mask]
        mae = mae[valid_mask]
    
    if len(params) < 2:
        raise ValueError("Need at least 2 valid data points for regression")
    
    return params, mae

def perform_log_log_regression(params: np.ndarray, mae: np.ndarray) -> Dict[str, Any]:
    """
    Perform log-log linear regression: log(MAE) ~ beta * log(params)
    
    Returns:
        Dict containing:
            - beta: scaling exponent
            - intercept: regression intercept
            - r_squared: coefficient of determination
            - p_value: p-value for the slope
            - std_err: standard error of the slope
    """
    log_params = np.log(params)
    log_mae = np.log(mae)
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_mae)
    
    return {
        'beta': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_value ** 2),
        'p_value': float(p_value),
        'std_err': float(std_err)
    }

def classify_trend(beta: float, tolerance: float = 0.1) -> str:
    """
    Classify the scaling trend based on the exponent beta.
    
    For log(MAE) ~ beta * log(params):
        - beta < 0: sublinear (error decreases as params increase)
        - beta ≈ 0: linear (no scaling relationship)
        - beta > 0: superlinear (error increases as params increase - unusual)
    
    Args:
        beta: The scaling exponent
        tolerance: Threshold for considering beta as zero
        
    Returns:
        One of: "sublinear", "linear", "superlinear"
    """
    if beta < -tolerance:
        return "sublinear"
    elif beta > tolerance:
        return "superlinear"
    else:
        return "linear"

def generate_scaling_law_report(
    csv_path: str,
    output_path: str,
    regression_results: Dict[str, Any],
    trend_type: str,
    metric_used: str = "MAE"
) -> None:
    """
    Generate a markdown report summarizing the scaling law analysis.
    
    Args:
        csv_path: Path to the input scaling data CSV
        output_path: Path where the report will be written
        regression_results: Dict from perform_log_log_regression
        trend_type: Classification of the trend
        metric_used: The metric used for analysis (e.g., "MAE")
    """
    beta = regression_results['beta']
    r_squared = regression_results['r_squared']
    p_value = regression_results['p_value']
    
    report_lines = [
        "# Scaling Law Analysis Report",
        "",
        "## Summary",
        "",
        f"This report analyzes the scaling behavior of the cortical column LLM model.",
        f"The metric used for analysis is **{metric_used}**.",
        "",
        "## Scaling Exponent",
        "",
        f"The scaling law is modeled as: `log({metric_used}) ~ beta * log(Parameter Count)`",
        "",
        f"**Calculated Beta (scaling exponent):** {beta:.6f}",
        "",
        f"**Trend Classification:** {trend_type}",
        "",
        "## Interpretation",
        "",
    ]
    
    if trend_type == "sublinear":
        report_lines.append(
            "The negative scaling exponent indicates that increasing the parameter count "
            "leads to a reduction in error. This is the expected behavior for scaling laws "
            "in machine learning models, where more parameters generally improve performance."
        )
    elif trend_type == "linear":
        report_lines.append(
            "The scaling exponent is near zero, suggesting no clear scaling relationship "
            "between parameter count and error. This may indicate saturation effects or "
            "insufficient data points to establish a trend."
        )
    else:  # superlinear
        report_lines.append(
            "The positive scaling exponent is unusual and suggests that increasing "
            "parameter count leads to higher error. This may indicate overfitting, "
            "optimization difficulties, or issues with the model architecture."
        )
    
    report_lines.extend([
        "",
        "## Statistical Metrics",
        "",
        f"- **R-squared:** {r_squared:.6f}",
        f"- **P-value:** {p_value:.6e}",
        f"- **Standard Error:** {regression_results['std_err']:.6f}",
        "",
        "## Data Source",
        "",
        f"Input data: `{csv_path}`",
        "",
        "## Conclusion",
        "",
        f"The scaling exponent beta = {beta:.6f} indicates a {trend_type} relationship "
        f"between parameter count and {metric_used}. This quantifies the efficiency of "
        "scaling the cortical column architecture."
    ])
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write report
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Scaling law report written to {output_path}")

def main() -> None:
    """
    Main entry point for the scaling analyzer script.
    
    Reads scaling data from data/results/scaling_law.csv,
    performs log-log regression, and writes the report to
    data/results/scaling_law_report.md.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    csv_path = project_root / "data" / "results" / "scaling_law.csv"
    output_path = project_root / "data" / "results" / "scaling_law_report.md"
    
    logger.info(f"Loading scaling data from {csv_path}")
    
    try:
        params, mae = load_scaling_data(str(csv_path))
        logger.info(f"Loaded {len(params)} data points")
        
        logger.info("Performing log-log regression")
        regression_results = perform_log_log_regression(params, mae)
        
        trend_type = classify_trend(regression_results['beta'])
        logger.info(f"Scaling trend classified as: {trend_type}")
        
        logger.info(f"Generating report at {output_path}")
        generate_scaling_law_report(
            csv_path=str(csv_path),
            output_path=str(output_path),
            regression_results=regression_results,
            trend_type=trend_type,
            metric_used="MAE"
        )
        
        logger.info("Scaling analysis completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
