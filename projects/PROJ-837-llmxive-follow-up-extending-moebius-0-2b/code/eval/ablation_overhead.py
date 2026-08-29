"""
Task T032c: Analyze prediction overhead vs. reduction gain.

This module compares the computational overhead of the gating mechanism
against the latency reduction gained by dynamic rank modulation.

It consumes:
- data/results/ablation_report.json (from T032d)
- data/results/latency_raw.csv (from T033a)

It produces:
- data/results/overhead_analysis.json
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils.logger import get_logger
from config import get_mode, is_ci_mode
from config_env import get_results_path

logger = get_logger("ablation_overhead")

# Constants
OVERHEAD_ANALYSIS_PATH = "data/results/overhead_analysis.json"
ABLATION_REPORT_PATH = "data/results/ablation_report.json"
LATENCY_RAW_PATH = "data/results/latency_raw.csv"


def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    full_path = Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"Required file not found: {full_path}")
    with open(full_path, 'r') as f:
        return json.load(f)


def load_latency_csv(path: str) -> List[Dict[str, Any]]:
    """Load latency raw CSV data."""
    full_path = Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"Required file not found: {full_path}")
    
    data = []
    with open(full_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            for key in ['latency_ms', 'complexity_score', 'rank']:
                if key in row and row[key]:
                    try:
                        row[key] = float(row[key])
                    except ValueError:
                        pass
            data.append(row)
    return data


def calculate_overhead_stats(ablation_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate overhead statistics based on ablation run times.
    
    We assume the ablation report contains timing info for:
    - 'dynamic_model': The model with gating + dynamic rank
    - 'static_low_rank': Baseline with forced low rank (no gating overhead)
    - 'static_high_rank': Baseline with forced high rank (no gating overhead)
    
    Overhead is defined as the extra time taken by the dynamic model 
    compared to the static low rank model (since they both target low complexity).
    """
    dynamic_time = ablation_data.get('dynamic_model', {}).get('total_time_ms', 0.0)
    static_low_time = ablation_data.get('static_low_rank', {}).get('total_time_ms', 0.0)
    static_high_time = ablation_data.get('static_high_rank', {}).get('total_time_ms', 0.0)
    
    # Gating overhead: Dynamic vs Static Low (both should be doing similar work, 
    # but dynamic has the extra gating step)
    gating_overhead_ms = dynamic_time - static_low_time
    
    # Potential savings: Static High vs Static Low (theoretical max gain)
    potential_savings_ms = static_high_time - static_low_time
    
    # Efficiency ratio: How much of the potential savings we actually captured
    # relative to the overhead introduced
    if gating_overhead_ms > 0:
        efficiency_ratio = (potential_savings_ms - gating_overhead_ms) / potential_savings_ms if potential_savings_ms > 0 else 0.0
    else:
        efficiency_ratio = 1.0 # No overhead, perfect efficiency (theoretical)

    return {
        "gating_overhead_ms": max(0.0, gating_overhead_ms),
        "potential_savings_ms": max(0.0, potential_savings_ms),
        "efficiency_ratio": efficiency_ratio,
        "dynamic_total_ms": dynamic_time,
        "static_low_total_ms": static_low_time,
        "static_high_total_ms": static_high_time
    }


def analyze_latency_reduction_by_complexity(latency_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze latency reduction grouped by complexity score.
    
    Returns a breakdown of average latency per complexity bin and the 
    reduction percentage compared to the high-rank baseline.
    """
    if not latency_data:
        return {"error": "No latency data found"}

    # Group by complexity score (round to nearest integer for binning)
    bins = {}
    for row in latency_data:
        score = row.get('complexity_score', 0)
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = 0
        score_bin = round(score)
        
        if score_bin not in bins:
            bins[score_bin] = []
        
        if 'latency_ms' in row and isinstance(row['latency_ms'], (int, float)):
            bins[score_bin].append(row['latency_ms'])

    results = {}
    all_latencies = [r.get('latency_ms') for r in latency_data if isinstance(r.get('latency_ms'), (int, float))]
    global_avg_high = max(all_latencies) if all_latencies else 0 # Assuming high rank is generally the max

    # Calculate baseline (High Rank) average from the dataset if available
    # If the dataset contains mixed ranks, we need to isolate 'high_rank' entries
    # For this analysis, we assume the 'static_high_rank' run in ablation_report is the baseline
    # However, if we are analyzing the 'latency_raw.csv' which might be from dynamic runs,
    # we need a reference. Let's assume the max observed latency in this file is the proxy for High Rank.
    baseline_latency = max(all_latencies) if all_latencies else 0.0

    for score_bin, latencies in sorted(bins.items()):
        avg_lat = sum(latencies) / len(latencies)
        reduction_pct = 0.0
        if baseline_latency > 0:
            reduction_pct = ((baseline_latency - avg_lat) / baseline_latency) * 100.0
        
        results[score_bin] = {
            "avg_latency_ms": round(avg_lat, 4),
            "sample_count": len(latencies),
            "reduction_vs_high_rank_pct": round(reduction_pct, 2)
        }

    return {
        "baseline_high_rank_avg_ms": round(baseline_latency, 4),
        "bins": results,
        "total_samples": len(latencies)
    }


def run_analysis(ablation_path: str, latency_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main analysis routine.
    """
    logger.info(f"Loading ablation report from {ablation_path}")
    ablation_data = load_json(ablation_path)

    logger.info(f"Loading latency raw data from {latency_path}")
    latency_data = load_latency_csv(latency_path)

    logger.info("Calculating overhead statistics...")
    overhead_stats = calculate_overhead_stats(ablation_data)

    logger.info("Analyzing latency reduction by complexity...")
    complexity_analysis = analyze_latency_reduction_by_complexity(latency_data)

    # Synthesize final report
    final_report = {
        "mode": get_mode(),
        "analysis_timestamp": "2023-10-27T10:00:00Z", # Placeholder, real code would use datetime
        "overhead_analysis": overhead_stats,
        "complexity_reduction_analysis": complexity_analysis,
        "summary": {
            "gating_overhead_ms": overhead_stats["gating_overhead_ms"],
            "avg_latency_reduction_pct": complexity_analysis.get("bins", {}).get(1, {}).get("reduction_vs_high_rank_pct", 0),
            "is_efficiency_positive": overhead_stats["efficiency_ratio"] > 0
        }
    }

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing analysis to {output_path}")
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)

    return final_report


def main():
    parser = argparse.ArgumentParser(description="Analyze prediction overhead vs reduction gain (T032c)")
    parser.add_argument("--ablation-report", type=str, default=ABLATION_REPORT_PATH,
                        help="Path to ablation_report.json")
    parser.add_argument("--latency-raw", type=str, default=LATENCY_RAW_PATH,
                        help="Path to latency_raw.csv")
    parser.add_argument("--output", type=str, default=OVERHEAD_ANALYSIS_PATH,
                        help="Path to output analysis JSON")
    
    args = parser.parse_args()

    try:
        results = run_analysis(args.ablation_report, args.latency_raw, args.output)
        print(json.dumps(results, indent=2))
        logger.info("Analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if is_ci_mode():
            # In CI, we might not have the data yet if previous steps failed, 
            # but we should still try to run if data exists.
            logger.error("In CI mode, failing loudly on missing data.")
        sys.exit(1)


if __name__ == "__main__":
    main()