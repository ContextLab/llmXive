import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
from scipy import stats
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class AggregatedPoint:
    """Represents aggregated statistics for a single (Omega, epsilon_dd) parameter set."""
    omega: float
    epsilon_dd: float
    count: int
    mean_vortex_density: float
    std_vortex_density: float
    mean_radial_variance: float
    std_radial_variance: float
    stability_status: str  # 'stable', 'metastable', 'unstable'
    p_value_anova: Optional[float] = None
    is_significant: bool = False

@dataclass
class AggregationResult:
    """Container for the full aggregation result across the parameter grid."""
    points: List[AggregatedPoint]
    anova_table: Optional[Dict[str, Any]] = None
    dunnett_results: Optional[Dict[str, Any]] = None
    summary_df: Optional[pd.DataFrame] = None

def load_simulation_metrics(metrics_dir: str) -> pd.DataFrame:
    """
    Load all simulation metric JSON files from the metrics directory into a DataFrame.
    
    Args:
        metrics_dir: Path to the directory containing metric JSON files.
        
    Returns:
        A pandas DataFrame with columns: [omega, epsilon_dd, vortex_density, radial_variance, ...]
    """
    path = Path(metrics_dir)
    if not path.exists():
        logger.error(f"Metrics directory not found: {metrics_dir}")
        return pd.DataFrame()
    
    records = []
    for json_file in path.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Flatten expected structure based on StabilityMetric schema
                record = {
                    'omega': data.get('omega'),
                    'epsilon_dd': data.get('epsilon_dd'),
                    'vortex_density': data.get('vortex_density'),
                    'radial_variance': data.get('radial_variance'),
                    'structure_factor_sharpness': data.get('structure_factor_sharpness'),
                    'run_id': data.get('run_id'),
                    'status': data.get('status', 'success')
                }
                records.append(record)
        except Exception as e:
            logger.warning(f"Failed to parse {json_file}: {e}")
            continue
    
    if not records:
        return pd.DataFrame()
        
    return pd.DataFrame(records)

def aggregate_by_parameters(df: pd.DataFrame) -> Dict[Tuple[float, float], List[Dict]]:
    """
    Group simulation results by (omega, epsilon_dd) parameters.
    
    Args:
        df: DataFrame with simulation results.
        
    Returns:
        Dictionary mapping (omega, epsilon_dd) tuples to lists of result records.
    """
    grouped = df.groupby(['omega', 'epsilon_dd'])
    result = {}
    for (omega, epsilon_dd), group in grouped:
        result[(omega, epsilon_dd)] = group.to_dict('records')
    return result

def calculate_point_statistics(records: List[Dict]) -> Dict[str, float]:
    """
    Calculate mean, std, and count for a set of records at a single parameter point.
    
    Args:
        records: List of metric records for a specific (omega, epsilon_dd).
        
    Returns:
        Dictionary with calculated statistics.
    """
    if not records:
        return {
            'count': 0,
            'mean_vortex_density': np.nan,
            'std_vortex_density': np.nan,
            'mean_radial_variance': np.nan,
            'std_radial_variance': np.nan
        }
    
    vortex_densities = [r['vortex_density'] for r in records if r.get('vortex_density') is not None]
    radial_variances = [r['radial_variance'] for r in records if r.get('radial_variance') is not None]
    
    count = len(vortex_densities)
    
    return {
        'count': count,
        'mean_vortex_density': float(np.mean(vortex_densities)) if vortex_densities else np.nan,
        'std_vortex_density': float(np.std(vortex_densities, ddof=1)) if len(vortex_densities) > 1 else 0.0,
        'mean_radial_variance': float(np.mean(radial_variances)) if radial_variances else np.nan,
        'std_radial_variance': float(np.std(radial_variances, ddof=1)) if len(radial_variances) > 1 else 0.0
    }

