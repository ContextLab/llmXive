import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
from typing import Dict, List, Any, Optional
import logging
import json
import os
import matplotlib.pyplot as plt

def run_regression_analysis(dataset_path: str) -> Dict[str, Any]:
    """
    Perform linear regression with perspective_score as predictor and moral_judgement_score as outcome.
    Returns a dictionary with slope, intercept, p_value, r_squared.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running regression analysis on {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # Validate required columns
    required_cols = ['perspective_score', 'moral_judgement_score']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Drop rows with NaN in relevant columns
    df = df.dropna(subset=required_cols)
    
    if len(df) < 2:
        raise ValueError("Insufficient data points for regression analysis")
    
    X = df['perspective_score'].values.reshape(-1, 1)
    y = df['moral_judgement_score'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R-squared
    r_squared = model.score(X, y)
    
    # Calculate p-value for the slope using scipy
    slope = model.coef_[0]
    intercept = model.intercept_
    residuals = y - model.predict(X)
    n = len(y)
    
    # Standard error of the estimate
    sse = np.sum(residuals**2)
    mse = sse / (n - 2)
    
    # Standard error of the slope
    s_x = np.sqrt(np.sum((X - np.mean(X))**2))
    se_slope = np.sqrt(mse / (s_x**2))
    
    # t-statistic
    t_stat = slope / se_slope
    
    # p-value (two-tailed)
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'p_value': float(p_value),
        'r_squared': float(r_squared),
        'sample_size': int(n)
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: Optional[int] = None) -> List[float]:
    """
    Adjust p-values based on the number of hypothesis tests performed (α/k).
    """
    if num_tests is None:
        num_tests = len(p_values)
    
    if num_tests == 0:
        return []
    
    adjusted = [min(p * num_tests, 1.0) for p in p_values]
    return adjusted

def calculate_vif(dataset_path: str) -> Dict[str, float]:
    """
    Calculate VIF for predictors. Warn if VIF > 5.0.
    For this simple model with one predictor, VIF is 1.0, but we implement for extensibility.
    """
    logger = logging.getLogger(__name__)
    df = pd.read_csv(dataset_path)
    
    # For now, we only have one predictor, so VIF is 1.0
    # In a more complex model, we would calculate VIF for each predictor
    vif_warning = False
    vif_values = {'perspective_score': 1.0}
    
    if any(v > 5.0 for v in vif_values.values()):
        vif_warning = True
        logger.warning("VIF > 5.0 detected, indicating potential multicollinearity")
    
    return {
        'vif_values': vif_values,
        'vif_warning': vif_warning
    }

def generate_scatter_plot(dataset_path: str, output_path: str = 'data/artifacts/regression_plot.png'):
    """
    Create scatter plot with regression line and % CI ribbon.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating scatter plot: {output_path}")
    
    df = pd.read_csv(dataset_path)
    df = df.dropna(subset=['perspective_score', 'moral_judgement_score'])
    
    X = df['perspective_score'].values
    y = df['moral_judgement_score'].values
    
    # Fit regression
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), y)
    
    # Create scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(X, y, alpha=0.6, label='Data points')
    
    # Regression line
    x_line = np.linspace(min(X), max(X), 100)
    y_line = model.predict(x_line.reshape(-1, 1))
    plt.plot(x_line, y_line, 'r-', label='Regression line')
    
    # Confidence interval (95%)
    y_pred = model.predict(x_line.reshape(-1, 1))
    residuals = y - model.predict(X.reshape(-1, 1))
    mse = np.sum(residuals**2) / (len(y) - 2)
    se_fit = np.sqrt(mse * (1/len(y) + (x_line - np.mean(X))**2 / np.sum((X - np.mean(X))**2)))
    ci = 1.96 * se_fit
    
    plt.fill_between(x_line, y_pred - ci, y_pred + ci, color='gray', alpha=0.2, label='95% CI')
    
    plt.xlabel('Perspective Score (First-person density)')
    plt.ylabel('Moral Judgement Score')
    plt.title('Relationship between Narrative Perspective and Moral Judgement')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def run_analysis_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full analysis pipeline and save results to JSON.
    Returns the results dictionary.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running full analysis pipeline: {input_path} -> {output_path}")
    
    # Run regression analysis
    regression_results = run_regression_analysis(input_path)
    
    # Apply Bonferroni correction (assuming 1 test for now, but extensible)
    bonferroni_p = apply_bonferroni_correction([regression_results['p_value']])[0]
    regression_results['bonferroni_adjusted_p'] = bonferroni_p
    
    # Calculate VIF
    vif_results = calculate_vif(input_path)
    regression_results['vif_warning'] = vif_results['vif_warning']
    
    # Generate plot
    generate_scatter_plot(input_path)
    
    # Compile final results
    final_results = {
        'slope': regression_results['slope'],
        'intercept': regression_results['intercept'],
        'p_value': regression_results['p_value'],
        'r_squared': regression_results['r_squared'],
        'bonferroni_adjusted_p': regression_results['bonferroni_adjusted_p'],
        'sample_size': regression_results['sample_size'],
        'vif_warning': regression_results['vif_warning']
    }
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")
    return final_results

