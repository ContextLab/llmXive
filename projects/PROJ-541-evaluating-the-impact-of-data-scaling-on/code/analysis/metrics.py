"""
Metrics and analysis functions for statistical testing pipeline.
Implements aggregation, confidence intervals, and mixed-effects modeling.
"""
import os
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass, field
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

# Import existing symbols from the project to maintain API surface
# These are assumed to exist in this file based on the API surface provided
# If they don't exist in the actual file, they would need to be defined here or imported
try:
    from analysis.tests import TestResult, ScalingMethod
except ImportError:
    # Fallback definitions if not imported
    @dataclass
    class TestResult:
        p_value: float
        statistic: float
        test_type: str
        scaling_method: str

    @dataclass
    class ScalingMethod:
        name: str
        params: Dict[str, Any]

# Constants
SIMULATION_RESULTS_PATH = Path("results/simulation_results.csv")
REAL_WORLD_RESULTS_PATH = Path("results/real_world_results.csv")
AGGREGATE_METRICS_PATH = Path("results/aggregate_metrics.csv")
DEVIATION_SUMMARY_PATH = Path("results/deviation_summary.json")
COMPARISON_REPORT_PATH = Path("results/comparison_report.md")

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class AnovaResult:
    f_statistic: float
    p_value: float
    degrees_of_freedom: Tuple[int, int]
    effect_size: Optional[float] = None

@dataclass
class MixedEffectsResult:
    model_summary: str
    fixed_effects: pd.DataFrame
    random_effects: pd.DataFrame
    p_values: Dict[str, float]
    is_significant: bool

def load_simulation_results() -> pd.DataFrame:
    """Load simulation results from CSV file."""
    if not SIMULATION_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Simulation results not found at {SIMULATION_RESULTS_PATH}")
    df = pd.read_csv(SIMULATION_RESULTS_PATH)
    logger.info(f"Loaded {len(df)} simulation results")
    return df

def load_real_world_results() -> pd.DataFrame:
    """Load real-world results from CSV file."""
    if not REAL_WORLD_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Real-world results not found at {REAL_WORLD_RESULTS_PATH}")
    df = pd.read_csv(REAL_WORLD_RESULTS_PATH)
    logger.info(f"Loaded {len(df)} real-world results")
    return df

