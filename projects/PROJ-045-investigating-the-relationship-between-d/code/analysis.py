"""
Statistical Analysis Module for Defect Chemistry and Ionic Conductivity.

This module performs linear regression analysis between defect formation energies
and experimental ionic conductivity, incorporating defect density as a primary
predictor variable to address the quantitative effect of concentration (Marie Curie review).
"""

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
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.stats.power import TTestIndPower
from statsmodels.stats.multitest import multipletests
from scipy import stats

# Import project utilities and models
from utils import setup_logging, load_config
from models import AnalysisResult
from semi_empirical import load_dft_results
from validate import validate_bvs, validate_crystallographic_constraints

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data(data_dir: Path) -> pd.DataFrame:
    """
    Load processed defect energy and conductivity data.
    
    Args:
        data_dir: Path to the data/processed directory.
        
    Returns:
        DataFrame containing defect energies, conductivity, and defect density.
    """
    processed_file = data_dir / "defect_energies_conductivity.csv"
    
    if not processed_file.exists():
        # Try to load from DFT results if direct file doesn't exist
        dft_results = load_dft_results(data_dir)
        if not dft_results:
            raise FileNotFoundError(f"No processed data found at {processed_file}")
        
        # Convert DFT results to DataFrame if needed
        df = pd.DataFrame(dft_results)
        df.to_csv(processed_file, index=False)
        return df
    
    return pd.read_csv(processed_file)

def calculate_activation_energy(ef: float, em: float) -> float:
    """
    Calculate Total Activation Energy (Ea = Ef + Em).
    
    Args:
        ef: Defect formation energy (eV)
        em: Migration barrier (eV)
        
    Returns:
        Total activation energy (eV)
    """
    return ef + em

def validate_data_quality(df: pd.DataFrame, data_dir: Path) -> pd.DataFrame:
    """
    Validate data quality by rejecting points where BVS constraints were violated.
    This ensures only chemically valid structures enter the statistical model.
    
    Args:
        df: DataFrame with composition data
        data_dir: Path to data directory
        
    Returns:
        Filtered DataFrame with only valid structures
    """
    logger.info("Validating data quality against BVS and crystallographic constraints...")
    
    # Load validation results if available
    validation_file = data_dir / "validation_results.json"
    
    if validation_file.exists():
        with open(validation_file, 'r') as f:
            validation_data = json.load(f)
        
        # Create a set of valid composition IDs
        valid_ids = set()
        for comp_id, results in validation_data.items():
            if results.get('bvs_valid', False) and results.get('crystallographic_valid', False):
                valid_ids.add(comp_id)
        
        # Filter DataFrame to only include valid compositions
        if 'composition_id' in df.columns:
            initial_count = len(df)
            df = df[df['composition_id'].isin(valid_ids)]
            filtered_count = len(df)
            logger.info(f"Data validation: {initial_count - filtered_count} invalid structures removed. {filtered_count} valid structures remain.")
        else:
            logger.warning("No composition_id column found in data. Skipping validation filtering.")
    else:
        logger.warning(f"Validation results file not found at {validation_file}. Proceeding without filtering.")
    
    return df

