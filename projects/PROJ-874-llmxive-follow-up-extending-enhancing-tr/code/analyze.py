import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestPower, WilcoxonPower

from config import get_config, get_results_dir, get_processed_dir, LlmXiveError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_pilot_variance(pilot_file: str = None) -> dict:
    """Load pilot study variance results."""
    if pilot_file is None:
        config = get_config()
        pilot_file = os.path.join(config.get_results_dir(), 'pilot_variance.json')
    
    if not os.path.exists(pilot_file):
        raise LlmXiveError(f"Pilot variance file not found: {pilot_file}")
    
    with open(pilot_file, 'r') as f:
        return json.load(f)

def calculate_power(effect_size: float, std_dev: float, n_samples: int, alpha: float = 0.05) -> float:
    """Calculate statistical power for a given effect size and sample size."""
    # For t-test, effect_size is Cohen's d
    # d = effect / std_dev
    if std_dev == 0:
        return 1.0 if effect_size == 0 else 0.0
    
    d = abs(effect_size) / std_dev
    power_calc = TTestPower()
    power = power_calc.solve_power(effect_size=d, nobs1=n_samples, alpha=alpha, ratio=1.0)
    return power

def run_power_analysis(pilot_results: dict, target_n: int = 50, alpha: float = 0.05) -> dict:
    """Run power analysis based on pilot study results."""
    mean = pilot_results.get('mean', 0)
    std = pilot_results.get('std', 1)
    n_samples = pilot_results.get('n_samples', 1)
    
    # Calculate effect size (assuming we're testing against 0 difference)
    effect_size = abs(mean)
    
    power = calculate_power(effect_size, std, target_n, alpha)
    
    return {
        'power': power,
        'target_n': target_n,
        'alpha': alpha,
        'sufficient': power >= 0.8,
        'effect_size': effect_size,
        'std_dev': std,
        'pilot_n': n_samples
    }

