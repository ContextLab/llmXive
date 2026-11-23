import pandas as pd
import numpy as np
import scipy.stats as stats
import logging
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.logging import get_sensitivity_logger
from analysis.anova import perform_two_way_anova, calculate_interaction_effect, ExtractedStats, AnovaResult
from analysis.effect_sizes import calculate_cohens_d, perform_pairwise_comparisons_by_stratum, EffectSizeResult

@dataclass
class ThresholdResult:
    """Result of a sensitivity analysis at a specific threshold."""
    threshold_years: float
    novice_mean_task_time: float
    novice_std_task_time: float
    novice_n: int
    intermediate_mean_task_time: float
    intermediate_std_task_time: float
    intermediate_n: int
    expert_mean_task_time: float
    expert_std_task_time: float
    expert_n: int
    novice_defect_rate: float
    intermediate_defect_rate: float
    expert_defect_rate: float
    anova_f_statistic: Optional[float]
    anova_p_value: Optional[float]
    interaction_f_statistic: Optional[float]
    interaction_p_value: Optional[float]
    effect_sizes: List[Dict[str, Any]]
    power_flag: bool
    is_significant: bool

@dataclass
class SensitivityReport:
    """Container for the full sensitivity analysis report."""
    thresholds_tested: List[float]
    results: List[ThresholdResult]
    summary: Dict[str, Any]
    timestamp: str
    config: Dict[str, Any]

def classify_experience(experience_years: float, threshold: float) -> str:
    """
    Classify experience level based on a dynamic threshold.
    
    Args:
        experience_years: Years of experience
        threshold: The threshold defining the split between novice and intermediate.
                   Experts are defined as > 5 years (fixed) as per T008b.
    
    Returns:
        'novice', 'intermediate', or 'expert'
    """
    if experience_years < threshold:
        return 'novice'
    elif experience_years <= 5:
        return 'intermediate'
    else:
        return 'expert'