def save_aggregate_metrics(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save aggregate metrics to CSV."""
    if output_path is None:
        output_path = AGGREGATE_METRICS_PATH
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert metrics to DataFrame
    df = pd.DataFrame([metrics])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregate metrics to {output_path}")
    return output_path

def calculate_confidence_interval(proportion: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Clopper-Pearson exact confidence interval for a proportion.
    
    Args:
        proportion: Observed proportion (0 <= p <= 1)
        n: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return (0.0, 0.0)
    
    alpha = 1 - confidence
    successes = int(round(proportion * n))
    
    # Clopper-Pearson exact interval using beta distribution
    lower = stats.beta.ppf(alpha / 2, successes, n - successes + 1) if successes > 0 else 0.0
    upper = stats.beta.ppf(1 - alpha / 2, successes + 1, n - successes) if successes < n else 1.0
    
    return (lower, upper)

def calculate_aggregate_metrics(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate aggregate metrics including Type I error rate and power.
    
    Args:
        results_df: DataFrame with p-values and ground truth labels
        alpha: Significance threshold (default 0.05)
    
    Returns:
        DataFrame with aggregated metrics per scaling method and test type
    """
    if results_df.empty:
        logger.warning("Empty results DataFrame provided")
        return pd.DataFrame()
    
    # Ensure required columns exist
    required_cols = ['p_value', 'ground_truth', 'scaling_method', 'test_type']
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate empirical error rates
    results_df['is_significant'] = results_df['p_value'] < alpha
    
    # For null hypothesis (ground_truth == 'null'), error rate = Type I error
    # For alternative hypothesis (ground_truth == 'alternative'), power = 1 - Type II error
    
    def calculate_metrics(group):
        n_total = len(group)
        n_significant = group['is_significant'].sum()
        
        if group['ground_truth'].iloc[0] == 'null':
            # Type I error rate
            error_rate = n_significant / n_total if n_total > 0 else 0.0
            ci_lower, ci_upper = calculate_confidence_interval(error_rate, n_total)
            return pd.Series({
                'metric_type': 'type1_error',
                'rate': error_rate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'n_total': n_total,
                'n_significant': n_significant
            })
        else:
            # Power (1 - Type II error)
            power = n_significant / n_total if n_total > 0 else 0.0
            ci_lower, ci_upper = calculate_confidence_interval(power, n_total)
            return pd.Series({
                'metric_type': 'power',
                'rate': power,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'n_total': n_total,
                'n_significant': n_significant
            })
    
    # Group by scaling_method and test_type
    agg_metrics = results_df.groupby(['scaling_method', 'test_type', 'ground_truth']).apply(
        calculate_metrics
    ).reset_index()
    
    logger.info(f"Calculated aggregate metrics for {len(agg_metrics)} groups")
    return agg_metrics

def fit_mixed_effects_model(
    results_df: pd.DataFrame,
    nominal_alpha: float = 0.05
) -> MixedEffectsResult:
    """
    Fit a mixed-effects model to analyze deviation from nominal alpha.
    
    Models the deviation from nominal alpha as a function of:
    - Fixed effect: scaling_method
    - Random effect: dataset_source (config_id for synthetic, dataset_id for real)
    
    Args:
        results_df: DataFrame with p-values, scaling_method, and dataset_source
        nominal_alpha: The nominal significance threshold (default 0.05)
    
    Returns:
        MixedEffectsResult containing model summary and statistics
    """
    if results_df.empty:
        raise ValueError("Cannot fit model on empty DataFrame")
    
    # Ensure required columns
    required_cols = ['p_value', 'scaling_method', 'dataset_source']
    missing_cols = [col for col in required_cols if col not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for mixed-effects model: {missing_cols}")
    
    # Calculate deviation from nominal alpha
    # We model whether the test is significant (binary outcome) or the p-value itself
    # For mixed-effects, we'll use the binary outcome (significant or not)
    results_df = results_df.copy()
    results_df['is_significant'] = (results_df['p_value'] < nominal_alpha).astype(int)
    results_df['deviation'] = results_df['is_significant'] - nominal_alpha
    
    # Prepare data for mixed-effects model
    # Convert scaling_method to categorical
    results_df['scaling_method'] = results_df['scaling_method'].astype('category')
    results_df['dataset_source'] = results_df['dataset_source'].astype('category')
    
    # Handle cases where there might be only one level for random effect
    n_sources = results_df['dataset_source'].nunique()
    if n_sources < 2:
        logger.warning(f"Only {n_sources} dataset sources found; using fixed-effects model instead")
        # Fall back to simple linear model
        model = sm.OLS(
            results_df['deviation'],
            sm.add_constant(pd.get_dummies(results_df['scaling_method'], drop_first=True))
        )
        results = model.fit()
        return MixedEffectsResult(
            model_summary=str(results.summary()),
            fixed_effects=pd.DataFrame(results.params),
            random_effects=pd.DataFrame(),
            p_values={'scaling_method': results.pvalues.iloc[1:] if len(results.pvalues) > 1 else {}},
            is_significant=results.pvalues.iloc[1:] < 0.05 if len(results.pvalues) > 1 else False
        )
    
    # Fit mixed-effects model
    # Formula: deviation ~ scaling_method + (1 | dataset_source)
    try:
        formula = "deviation ~ C(scaling_method) + (1 | dataset_source)"
        model = mixedlm.from_formula(formula, results_df)
        fit = model.fit(reml=False)
        
        # Extract results
        fixed_effects_df = pd.DataFrame({
            'parameter': fit.params.index,
            'estimate': fit.params.values,
            'std_err': fit.bse.values,
            'z_value': fit.tvalues.values,
            'p_value': fit.pvalues.values
        })
        
        random_effects_df = pd.DataFrame({
            'group': fit.random_effects.index,
            'variance': fit.cov_re.values.diagonal() if hasattr(fit.cov_re, 'diagonal') else [fit.cov_re.values]
        })
        
        # Check significance of scaling_method
        scaling_p_values = fit.pvalues.filter(like='scaling_method')
        is_significant = (scaling_p_values < 0.05).any() if len(scaling_p_values) > 0 else False
        
        logger.info(f"Mixed-effects model fitted. Scaling method significant: {is_significant}")
        
        return MixedEffectsResult(
            model_summary=str(fit.summary()),
            fixed_effects=fixed_effects_df,
            random_effects=random_effects_df,
            p_values=fit.pvalues.to_dict(),
            is_significant=is_significant
        )
        
    except Exception as e:
        logger.error(f"Failed to fit mixed-effects model: {e}")
        # Fallback to simple model if mixed-effects fails
        try:
            model = sm.OLS(
                results_df['deviation'],
                sm.add_constant(pd.get_dummies(results_df['scaling_method'], drop_first=True))
            )
            fit = model.fit()
            return MixedEffectsResult(
                model_summary=str(fit.summary()),
                fixed_effects=pd.DataFrame({'parameter': fit.params.index, 'estimate': fit.params.values}),
                random_effects=pd.DataFrame(),
                p_values=fit.pvalues.to_dict(),
                is_significant=(fit.pvalues.iloc[1:] < 0.05).any() if len(fit.pvalues) > 1 else False
            )
        except Exception as fallback_error:
            logger.error(f"Fallback model also failed: {fallback_error}")
            raise RuntimeError(f"Could not fit any model: {e}")

def calculate_deviation_summary(results_df: pd.DataFrame, nominal_alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate summary statistics of deviation from nominal alpha."""
    if results_df.empty:
        return {}
    
    results_df = results_df.copy()
    results_df['is_significant'] = (results_df['p_value'] < nominal_alpha).astype(int)
    results_df['deviation'] = results_df['is_significant'] - nominal_alpha
    
    summary = {
        'nominal_alpha': nominal_alpha,
        'total_tests': len(results_df),
        'significant_tests': int(results_df['is_significant'].sum()),
        'empirical_error_rate': float(results_df['is_significant'].mean()),
        'mean_deviation': float(results_df['deviation'].mean()),
        'std_deviation': float(results_df['deviation'].std()),
        'by_scaling_method': {}
    }
    
    for method in results_df['scaling_method'].unique():
        method_data = results_df[results_df['scaling_method'] == method]
        summary['by_scaling_method'][method] = {
            'n_tests': int(len(method_data)),
            'significant': int(method_data['is_significant'].sum()),
            'error_rate': float(method_data['is_significant'].mean()),
            'mean_deviation': float(method_data['deviation'].mean())
        }
    
    return summary

def generate_summary_report(summary: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Generate a markdown summary report."""
    if output_path is None:
        output_path = DEVIATION_SUMMARY_PATH
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Deviation from Nominal Alpha Summary\n\n")
        f.write(f"**Nominal Alpha**: {summary['nominal_alpha']}\n")
        f.write(f"**Total Tests**: {summary['total_tests']}\n")
        f.write(f"**Significant Tests**: {summary['significant_tests']}\n")
        f.write(f"**Empirical Error Rate**: {summary['empirical_error_rate']:.4f}\n")
        f.write(f"**Mean Deviation**: {summary['mean_deviation']:.4f}\n")
        f.write(f"**Std Deviation**: {summary['std_deviation']:.4f}\n\n")
        
        f.write("## By Scaling Method\n\n")
        f.write("| Method | Tests | Significant | Error Rate | Mean Deviation |\n")
        f.write("|--------|-------|-------------|------------|----------------|\n")
        for method, data in summary['by_scaling_method'].items():
            f.write(f"| {method} | {data['n_tests']} | {data['significant']} | "
                   f"{data['error_rate']:.4f} | {data['mean_deviation']:.4f} |\n")
    
    logger.info(f"Generated summary report at {output_path}")
    return output_path

def run_full_analysis_pipeline(
    results_df: Optional[pd.DataFrame] = None,
    nominal_alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline on simulation results.
    
    Args:
        results_df: Optional DataFrame with results. If None, loads from file.
        nominal_alpha: Significance threshold (default 0.05)
    
    Returns:
        Dictionary containing analysis results
    """
    if results_df is None:
        try:
            results_df = load_simulation_results()
        except FileNotFoundError as e:
            logger.error(f"Cannot run analysis: {e}")
            return {'error': str(e)}
    
    if results_df.empty:
        logger.warning("No results to analyze")
        return {'warning': 'No results to analyze'}
    
    # Calculate aggregate metrics
    agg_metrics = calculate_aggregate_metrics(results_df, nominal_alpha)
    
    # Calculate deviation summary
    deviation_summary = calculate_deviation_summary(results_df, nominal_alpha)
    
    # Fit mixed-effects model if dataset_source column exists
    mixed_effects_result = None
    if 'dataset_source' in results_df.columns:
        try:
            mixed_effects_result = fit_mixed_effects_model(results_df, nominal_alpha)
        except Exception as e:
            logger.warning(f"Could not fit mixed-effects model: {e}")
    else:
        logger.info("No dataset_source column found; skipping mixed-effects model")
    
    # Generate summary report
    generate_summary_report(deviation_summary)
    
    return {
        'aggregate_metrics': agg_metrics,
        'deviation_summary': deviation_summary,
        'mixed_effects_result': mixed_effects_result,
        'nominal_alpha': nominal_alpha
    }

def run_real_world_scaling_and_testing(
    real_world_df: pd.DataFrame,
    scaling_methods: List[str],
    test_types: List[str]
) -> pd.DataFrame:
    """
    Run scaling and testing pipeline on real-world data.
    
    Args:
        real_world_df: DataFrame with real-world data
        scaling_methods: List of scaling methods to apply
        test_types: List of test types to run
    
    Returns:
        DataFrame with test results
    """
    # This is a placeholder - actual implementation would depend on data structure
    # For now, return an empty DataFrame with expected schema
    results = []
    
    for method in scaling_methods:
        for test_type in test_types:
            # Placeholder: in real implementation, would actually run tests
            results.append({
                'scaling_method': method,
                'test_type': test_type,
                'p_value': 0.05,  # Placeholder
                'statistic': 0.0,  # Placeholder
                'dataset_source': 'real_world',
                'ground_truth': 'unknown'
            })
    
    return pd.DataFrame(results)

def generate_comparison_report(
    synthetic_results: pd.DataFrame,
    real_world_results: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a comparison report between synthetic and real-world results.
    
    Args:
        synthetic_results: DataFrame with synthetic simulation results
        real_world_results: DataFrame with real-world test results
        output_path: Optional path for output file
    
    Returns:
        Path to generated report
    """
    if output_path is None:
        output_path = COMPARISON_REPORT_PATH
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Synthetic vs Real-World Comparison Report\n\n")
        
        # Summary statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"**Synthetic Tests**: {len(synthetic_results)}\n")
        f.write(f"**Real-World Tests**: {len(real_world_results)}\n\n")
        
        # Error rate comparison
        f.write("## Error Rate Comparison\n\n")
        f.write("| Method | Synthetic Error Rate | Real-World Error Rate |\n")
        f.write("|--------|---------------------|----------------------|\n")
        
        synthetic_error_rates = synthetic_results.groupby('scaling_method')['p_value'].apply(
            lambda x: (x < 0.05).mean()
        )
        real_world_error_rates = real_world_results.groupby('scaling_method')['p_value'].apply(
            lambda x: (x < 0.05).mean()
        )
        
        for method in set(synthetic_error_rates.index) | set(real_world_error_rates.index):
            syn_rate = synthetic_error_rates.get(method, 'N/A')
            real_rate = real_world_error_rates.get(method, 'N/A')
            f.write(f"| {method} | {syn_rate:.4f} | {real_rate:.4f} |\n")
        
        f.write("\n## Conclusions\n\n")
        f.write("TODO: Add analysis of differences between synthetic and real-world results.\n")
    
    logger.info(f"Generated comparison report at {output_path}")
    return output_path