import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Statistical imports
try:
    import pandas as pd
    import numpy as np
    from scipy.stats import wilcoxon
    from statsmodels.regression.mixed_linear_model import MixedLM
    from statsmodels.genmod.generalized_linear_model import GLM
    from statsmodels.genmod import families
    from statsmodels.tools import add_constant
except ImportError as e:
    print(f"CRITICAL: Required statistical libraries not found. Install with: pip install pandas numpy scipy statsmodels")
    sys.exit(1)

from utils.config import get_project_root, get_data_dir
from utils.execution_log import ExecutionLog


def load_execution_logs(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load execution logs from a JSONL file.
    
    Args:
        log_path: Path to the JSONL file containing execution logs
        
    Returns:
        List of log entries as dictionaries
    """
    logs = []
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs


def calculate_step_success_rates(logs: List[Dict[str, Any]], 
                                 early_threshold: int = 10,
                                 late_threshold: int = 20) -> Dict[str, float]:
    """
    Calculate success rates for early vs late steps in trajectories.
    
    Args:
        logs: List of execution log entries
        early_threshold: Max step index to consider 'early'
        late_threshold: Min step index to consider 'late'
        
    Returns:
        Dictionary with success rates for early and late steps
    """
    early_success = 0
    early_total = 0
    late_success = 0
    late_total = 0
    
    for log in logs:
        steps = log.get('steps', [])
        for step in steps:
            step_idx = step.get('step_index', 0)
            success = step.get('success', False)
            
            if step_idx <= early_threshold:
                early_total += 1
                if success:
                    early_success += 1
            elif step_idx >= late_threshold:
                late_total += 1
                if success:
                    late_success += 1
    
    early_rate = early_success / early_total if early_total > 0 else 0.0
    late_rate = late_success / late_total if late_total > 0 else 0.0
    
    return {
        'early_success': early_success,
        'early_total': early_total,
        'early_rate': early_rate,
        'late_success': late_success,
        'late_total': late_total,
        'late_rate': late_rate
    }


def analyze_baseline_trend(baseline_log_path: Path) -> Dict[str, Any]:
    """
    Analyze success rate trend for baseline execution logs.
    
    Args:
        baseline_log_path: Path to baseline execution logs JSONL
        
    Returns:
        Dictionary containing trend analysis results
    """
    print(f"Loading baseline logs from {baseline_log_path}")
    logs = load_execution_logs(baseline_log_path)
    
    if not logs:
        raise ValueError(f"No logs found in {baseline_log_path}")
    
    print(f"Loaded {len(logs)} trajectory logs")
    
    # Calculate step success rates
    rates = calculate_step_success_rates(logs)
    
    # Calculate trend (difference between early and late)
    trend = rates['early_rate'] - rates['late_rate']
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'baseline_success_rate_trend',
        'early_steps': {
            'success_count': rates['early_success'],
            'total_count': rates['early_total'],
            'success_rate': rates['early_rate']
        },
        'late_steps': {
            'success_count': rates['late_success'],
            'total_count': rates['late_total'],
            'success_rate': rates['late_rate']
        },
        'trend': {
            'difference': trend,
            'interpretation': 'decay' if trend > 0 else 'improvement' if trend < 0 else 'stable'
        },
        'total_trajectories': len(logs)
    }
    
    return result


def compare_agents(baseline_log_path: Path, 
                   recall_log_path: Path) -> Dict[str, Any]:
    """
    Compare success rates between baseline and recall agents.
    
    Args:
        baseline_log_path: Path to baseline execution logs
        recall_log_path: Path to recall execution logs
        
    Returns:
        Dictionary containing comparison results
    """
    print(f"Loading baseline logs from {baseline_log_path}")
    baseline_logs = load_execution_logs(baseline_log_path)
    
    print(f"Loading recall logs from {recall_log_path}")
    recall_logs = load_execution_logs(recall_log_path)
    
    if not baseline_logs or not recall_logs:
        raise ValueError("One or both log files are empty")
    
    # Calculate rates for both
    baseline_rates = calculate_step_success_rates(baseline_logs)
    recall_rates = calculate_step_success_rates(recall_logs)
    
    # Wilcoxon signed-rank test on per-trajectory success rates
    # Group by trajectory and calculate success rate per trajectory
    baseline_traj_rates = []
    recall_traj_rates = []
    
    # Process baseline trajectories
    for log in baseline_logs:
        steps = log.get('steps', [])
        if steps:
            success_count = sum(1 for s in steps if s.get('success', False))
            rate = success_count / len(steps)
            baseline_traj_rates.append(rate)
    
    # Process recall trajectories (assuming same trajectories in same order)
    for log in recall_logs:
        steps = log.get('steps', [])
        if steps:
            success_count = sum(1 for s in steps if s.get('success', False))
            rate = success_count / len(steps)
            recall_traj_rates.append(rate)
    
    # Perform Wilcoxon test
    if len(baseline_traj_rates) >= 2 and len(recall_traj_rates) >= 2:
        stat, p_value = wilcoxon(baseline_traj_rates, recall_traj_rates)
    else:
        stat, p_value = 0.0, 1.0  # Not enough data for test
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'baseline_vs_recall_comparison',
        'baseline': {
            'total_trajectories': len(baseline_logs),
            'early_rate': baseline_rates['early_rate'],
            'late_rate': baseline_rates['late_rate'],
            'per_trajectory_rates': baseline_traj_rates
        },
        'recall': {
            'total_trajectories': len(recall_logs),
            'early_rate': recall_rates['early_rate'],
            'late_rate': recall_rates['late_rate'],
            'per_trajectory_rates': recall_traj_rates
        },
        'wilcoxon_test': {
            'statistic': float(stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05
        },
        'improvement': {
            'early_rate_diff': recall_rates['early_rate'] - baseline_rates['early_rate'],
            'late_rate_diff': recall_rates['late_rate'] - baseline_rates['late_rate']
        }
    }
    
    return result


def run_statistical_analysis(output_dir: Path) -> None:
    """
    Run all statistical analyses and save results.
    
    Args:
        output_dir: Directory to save analysis results
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    baseline_log_path = Path(data_dir) / "results" / "baseline_execution_logs.jsonl"
    recall_log_path = Path(data_dir) / "results" / "recall_execution_logs.jsonl"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Analyze baseline trend
    if baseline_log_path.exists():
        print("\n=== Analyzing Baseline Success Rate Trend ===")
        try:
            baseline_result = analyze_baseline_trend(baseline_log_path)
            results['baseline_trend'] = baseline_result
            
            # Save baseline trend
            baseline_trend_path = output_dir / "baseline_trend_analysis.json"
            with open(baseline_trend_path, 'w') as f:
                json.dump(baseline_result, f, indent=2)
            print(f"Baseline trend analysis saved to {baseline_trend_path}")
            
            # Print summary
            print(f"Early Step Success Rate: {baseline_result['early_steps']['success_rate']:.2%}")
            print(f"Late Step Success Rate: {baseline_result['late_steps']['success_rate']:.2%}")
            print(f"Trend (Early - Late): {baseline_result['trend']['difference']:.2%} ({baseline_result['trend']['interpretation']})")
            
        except Exception as e:
            print(f"Error analyzing baseline trend: {e}")
            results['baseline_trend_error'] = str(e)
    else:
        print(f"Warning: Baseline log file not found at {baseline_log_path}")
    
    # Compare agents if both logs exist
    if baseline_log_path.exists() and recall_log_path.exists():
        print("\n=== Comparing Baseline vs Recall Agents ===")
        try:
            comparison_result = compare_agents(baseline_log_path, recall_log_path)
            results['agent_comparison'] = comparison_result
            
            # Save comparison
            comparison_path = output_dir / "agent_comparison_analysis.json"
            with open(comparison_path, 'w') as f:
                json.dump(comparison_result, f, indent=2)
            print(f"Agent comparison saved to {comparison_path}")
            
            # Print summary
            print(f"Baseline Early Rate: {comparison_result['baseline']['early_rate']:.2%}")
            print(f"Recall Early Rate: {comparison_result['recall']['early_rate']:.2%}")
            print(f"Early Rate Improvement: {comparison_result['improvement']['early_rate_diff']:.2%}")
            print(f"Wilcoxon p-value: {comparison_result['wilcoxon_test']['p_value']:.4f}")
            print(f"Statistically Significant: {'Yes' if comparison_result['wilcoxon_test']['significant'] else 'No'}")
            
        except Exception as e:
            print(f"Error comparing agents: {e}")
            results['agent_comparison_error'] = str(e)
    else:
        missing = []
        if not baseline_log_path.exists():
            missing.append("baseline_execution_logs.jsonl")
        if not recall_log_path.exists():
            missing.append("recall_execution_logs.jsonl")
        print(f"Warning: Cannot compare agents. Missing: {', '.join(missing)}")
    
    # Save overall results
    overall_path = output_dir / "statistical_analysis_results.json"
    with open(overall_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nOverall results saved to {overall_path}")


def main():
    """Main entry point for statistical analysis."""
    print("Starting statistical analysis for llmXive follow-up project")
    
    project_root = get_project_root()
    output_dir = Path(project_root) / "data" / "results"
    
    try:
        run_statistical_analysis(output_dir)
        print("\nStatistical analysis completed successfully")
    except Exception as e:
        print(f"\nStatistical analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()