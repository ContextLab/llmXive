import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config

def load_cleaned_dataset():
    """Load the final cleaned dataset from data/processed/final_cleaned_dataset.csv."""
    config = get_config()
    input_path = Path(config['data_processed_path']) / 'final_cleaned_dataset.csv'
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    log_info(f"Loaded cleaned dataset with {len(df)} records from {input_path}")
    return df

def load_statistical_analysis_results():
    """Load statistical results from the analysis pipeline (T018, T019, T020)."""
    # We expect T018 (Welch's t-test), T019 (Bonferroni), and T020 (Effect Size)
    # to have produced intermediate results. For T022, we assume these are
    # aggregated in a temporary state or we re-run the necessary calculations
    # from the cleaned dataset if intermediate files are missing.
    # However, per task dependencies, T019 and T020 are completed.
    # We will construct the results based on the standard output of T018-T021 logic.
    
    # Since T018, T019, T020, T021 are marked completed, we assume their outputs
    # are available or we can derive them. To be robust, we will re-run the
    # core statistical logic on the cleaned dataset to ensure the report is
    # generated from the current state of the data, ensuring consistency.
    
    # This function effectively re-calculates the statistics required for the report
    # to ensure the report is accurate and up-to-date.
    
    return None # Placeholder, logic moved to run_analysis_pipeline

def load_power_analysis_results():
    """Load power analysis results (T021)."""
    # Similar to statistical results, we will ensure the power analysis is
    # performed as part of the report generation to guarantee accuracy.
    return None

def run_analysis_pipeline(df):
    """Run the statistical analysis pipeline on the cleaned dataset."""
    from scipy import stats
    from statsmodels.stats.power import power_analysis

    results = []
    
    # Group by stimulus_type: 'nostalgia' and 'control'
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']
    control_group = df[df['stimulus_type'] == 'control']
    
    if nostalgia_group.empty or control_group.empty:
        log_error("One or both groups are empty. Cannot perform analysis.")
        return []

    metrics = ['perseverative_errors', 'categories_completed']
    
    for metric in metrics:
        if metric not in df.columns:
            log_warning(f"Metric {metric} not found in dataset, skipping.")
            continue
        
        y1 = nostalgia_group[metric].dropna()
        y2 = control_group[metric].dropna()
        
        if len(y1) < 2 or len(y2) < 2:
            log_warning(f"Sample size too small for {metric}, skipping.")
            continue
        
        # Welch's t-test
        t_stat, p_raw = stats.ttest_ind(y1, y2, equal_var=False)
        
        # Bonferroni correction (2 comparisons)
        p_corr = p_raw * 2
        if p_corr > 1.0:
            p_corr = 1.0
        
        # Effect Size (Cohen's d)
        # d = (mean1 - mean2) / pooled_std
        # Using Hedges' g approximation or standard Cohen's d
        n1, n2 = len(y1), len(y2)
        mean1, mean2 = y1.mean(), y2.mean()
        std1, std2 = y1.std(ddof=1), y2.std(ddof=1)
        
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        if pooled_std == 0:
            cohens_d = 0.0
        else:
            cohens_d = (mean1 - mean2) / pooled_std
        
        # 95% CI for Cohen's d (approximation)
        # Using non-central t-distribution or approximation
        # Simple approximation: d +/- 1.96 * SE_d
        # SE_d approx sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
        se_d = np.sqrt((n1 + n2) / (n1 * n2) + (cohens_d**2) / (2 * (n1 + n2)))
        ci_lower = cohens_d - 1.96 * se_d
        ci_upper = cohens_d + 1.96 * se_d
        
        results.append({
            'metric': metric,
            'group_nostalgia': {
                'n': int(n1),
                'mean': float(mean1),
                'std': float(std1)
            },
            'group_control': {
                'n': int(n2),
                'mean': float(mean2),
                'std': float(std2)
            },
            't_statistic': float(t_stat),
            'p_value_raw': float(p_raw),
            'p_value_corrected': float(p_corr),
            'effect_size': {
                'cohen_d': float(cohens_d),
                'ci_95_lower': float(ci_lower),
                'ci_95_upper': float(ci_upper)
            }
        })
    
    return results

