import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from scipy import stats
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_aggregate_metrics(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate aggregate metrics (Type I error rate and Power) from simulation results.
    
    Args:
        results_df: DataFrame containing simulation results with columns:
                    'p_value', 'hypothesis_type' (null/alternative), 'scaling_method'
        alpha: Nominal significance level (default 0.05)
        
    Returns:
        DataFrame with aggregate metrics per scaling method
    """
    if results_df.empty:
        logger.warning("Empty results DataFrame provided")
        return pd.DataFrame()
    
    metrics = []
    
    for method in results_df['scaling_method'].unique():
        method_data = results_df[results_df['scaling_method'] == method]
        
        # Type I error rate (for null hypothesis)
        null_data = method_data[method_data['hypothesis_type'] == 'null']
        if not null_data.empty:
            type1_errors = (null_data['p_value'] < alpha).sum()
            type1_rate = type1_errors / len(null_data)
        else:
            type1_rate = np.nan
        
        # Power (for alternative hypothesis)
        alt_data = method_data[method_data['hypothesis_type'] == 'alternative']
        if not alt_data.empty:
            power = (alt_data['p_value'] < alpha).sum() / len(alt_data)
        else:
            power = np.nan
        
        metrics.append({
            'scaling_method': method,
            'type1_error_rate': type1_rate,
            'power': power,
            'n_null': len(null_data) if not null_data.empty else 0,
            'n_alternative': len(alt_data) if not alt_data.empty else 0
        })
    
    return pd.DataFrame(metrics)

def save_aggregate_metrics(metrics_df: pd.DataFrame, output_path: str) -> None:
    """Save aggregate metrics to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_file, index=False)
    logger.info(f"Saved aggregate metrics to {output_file}")

