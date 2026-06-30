"""
Run Analysis Script for KVarN Variance-Normalized KV-Cache Quantization.

This script ingests benchmark results and raw MSE data, performs statistical
analyses (McNemar's test, correlation, slope comparison), and outputs a
summary JSON adhering to the analysis summary schema.

Usage:
    python code/run_analysis.py --input data/processed/benchmark_results.jsonl --output data/processed/analysis_summary.json
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.stats import (
    mcnemar_test,
    paired_ttest,
    pearson_correlation,
    calculate_correlation_mse_accuracy,
    compare_error_accumulation_slopes,
    aggregate_mse_by_position
)

SCHEMA_PATH = Path(__file__).parent / "contracts" / "analysis_summary_schema.schema.yaml"

def load_benchmark_results(filepath: str) -> List[Dict[str, Any]]:
    """Load benchmark results from a JSONL file."""
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def load_raw_mse_data(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Load raw MSE data points.
    Defaults to data/processed/cumulative_mse_raw.jsonl if not specified.
    """
    if filepath is None:
        filepath = str(Path(__file__).parent.parent / "data" / "processed" / "cumulative_mse_raw.jsonl")
    
    if not os.path.exists(filepath):
        print(f"Warning: Raw MSE data file not found at {filepath}. Skipping MSE-based analysis.")
        return []

    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def run_mcnemar_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform McNemar's test comparing KVarN vs Uniform accuracy on binary outcomes.
    Expects results to have 'accuracy' and 'quantizer_type'.
    """
    # Group by task
    tasks = {}
    for r in results:
        task_name = r.get('task_name', 'unknown')
        if task_name not in tasks:
            tasks[task_name] = {'kvarn': [], 'uniform': []}
        
        # We need paired binary outcomes (correct/incorrect) for McNemar.
        # Since we only have accuracy (scalar), we approximate by checking if accuracy > 0.5
        # or by reconstructing counts if available. For this implementation,
        # we will assume the benchmark results contain 'correct' and 'total' counts 
        # or we simulate a confusion matrix based on accuracy difference if raw counts aren't there.
        # Ideally, benchmark_results.jsonl should have 'correct' and 'total'.
        
        if 'correct' in r and 'total' in r:
            tasks[task_name][r['quantizer_type']].append({
                'correct': r['correct'],
                'total': r['total']
            })
        else:
            # Fallback: treat accuracy as a probability and simulate a binary outcome for the test
            # This is a simplification. Real McNemar needs paired contingency table.
            # We will return N/A for tasks missing raw counts.
            tasks[task_name][r['quantizer_type']].append(None)

    analysis = {}
    for task_name, data in tasks.items():
        kvarn_data = data['kvarn']
        uniform_data = data['uniform']
        
        # Simple check: if we have paired counts
        if kvarn_data and uniform_data and kvarn_data[0] and uniform_data[0]:
            # Construct contingency table
            # Assuming same total N for both (typical in benchmarks)
            n = kvarn_data[0]['total']
            # This is a simplified aggregation. Real McNemar needs per-sample pair.
            # We will aggregate total correct counts to approximate.
            # Correct KVarN / Total, Correct Uniform / Total
            # We cannot do exact McNemar without per-sample pair data.
            # We will use a paired t-test on accuracy if we have multiple samples, 
            # or just report accuracy diff if single run.
            # Given the constraint of the schema and data, we will report accuracy comparison.
            
            avg_acc_k = sum(d['correct']/d['total'] for d in kvarn_data if d) / len([d for d in kvarn_data if d])
            avg_acc_u = sum(d['correct']/d['total'] for d in uniform_data if d) / len([d for d in uniform_data if d])
            
            analysis[task_name] = {
                "method": "accuracy_comparison",
                "kvarn_accuracy": avg_acc_k,
                "uniform_accuracy": avg_acc_u,
                "difference": avg_acc_k - avg_acc_u,
                "mcnemar_p_value": None, # Cannot compute without per-sample pairs
                "note": "McNemar requires per-sample paired binary outcomes. Using accuracy difference as proxy."
            }
        else:
            analysis[task_name] = {
                "method": "insufficient_data",
                "note": "Missing correct/total counts for McNemar."
            }
    
    return analysis

def run_correlation_analysis(raw_mse_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run Pearson correlation between cumulative MSE and token position, 
    and analyze correlation with accuracy if available.
    """
    if not raw_mse_data:
        return {"error": "No raw MSE data available"}

    # Aggregate by position
    position_mse = aggregate_mse_by_position(raw_mse_data)
    
    if not position_mse:
        return {"error": "No aggregated MSE data"}

    positions = list(position_mse.keys())
    mse_values = list(position_mse.values())

    # Correlation between position and MSE (error accumulation trend)
    if len(positions) > 1:
        corr_pos_mse = pearson_correlation(np.array(positions), np.array(mse_values))
    else:
        corr_pos_mse = None

    # Note: Calculating correlation with accuracy requires linking MSE data to specific task accuracy.
    # The raw MSE data format is usually per-token per-sequence.
    # We will report the position-MSE correlation as the primary metric here.
    return {
        "positions": positions,
        "mse_values": mse_values,
        "correlation_position_mse": corr_pos_mse,
        "description": "Correlation between token position and average MSE (error accumulation)"
    }

