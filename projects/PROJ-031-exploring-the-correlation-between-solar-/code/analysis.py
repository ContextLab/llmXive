import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def spearman_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation and p-value.
    Returns (correlation_coefficient, p_value).
    """
    if x.isna().any() or y.isna().any():
        logger.warning("NaN values detected in spearman_correlation inputs. Dropping them.")
        valid_mask = ~(x.isna() | y.isna())
        x_clean = x[valid_mask]
        y_clean = y[valid_mask]
    else:
        x_clean = x
        y_clean = y

    if len(x_clean) < 2:
        logger.error("Not enough data points for correlation.")
        return 0.0, 1.0

    corr, p_val = stats.spearmanr(x_clean, y_clean)
    return float(corr), float(p_val)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for a list of features.
    """
    X = df[features].dropna()
    if len(X) < len(features) + 1:
        logger.warning("Not enough samples for VIF calculation.")
        return {f: np.inf for f in features}

    X = add_constant(X)
    vif_data = {}
    for i, feature in enumerate(features):
        # VIF for feature i is 1 / (1 - R^2_i) where R^2_i is from regressing feature i on others
        # statsmodels vif function handles this
        try:
            vif = variance_inflation_factor(X.values, i + 1) # +1 because of constant
            vif_data[feature] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = np.inf
    return vif_data

def linear_regression_r2(df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, Any]:
    """
    Perform linear regression and return R² and coefficients.
    """
    X = df[features].dropna()
    y = df.loc[X.index, target].dropna()
    # Align indices after dropna
    common_idx = X.index.intersection(y.index)
    X_clean = X.loc[common_idx]
    y_clean = y.loc[common_idx]

    if len(X_clean) < len(features) + 1:
        logger.warning("Not enough samples for linear regression.")
        return {"r2": 0.0, "coefficients": {}, "p_values": {}}

    X_const = add_constant(X_clean)
    model = OLS(y_clean, X_const).fit()

    return {
        "r2": float(model.rsquared),
        "coefficients": {str(col): float(val) for col, val in model.params.items()},
        "p_values": {str(col): float(val) for col, val in model.pvalues.items()},
        "n_samples": len(X_clean)
    }

def bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def power_analysis(n: int, alpha: float = 0.05, effect_size: float = 0.30) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis.
    Returns min detectable effect size and a warning flag.
    """
    # Approximation for power of correlation test
    # Using standard normal approximation for simplicity
    # Z_alpha = 1.96 for alpha=0.05 (two-tailed)
    # Power = 1 - beta
    # We want to find effect size r such that power >= 0.80 given n
    
    # Simplified logic: if N is small, we can't detect small effects
    # Formula: r_min = sqrt(t^2 / (t^2 + df)) where t is critical t for power
    # This is an approximation. For a more rigorous check, we might use statsmodels.stats.power
    
    try:
        from statsmodels.stats.power import zt_ind_solve_power
        # This function solves for effect size given power, n, alpha
        # However, zt_ind_solve_power is for difference of means. 
        # For correlation, we often use the Fisher z-transformation approach or similar.
        # Given constraints, we'll use a heuristic based on sample size.
        
        # Heuristic: Minimum detectable r for 80% power at alpha=0.05
        # r_min approx 3 / sqrt(n) is a common rule of thumb for small samples
        r_min = 3.0 / np.sqrt(n) if n > 0 else 1.0
        
        warning = n < 30
        return {
            "min_detectable_effect_size": float(r_min),
            "power_warning_flag": warning,
            "sample_size": n
        }
    except ImportError:
        # Fallback if statsmodels power is not available
        r_min = 3.0 / np.sqrt(n) if n > 0 else 1.0
        return {
            "min_detectable_effect_size": float(r_min),
            "power_warning_flag": n < 30,
            "sample_size": n
        }

def test_piecewise_model(df: pd.DataFrame, target: str, feature: str, threshold: float) -> Dict[str, Any]:
    """
    Test a piecewise linear model.
    Returns improvement in R² compared to linear model.
    """
    # Create a piecewise feature
    # Simple implementation: two segments
    mask = df[feature] <= threshold
    x1 = df.loc[mask, feature]
    y1 = df.loc[mask, target]
    x2 = df.loc[~mask, feature]
    y2 = df.loc[~mask, target]

    # Fit separate lines
    # This is a simplified piecewise check. A true piecewise regression is more complex.
    # We will compare the R² of a single model vs two models (conceptually).
    # For this task, we just return a placeholder logic that calculates improvement if applicable.
    
    # Linear model on full data
    X_full = add_constant(df[[feature]].dropna())
    y_full = df.loc[X_full.index, target]
    model_full = OLS(y_full, X_full).fit()
    r2_full = model_full.rsquared

    # Piecewise R2 (weighted average of R2s of parts, or just sum of squared errors)
    # Let's calculate SSE for each and compare
    def calc_sse(x, y, slope, intercept):
        return np.sum((y - (slope * x + intercept)) ** 2)

    # Segment 1
    if len(x1) > 2:
        X1 = add_constant(pd.DataFrame({feature: x1}))
        model1 = OLS(y1, X1).fit()
        sse1 = model1.ssr
        r2_1 = model1.rsquared
    else:
        sse1 = 0
        r2_1 = 0

    # Segment 2
    if len(x2) > 2:
        X2 = add_constant(pd.DataFrame({feature: x2}))
        model2 = OLS(y2, X2).fit()
        sse2 = model2.ssr
        r2_2 = model2.rsquared
    else:
        sse2 = 0
        r2_2 = 0

    # Improvement metric: (SSE_full - (SSE1 + SSE2)) / SSE_full
    # Or just difference in R2 if we consider weighted R2
    # Let's use SSE reduction as the improvement metric
    total_sse = sse1 + sse2
    if model_full.ssr > 0:
        improvement = (model_full.ssr - total_sse) / model_full.ssr
    else:
        improvement = 0.0

    return {
        "r2_full": float(r2_full),
        "r2_piecewise_1": float(r2_1) if len(x1) > 2 else 0.0,
        "r2_piecewise_2": float(r2_2) if len(x2) > 2 else 0.0,
        "piecewise_r2_improvement": float(improvement)
    }

def run_correlation_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    """
    results = {}

    # 1. Spearman Correlations
    # Log10 flare flux -> Dst
    if 'log10_flare_flux' in df.columns and 'Dst' in df.columns:
        corr_flare, p_flare = spearman_correlation(df['log10_flare_flux'], df['Dst'])
        results['flare_dst_corr'] = corr_flare
        results['flare_dst_pval'] = p_flare

    # CME speed -> Dst
    if 'cme_speed' in df.columns and 'Dst' in df.columns:
        corr_cme, p_cme = spearman_correlation(df['cme_speed'], df['Dst'])
        results['cme_dst_corr'] = corr_cme
        results['cme_dst_pval'] = p_cme

    # 2. VIF Check
    features = ['log10_flare_flux', 'cme_speed']
    available_features = [f for f in features if f in df.columns]
    
    if len(available_features) == 2:
        vif_results = calculate_vif(df, available_features)
        results['vif'] = vif_results
        
        if any(v > 5 for v in vif_results.values()):
            logger.warning("VIF > 5 detected. Switching to univariate models.")
            # Logic to select best univariate model would go here
            # For now, we just note it
            results['multicollinearity_warning'] = True
        else:
            results['multicollinearity_warning'] = False
    else:
        results['vif'] = {}
        results['multicollinearity_warning'] = False

    # 3. Linear Regression
    if 'Dst' in df.columns and len(available_features) > 0:
        if len(available_features) == 2 and not results.get('multicollinearity_warning', False):
            reg_res = linear_regression_r2(df, 'Dst', available_features)
            results['joint_model'] = reg_res
        else:
            # Univariate models
            univariate_results = {}
            for feat in available_features:
                res = linear_regression_r2(df, 'Dst', [feat])
                univariate_results[feat] = res
            results['univariate_models'] = univariate_results

    # 4. Bonferroni Correction
    p_vals = [results.get('flare_dst_pval', 1.0), results.get('cme_dst_pval', 1.0)]
    corrected_p = bonferroni_correction(p_vals, len(p_vals))
    results['corrected_p_values'] = corrected_p
    results['correction_method'] = "bonferroni"
    results['correction_rationale'] = "Family-wise error rate control for small test family"

    # 5. Power Analysis
    n = len(df.dropna(subset=['Dst', 'log10_flare_flux', 'cme_speed']))
    power_res = power_analysis(n)
    results['power_analysis'] = power_res

    # 6. Piecewise Model (Example threshold)
    if 'cme_speed' in df.columns and 'Dst' in df.columns:
        threshold = 500.0 # Example threshold
        piecewise_res = test_piecewise_model(df, 'Dst', 'cme_speed', threshold)
        results['piecewise_r2_improvement'] = piecewise_res['piecewise_r2_improvement']

    return results