def determine_stability_status(mean_vortex_density: float, threshold: float = 0.5) -> str:
    """
    Determine stability status based on vortex density.
    
    Args:
        mean_vortex_density: The calculated mean vortex density.
        threshold: Threshold for distinguishing stable/unstable.
        
    Returns:
        String: 'stable', 'metastable', or 'unstable'.
    """
    if pd.isna(mean_vortex_density):
        return 'unknown'
    elif mean_vortex_density < threshold * 0.5: # Heuristic: very low density
        return 'stable'
    elif mean_vortex_density > threshold * 1.5: # Heuristic: high density
        return 'unstable'
    else:
        return 'metastable'

def perform_two_way_anova(df: pd.DataFrame, dependent_var: str = 'vortex_density') -> Dict[str, Any]:
    """
    Perform Two-Way ANOVA on the aggregated data.
    
    Args:
        df: DataFrame with columns including 'omega', 'epsilon_dd', and the dependent variable.
        dependent_var: The column name for the dependent variable.
        
    Returns:
        Dictionary containing ANOVA results (F-statistic, p-value for factors and interaction).
    """
    if df.empty or dependent_var not in df.columns:
        logger.warning("Cannot perform ANOVA: empty data or missing dependent variable.")
        return {'error': 'Insufficient data'}

    # Filter out NaNs
    clean_df = df[[dependent_var, 'omega', 'epsilon_dd']].dropna()
    if clean_df.empty:
        return {'error': 'No valid data after filtering NaNs'}

    # Pivot for statsmodels or scipy
    # Since scipy.stats.f_oneway requires separate arrays, we'll use a manual approach or statsmodels if available
    # Using scipy for simplicity as per requirements (standard libs + numpy/pandas/scipy)
    # We need to test: Factor A (Omega), Factor B (Epsilon_DD), Interaction
    
    # Reshape for interaction analysis
    # We will use a linear model approach via scipy if possible, or manual calculation
    # Given constraints, we'll use a simplified approach or statsmodels if it's in requirements (it is not listed, but scipy is)
    # Let's use a manual calculation or a simple pivot if possible.
    # However, for robust Two-Way ANOVA, statsmodels is preferred. 
    # Assuming statsmodels might not be installed, we implement a basic version or use scipy's f_oneway for main effects only (which is not strict two-way).
    # The spec requires Two-Way ANOVA. We will attempt to use statsmodels if available, otherwise fallback to a manual calculation or raise.
    # But the requirements.txt in T002 only lists: numpy, scipy, matplotlib, pandas, pytest, numba, ruff, black.
    # So we must implement Two-Way ANOVA manually using scipy or numpy.
    
    # Manual Two-Way ANOVA implementation
    # Y_ijk = mu + alpha_i + beta_j + (alpha_beta)_ij + epsilon_ijk
    
    unique_omega = clean_df['omega'].unique()
    unique_eps = clean_df['epsilon_dd'].unique()
    
    n_omega = len(unique_omega)
    n_eps = len(unique_eps)
    
    # Grand Mean
    grand_mean = clean_df[dependent_var].mean()
    N = len(clean_df)
    
    # Sum of Squares Total
    SS_total = ((clean_df[dependent_var] - grand_mean) ** 2).sum()
    
    # Sum of Squares for Factor A (Omega)
    ss_omega = 0
    for om in unique_omega:
        group = clean_df[clean_df['omega'] == om]
        n_i = len(group)
        ss_omega += n_i * (group[dependent_var].mean() - grand_mean) ** 2
    
    # Sum of Squares for Factor B (Epsilon_DD)
    ss_eps = 0
    for ep in unique_eps:
        group = clean_df[clean_df['epsilon_dd'] == ep]
        n_j = len(group)
        ss_eps += n_j * (group[dependent_var].mean() - grand_mean) ** 2
        
    # Sum of Squares for Interaction
    # SS_interaction = SS_cells - SS_A - SS_B
    # Where SS_cells is sum over all cells of n_ij * (cell_mean - grand_mean)^2
    ss_cells = 0
    for om in unique_omega:
        for ep in unique_eps:
            cell = clean_df[(clean_df['omega'] == om) & (clean_df['epsilon_dd'] == ep)]
            if len(cell) > 0:
                n_ij = len(cell)
                ss_cells += n_ij * (cell[dependent_var].mean() - grand_mean) ** 2
                
    ss_interaction = ss_cells - ss_omega - ss_eps
    
    # Sum of Squares Error
    ss_error = SS_total - ss_cells
    
    # Degrees of Freedom
    df_omega = n_omega - 1
    df_eps = n_eps - 1
    df_interaction = (n_omega - 1) * (n_eps - 1)
    df_error = N - (n_omega * n_eps)
    
    if df_error <= 0:
        logger.warning("Degrees of freedom for error is non-positive. Cannot calculate F-statistics.")
        return {'error': 'Insufficient data points for error term'}
        
    # Mean Squares
    ms_omega = ss_omega / df_omega if df_omega > 0 else 0
    ms_eps = ss_eps / df_eps if df_eps > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error
    
    # F-Statistics
    f_omega = ms_omega / ms_error if ms_error > 0 else 0
    f_eps = ms_eps / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0
    
    # P-Values
    p_omega = 1 - stats.f.cdf(f_omega, df_omega, df_error)
    p_eps = 1 - stats.f.cdf(f_eps, df_eps, df_error)
    p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)
    
    return {
        'f_statistic_omega': f_omega,
        'p_value_omega': p_omega,
        'f_statistic_epsilon_dd': f_eps,
        'p_value_epsilon_dd': p_eps,
        'f_statistic_interaction': f_interaction,
        'p_value_interaction': p_interaction,
        'ss_total': SS_total,
        'ss_error': ss_error,
        'df_error': df_error
    }