def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: List[float],
    tool_col: str = 'tool_usage',
    time_col: str = 'task_time',
    defect_col: str = 'defect_rate',
    exp_col: str = 'experience_years'
) -> List[ThresholdResult]:
    """
    Run ANOVA and effect size calculations across a sweep of experience thresholds.
    
    Args:
        df: DataFrame with required columns
        thresholds: List of threshold years to test (e.g., [1.0, 2.0, 3.0])
        tool_col: Column name for tool usage
        time_col: Column name for task time
        defect_col: Column name for defect rate
        exp_col: Column name for experience years
    
    Returns:
        List of ThresholdResult objects
    """
    logger = get_sensitivity_logger()
    results = []
    
    for threshold in thresholds:
        logger.info(f"Running sensitivity sweep at threshold: {threshold} years")
        
        # Classify experience
        df['experience_class'] = df[exp_col].apply(lambda x: classify_experience(x, threshold))
        
        # Check minimum observations per stratum (SC-006)
        counts = df['experience_class'].value_counts()
        min_obs = counts.min() if not counts.empty else 0
        power_flag = min_obs < 30
        
        if power_flag:
            logger.warning(f"Power flag raised: min observations ({min_obs}) < 30 at threshold {threshold}")
        
        # Prepare data for ANOVA: tool_usage x experience_class -> task_time
        # We need to group by tool_usage and experience_class
        if df['experience_class'].nunique() < 2 or df[tool_col].nunique() < 2:
            logger.warning(f"Insufficient groups at threshold {threshold} for ANOVA. Skipping ANOVA.")
            anova_result = None
            interaction_result = None
            effect_size_list = []
        else:
            # Perform two-way ANOVA
            try:
                # Reshape for statsmodels or use scipy if available, but here we use manual calculation or scipy.stats.f_oneway for simple cases
                # Since we need interaction, we use a pivot or groupby approach with scipy.stats.f_oneway for main effects 
                # and manual calculation for interaction if needed, or rely on the existing anova module.
                # The existing anova module (T021a) expects specific inputs. Let's adapt.
                
                # We will use the existing perform_two_way_anova if it accepts dataframes, 
                # otherwise we replicate the logic briefly here to ensure it works with our dynamic classes.
                # Assuming perform_two_way_anova can handle the dataframe or we pass the necessary arrays.
                # To be safe and consistent with T021a which likely uses scipy or statsmodels, 
                # we will call the existing function if it's robust, or implement a simplified version here.
                # Given the constraints, we will assume the anova module handles the grouping.
                
                # Let's extract groups for scipy.stats.f_oneway (main effects)
                # For interaction, we need the specific module function.
                
                # Group data
                groups = []
                for tool in df[tool_col].unique():
                    for exp in df['experience_class'].unique():
                        subset = df[(df[tool_col] == tool) & (df['experience_class'] == exp)][time_col]
                        if len(subset) > 0:
                            groups.append(subset.values)
                
                if len(groups) >= 2:
                    # Simple ANOVA on groups (ignoring interaction for a moment, or using the module)
                    # We will use the module's logic if possible. 
                    # Since we don't have the full source of anova.py here, we will implement a robust local version 
                    # that mirrors the expected behavior of T021a for this specific task.
                    
                    # Calculate means and stats for the report
                    # Using scipy.stats.f_oneway for the combined groups to get a global F (approximation)
                    # But for a proper 2-way, we need the module. 
                    # Let's assume the module 'perform_two_way_anova' works on the dataframe if we pass the columns.
                    # If not, we fallback to a manual calculation or skip.
                    
                    # Attempt to use the module (imported above)
                    # We need to ensure the module can handle the dynamic 'experience_class' column.
                    # If the module is rigid, we might need to construct the formula string.
                    # Let's assume it takes the dataframe and column names.
                    
                    # Fallback: Manual calculation of 2-way ANOVA if the module is too rigid
                    # For now, we will try to call the module with the dataframe and column names.
                    # If the module expects specific named columns, we might need to rename 'experience_class' temporarily.
                    # To be safe, we will implement a local 2-way ANOVA using scipy if the module fails or is not flexible.
                    
                    # Local 2-way ANOVA implementation for robustness
                    unique_tools = df[tool_col].unique()
                    unique_exps = df['experience_class'].unique()
                    
                    # Organize data
                    data_dict = {}
                    for t in unique_tools:
                        for e in unique_exps:
                            key = (t, e)
                            data_dict[key] = df[(df[tool_col] == t) & (df['experience_class'] == e)][time_col].values
                    
                    if len(data_dict) >= 4: # Full factorial
                        # Calculate Grand Mean
                        all_vals = np.concatenate(list(data_dict.values()))
                        grand_mean = np.mean(all_vals)
                        
                        # Calculate SS
                        n_total = len(all_vals)
                        ss_total = np.sum((all_vals - grand_mean) ** 2)
                        
                        # SS Between Groups (Cells)
                        ss_cells = 0
                        cell_means = {}
                        for key, vals in data_dict.items():
                            cell_mean = np.mean(vals)
                            cell_means[key] = cell_mean
                            n_cell = len(vals)
                            ss_cells += n_cell * (cell_mean - grand_mean) ** 2
                        
                        # SS Main Effects
                        # Tool
                        tool_means = {}
                        for t in unique_tools:
                            vals_t = np.concatenate([data_dict[(t, e)] for e in unique_exps])
                            tool_means[t] = np.mean(vals_t)
                        
                        ss_tool = 0
                        for t, mean_t in tool_means.items():
                            n_t = sum(len(data_dict[(t, e)]) for e in unique_exps)
                            ss_tool += n_t * (mean_t - grand_mean) ** 2
                        
                        # Experience
                        exp_means = {}
                        for e in unique_exps:
                            vals_e = np.concatenate([data_dict[(t, e)] for t in unique_tools])
                            exp_means[e] = np.mean(vals_e)
                        
                        ss_exp = 0
                        for e, mean_e in exp_means.items():
                            n_e = sum(len(data_dict[(t, e)]) for t in unique_tools)
                            ss_exp += n_e * (mean_e - grand_mean) ** 2
                        
                        # Interaction
                        ss_interaction = ss_cells - ss_tool - ss_exp
                        
                        # Degrees of Freedom
                        df_tool = len(unique_tools) - 1
                        df_exp = len(unique_exps) - 1
                        df_interaction = df_tool * df_exp
                        df_error = n_total - (len(unique_tools) * len(unique_exps))
                        
                        # Mean Squares
                        ms_tool = ss_tool / df_tool if df_tool > 0 else 0
                        ms_exp = ss_exp / df_exp if df_exp > 0 else 0
                        ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
                        ms_error = (ss_total - ss_cells) / df_error if df_error > 0 else 1
                        
                        # F Statistics
                        f_tool = ms_tool / ms_error if ms_error > 0 else 0
                        f_exp = ms_exp / ms_error if ms_error > 0 else 0
                        f_interaction = ms_interaction / ms_error if ms_error > 0 else 0
                        
                        # P-values
                        p_tool = 1 - stats.f.cdf(f_tool, df_tool, df_error)
                        p_exp = 1 - stats.f.cdf(f_exp, df_exp, df_error)
                        p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)
                        
                        anova_result = {
                            'f_statistic': f_exp,
                            'p_value': p_exp,
                            'df': (df_exp, df_error)
                        }
                        interaction_result = {
                            'f_statistic': f_interaction,
                            'p_value': p_interaction,
                            'df': (df_interaction, df_error)
                        }
                    else:
                        anova_result = None
                        interaction_result = None
                else:
                    anova_result = None
                    interaction_result = None
                    
            except Exception as e:
                logger.error(f"Error in ANOVA at threshold {threshold}: {e}")
                anova_result = None
                interaction_result = None

            # Effect Sizes
            effect_size_list = []
            try:
                # Perform pairwise comparisons by stratum (novice, intermediate, expert)
                # Compare tool usage groups within each experience level
                for exp_level in unique_exps:
                    subset = df[df['experience_class'] == exp_level]
                    if subset[tool_col].nunique() >= 2:
                        # Calculate Cohen's d between tool groups
                        groups_to_compare = []
                        for t in subset[tool_col].unique():
                            groups_to_compare.append(subset[subset[tool_col] == t][time_col].values)
                        
                        if len(groups_to_compare) == 2:
                            d = calculate_cohens_d(groups_to_compare[0], groups_to_compare[1])
                            effect_size_list.append({
                                'stratum': exp_level,
                                'comparison': f"Tool A vs Tool B",
                                'cohens_d': d
                            })
            except Exception as e:
                logger.error(f"Error in effect sizes at threshold {threshold}: {e}")

        # Calculate descriptive stats
        novice_data = df[df['experience_class'] == 'novice']
        intermediate_data = df[df['experience_class'] == 'intermediate']
        expert_data = df[df['experience_class'] == 'expert']
        
        def get_stats(data, col):
            if len(data) == 0:
                return 0, 0, 0
            return np.mean(data[col]), np.std(data[col]), len(data)
        
        nov_mean, nov_std, nov_n = get_stats(novice_data, time_col)
        int_mean, int_std, int_n = get_stats(intermediate_data, time_col)
        exp_mean, exp_std, exp_n = get_stats(expert_data, time_col)
        
        nov_def = np.mean(novice_data[defect_col]) if len(novice_data) > 0 else 0
        int_def = np.mean(intermediate_data[defect_col]) if len(intermediate_data) > 0 else 0
        exp_def = np.mean(expert_data[defect_col]) if len(expert_data) > 0 else 0
        
        anova_f = anova_result['f_statistic'] if anova_result else None
        anova_p = anova_result['p_value'] if anova_result else None
        inter_f = interaction_result['f_statistic'] if interaction_result else None
        inter_p = interaction_result['p_value'] if interaction_result else None
        
        is_sig = (anova_p is not None and anova_p < 0.05) or (inter_p is not None and inter_p < 0.05)
        
        result = ThresholdResult(
            threshold_years=threshold,
            novice_mean_task_time=nov_mean,
            novice_std_task_time=nov_std,
            novice_n=nov_n,
            intermediate_mean_task_time=int_mean,
            intermediate_std_task_time=int_std,
            intermediate_n=int_n,
            expert_mean_task_time=exp_mean,
            expert_std_task_time=exp_std,
            expert_n=exp_n,
            novice_defect_rate=nov_def,
            intermediate_defect_rate=int_def,
            expert_defect_rate=exp_def,
            anova_f_statistic=anova_f,
            anova_p_value=anova_p,
            interaction_f_statistic=inter_f,
            interaction_p_value=inter_p,
            effect_sizes=effect_size_list,
            power_flag=power_flag,
            is_significant=is_sig
        )
        results.append(result)
    
    return results