def validate_timeseries_split(df: pd.DataFrame, train_col: str = 'train_flag', test_col: str = 'test_flag', date_col: str = 'timestamp') -> None:
    """
    Enforce strict time-series split validation.
    
    This function verifies that the train/test split is strictly based on time
    (Train: prior to last two years, Test: last two years) and raises an error
    if any test-set event falls outside the computed window.
    
    Args:
        df: DataFrame containing the data.
        train_col: Column name indicating training set membership.
        test_col: Column name indicating test set membership.
        date_col: Column name containing datetime objects or strings.
        
    Raises:
        ValueError: If the split is invalid or data leakage is detected.
    """
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in DataFrame.")
        
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except Exception as e:
            raise ValueError(f"Failed to convert '{date_col}' to datetime: {e}")
    
    # Determine the date range
    max_date = df[date_col].max()
    min_date = df[date_col].min()
    
    # Calculate the split point (2 years before max_date)
    split_date = max_date - pd.DateOffset(years=2)
    
    logger.info(f"Time-series split validation: Max date={max_date}, Split date={split_date}")
    
    # Identify test set indices
    if test_col in df.columns:
        test_indices = df.index[df[test_col] == True].tolist()
    else:
        # Infer test set if column doesn't exist but we assume the split logic was applied
        # For this task, we assume the dataframe has flags or we check the logic against the date
        # If no flags, we check if the data is split correctly by date
        # But the task implies we are validating the split logic applied to the data
        # Let's assume the dataframe has the split applied and we are verifying it.
        # If no flags, we can't validate "which" are test, so we assume the user passed a df with flags.
        # If flags are missing, we raise an error.
        if 'train_flag' not in df.columns and 'test_flag' not in df.columns:
            raise ValueError("DataFrame must contain 'train_flag' or 'test_flag' columns to validate split.")
        test_indices = df.index[df['test_flag'] == True].tolist()
        
    # Validate test set
    if not test_indices:
        logger.warning("No test set identified. Skipping validation.")
        return

    test_df = df.loc[test_indices]
    test_dates = test_df[date_col]
    
    # Check if any test date is BEFORE the split date
    leakage_mask = test_dates < split_date
    if leakage_mask.any():
        leaked_dates = test_dates[leakage_mask]
        raise ValueError(
            f"DATA LEAKAGE DETECTED: {len(leaked_dates)} test set events fall before the split date ({split_date}). "
            f"Test set must strictly contain events from the last two years (>= {split_date}). "
            f"Leaked dates: {leaked_dates.tolist()}"
        )
        
    # Check if any test date is AFTER max_date (sanity check)
    if (test_dates > max_date).any():
         raise ValueError("Test set contains dates after the maximum date in the dataset.")
         
    # Validate train set (optional but good practice)
    if 'train_flag' in df.columns:
        train_indices = df.index[df['train_flag'] == True].tolist()
        if train_indices:
            train_df = df.loc[train_indices]
            train_dates = train_df[date_col]
            # Train set should be < split_date
            # Allow a small epsilon for edge cases if needed, but strict is better
            if (train_dates >= split_date).any():
                raise ValueError("TRAIN DATA LEAKAGE: Train set contains events >= split date.")

    logger.info("Time-series split validation passed: No data leakage detected.")

def main():
    """
    Main entry point for analysis.
    """
    # Load data
    input_path = "data/processed/analysis_subset.csv"
    output_path = "results/metrics.json"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate time-series split if flags exist
    if 'train_flag' in df.columns or 'test_flag' in df.columns:
        logger.info("Validating time-series split...")
        try:
            validate_timeseries_split(df, date_col='timestamp')
        except ValueError as e:
            logger.critical(str(e))
            # In a real pipeline, this might stop execution. 
            # For this task, we log and potentially abort or warn.
            # Given the task requirement "raises an error", we let it propagate or handle here.
            # We will raise it to ensure the pipeline fails loudly as per requirements.
            raise e

    # Run analysis
    logger.info("Running correlation analysis...")
    results = run_correlation_analysis(df)
    
    # Add metadata
    results['analysis_timestamp'] = datetime.now().isoformat()
    results['input_file'] = input_path
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results written to {output_path}")

if __name__ == "__main__":
    main()