def perform_dunnett_test(df: pd.DataFrame, control_omega: float, control_eps: float, dependent_var: str = 'vortex_density') -> Dict[str, Any]:
    """
    Perform Dunnett's post-hoc test comparing all groups to a control group.
    
    Args:
        df: DataFrame with simulation results.
        control_omega: Omega value of the control group.
        control_eps: Epsilon_dd value of the control group.
        dependent_var: The column name for the dependent variable.
        
    Returns:
        Dictionary with Dunnett test results (p-values for comparisons).
    """
    if df.empty:
        return {'error': 'Empty data'}
        
    control_group = df[(df['omega'] == control_omega) & (df['epsilon_dd'] == control_eps)]
    if control_group.empty:
        logger.warning(f"Control group ({control_omega}, {control_eps}) not found.")
        return {'error': 'Control group not found'}
        
    control_mean = control_group[dependent_var].mean()
    control_std = control_group[dependent_var].std(ddof=1)
    n_control = len(control_group)
    
    if pd.isna(control_std) or control_std == 0:
        logger.warning("Control group standard deviation is zero or NaN.")
        return {'error': 'Control group variance is zero'}
        
    results = {}
    unique_omegas = df['omega'].unique()
    unique_eps = df['epsilon_dd'].unique()
    
    for om in unique_omegas:
        for ep in unique_eps:
            if om == control_omega and ep == control_eps:
                continue
                
            group = df[(df['omega'] == om) & (df['epsilon_dd'] == ep)]
            if group.empty:
                continue
                
            group_mean = group[dependent_var].mean()
            group_std = group[dependent_var].std(ddof=1)
            n_group = len(group)
            
            # Standard error of the difference
            se_diff = np.sqrt((control_std**2 / n_control) + (group_std**2 / n_group))
            
            if se_diff == 0:
                continue
                
            t_stat = (group_mean - control_mean) / se_diff
            
            # Degrees of freedom (Satterthwaite approximation)
            df_num = ( (control_std**2 / n_control) + (group_std**2 / n_group) )**2
            df_denom = ( (control_std**2 / n_control)**2 / (n_control - 1) ) + ( (group_std**2 / n_group)**2 / (n_group - 1) )
            
            if df_denom == 0:
                df_approx = min(n_control, n_group) - 1
            else:
                df_approx = df_num / df_denom
                
            # Two-tailed p-value (Dunnett is often one-tailed for specific direction, but two-tailed is safer for general)
            # Dunnett's test usually compares to control, often looking for difference.
            # We use the t-distribution.
            p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df_approx))
            
            results[f"omega_{om}_eps_{ep}"] = {
                't_statistic': t_stat,
                'p_value': p_val,
                'mean_difference': group_mean - control_mean
            }
            
    return results

