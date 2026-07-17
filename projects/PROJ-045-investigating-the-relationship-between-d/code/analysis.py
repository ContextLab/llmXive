import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from models import AnalysisResult
from utils import setup_logging, load_config

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load processed data from JSON/CSV."""
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    if data_path.suffix == '.json':
        with open(data_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def calculate_activation_energy(defect_energy: float, migration_barrier: float) -> float:
    """Calculate total activation energy: Ea = Ef + Em."""
    return defect_energy + migration_barrier

def validate_data_quality(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate data quality for regression analysis."""
    issues = []
    
    required_cols = ['defect_energy', 'conductivity', 'defect_density', 'migration_barrier']
    for col in required_cols:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")
    
    if issues:
        return False, issues
    
    # Check for NaN values
    nan_counts = df[required_cols].isna().sum()
    if nan_counts.any():
        issues.append(f"NaN values found: {nan_counts[nan_counts > 0].to_dict()}")
    
    # Check for valid ranges
    if (df['defect_energy'] < 0).any():
        issues.append("Negative defect energies detected")
    
    if (df['conductivity'] <= 0).any():
        issues.append("Non-positive conductivity values detected")
    
    if (df['defect_density'] <= 0).any():
        issues.append("Non-positive defect density values detected")
    
    return len(issues) == 0, issues

def perform_regression_with_density(
    df: pd.DataFrame,
    target_col: str = 'conductivity'
) -> Dict[str, Any]:
    """
    Perform linear regression between defect energies and conductivity
    using defect density as a primary predictor.
    
    Model: log(conductivity) ~ defect_energy + defect_density + migration_barrier
    """
    # Prepare features
    X = df[['defect_energy', 'defect_density', 'migration_barrier']].values
    y = np.log(df[target_col].values)  # Log-transform conductivity for linear relationship
    
    # Fit model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predictions
    y_pred = model.predict(X)
    
    # Metrics
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    rmse = np.sqrt(mse)
    
    # P-values using scipy
    n, p = X.shape
    residuals = y - y_pred
    dof = n - p - 1
    
    # Calculate standard errors and t-statistics for coefficients
    X_with_intercept = np.column_stack([np.ones(n), X])
    XtX_inv = np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    sigma2 = np.sum(residuals**2) / dof
    se = np.sqrt(np.diag(sigma2 * XtX_inv))
    
    t_stats = model.coef_ / se[1:]  # Skip intercept
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), dof))
    
    results = {
        'r2': r2,
        'rmse': rmse,
        'coefficients': {
            'intercept': model.intercept_,
            'defect_energy': model.coef_[0],
            'defect_density': model.coef_[1],
            'migration_barrier': model.coef_[2]
        },
        'p_values': {
            'defect_energy': p_values[0],
            'defect_density': p_values[1],
            'migration_barrier': p_values[2]
        },
        'standard_errors': {
            'defect_energy': se[1],
            'defect_density': se[2],
            'migration_barrier': se[3]
        },
        'n_samples': n,
        'degrees_of_freedom': dof
    }
    
    logger.info(f"Regression R²: {r2:.4f}")
    logger.info(f"Regression RMSE: {rmse:.4f}")
    logger.info(f"Defect density coefficient: {model.coef_[1]:.6f} (p={p_values[1]:.4f})")
    
    return results

def apply_multiple_comparison_correction(
    p_values: Dict[str, float],
    method: str = 'bonferroni'
) -> Dict[str, float]:
    """
    Apply multiple-comparison correction to p-values.
    
    Args:
        p_values: Dictionary of variable names to p-values
        method: 'bonferroni' or 'bh' (Benjamini-Hochberg)
    
    Returns:
        Dictionary of corrected p-values
    """
    variables = list(p_values.keys())
    raw_p = np.array([p_values[v] for v in variables])
    n_tests = len(raw_p)
    
    if method == 'bonferroni':
        corrected_p = np.minimum(raw_p * n_tests, 1.0)
    elif method == 'bh':
        # Benjamini-Hochberg procedure
        sorted_indices = np.argsort(raw_p)
        sorted_p = raw_p[sorted_indices]
        ranks = np.arange(1, n_tests + 1)
        corrected_sorted_p = np.minimum(sorted_p * n_tests / ranks, 1.0)
        # Ensure monotonicity
        for i in range(n_tests - 2, -1, -1):
            corrected_sorted_p[i] = min(corrected_sorted_p[i], corrected_sorted_p[i + 1])
        corrected_p = np.empty(n_tests)
        corrected_p[sorted_indices] = corrected_sorted_p
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    corrected_p_values = dict(zip(variables, corrected_p))
    
    logger.info(f"Applied {method} correction to {n_tests} hypothesis tests")
    for var, p in corrected_p_values.items():
        logger.info(f"  {var}: {p:.4f}")
    
    return corrected_p_values