def generate_sensitivity_report(
    df: pd.DataFrame,
    thresholds: List[float],
    config: Dict[str, Any]
) -> SensitivityReport:
    """
    Generate a full sensitivity report.
    
    Args:
        df: Input data
        thresholds: Thresholds to test
        config: Configuration dictionary
    
    Returns:
        SensitivityReport object
    """
    logger = get_sensitivity_logger()
    logger.info("Generating sensitivity analysis report")
    
    results = run_sensitivity_sweep(df, thresholds)
    
    # Generate summary
    summary = {
        'thresholds_tested': thresholds,
        'significant_thresholds': [r.threshold_years for r in results if r.is_significant],
        'power_flags_raised': [r.threshold_years for r in results if r.power_flag],
        'variation_in_task_time': {
            'novice': [r.novice_mean_task_time for r in results],
            'intermediate': [r.intermediate_mean_task_time for r in results],
            'expert': [r.expert_mean_task_time for r in results]
        },
        'variation_in_defect_rates': {
            'novice': [r.novice_defect_rate for r in results],
            'intermediate': [r.intermediate_defect_rate for r in results],
            'expert': [r.expert_defect_rate for r in results]
        }
    }
    
    report = SensitivityReport(
        thresholds_tested=thresholds,
        results=results,
        summary=summary,
        timestamp=pd.Timestamp.now().isoformat(),
        config=config
    )
    
    return report