def calculate_deviation_summary(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate deviation of empirical error rates from nominal alpha for each scaling method.
    
    Args:
        results_df: DataFrame with simulation results including 'p_value', 
                    'hypothesis_type', 'scaling_method'
        alpha: Nominal significance level (default 0.05)
        
    Returns:
        DataFrame with deviation summary per scaling method
    """
    if results_df.empty:
        logger.warning("Empty results DataFrame provided")
        return pd.DataFrame()
    
    # Filter for null hypothesis to calculate Type I error deviation
    null_results = results_df[results_df['hypothesis_type'] == 'null'].copy()
    
    if null_results.empty:
        logger.warning("No null hypothesis results found for deviation calculation")
        return pd.DataFrame()
    
    deviations = []
    
    for method in null_results['scaling_method'].unique():
        method_data = null_results[null_results['scaling_method'] == method]
        
        empirical_rate = (method_data['p_value'] < alpha).mean()
        deviation = empirical_rate - alpha
        
        # Calculate 95% CI for the error rate
        n = len(method_data)
        if n > 0:
            se = np.sqrt(empirical_rate * (1 - empirical_rate) / n)
            ci_lower = empirical_rate - 1.96 * se
            ci_upper = empirical_rate + 1.96 * se
        else:
            se = np.nan
            ci_lower = np.nan
            ci_upper = np.nan
        
        deviations.append({
            'scaling_method': method,
            'nominal_alpha': alpha,
            'empirical_error_rate': empirical_rate,
            'deviation_from_nominal': deviation,
            'std_error': se,
            'ci_lower_95': ci_lower,
            'ci_upper_95': ci_upper,
            'n_simulations': n
        })
    
    return pd.DataFrame(deviations)

def fit_synthetic_mixed_effects_model(deviation_df: pd.DataFrame) -> Tuple[object, str]:
    """
    Fit mixed-effects model for synthetic data analysis.
    
    Args:
        deviation_df: DataFrame with deviation metrics including 'scaling_method',
                     'distribution_type', 'simulation_batch', 'deviation_from_nominal'
                     
    Returns:
        Tuple of (model summary string, CSV file path)
    """
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Cannot fit mixed-effects model.")
        return None, None
    
    # Ensure required columns exist
    required_cols = ['deviation_from_nominal', 'scaling_method', 'distribution_type', 'simulation_batch']
    if not all(col in deviation_df.columns for col in required_cols):
        logger.error(f"Missing required columns. Found: {list(deviation_df.columns)}")
        return None, None
    
    formula = "deviation_from_nominal ~ scaling_method + distribution_type + (1|simulation_batch)"
    
    try:
        model = smf.mixedlm(formula, deviation_df, groups=deviation_df["simulation_batch"])
        result = model.fit()
        
        summary_str = result.summary().as_csv()
        
        # Save to CSV
        output_path = Path("results/mixed_effects_synthetic.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract coefficients and stats to DataFrame for CSV
        coef_df = pd.DataFrame({
            'parameter': result.params.index,
            'coefficient': result.params.values,
            'std_err': result.bse.values,
            'z_value': result.tvalues.values,
            'p_value': result.pvalues.values
        })
        coef_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved synthetic mixed-effects model results to {output_path}")
        return result, summary_str
        
    except Exception as e:
        logger.error(f"Error fitting synthetic mixed-effects model: {e}")
        return None, None

def fit_real_world_mixed_effects_model(deviation_df: pd.DataFrame) -> Tuple[object, str]:
    """
    Fit mixed-effects model for real-world data analysis.
    
    Args:
        deviation_df: DataFrame with deviation metrics including 'scaling_method',
                     'dataset_id', 'deviation_from_nominal'
                     
    Returns:
        Tuple of (model summary string, CSV file path)
    """
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Cannot fit mixed-effects model.")
        return None, None
    
    # Ensure required columns exist
    required_cols = ['deviation_from_nominal', 'scaling_method', 'dataset_id']
    if not all(col in deviation_df.columns for col in required_cols):
        logger.error(f"Missing required columns. Found: {list(deviation_df.columns)}")
        return None, None
    
    formula = "deviation_from_nominal ~ scaling_method + (1|dataset_id)"
    
    try:
        model = smf.mixedlm(formula, deviation_df, groups=deviation_df["dataset_id"])
        result = model.fit()
        
        summary_str = result.summary().as_csv()
        
        # Save to CSV
        output_path = Path("results/mixed_effects_summary.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract coefficients and stats to DataFrame for CSV
        coef_df = pd.DataFrame({
            'parameter': result.params.index,
            'coefficient': result.params.values,
            'std_err': result.bse.values,
            'z_value': result.tvalues.values,
            'p_value': result.pvalues.values
        })
        coef_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved real-world mixed-effects model results to {output_path}")
        return result, summary_str
        
    except Exception as e:
        logger.error(f"Error fitting real-world mixed-effects model: {e}")
        return None, None

def generate_summary_report(deviation_df: pd.DataFrame, output_path: str = "results/summary_report.txt") -> None:
    """
    Generate a summary report comparing deviations of each scaling method from nominal 0.05.
    
    Args:
        deviation_df: DataFrame from calculate_deviation_summary containing 
                     'scaling_method', 'empirical_error_rate', 'deviation_from_nominal',
                     'ci_lower_95', 'ci_upper_95'
        output_path: Path to save the text report
    """
    if deviation_df.empty:
        logger.error("Cannot generate report: empty deviation DataFrame")
        return
    
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("SUMMARY REPORT: Scaling Method Deviations from Nominal Alpha (0.05)")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total methods analyzed: {len(deviation_df)}")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append(f"{'Scaling Method':<25} {'Empirical Rate':<15} {'Deviation':<12} {'95% CI':<25}")
    report_lines.append("-" * 70)
    
    for _, row in deviation_df.iterrows():
        method = row['scaling_method']
        rate = f"{row['empirical_error_rate']:.4f}"
        dev = f"{row['deviation_from_nominal']:+.4f}"
        ci = f"[{row['ci_lower_95']:.4f}, {row['ci_upper_95']:.4f}]"
        report_lines.append(f"{method:<25} {rate:<15} {dev:<12} {ci:<25}")
    
    report_lines.append("-" * 70)
    report_lines.append("")
    
    # Summary statistics
    best_method = deviation_df.loc[deviation_df['deviation_from_nominal'].abs().idxmin()]
    worst_method = deviation_df.loc[deviation_df['deviation_from_nominal'].abs().idxmax()]
    
    report_lines.append("KEY FINDINGS:")
    report_lines.append(f"  - Best performing method: {best_method['scaling_method']} "
                      f"(deviation: {best_method['deviation_from_nominal']:+.4f})")
    report_lines.append(f"  - Worst performing method: {worst_method['scaling_method']} "
                      f"(deviation: {worst_method['deviation_from_nominal']:+.4f})")
    report_lines.append("")
    
    # Check if deviations are statistically significant (CI excludes 0)
    significant = deviation_df[
        (deviation_df['ci_lower_95'] > 0) | (deviation_df['ci_upper_95'] < 0)
    ]
    
    if not significant.empty:
        report_lines.append("STATISTICALLY SIGNIFICANT DEVIATIONS (95% CI excludes 0):")
        for _, row in significant.iterrows():
            report_lines.append(f"  - {row['scaling_method']}: {row['deviation_from_nominal']:+.4f}")
    else:
        report_lines.append("No statistically significant deviations found at 95% confidence level.")
    
    report_lines.append("")
    report_lines.append("=" * 70)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 70)
    
    # Write report to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Summary report saved to {output_file}")
    
    # Also print to console
    print('\n'.join(report_lines))

def run_full_analysis_pipeline(results_df: pd.DataFrame, alpha: float = 0.05) -> Dict[str, str]:
    """
    Run the full analysis pipeline: calculate deviations, fit models, and generate report.
    
    Args:
        results_df: Raw simulation results DataFrame
        alpha: Nominal significance level
        
    Returns:
        Dictionary with paths to generated artifacts
    """
    artifacts = {}
    
    # Calculate deviations
    logger.info("Calculating deviation summary...")
    deviation_df = calculate_deviation_summary(results_df, alpha)
    if not deviation_df.empty:
        artifacts['deviation_csv'] = "results/deviation_summary.csv"
        deviation_df.to_csv(artifacts['deviation_csv'], index=False)
        logger.info(f"Saved deviation summary to {artifacts['deviation_csv']}")
    
    # Generate summary report
    logger.info("Generating summary report...")
    report_path = "results/summary_report.txt"
    generate_summary_report(deviation_df, report_path)
    artifacts['report'] = report_path
    
    # Fit mixed-effects models if data allows
    if 'distribution_type' in results_df.columns and 'simulation_batch' in results_df.columns:
        logger.info("Fitting synthetic mixed-effects model...")
        # Create a simplified deviation DataFrame for the model
        model_input = deviation_df.copy()
        model_input['distribution_type'] = results_df['distribution_type'].iloc[0] if 'distribution_type' in results_df.columns else 'normal'
        model_input['simulation_batch'] = 'batch_1'
        _, _ = fit_synthetic_mixed_effects_model(model_input)
        artifacts['synthetic_model'] = "results/mixed_effects_synthetic.csv"
    
    if 'dataset_id' in results_df.columns:
        logger.info("Fitting real-world mixed-effects model...")
        model_input = deviation_df.copy()
        model_input['dataset_id'] = results_df['dataset_id'].iloc[0] if 'dataset_id' in results_df.columns else 'unknown'
        _, _ = fit_real_world_mixed_effects_model(model_input)
        artifacts['real_model'] = "results/mixed_effects_summary.csv"
    
    return artifacts