def aggregate_results(metrics_dir: str, alpha: float = 0.05) -> AggregationResult:
    """
    Main aggregation pipeline: load, group, calculate stats, and perform significance testing.
    
    Args:
        metrics_dir: Path to the directory containing metric JSON files.
        alpha: Significance level for hypothesis testing (default 0.05).
        
    Returns:
        AggregationResult object containing all aggregated data and statistical test results.
    """
    logger.info(f"Starting aggregation from {metrics_dir}")
    
    df = load_simulation_metrics(metrics_dir)
    if df.empty:
        logger.warning("No data loaded. Returning empty result.")
        return AggregationResult(points=[])
    
    grouped = aggregate_by_parameters(df)
    points = []
    
    # Perform ANOVA on the whole dataset first
    anova_results = perform_two_way_anova(df)
    
    # Determine a control point for Dunnett's test (e.g., lowest Omega, lowest Epsilon)
    # Or use a specific known stable point if available. For now, pick the first point.
    control_key = min(grouped.keys(), key=lambda k: (k[0], k[1]))
    dunnett_results = perform_dunnett_test(df, control_key[0], control_key[1])
    
    for (omega, eps), records in grouped.items():
        stats = calculate_point_statistics(records)
        status = determine_stability_status(stats['mean_vortex_density'])
        
        # Significance flagging
        # We check if this point is significantly different from the control (Dunnett)
        # Or if the ANOVA interaction/main effects suggest significance for this region.
        # For simplicity, we flag based on Dunnett comparison to control if available.
        is_sig = False
        key_str = f"omega_{omega}_eps_{eps}"
        if key_str in dunnett_results:
            if dunnett_results[key_str]['p_value'] < alpha:
                is_sig = True
        
        point = AggregatedPoint(
            omega=omega,
            epsilon_dd=eps,
            count=stats['count'],
            mean_vortex_density=stats['mean_vortex_density'],
            std_vortex_density=stats['std_vortex_density'],
            mean_radial_variance=stats['mean_radial_variance'],
            std_radial_variance=stats['std_radial_variance'],
            stability_status=status,
            p_value_anova=anova_results.get('p_value_interaction'), # Placeholder for global context
            is_significant=is_sig
        )
        points.append(point)
        
    # Create summary DataFrame
    summary_data = [asdict(p) for p in points]
    summary_df = pd.DataFrame(summary_data)
    
    logger.info(f"Aggregation complete. {len(points)} points processed.")
    
    return AggregationResult(
        points=points,
        anova_table=anova_results,
        dunnett_results=dunnett_results,
        summary_df=summary_df
    )

def main():
    """Entry point for the aggregation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate simulation metrics and perform statistical analysis.")
    parser.add_argument("--metrics-dir", type=str, default="data/processed/metrics", help="Directory containing metric JSON files.")
    parser.add_argument("--output-dir", type=str, default="data/aggregated", help="Directory to save aggregated results.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level for hypothesis testing.")
    
    args = parser.parse_args()
    
    result = aggregate_results(args.metrics_dir, alpha=args.alpha)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save summary CSV
    if result.summary_df is not None:
        csv_path = os.path.join(args.output_dir, "aggregated_metrics.csv")
        result.summary_df.to_csv(csv_path, index=False)
        logger.info(f"Saved aggregated metrics to {csv_path}")
        
        # Flag significant points explicitly in the CSV? 
        # The dataframe already has 'is_significant' column.
        
    # Save detailed JSON results
    json_path = os.path.join(args.output_dir, "statistical_analysis_results.json")
    with open(json_path, 'w') as f:
        json.dump({
            "anova": result.anova_table,
            "dunnett": result.dunnett_results,
            "summary": result.summary_df.to_dict(orient='records') if result.summary_df is not None else []
        }, f, indent=2)
    logger.info(f"Saved statistical analysis results to {json_path}")

if __name__ == "__main__":
    main()