def calculate_statistical_power(
    n_samples: int,
    effect_size: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for the regression model.
    
    Uses the F-test power approximation for multiple regression.
    """
    from statsmodels.stats.power import FTestPower
    
    # Number of predictors
    k = 3  # defect_energy, defect_density, migration_barrier
    
    # Non-centrality parameter approximation
    f2 = effect_size ** 2
    ncp = f2 * n_samples
    
    # Critical F value
    df1 = k
    df2 = n_samples - k - 1
    f_crit = stats.f.ppf(1 - alpha, df1, df2)
    
    # Power calculation (approximation)
    power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
    
    logger.info(f"Statistical power (n={n_samples}, effect_size={effect_size}): {power:.4f}")
    return power

def generate_regression_plot(
    df: pd.DataFrame,
    regression_results: Dict[str, Any],
    output_path: Path
) -> None:
    """Generate correlation plot with statistical significance markers."""
    plt.figure(figsize=(12, 10))
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Defect Energy vs Conductivity
    ax1 = axes[0, 0]
    ax1.scatter(df['defect_energy'], df['conductivity'], alpha=0.6, edgecolors='w')
    ax1.set_xlabel('Defect Energy (eV)')
    ax1.set_ylabel('Conductivity (S/cm)')
    ax1.set_title(f'Defect Energy vs Conductivity\n(R² = {regression_results["r2"]:.3f})')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Defect Density vs Conductivity
    ax2 = axes[0, 1]
    ax2.scatter(df['defect_density'], df['conductivity'], alpha=0.6, edgecolors='w', c='orange')
    ax2.set_xlabel('Defect Density (defects/Å³)')
    ax2.set_ylabel('Conductivity (S/cm)')
    ax2.set_title('Defect Density vs Conductivity')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Migration Barrier vs Conductivity
    ax3 = axes[1, 0]
    ax3.scatter(df['migration_barrier'], df['conductivity'], alpha=0.6, edgecolors='w', c='green')
    ax3.set_xlabel('Migration Barrier (eV)')
    ax3.set_ylabel('Conductivity (S/cm)')
    ax3.set_title('Migration Barrier vs Conductivity')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Coefficient bar plot with significance
    ax4 = axes[1, 1]
    variables = ['Defect Energy', 'Defect Density', 'Migration Barrier']
    coefficients = [
        regression_results['coefficients']['defect_energy'],
        regression_results['coefficients']['defect_density'],
        regression_results['coefficients']['migration_barrier']
    ]
    p_values = [
        regression_results['p_values']['defect_energy'],
        regression_results['p_values']['defect_density'],
        regression_results['p_values']['migration_barrier']
    ]
    
    colors = ['red' if p < 0.05 else 'gray' for p in p_values]
    bars = ax4.bar(variables, coefficients, color=colors, edgecolor='black')
    ax4.set_ylabel('Coefficient')
    ax4.set_title('Regression Coefficients\n(Red: p < 0.05)')
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # Add p-value annotations
    for i, (bar, p) in enumerate(zip(bars, p_values)):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'p={p:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Regression plot saved to {output_path}")

def run_full_analysis(
    data_path: Path,
    output_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    Run the complete analysis pipeline.
    
    1. Load processed data
    2. Validate data quality
    3. Perform regression with defect density
    4. Apply multiple-comparison correction
    5. Calculate statistical power
    6. Generate plots
    7. Save results
    """
    if config is None:
        config = load_config()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = load_processed_data(data_path)
    logger.info(f"Loaded {len(df)} samples")
    
    # Validate data
    is_valid, issues = validate_data_quality(df)
    if not is_valid:
        logger.warning(f"Data validation issues: {issues}")
        # Filter out invalid rows
        valid_mask = pd.Series([True] * len(df))
        for col in ['defect_energy', 'conductivity', 'defect_density', 'migration_barrier']:
            valid_mask &= df[col].notna() & (df[col] > 0)
        df = df[valid_mask]
        logger.info(f"Filtered to {len(df)} valid samples")
    
    if len(df) < 3:
        raise ValueError("Insufficient valid data points for regression analysis")
    
    # Perform regression
    logger.info("Performing regression analysis with defect density...")
    regression_results = perform_regression_with_density(df)
    
    # Apply multiple-comparison correction
    logger.info("Applying multiple-comparison correction...")
    corrected_p_values = apply_multiple_comparison_correction(
        regression_results['p_values'],
        method='bonferroni'
    )
    regression_results['corrected_p_values'] = corrected_p_values
    
    # Calculate statistical power
    logger.info("Calculating statistical power...")
    power = calculate_statistical_power(
        n_samples=len(df),
        effect_size=0.1,  # Small effect size as per spec
        alpha=0.05
    )
    regression_results['statistical_power'] = power
    
    # Generate plot
    plot_path = output_dir / 'regression_analysis.png'
    logger.info(f"Generating regression plot at {plot_path}")
    generate_regression_plot(df, regression_results, plot_path)
    
    # Save results
    results_path = output_dir / 'analysis_results.json'
    with open(results_path, 'w') as f:
        json.dump(regression_results, f, indent=2)
    logger.info(f"Results saved to {results_path}")
    
    # Create AnalysisResult object
    analysis_result = AnalysisResult(
        r_squared=regression_results['r2'],
        rmse=regression_results['rmse'],
        coefficients=regression_results['coefficients'],
        p_values=regression_results['p_values'],
        corrected_p_values=corrected_p_values,
        statistical_power=power,
        n_samples=len(df),
        plot_path=str(plot_path),
        results_path=str(results_path)
    )
    
    return analysis_result

def main():
    """Main entry point for analysis script."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Load configuration
    config = load_config()
    
    # Define paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / config.get('data_path', 'data/processed/defect_data.json')
    output_dir = project_root / 'data/processed'
    
    try:
        # Run full analysis
        result = run_full_analysis(data_path, output_dir, config)
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS RESULTS SUMMARY")
        print("="*60)
        print(f"R²: {result.r_squared:.4f}")
        print(f"RMSE: {result.rmse:.4f}")
        print(f"Statistical Power: {result.statistical_power:.4f}")
        print(f"Samples: {result.n_samples}")
        print("\nCoefficients:")
        for var, coef in result.coefficients.items():
            if var != 'intercept':
                print(f"  {var}: {coef:.6f} (p={result.p_values[var]:.4f}, "
                      f"corrected p={result.corrected_p_values[var]:.4f})")
        print(f"\nResults saved to: {result.results_path}")
        print(f"Plot saved to: {result.plot_path}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
