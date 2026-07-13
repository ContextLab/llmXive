import argparse
import sys
import json
import os
from typing import List, Optional
from pathlib import Path

from .logging_config import setup_logging
from .data_loader import load_public_dataset, calculate_gain_scores
from .synthetic_gen import SyntheticDataGenerator
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, check_collinearity, calculate_power, aggregate_results
from .sensitivity import run_sensitivity_sweep, aggregate_sweep_results
from .models import AnalysisResult, SensitivitySweep

def parse_args():
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument("--mode", type=str, choices=["secondary_analysis", "synthetic"], required=True,
                        help="Mode of operation: 'secondary_analysis' or 'synthetic'")
    parser.add_argument("--input", type=str, required=False, help="Input data file path (CSV/JSON)")
    parser.add_argument("--sweep_thresholds", type=str, required=False, default="0.01,0.05,0.1",
                        help="Comma-separated list of thresholds for sensitivity sweep (e.g., 0.01,0.05,0.1)")
    parser.add_argument("--seed", type=int, required=False, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, required=False, default="data/processed/results.json",
                        help="Output file path for results")
    return parser.parse_args()

def run_secondary_analysis(input_path: str, output_path: str, sweep_thresholds: List[float], seed: int):
    """Run secondary analysis on public dataset."""
    setup_logging()
    
    # Load data
    records = load_public_dataset(input_path)
    if not records:
        print("Error: No records loaded.")
        sys.exit(1)
    
    # Calculate gain scores
    gain_embodied = [r.gain_score() for r in records if r.instruction_type == "embodied" and r.gain_score() is not None]
    gain_static = [r.gain_score() for r in records if r.instruction_type == "static" and r.gain_score() is not None]
    
    if not gain_embodied or not gain_static:
        print("Error: Insufficient data for one of the groups.")
        sys.exit(1)
    
    # Run base stats
    t_stat, p_val, df = run_t_test(gain_embodied, gain_static)
    effect_size, ci_low, ci_high = calculate_effect_size(gain_embodied, gain_static)
    
    # Run sensitivity sweep if thresholds provided
    sweep_results = []
    if sweep_thresholds:
        sweep_results = run_sensitivity_sweep(gain_embodied, gain_static, sweep_thresholds)
        robustness_warning = any(s.robustness_warning for s in sweep_results) if sweep_results else False
    else:
        robustness_warning = False
    
    # Aggregate
    base = aggregate_results(t_stat, p_val, effect_size, ci_low, ci_high, 
                             calculate_power(effect_size, len(gain_embodied)+len(gain_static)),
                             frame_inference(p_val, effect_size, 0.05),
                             check_collinearity(), robustness_warning)
    
    final_result = aggregate_sweep_results(sweep_results, base)
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(final_result.to_json())
    
    print(f"Results written to {output_path}")

def run_synthetic_generation(output_path: str, sweep_thresholds: List[float], seed: int):
    """Run synthetic data generation and analysis."""
    setup_logging()
    
    generator = SyntheticDataGenerator(seed=seed)
    
    # Generate data with known ground truth
    records = generator.generate(
        n_embodied=100,
        n_static=100,
        mean_diff=0.5,
        std_dev=1.0
    )
    
    # Calculate gain scores
    gain_embodied = [r.gain_score() for r in records if r.instruction_type == "embodied" and r.gain_score() is not None]
    gain_static = [r.gain_score() for r in records if r.instruction_type == "static" and r.gain_score() is not None]
    
    if not gain_embodied or not gain_static:
        print("Error: Insufficient synthetic data generated.")
        sys.exit(1)
    
    # Run base stats
    t_stat, p_val, df = run_t_test(gain_embodied, gain_static)
    effect_size, ci_low, ci_high = calculate_effect_size(gain_embodied, gain_static)
    
    # Run sensitivity sweep
    sweep_results = []
    if sweep_thresholds:
        sweep_results = run_sensitivity_sweep(gain_embodied, gain_static, sweep_thresholds)
        robustness_warning = any(s.robustness_warning for s in sweep_results) if sweep_results else False
    else:
        robustness_warning = False
    
    # Aggregate
    base = aggregate_results(t_stat, p_val, effect_size, ci_low, ci_high,
                             calculate_power(effect_size, len(gain_embodied)+len(gain_static)),
                             frame_inference(p_val, effect_size, 0.05),
                             check_collinearity(), robustness_warning)
    
    final_result = aggregate_sweep_results(sweep_results, base)
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(final_result.to_json())
    
    print(f"Synthetic analysis results written to {output_path}")

def main():
    args = parse_args()
    
    thresholds = [float(t) for t in args.sweep_thresholds.split(",")] if args.sweep_thresholds else []
    
    if args.mode == "secondary_analysis":
        if not args.input:
            print("Error: --input is required for secondary_analysis mode.")
            sys.exit(1)
        run_secondary_analysis(args.input, args.output, thresholds, args.seed)
    elif args.mode == "synthetic":
        run_synthetic_generation(args.output, thresholds, args.seed)

if __name__ == "__main__":
    main()