def run_slope_comparison(raw_mse_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare error accumulation slopes between KVarN and Uniform quantizers.
    """
    if not raw_mse_data:
        return {"error": "No raw MSE data available"}

    # Separate by quantizer type
    kvarn_data = [d for d in raw_mse_data if d.get('quantizer_type') == 'kvarn']
    uniform_data = [d for d in raw_mse_data if d.get('quantizer_type') == 'uniform']

    result = {}

    if kvarn_data:
        pos_k = [d['token_position'] for d in kvarn_data]
        mse_k = [d['mse'] for d in kvarn_data]
        # Aggregate for trend
        agg_k = aggregate_mse_by_position(kvarn_data)
        if len(agg_k) > 1:
            slope_k = compare_error_accumulation_slopes(list(agg_k.keys()), list(agg_k.values()), return_slope=True)
            result['kvarn_slope'] = slope_k
        else:
            result['kvarn_slope'] = None

    if uniform_data:
        pos_u = [d['token_position'] for d in uniform_data]
        mse_u = [d['mse'] for d in uniform_data]
        agg_u = aggregate_mse_by_position(uniform_data)
        if len(agg_u) > 1:
            slope_u = compare_error_accumulation_slopes(list(agg_u.keys()), list(agg_u.values()), return_slope=True)
            result['uniform_slope'] = slope_u
        else:
            result['uniform_slope'] = None

    if 'kvarn_slope' in result and 'uniform_slope' in result:
        result['slope_difference'] = result['kvarn_slope'] - result['uniform_slope']
        result['interpretation'] = "Lower slope indicates slower error accumulation." if result['slope_difference'] < 0 else "Higher slope indicates faster error accumulation."

    return result

def main():
    parser = argparse.ArgumentParser(description="Run statistical analysis on benchmark results.")
    parser.add_argument('--input', type=str, default='data/processed/benchmark_results.jsonl',
                        help='Path to benchmark results JSONL file.')
    parser.add_argument('--mse-input', type=str, default=None,
                        help='Path to raw MSE data JSONL file. Defaults to data/processed/cumulative_mse_raw.jsonl.')
    parser.add_argument('--output', type=str, default='data/processed/analysis_summary.json',
                        help='Path to output analysis summary JSON file.')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading benchmark results from {input_path}...")
    benchmark_results = load_benchmark_results(str(input_path))
    
    print(f"Loading raw MSE data from {args.mse_input or 'default location'}...")
    raw_mse_data = load_raw_mse_data(args.mse_input)

    summary = {
        "status": "completed",
        "input_files": {
            "benchmark_results": str(input_path),
            "raw_mse_data": args.mse_input or "data/processed/cumulative_mse_raw.jsonl"
        },
        "analysis_results": {}
    }

    # 1. McNemar / Accuracy Analysis
    print("Running accuracy comparison (McNemar proxy)...")
    summary["analysis_results"]["accuracy_comparison"] = run_mcnemar_analysis(benchmark_results)

    # 2. Correlation Analysis
    print("Running correlation analysis...")
    summary["analysis_results"]["correlation_analysis"] = run_correlation_analysis(raw_mse_data)

    # 3. Slope Comparison
    print("Running error accumulation slope comparison...")
    summary["analysis_results"]["slope_comparison"] = run_slope_comparison(raw_mse_data)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"Analysis summary written to {output_path}")

if __name__ == "__main__":
    main()