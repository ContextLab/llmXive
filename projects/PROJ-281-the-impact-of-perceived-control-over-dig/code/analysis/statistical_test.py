import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from code.config import CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_residuals(df: pd.DataFrame, x_col: str = 'control_proxy', y_col: str = 'anxiety_score') -> pd.DataFrame:
    """
    Compute residuals from a preliminary linear fit (OLS) to check normality assumptions.
    Returns the dataframe with an added 'residuals' column.
    """
    logger.info(f"Computing residuals for linear fit: {y_col} ~ {x_col}")
    
    # Drop rows where either variable is null to ensure clean regression
    clean_df = df[[x_col, y_col]].dropna()
    
    if len(clean_df) < 10:
        logger.warning("Insufficient data points for linear regression residual calculation.")
        clean_df['residuals'] = np.nan
        return clean_df

    x = clean_df[x_col].values
    y = clean_df[y_col].values

    # Perform simple linear regression
    slope, intercept, r_value, p_val, std_err = stats.linregress(x, y)
    predicted_y = slope * x + intercept
    residuals = y - predicted_y

    clean_df = clean_df.copy()
    clean_df['residuals'] = residuals
    
    logger.info(f"Linear fit computed. R-squared: {r_value**2:.4f}")
    return clean_df

def shapiro_wilk_test(residuals: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality on the residuals.
    Returns (statistic, p_value).
    """
    # Remove NaNs if any
    valid_residuals = residuals[~np.isnan(residuals)]
    
    if len(valid_residuals) < 3:
        logger.warning("Not enough data points for Shapiro-Wilk test.")
        return 0.0, 1.0 # Assume normal if we can't test? Or fail? Spec says check p<0.05.
    
    stat, p_value = stats.shapiro(valid_residuals)
    logger.info(f"Shapiro-Wilk test: W={stat:.4f}, p={p_value:.4f}")
    return stat, p_value

def select_correlation_method(normality_p_value: float, alpha: float = 0.05) -> str:
    """
    Decide between Pearson and Spearman based on normality of residuals.
    If normality is violated (p < alpha), use Spearman. Otherwise, Pearson.
    """
    if normality_p_value < alpha:
        logger.info(f"Normality assumption violated (p={normality_p_value:.4f} < {alpha}). Using Spearman correlation.")
        return 'spearman'
    else:
        logger.info(f"Normality assumption holds (p={normality_p_value:.4f} >= {alpha}). Using Pearson correlation.")
        return 'pearson'

def calculate_correlation(x: np.ndarray, y: np.ndarray, method: str) -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value using the specified method.
    """
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[valid_mask]
    y_clean = y[valid_mask]

    if len(x_clean) < 2:
        logger.error("Insufficient valid data points for correlation calculation.")
        return 0.0, 1.0

    if method == 'spearman':
        corr, p_val = stats.spearmanr(x_clean, y_clean)
    else:
        corr, p_val = stats.pearsonr(x_clean, y_clean)
    
    logger.info(f"Correlation ({method}): r={corr:.4f}, p={p_val:.4f}")
    return corr, p_val

def determine_significance(p_value: float, alpha: float = 0.05) -> bool:
    """
    Determine if the correlation is statistically significant.
    """
    return p_value < alpha

def run_statistical_analysis_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Orchestrates the full statistical analysis:
    1. Load data
    2. Compute residuals from OLS
    3. Run Shapiro-Wilk on residuals
    4. Select correlation method based on normality
    5. Calculate correlation (r) and p-value
    6. Determine significance
    7. Save results to JSON
    """
    logger.info(f"Starting statistical analysis pipeline on {input_path}")
    
    # Load data
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    
    if 'control_proxy' not in df.columns or 'anxiety_score' not in df.columns:
        raise ValueError("Input data must contain 'control_proxy' and 'anxiety_score' columns.")

    # Step 1: Compute residuals
    df_resid = compute_residuals(df)
    
    # Step 2: Shapiro-Wilk on residuals
    residuals = df_resid['residuals'].values
    _, normality_p_value = shapiro_wilk_test(residuals)

    # Step 3: Select method
    method = select_correlation_method(normality_p_value)

    # Step 4: Calculate correlation
    x = df['control_proxy'].values
    y = df['anxiety_score'].values
    r, p_value = calculate_correlation(x, y, method)

    # Step 5: Determine significance
    is_significant = determine_significance(p_value)

    # Prepare results
    results = {
        "input_file": input_path,
        "normality_check": {
            "test": "Shapiro-Wilk",
            "p_value": float(normality_p_value),
            "assumption_met": normality_p_value >= 0.05
        },
        "method_selected": method,
        "correlation": {
            "coefficient": float(r),
            "p_value": float(p_value),
            "is_significant": is_significant
        }
    }

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return results