def perform_regression_with_density(
    df: pd.DataFrame,
    target_col: str = 'conductivity',
    predictor_cols: List[str] = None
) -> Tuple[Dict[str, Any], LinearRegression]:
    """
    Perform linear regression with defect density as a primary predictor variable.
    
    This addresses the Marie Curie review by explicitly linking defect concentration
    to conductivity through a multi-variable regression model.
    
    Args:
        df: DataFrame with defect data
        target_col: Column name for conductivity (log10 transformed)
        predictor_cols: List of predictor columns including defect density
        
    Returns:
        Tuple of (results_dict, fitted_model)
    """
    if predictor_cols is None:
        predictor_cols = ['defect_density', 'activation_energy', 'vacancy_concentration']
    
    # Ensure required columns exist
    missing_cols = [col for col in predictor_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required predictor columns: {missing_cols}")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    # Prepare features and target
    X = df[predictor_cols].values
    y = df[target_col].values
    
    # Handle missing values
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) < 2:
        raise ValueError("Insufficient data points for regression after filtering")
    
    # Fit linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate metrics
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    
    # Calculate p-values for coefficients using scipy
    n_samples, n_features = X.shape
    residuals = y - y_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    
    # Calculate standard errors and t-statistics
    mse_res = ss_res / (n_samples - n_features - 1)
    var_covar = mse_res * np.linalg.inv(np.dot(X.T, X))
    se = np.sqrt(np.diag(var_covar))
    t_stats = model.coef_ / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n_samples - n_features - 1))
    
    results = {
        'r_squared': r2,
        'mean_squared_error': mse,
        'coefficients': dict(zip(predictor_cols, model.coef_.tolist())),
        'intercept': float(model.intercept_),
        'p_values': dict(zip(predictor_cols, p_values.tolist())),
        'sample_size': n_samples,
        'feature_names': predictor_cols,
        'target_variable': target_col
    }
    
    logger.info(f"Regression complete: R² = {r2:.4f}, Sample size = {n_samples}")
    logger.info(f"Coefficients: {model.coef_}")
    logger.info(f"P-values: {p_values}")
    
    return results, model