def check_normality(data: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Perform Shapiro-Wilk test for normality.
    
    Returns:
        dict with 'p_value', 'is_normal', 'statistic'
        
    Note: p < 0.05 implies non-normality (reject null hypothesis of normality)
    """
    if len(data) < 3:
        logger.warning("Insufficient data points for normality test (n < 3). Assuming normal.")
        return {
            'p_value': 1.0,
            'is_normal': True,
            'statistic': 1.0,
            'note': 'Insufficient data points'
        }
    
    statistic, p_value = stats.shapiro(data)
    is_normal = p_value >= alpha
    
    return {
        'p_value': p_value,
        'is_normal': is_normal,
        'statistic': statistic
    }

def perform_statistical_test(data_baseline: np.ndarray, data_corrected: np.ndarray, 
                             alpha: float = 0.05) -> dict:
    """
    Perform adaptive statistical testing:
    1. Check normality of differences (Shapiro-Wilk)
    2. If p < 0.05 (non-normal), use Wilcoxon signed-rank test
    3. If p >= 0.05 (normal), use paired t-test
    
    Args:
        data_baseline: Metrics from baseline condition
        data_corrected: Metrics from corrected condition
        alpha: Significance level (default 0.05)
        
    Returns:
        dict with 'test_type', 'p_value', 'statistic', 'significant', 'normality_test'
    """
    if len(data_baseline) != len(data_corrected):
        raise ValueError(f"Data lengths must match: {len(data_baseline)} vs {len(data_corrected)}")
    
    if len(data_baseline) < 2:
        raise ValueError(f"Insufficient data points for statistical test (n={len(data_baseline)})")
    
    # Calculate differences
    differences = data_corrected - data_baseline
    
    # Step 1: Check normality of differences
    normality_result = check_normality(differences, alpha)
    
    # Step 2: Choose test based on normality
    if not normality_result['is_normal']:
        # Non-normal: Use Wilcoxon signed-rank test
        statistic, p_value = stats.wilcoxon(differences)
        test_type = 'wilcoxon_signed_rank'
        logger.info(f"Normality rejected (p={normality_result['p_value']:.4f}). Using Wilcoxon signed-rank test.")
    else:
        # Normal: Use paired t-test
        statistic, p_value = stats.ttest_rel(data_corrected, data_baseline)
        test_type = 'paired_t_test'
        logger.info(f"Normality not rejected (p={normality_result['p_value']:.4f}). Using paired t-test.")
    
    significant = p_value < alpha
    
    return {
        'test_type': test_type,
        'p_value': p_value,
        'statistic': statistic,
        'significant': significant,
        'normality_test': normality_result,
        'alpha': alpha
    }

def load_metrics_from_json(metrics_file: str) -> dict:
    """Load metrics from a JSON file."""
    if not os.path.exists(metrics_file):
        raise LlmXiveError(f"Metrics file not found: {metrics_file}")
    
    with open(metrics_file, 'r') as f:
        return json.load(f)

def identify_failure_cases(metrics_data: dict, threshold_permanence: float = 0.05, 
                           threshold_vbench: float = 0.1) -> list:
    """
    Identify videos where the corrected condition shows significant degradation.
    
    Flags videos where:
    - Object permanence drops >= threshold_permanence (5%)
    - VBench score drops >= threshold_vbench (0.1)
    
    Returns:
        list of dicts with video_id, condition, and failure reasons
    """
    failure_cases = []
    
    for video_id, metrics in metrics_data.items():
        if 'baseline' not in metrics or 'corrected' not in metrics:
            logger.warning(f"Skipping {video_id}: missing baseline or corrected metrics")
            continue
        
        baseline = metrics['baseline']
        corrected = metrics['corrected']
        
        reasons = []
        
        # Check object permanence drop
        if 'object_permanence' in baseline and 'object_permanence' in corrected:
            perm_drop = baseline['object_permanence'] - corrected['object_permanence']
            if perm_drop >= threshold_permanence:
                reasons.append(f"Object permanence drop: {perm_drop:.4f} (>= {threshold_permanence})")
        
        # Check VBench score drop
        if 'vbench_score' in baseline and 'vbench_score' in corrected:
            vbench_drop = baseline['vbench_score'] - corrected['vbench_score']
            if vbench_drop >= threshold_vbench:
                reasons.append(f"VBench score drop: {vbench_drop:.4f} (>= {threshold_vbench})")
        
        if reasons:
            failure_cases.append({
                'video_id': video_id,
                'baseline_metrics': baseline,
                'corrected_metrics': corrected,
                'failure_reasons': reasons,
                'note': 'These are 2D perceptual proxies and do not guarantee 3D geometric correctness'
            })
    
    return failure_cases

def generate_report(metrics_data: dict, power_analysis: dict, statistical_results: dict, 
                   output_file: str = None) -> str:
    """
    Generate a comprehensive report including metrics, power analysis, and statistical tests.
    
    Returns:
        Path to the generated report file
    """
    if output_file is None:
        config = get_config()
        output_file = os.path.join(config.get_results_dir(), 'analysis_report.json')
    
    report = {
        'power_analysis': power_analysis,
        'statistical_test': statistical_results,
        'metrics_summary': {
            'total_videos': len(metrics_data),
            'videos_analyzed': sum(1 for v in metrics_data.values() if 'baseline' in v and 'corrected' in v)
        },
        'note': 'Power analysis gate: if power < 0.8, statistical tests may be invalid'
    }
    
    # Add per-video metrics if available
    video_summaries = []
    for video_id, metrics in metrics_data.items():
        if 'baseline' in metrics and 'corrected' in metrics:
            baseline = metrics['baseline']
            corrected = metrics['corrected']
            
            summary = {
                'video_id': video_id,
                'condition_baseline': baseline.get('condition', 'baseline'),
                'condition_corrected': corrected.get('condition', 'corrected'),
                'vbench_score_baseline': baseline.get('vbench_score'),
                'vbench_score_corrected': corrected.get('vbench_score'),
                'fvd_baseline': baseline.get('fvd'),
                'fvd_corrected': corrected.get('fvd'),
                'object_permanence_baseline': baseline.get('object_permanence'),
                'object_permanence_corrected': corrected.get('object_permanence'),
                'p_value': statistical_results.get('p_value'),
                'test_type': statistical_results.get('test_type'),
                'power_sufficient': power_analysis.get('sufficient', False)
            }
            video_summaries.append(summary)
    
    report['video_summaries'] = video_summaries
    
    # Write report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report generated: {output_file}")
    return output_file

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Run statistical analysis on video generation metrics')
    parser.add_argument('--pilot-file', type=str, default=None,
                      help='Path to pilot variance JSON file')
    parser.add_argument('--metrics-file', type=str, required=True,
                      help='Path to metrics JSON file')
    parser.add_argument('--output-file', type=str, default=None,
                      help='Path to output report file')
    parser.add_argument('--target-n', type=int, default=50,
                      help='Target sample size for power analysis')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='Significance level')
    
    args = parser.parse_args()
    
    try:
        # Load pilot variance
        pilot_results = load_pilot_variance(args.pilot_file)
        logger.info(f"Loaded pilot variance: n={pilot_results.get('n_samples')}, "
                   f"mean={pilot_results.get('mean'):.4f}, std={pilot_results.get('std'):.4f}")
        
        # Run power analysis
        power_analysis = run_power_analysis(pilot_results, args.target_n, args.alpha)
        logger.info(f"Power analysis: power={power_analysis['power']:.4f}, "
                   f"sufficient={power_analysis['sufficient']}")
        
        # Load metrics
        metrics_data = load_metrics_from_json(args.metrics_file)
        logger.info(f"Loaded metrics for {len(metrics_data)} videos")
        
        # Extract baseline and corrected metrics for statistical testing
        baseline_metrics = []
        corrected_metrics = []
        
        for video_id, metrics in metrics_data.items():
            if 'baseline' in metrics and 'corrected' in metrics:
                # Use VBench score for statistical testing
                if 'vbench_score' in metrics['baseline'] and 'vbench_score' in metrics['corrected']:
                    baseline_metrics.append(metrics['baseline']['vbench_score'])
                    corrected_metrics.append(metrics['corrected']['vbench_score'])
        
        if len(baseline_metrics) < 2:
            logger.warning("Insufficient data for statistical test. At least 2 video pairs required.")
            statistical_results = {
                'test_type': 'skipped',
                'p_value': None,
                'statistic': None,
                'significant': None,
                'error': 'Insufficient data'
            }
        else:
            # Perform statistical test
            statistical_results = perform_statistical_test(
                np.array(baseline_metrics),
                np.array(corrected_metrics),
                args.alpha
            )
            logger.info(f"Statistical test: {statistical_results['test_type']}, "
                       f"p={statistical_results['p_value']:.4f}, "
                       f"significant={statistical_results['significant']}")
        
        # Generate report
        report_path = generate_report(metrics_data, power_analysis, statistical_results, args.output_file)
        
        # If power is insufficient, log a warning
        if not power_analysis['sufficient']:
            logger.warning("STUDY UNDERPOWERED: Power < 0.8. Statistical test results may be invalid.")
            logger.warning("Consider increasing sample size or re-running pilot study for better variance estimate.")
        
        print(f"\nAnalysis complete. Report saved to: {report_path}")
        print(f"Power sufficient: {power_analysis['sufficient']}")
        print(f"Statistical test: {statistical_results.get('test_type', 'N/A')}")
        print(f"P-value: {statistical_results.get('p_value', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()