def export_sensitivity_report(report: SensitivityReport, output_path: str):
    """
    Export the sensitivity report to JSON.
    
    Args:
        report: SensitivityReport object
        output_path: Path to save the JSON file
    """
    logger = get_sensitivity_logger()
    logger.info(f"Exporting sensitivity report to {output_path}")
    
    # Convert dataclasses to dict
    def serialize(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize(i) for i in obj]
        else:
            return obj
    
    serializable_report = serialize(report)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_report, f, indent=2)
    
    logger.info("Sensitivity report exported successfully")

def run_sensitivity_pipeline(
    data_path: str,
    output_path: str,
    thresholds: Optional[List[float]] = None
):
    """
    Run the full sensitivity analysis pipeline.
    
    Args:
        data_path: Path to the input CSV file
        output_path: Path to save the output JSON report
        thresholds: List of thresholds to test. Defaults to [1.0, 2.0, 3.0]
    """
    if thresholds is None:
        thresholds = [1.0, 2.0, 3.0]
    
    logger = get_sensitivity_logger()
    logger.info("Starting sensitivity analysis pipeline")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_cols = ['task_time', 'defect_rate', 'experience_years', 'tool_usage']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Generate report
    config = {
        'thresholds': thresholds,
        'alpha': 0.05,
        'min_observations': 30
    }
    
    report = generate_sensitivity_report(df, thresholds, config)
    
    # Export
    export_sensitivity_report(report, output_path)
    
    logger.info("Sensitivity analysis pipeline completed")

def main():
    """Entry point for running sensitivity analysis from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity analysis for experience thresholds")
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--thresholds', type=str, default='1.0,2.0,3.0', help='Comma-separated list of thresholds')
    
    args = parser.parse_args()
    
    thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
    
    run_sensitivity_pipeline(args.input, args.output, thresholds)

if __name__ == "__main__":
    main()