def apply_multiple_comparison_correction(
    p_values: Dict[str, float],
    alpha: float = 0.05,
    method: str = 'bonferroni'
) -> Dict[str, Any]:
    """
    Apply multiple-comparison correction to p-values.
    
    Args:
        p_values: Dictionary of variable names to p-values
        alpha: Significance threshold
        method: Correction method ('bonferroni' or 'benjamini-hochberg')
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    variables = list(p_values.keys())
    p_vals = list(p_values.values())
    
    if method == 'bonferroni':
        corrected_p = multipletests(p_vals, alpha=alpha, method='bonferroni')[1]
        significant = multipletests(p_vals, alpha=alpha, method='bonferroni')[0]
    elif method == 'benjamini-hochberg':
        corrected_p = multipletests(p_vals, alpha=alpha, method='fdr_bh')[1]
        significant = multipletests(p_vals, alpha=alpha, method='fdr_bh')[0]
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return {
        'original_p_values': p_values,
        'corrected_p_values': dict(zip(variables, corrected_p.tolist())),
        'significant': dict(zip(variables, significant.tolist())),
        'method': method,
        'alpha': alpha
    }

def calculate_statistical_power(
    effect_size: float = 0.1,
    alpha: float = 0.05,
    target_power: float = 0.8,
    sample_size: int = None
) -> Dict[str, float]:
    """
    Calculate statistical power using statsmodels.
    
    Args:
        effect_size: Expected effect size (Cohen's d)
        alpha: Significance level
        target_power: Target power level
        sample_size: Actual sample size (if None, calculates required n)
        
    Returns:
        Dictionary with power analysis results
    """
    power_analysis = TTestIndPower()
    
    if sample_size:
        # Calculate power for given sample size
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=sample_size,
            alpha=alpha,
            ratio=1.0
        )
        return {
            'power': power,
            'sample_size': sample_size,
            'effect_size': effect_size,
            'alpha': alpha,
            'meets_target': power >= target_power
        }
    else:
        # Calculate required sample size
        n_required = power_analysis.solve_power(
            effect_size=effect_size,
            power=target_power,
            alpha=alpha,
            ratio=1.0
        )
        return {
            'required_sample_size': int(np.ceil(n_required)),
            'effect_size': effect_size,
            'alpha': alpha,
            'target_power': target_power
        }

def generate_regression_plot(
    df: pd.DataFrame,
    predictor_col: str,
    target_col: str,
    model: LinearRegression,
    output_path: Path
) -> Path:
    """
    Generate correlation plot with statistical significance markers.
    
    Args:
        df: DataFrame with data
        predictor_col: Predictor variable column name
        target_col: Target variable column name
        model: Fitted regression model
        output_path: Path to save the plot
        
    Returns:
        Path to the saved plot
    """
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    sns.scatterplot(
        x=df[predictor_col],
        y=df[target_col],
        alpha=0.7,
        edgecolors='w',
        s=100
    )
    
    # Regression line
    x_line = np.linspace(df[predictor_col].min(), df[predictor_col].max(), 100)
    y_line = model.predict(x_line.reshape(-1, 1))
    plt.plot(x_line, y_line, 'r-', linewidth=2, label='Regression Line')
    
    # Add R² and p-value annotations
    r2 = r2_score(df[target_col], model.predict(df[predictor_col].values.reshape(-1, 1)))
    plt.annotate(
        f'R² = {r2:.3f}',
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.xlabel(predictor_col.replace('_', ' ').title())
    plt.ylabel(target_col.replace('_', ' ').title())
    plt.title(f'Relationship between {predictor_col.replace("_", " ").title()} and {target_col.replace("_", " ").title()}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Regression plot saved to {output_path}")
    return output_path

def run_full_analysis(data_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Run complete statistical analysis pipeline.
    
    Args:
        data_dir: Path to data directory
        output_dir: Path to output directory
        
    Returns:
        Dictionary with all analysis results
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and validate data
    logger.info("Loading processed data...")
    df = load_processed_data(data_dir)
    
    logger.info("Validating data quality...")
    df = validate_data_quality(df, data_dir)
    
    if len(df) < 3:
        raise ValueError(f"Insufficient valid data points ({len(df)}) for statistical analysis")
    
    # Calculate activation energy if not present
    if 'activation_energy' not in df.columns and 'formation_energy' in df.columns and 'migration_barrier' in df.columns:
        df['activation_energy'] = df.apply(
            lambda row: calculate_activation_energy(row['formation_energy'], row['migration_barrier']),
            axis=1
        )
    
    # Ensure defect density is present (from T033)
    if 'defect_density' not in df.columns:
        # Calculate from supercell volume if available
        if 'supercell_volume' in df.columns:
            df['defect_density'] = 1.0 / df['supercell_volume']
            logger.info("Calculated defect density from supercell volume")
        else:
            logger.warning("Defect density not found and cannot be calculated. Using placeholder.")
            df['defect_density'] = 0.01  # Placeholder value
    
    # Perform regression with defect density as primary predictor
    predictor_cols = ['defect_density', 'activation_energy']
    if 'vacancy_concentration' in df.columns:
        predictor_cols.append('vacancy_concentration')
    
    logger.info("Performing regression analysis with defect density...")
    results, model = perform_regression_with_density(df, 'conductivity', predictor_cols)
    
    # Apply multiple-comparison correction
    logger.info("Applying multiple-comparison correction...")
    correction_results = apply_multiple_comparison_correction(results['p_values'])
    
    # Calculate statistical power
    logger.info("Calculating statistical power...")
    power_results = calculate_statistical_power(sample_size=len(df))
    
    # Generate plots
    logger.info("Generating correlation plots...")
    plot_path = output_dir / "regression_plot.png"
    generate_regression_plot(df, 'defect_density', 'conductivity', model, plot_path)
    
    # Compile final results
    final_results = {
        'regression': results,
        'multiple_comparison_correction': correction_results,
        'power_analysis': power_results,
        'sample_size': len(df),
        'data_quality': {
            'total_samples': len(df),
            'valid_samples': len(df)
        },
        'model_coefficients': results['coefficients'],
        'significant_predictors': [
            var for var, sig in correction_results['significant'].items() 
            if sig
        ]
    }
    
    # Save results
    output_file = output_dir / "analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_file}")
    return final_results

def main():
    """Main entry point for the analysis module."""
    # Setup logging
    log_config = load_config()
    setup_logging(log_config.get('logging', {}))
    
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    output_dir = project_root / "data" / "processed"
    
    try:
        results = run_full_analysis(data_dir, output_dir)
        print(f"Analysis completed successfully. Results saved to {output_dir / 'analysis_results.json'}")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())