def run_power_pipeline(df, analysis_results):
    """Run power analysis and MDES calculation for each comparison."""
    from statsmodels.stats.power import TTestIndPower
    
    power_results = []
    alpha = 0.05
    power_analysis_obj = TTestIndPower()
    
    for res in analysis_results:
        n1 = res['group_nostalgia']['n']
        n2 = res['group_control']['n']
        d = res['effect_size']['cohen_d']
        
        # Calculate Power
        # power = TTestIndPower().power(effect_size=d, n1=n1, n2=n2, alpha=alpha)
        # Handle edge cases where d might be 0 or NaN
        if d == 0 or np.isnan(d):
            power = 0.0
        else:
            try:
                power = power_analysis_obj.power(effect_size=abs(d), n1=n1, n2=n2, alpha=alpha)
            except Exception:
                power = 0.0
        
        # Calculate MDES (Minimum Detectable Effect Size) for 80% power
        # Solve for effect_size given n1, n2, alpha, power=0.8
        target_power = 0.8
        try:
            mdes = power_analysis_obj.solve_power(n1=n1, n2=n2, alpha=alpha, power=target_power)
        except Exception:
            mdes = float('inf')
        
        power_results.append({
            'metric': res['metric'],
            'statistical_power': float(power),
            'minimum_detectable_effect_size': float(mdes) if mdes != float('inf') else None,
            'alpha': alpha,
            'sample_size_nostalgia': n1,
            'sample_size_control': n2
        })
    
    return power_results

def compile_final_report(analysis_results, power_results):
    """Compile the final statistical report."""
    comparisons = []
    significant_05 = 0
    significant_01 = 0
    total_power = 0.0
    total_mdes = 0.0
    count = 0
    
    for i, res in enumerate(analysis_results):
        # Attach power analysis results
        power_res = power_results[i]
        comparison = {
            'metric': res['metric'],
            'group_nostalgia': res['group_nostalgia'],
            'group_control': res['group_control'],
            't_statistic': res['t_statistic'],
            'p_value_raw': res['p_value_raw'],
            'p_value_corrected': res['p_value_corrected'],
            'effect_size': res['effect_size'],
            'power_analysis': {
                'statistical_power': power_res['statistical_power'],
                'minimum_detectable_effect_size': power_res['minimum_detectable_effect_size'],
                'alpha': power_res['alpha'],
                'sample_size_nostalgia': power_res['sample_size_nostalgia'],
                'sample_size_control': power_res['sample_size_control']
            }
        }
        comparisons.append(comparison)
        
        if comparison['p_value_corrected'] < 0.05:
            significant_05 += 1
        if comparison['p_value_corrected'] < 0.01:
            significant_01 += 1
        
        total_power += comparison['power_analysis']['statistical_power']
        if comparison['power_analysis']['minimum_detectable_effect_size'] is not None:
            total_mdes += comparison['power_analysis']['minimum_detectable_effect_size']
            count += 1
    
    avg_power = total_power / len(comparisons) if comparisons else 0.0
    avg_mdes = total_mdes / count if count > 0 else 0.0
    
    report = {
        'report_metadata': {
            'task_id': 'T022',
            'description': 'Statistical Report: p-values, effect sizes, power, MDES',
            'analysis_method': "Welch's independent samples t-test",
            'correction_method': 'Bonferroni',
            'generated_at': get_timestamp()
        },
        'comparisons': comparisons,
        'summary': {
            'total_comparisons': len(comparisons),
            'significant_at_alpha_05': significant_05,
            'significant_at_alpha_01': significant_01,
            'average_power': round(avg_power, 3),
            'average_mdes': round(avg_mdes, 3)
        }
    }
    
    return report

def save_report(report):
    """Save the final report to data/results/statistical_report.json."""
    config = get_config()
    output_dir = Path(config['data_results_path'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'statistical_report.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Statistical report saved to {output_path}")
    return output_path

def main():
    """Main entry point for T022."""
    setup_logging()
    log_info("Starting T022: Generate Statistical Report")
    
    try:
        # 1. Load cleaned dataset
        df = load_cleaned_dataset()
        
        # 2. Run analysis pipeline (T018, T019, T020 logic)
        analysis_results = run_analysis_pipeline(df)
        
        if not analysis_results:
            log_error("No analysis results generated. Aborting report generation.")
            return
        
        # 3. Run power analysis pipeline (T021 logic)
        power_results = run_power_pipeline(df, analysis_results)
        
        # 4. Compile final report
        report = compile_final_report(analysis_results, power_results)
        
        # 5. Save report
        save_report(report)
        
        log_info("T022 completed successfully.")
        
    except FileNotFoundError as e:
        log_error(f"Data file missing: {e}")
        raise
    except Exception as e:
        log_error(f"Error during report generation: {e}")
        raise

if __name__ == "__main__":
    main()