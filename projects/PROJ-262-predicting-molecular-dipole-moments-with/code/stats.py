from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from scipy import stats

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.generate_processed_data import main as generate_processed_main
from training.train_gnn import main as train_gnn_main, parse_args as parse_gnn_args
from training.train_rf import main as train_rf_main, parse_args as parse_rf_args
from analysis.generate_significance import main as generate_significance_main
from data.handle_missing_coords import main as handle_missing_main

def load_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    """Load metrics from CSV file."""
    if not metrics_path.exists():
        return []
    
    metrics = []
    with open(metrics_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)
    return metrics

def compute_summary_statistics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics from metrics."""
    if not metrics:
        return {
            "total_samples": 0,
            "model_performance": {},
            "statistical_significance": {}
        }
    
    # Group by model
    model_metrics = {}
    for m in metrics:
        model = m.get('model', 'unknown')
        if model not in model_metrics:
            model_metrics[model] = {'mae': [], 'rmse': []}
        
        try:
            model_metrics[model]['mae'].append(float(m['mae']))
            model_metrics[model]['rmse'].append(float(m['rmse']))
        except (ValueError, KeyError):
            continue
    
    # Compute statistics
    summary = {
        "total_samples": len(metrics),
        "model_performance": {}
    }
    
    for model, values in model_metrics.items():
        if values['mae']:
            summary["model_performance"][model] = {
                "mae_mean": float(np.mean(values['mae'])),
                "mae_std": float(np.std(values['mae'])),
                "mae_min": float(np.min(values['mae'])),
                "mae_max": float(np.max(values['mae'])),
                "rmse_mean": float(np.mean(values['rmse'])),
                "rmse_std": float(np.std(values['rmse'])),
                "rmse_min": float(np.min(values['rmse'])),
                "rmse_max": float(np.max(values['rmse']))
            }
    
    return summary

def compute_comparison_stats(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute comparison statistics between models."""
    gnn_metrics = []
    rf_metrics = []
    
    for m in metrics:
        model = m.get('model', '')
        try:
            rmse = float(m['rmse'])
            if 'gnn' in model.lower():
                gnn_metrics.append(rmse)
            elif 'rf' in model.lower() or 'random' in model.lower():
                rf_metrics.append(rmse)
        except (ValueError, KeyError):
            continue
    
    comparison = {
        "gnn_count": len(gnn_metrics),
        "rf_count": len(rf_metrics),
        "gnn_mean_rmse": float(np.mean(gnn_metrics)) if gnn_metrics else None,
        "rf_mean_rmse": float(np.mean(rf_metrics)) if rf_metrics else None
    }
    
    if gnn_metrics and rf_metrics:
        # Paired t-test if same seeds
        min_len = min(len(gnn_metrics), len(rf_metrics))
        if min_len >= 2:
            gnn_sorted = sorted(gnn_metrics)[:min_len]
            rf_sorted = sorted(rf_metrics)[:min_len]
            t_stat, p_value = stats.ttest_rel(gnn_sorted, rf_sorted)
            comparison["paired_t_test"] = {
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant_at_0.05": bool(p_value < 0.05)
            }
        else:
            comparison["paired_t_test"] = {
                "t_statistic": None,
                "p_value": None,
                "significant_at_0.05": False,
                "note": "Insufficient data for paired test"
            }
    
    return comparison

def generate_stats_report(metrics_path: Path, output_path: Path) -> Dict[str, Any]:
    """Generate comprehensive statistics report."""
    metrics = load_metrics(metrics_path)
    
    summary = compute_summary_statistics(metrics)
    comparison = compute_comparison_stats(metrics)
    
    report = {
        "summary": summary,
        "comparison": comparison,
        "raw_metrics_count": len(metrics)
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def parse_args():
    parser = argparse.ArgumentParser(description='Generate statistics report')
    parser.add_argument('--metrics', type=str, default='results/metrics.csv',
                      help='Path to metrics CSV file')
    parser.add_argument('--output', type=str, default='results/stats_report.json',
                      help='Path to output report file')
    return parser.parse_args()

def main():
    """Main entry point for stats generation."""
    args = parse_args()
    
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / args.metrics
    output_path = project_root / args.output
    
    if not metrics_path.exists():
        print(f"Error: Metrics file not found at {metrics_path}")
        print("Please run training first to generate metrics.csv")
        sys.exit(1)
    
    print(f"Generating statistics from {metrics_path}")
    report = generate_stats_report(metrics_path, output_path)
    
    print(f"Statistics report written to {output_path}")
    print(f"Total metrics processed: {report['raw_metrics_count']}")
    
    if report['comparison']['gnn_mean_rmse'] and report['comparison']['rf_mean_rmse']:
        print(f"GNN Mean RMSE: {report['comparison']['gnn_mean_rmse']:.4f}")
        print(f"RF Mean RMSE: {report['comparison']['rf_mean_rmse']:.4f}")
        if 'paired_t_test' in report['comparison']:
            p_val = report['comparison']['paired_t_test']['p_value']
            if p_val is not None:
                print(f"Paired t-test p-value: {p_val:.4f}")
                print(f"Significant at 0.05: {report['comparison']['paired_t_test']['significant_at_0.05']}")

if __name__ == '__main__':
    main()