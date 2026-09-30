import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
import numpy as np

from config import (
    get_config, get_results_dir, get_processed_dir, 
    LlmXiveError, ConfigError, ValidationError
)

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_metrics_data(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Load metric data from the results directory.
    Expects a CSV or JSON file containing metrics for baseline and corrected videos.
    For this implementation, we assume a standard metrics file exists from previous steps.
    """
    metrics_file = results_dir / "metrics_raw.json"
    if not metrics_file.exists():
        # Fallback: try to construct from individual video results if a aggregate doesn't exist
        # This is a robustness check for the pipeline state
        logger.warning(f"Metrics file {metrics_file} not found. Attempting to aggregate individual results.")
        # In a real scenario, we would scan data/results/ for specific metric files
        # For now, we raise a clear error if the expected input is missing
        raise FileNotFoundError(f"Required metrics input file {metrics_file} not found. "
                                "Ensure T022 (warping) and T037 (metrics calculation) have run.")
    
    with open(metrics_file, 'r') as f:
        return json.load(f)

def load_pilot_variance(pilot_file: Path) -> Dict[str, Any]:
    """
    Load the pilot variance data from T017.
    """
    if not pilot_file.exists():
        raise FileNotFoundError(f"Pilot variance file {pilot_file} not found. "
                                "Run T017 (pilot_study.py) first.")
    with open(pilot_file, 'r') as f:
        return json.load(f)

def calculate_power(pilot_variance: Dict[str, Any], n_samples: int = 50) -> Dict[str, Any]:
    """
    Calculate statistical power based on pilot variance.
    Returns a dict with 'power', 'sufficient' (bool), and details.
    """
    # Placeholder for actual power calculation logic using statsmodels
    # Since T030a is completed, we assume the logic exists or is imported.
    # However, to be self-contained for T027, we implement the logic here
    # assuming the pilot variance provides 'std' and 'mean'.
    std_dev = pilot_variance.get('std', 0.1)
    mean_diff = pilot_variance.get('mean', 0.05)
    
    if std_dev == 0:
        return {'power': 1.0, 'sufficient': True, 'details': 'Zero variance'}

    # Simple approximation or call to statsmodels
    # Using statsmodels.stats.power.tt_solve_power if available, else simplified logic
    try:
        from statsmodels.stats.power import TTestPower
        effect_size = abs(mean_diff) / std_dev
        power_analysis = TTestPower()
        power = power_analysis.solve_power(effect_size=effect_size, nobs1=n_samples, alpha=0.05, alternative='two-sided')
        return {
            'power': float(power),
            'sufficient': power >= 0.8,
            'details': f'Effect size: {effect_size:.4f}, N: {n_samples}'
        }
    except ImportError:
        logger.warning("statsmodels not found. Using simplified heuristic for power.")
        # Heuristic: if effect size > 0.5 and N=50, assume sufficient
        effect_size = abs(mean_diff) / std_dev
        sufficient = effect_size > 0.5
        return {
            'power': 0.85 if sufficient else 0.4,
            'sufficient': sufficient,
            'details': 'Heuristic estimate (statsmodels missing)'
        }

def run_power_analysis(metrics_data: List[Dict[str, Any]], pilot_file: Path) -> Dict[str, Any]:
    """
    Run the full power analysis pipeline.
    Depends on T030a completion.
    """
    pilot_data = load_pilot_variance(pilot_file)
    result = calculate_power(pilot_data)
    
    # Generate report file
    results_dir = get_results_dir()
    report_path = results_dir / "power_analysis_report.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# Power Analysis Report\n\n")
        f.write(f"- **Power**: {result['power']:.4f}\n")
        f.write(f"- **Sufficient (>= 0.8)**: {result['sufficient']}\n")
        f.write(f"- **Details**: {result['details']}\n\n")
        if not result['sufficient']:
            f.write("## WARNING\n")
            f.write("The study is **UNDERPOWERED**. Statistical tests (T027/T028) may yield unreliable results.\n")
    
    return result

def generate_power_report(power_result: Dict[str, Any], output_path: Path) -> None:
    """
    Helper to write the power report (already done in run_power_analysis, but exposed for API consistency).
    """
    pass

def check_normality(differences: List[float]) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality on the list of differences.
    
    Args:
        differences: List of metric differences (Corrected - Baseline)
        
    Returns:
        Dict with 'p_value', 'is_normal' (bool), 'statistic'
    """
    if len(differences) < 3:
        logger.warning("Less than 3 data points for normality test. Assuming non-normal for safety.")
        return {'p_value': 0.0, 'is_normal': False, 'statistic': 0.0, 'reason': 'Insufficient data'}
    
    try:
        stat, p_value = stats.shapiro(differences)
        is_normal = p_value >= 0.05
        return {
            'p_value': float(p_value),
            'is_normal': is_normal,
            'statistic': float(stat)
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        # Fail safe: assume non-normal if test fails
        return {'p_value': 0.0, 'is_normal': False, 'statistic': 0.0, 'error': str(e)}

def run_significance_test(differences: List[float], test_type: str) -> Dict[str, Any]:
    """
    Run the appropriate significance test based on normality.
    
    Args:
        differences: List of metric differences
        test_type: 't-test' or 'wilcoxon'
        
    Returns:
        Dict with 'test_type', 'p_value', 'statistic'
    """
    if len(differences) < 2:
        raise ValueError("Need at least 2 differences to run significance test.")
    
    if test_type == 't-test':
        stat, p_value = stats.ttest_rel(differences, [0]*len(differences)) # Paired t-test against 0
        # Or ttest_rel(a, b) if we had two arrays. Here we have differences.
        # If differences are (A-B), we test if mean(differences) != 0.
        # stats.ttest_1samp is more appropriate for a list of differences against 0.
        stat, p_value = stats.ttest_1samp(differences, 0.0)
        return {
            'test_type': 'paired_t_test',
            'p_value': float(p_value),
            'statistic': float(stat)
        }
    elif test_type == 'wilcoxon':
        stat, p_value = stats.wilcoxon(differences)
        return {
            'test_type': 'wilcoxon_signed_rank',
            'p_value': float(p_value),
            'statistic': float(stat)
        }
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def perform_statistical_analysis(metrics_data: List[Dict[str, Any]], power_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function for T027: Perform Shapiro-Wilk and significance testing.
    
    Logic:
    1. Extract differences for a specific metric (e.g., Object Permanence) between conditions.
    2. Run Shapiro-Wilk.
    3. If p < 0.05 -> Wilcoxon. Else -> Paired t-test.
    4. Return results.
    """
    if not power_result.get('sufficient', False):
        logger.warning("Power analysis indicates study is underpowered. Proceeding with caution.")
        # We continue but flag the result
    
    # Assume we are analyzing 'object_permanence' differences
    # We need to pair data by video_id
    baseline_scores = {}
    corrected_scores = {}
    
    for item in metrics_data:
        vid = item['video_id']
        cond = item['condition']
        if cond == 'baseline':
            baseline_scores[vid] = item['object_permanence']
        elif cond == 'corrected':
            corrected_scores[vid] = item['object_permanence']
    
    common_videos = set(baseline_scores.keys()) & set(corrected_scores.keys())
    if not common_videos:
        raise ValueError("No common videos found between baseline and corrected sets.")
    
    differences = [corrected_scores[v] - baseline_scores[v] for v in common_videos]
    
    # Step 1: Normality Check
    normality_result = check_normality(differences)
    logger.info(f"Normality Check (Shapiro-Wilk): p={normality_result['p_value']:.4f}, is_normal={normality_result['is_normal']}")
    
    # Step 2: Select Test
    if normality_result['is_normal']:
        test_type = 't-test'
    else:
        test_type = 'wilcoxon'
    
    # Step 3: Run Test
    significance_result = run_significance_test(differences, test_type)
    
    return {
        'normality': normality_result,
        'significance': significance_result,
        'n_samples': len(differences),
        'power_sufficient': power_result.get('sufficient', False)
    }

def main():
    """
    Entry point for T027.
    Usage: python code/analyze.py --task t027
    """
    parser = argparse.ArgumentParser(description="Analyze metrics for T027 (Statistical Testing)")
    parser.add_argument('--task', type=str, default='t027', help='Task identifier')
    parser.add_argument('--metrics-file', type=str, help='Path to metrics JSON file')
    parser.add_argument('--pilot-file', type=str, help='Path to pilot variance JSON file')
    args = parser.parse_args()
    
    config = get_config()
    results_dir = get_results_dir()
    
    # Determine input paths
    metrics_path = Path(args.metrics_file) if args.metrics_file else (results_dir / "metrics_raw.json")
    pilot_path = Path(args.pilot_file) if args.pilot_file else (results_dir.parent / "data" / "pilot_variance.json")
    
    # 1. Load Data
    try:
        metrics_data = load_metrics_data(results_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Power Analysis (Gatekeeper)
    try:
        power_result = run_power_analysis(metrics_data, pilot_path)
    except FileNotFoundError as e:
        logger.error(f"Power analysis failed (missing pilot data): {e}")
        sys.exit(1)
    
    # 3. Statistical Testing (T027 Core)
    try:
        analysis_result = perform_statistical_analysis(metrics_data, power_result)
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        sys.exit(1)
    
    # 4. Output Results
    output_file = results_dir / "statistical_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    logger.info(f"Statistical analysis complete. Results saved to {output_file}")
    print(json.dumps(analysis_result, indent=2))

if __name__ == "__main__":
    main()