def run_sensitivity_sweep(
    matching_results_path: str,
    thresholds_path: str,
    dataset_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Execute sensitivity analysis on the text-similarity matching threshold.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running sensitivity sweep: {matching_results_path}, {thresholds_path}, {dataset_path}")
    
    # Load matching results
    with open(matching_results_path, 'r') as f:
        matching_results = json.load(f)
    
    # Load thresholds
    with open(thresholds_path, 'r') as f:
        thresholds_data = json.load(f)
    thresholds = thresholds_data['thresholds']
    
    # Load aligned dataset
    df = pd.read_csv(dataset_path)
    
    # Load matching results as DataFrame for easier filtering
    matching_df = pd.DataFrame(matching_results)
    
    slopes = []
    sample_sizes = []
    temp_files = []
    
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        
        # Filter matches with similarity_score >= threshold
        filtered_matches = matching_df[matching_df['similarity_score'] >= threshold]
        
        # Join with aligned dataset on story_id
        # Assuming matching_df has 'story_id' and 'match_id' columns
        # We need to join on story_id from matching_df with story_id from df
        if 'story_id' not in filtered_matches.columns or 'story_id' not in df.columns:
            logger.warning(f"Threshold {threshold}: Missing story_id column. Skipping.")
            slopes.append(None)
            sample_sizes.append(0)
            continue
        
        joined_df = pd.merge(filtered_matches, df, on='story_id', how='inner')
        
        # Check sample size
        sample_size = len(joined_df)
        min_sample_size = max(5, int(len(df) * 0.1))  # At least 5 or 10% of total
        
        if sample_size < min_sample_size:
            logger.warning(f"Threshold {threshold}: Sample size ({sample_size}) insufficient for regression.")
            slopes.append(None)
            sample_sizes.append(sample_size)
            continue
        
        # Save temporary CSV
        temp_file = f"data/processed/temp_sweep_{threshold}.csv"
        joined_df.to_csv(temp_file, index=False)
        temp_files.append(temp_file)
        
        # Run regression on temporary dataset
        try:
            regression_results = run_regression_analysis(temp_file)
            slopes.append(regression_results['slope'])
            sample_sizes.append(sample_size)
        except Exception as e:
            logger.error(f"Threshold {threshold}: Regression failed: {e}")
            slopes.append(None)
            sample_sizes.append(sample_size)
    
    # Calculate slope variance (ignoring None values)
    valid_slopes = [s for s in slopes if s is not None]
    if len(valid_slopes) > 1:
        slope_variance = float(np.var(valid_slopes))
    else:
        slope_variance = None
    
    # Compile results
    results = {
        'thresholds': thresholds,
        'slopes': slopes,
        'sample_sizes': sample_sizes,
        'slope_variance': slope_variance
    }
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    return results
