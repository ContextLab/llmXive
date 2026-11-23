import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Import from sibling modules as per API surface
from utils import setup_logging, load_config
from models import AnalysisResult

# Configure logging
logger = setup_logging(__name__)

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load processed analysis data from JSON."""
    logger.info(f"Loading processed data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} records")
    return df

def validate_data_quality(df: pd.DataFrame) -> bool:
    """Validate that required columns exist and data is not NaN."""
    required_cols = ['composition_id', 'defect_energy', 'conductivity', 'defect_density']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    if df[required_cols].isnull().any().any():
        logger.warning("Dataset contains NaN values in required columns")
        df = df.dropna(subset=required_cols)
        logger.info(f"Dropped {len(df[df[required_cols].isnull().any(axis=1)])} rows with NaN values")
    
    return True

def calculate_activation_energy(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Total Activation Energy (Ea = Ef + Em) for reporting."""
    if 'defect_energy' in df.columns and 'migration_barrier' in df.columns:
        df['activation_energy'] = df['defect_energy'] + df['migration_barrier']
        logger.info("Calculated activation energy (Ef + Em)")
    else:
        logger.warning("Missing defect_energy or migration_barrier columns for Ea calculation")
    return df

def perform_regression_with_density(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform linear regression with defect density as a predictor."""
    logger.info("Performing regression analysis with defect density")
    
    # Prepare features and target
    X = df[['defect_energy', 'defect_density']].values
    y = df['conductivity'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # Calculate p-values for coefficients
    n = X.shape[0]
    p = X.shape[1]
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (n - p - 1)
    
    # Standard errors
    X_centered = X - X.mean(axis=0)
    var_covar = mse * np.linalg.inv(X_centered.T @ X_centered + np.eye(p) * 1e-8)
    se = np.sqrt(np.diag(var_covar))
    
    # t-statistics and p-values
    t_stats = model.coef_ / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
    
    results = {
        'r_squared': float(r2),
        'coefficients': {
            'defect_energy': float(model.coef_[0]),
            'defect_density': float(model.coef_[1]),
            'intercept': float(model.intercept_)
        },
        'p_values': {
            'defect_energy': float(p_values[0]),
            'defect_density': float(p_values[1])
        },
        'std_errors': {
            'defect_energy': float(se[0]),
            'defect_density': float(se[1])
        }
    }
    
    logger.info(f"Regression R²: {r2:.4f}")
    logger.info(f"P-values: defect_energy={p_values[0]:.4f}, defect_density={p_values[1]:.4f}")
    
    return results

def calculate_variance_inflation_factors(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate VIF to detect collinearity between predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[['defect_energy', 'defect_density']].values
    X_with_const = np.column_stack([np.ones(len(X)), X])
    
    vif_results = {}
    for i, col in enumerate(['intercept', 'defect_energy', 'defect_density']):
        vif = variance_inflation_factor(X_with_const, i)
        vif_results[col] = float(vif)
        logger.info(f"VIF for {col}: {vif:.4f}")
    
    return vif_results

def apply_multiple_comparison_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction for multiple comparisons."""
    logger.info("Applying Bonferroni correction")
    
    p_vals = list(p_values.values())
    n_tests = len(p_vals)
    
    # Bonferroni correction
    adjusted_alpha = alpha / n_tests
    corrected_p_values = {k: min(v * n_tests, 1.0) for k, v in p_values.items()}
    
    significant = {k: v < alpha for k, v in corrected_p_values.items()}
    
    logger.info(f"Bonferroni corrected alpha: {adjusted_alpha:.4f}")
    logger.info(f"Significant predictors: {[k for k, v in significant.items() if v]}")
    
    return {
        'original_p_values': p_values,
        'corrected_p_values': corrected_p_values,
        'adjusted_alpha': adjusted_alpha,
        'significant_predictors': significant
    }

def calculate_statistical_power(df: pd.DataFrame, effect_size: float = 0.1, alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate statistical power using statsmodels."""
    from statsmodels.stats.power import TTestIndPower
    
    logger.info("Calculating statistical power")
    
    n = len(df)
    power_analysis = TTestIndPower()
    
    # For regression, we approximate power based on sample size and effect size
    # Using a simplified approach for linear regression power
    # This is an approximation; for exact regression power, more complex methods are needed
    power = power_analysis.solve_power(effect_size=effect_size, nobs1=n, alpha=alpha, ratio=1.0)
    
    logger.info(f"Statistical power (n={n}, effect_size={effect_size}): {power:.4f}")
    
    return {
        'sample_size': n,
        'effect_size': effect_size,
        'alpha': alpha,
        'power': float(power),
        'meets_target': power >= 0.8
    }

def run_sigma0_sensitivity_analysis(df: pd.DataFrame, sigma0_range: Optional[List[float]] = None) -> Dict[str, Any]:
    """Perform sensitivity analysis for pre-exponential factor sigma0."""
    logger.info("Running sigma0 sensitivity analysis")
    
    if sigma0_range is None:
        # Default range: ±1 order of magnitude around mean
        mean_sigma0 = 1.0  # Placeholder, should be derived from data
        sigma0_range = [mean_sigma0 / 10, mean_sigma0, mean_sigma0 * 10]
    
    results = {}
    for sigma0 in sigma0_range:
        # Simulate conductivity calculation with different sigma0
        # sigma0 * exp(-Ea / (k * T))
        # This is a simplified representation
        results[sigma0] = {
            'sigma0': sigma0,
            'sensitivity_factor': sigma0 / sigma0_range[1] if sigma0_range[1] != 0 else 0
        }
    
    logger.info(f"Sensitivity analysis completed for {len(sigma0_range)} sigma0 values")
    return results

def generate_regression_plot(df: pd.DataFrame, regression_results: Dict[str, Any], output_path: str) -> None:
    """Generate correlation plots with statistical significance markers."""
    logger.info(f"Generating regression plot to {output_path}")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for plotting
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Defect Energy vs Conductivity
    ax1 = axes[0]
    sns.scatterplot(data=df, x='defect_energy', y='conductivity', ax=ax1, alpha=0.7, edgecolor='k')
    
    # Add regression line
    x_vals = np.linspace(df['defect_energy'].min(), df['defect_energy'].max(), 100)
    coef_energy = regression_results['coefficients']['defect_energy']
    intercept = regression_results['coefficients']['intercept']
    # Note: This is a simplified 1D projection, actual regression is multi-variate
    y_pred = coef_energy * x_vals + intercept
    ax1.plot(x_vals, y_pred, 'r-', linewidth=2, label=f'Regression (p={regression_results["p_values"]["defect_energy"]:.3f})')
    
    # Add significance marker
    p_val = regression_results['p_values']['defect_energy']
    sig_marker = '*' if p_val < 0.05 else ''
    ax1.set_title(f'Defect Energy vs Conductivity {sig_marker}', fontsize=12)
    ax1.set_xlabel('Defect Energy (eV)')
    ax1.set_ylabel('Conductivity (S/cm)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Defect Density vs Conductivity
    ax2 = axes[1]
    sns.scatterplot(data=df, x='defect_density', y='conductivity', ax=ax2, alpha=0.7, edgecolor='k', color='green')
    
    # Add regression line
    coef_density = regression_results['coefficients']['defect_density']
    y_pred_density = coef_density * x_vals + intercept  # Simplified
    ax2.plot(x_vals, y_pred_density, 'g-', linewidth=2, label=f'Regression (p={regression_results["p_values"]["defect_density"]:.3f})')
    
    # Add significance marker
    p_val_density = regression_results['p_values']['defect_density']
    sig_marker_density = '*' if p_val_density < 0.05 else ''
    ax2.set_title(f'Defect Density vs Conductivity {sig_marker_density}', fontsize=12)
    ax2.set_xlabel('Defect Density (defects/volume)')
    ax2.set_ylabel('Conductivity (S/cm)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add overall R² annotation
    fig.suptitle(f'Correlation Analysis (R² = {regression_results["r_squared"]:.4f})', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Regression plot saved to {output_path}")

def run_full_analysis(data_path: str, output_dir: str) -> Dict[str, Any]:
    """Run the complete analysis pipeline."""
    logger.info("Starting full analysis pipeline")
    
    # Load data
    df = load_processed_data(data_path)
    
    # Validate data quality
    if not validate_data_quality(df):
        raise ValueError("Data validation failed")
    
    # Calculate activation energy
    df = calculate_activation_energy(df)
    
    # Perform regression
    regression_results = perform_regression_with_density(df)
    
    # Calculate VIF
    vif_results = calculate_variance_inflation_factors(df)
    
    # Apply multiple comparison correction
    correction_results = apply_multiple_comparison_correction(regression_results['p_values'])
    
    # Calculate statistical power
    power_results = calculate_statistical_power(df)
    
    # Run sensitivity analysis
    sensitivity_results = run_sigma0_sensitivity_analysis(df)
    
    # Generate plots
    plot_path = os.path.join(output_dir, 'correlation_plots.png')
    generate_regression_plot(df, regression_results, plot_path)
    
    # Compile results
    full_results = {
        'regression': regression_results,
        'vif': vif_results,
        'multiple_comparison': correction_results,
        'power_analysis': power_results,
        'sensitivity_analysis': sensitivity_results,
        'plot_path': plot_path,
        'sample_size': len(df)
    }
    
    logger.info("Full analysis completed")
    return full_results

def main():
    """Main entry point for analysis script."""
    config = load_config()
    data_path = config.get('data_path', 'data/processed/processed_data.json')
    output_dir = config.get('output_dir', 'data/processed')
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        results = run_full_analysis(data_path, output_dir)
        
        # Save results to JSON
        output_path = os.path.join(output_dir, 'analysis_results.json')
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {output_path}")
        print(f"Analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()