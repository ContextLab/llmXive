"""
Orchestration script for Phase 3: User Story 3 Evaluation.

This script performs the following steps:
1. Runs Baseline (Static Rotation) inference.
2. Runs Dynamic (Router-based) inference.
3. Computes metrics (FID, CLIP, MSE) for both.
4. Runs statistical tests (paired t-test, Bonferroni).
5. Generates the final evaluation report.

Artifacts produced:
- data/evaluations/baseline_metrics.json
- data/evaluations/dynamic_metrics.json
- data/evaluations/timing_results.json
- data/processed/final_evaluation_report.json (T035)
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Project imports
from config import Config
from evaluation.metrics import compute_metrics_batch, save_metrics_to_json, load_metrics_from_json
from evaluation.timing import load_prompts_for_timing, run_static_inference, run_dynamic_inference, compute_statistics, save_timing_results
from analysis.statistical_test import load_metrics_from_json as stats_load_metrics, perform_paired_ttest, apply_bonferroni_correction, save_results as save_stats_results
from analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_results
from models.flux_wan_loader import ModelLoader
from quantization.w2a4_engine import W2A4Engine
from quantization.static_baseline import StaticRotationBaseline
from analysis.router import EntropyRouter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_prompts_for_evaluation() -> List[Dict[str, Any]]:
    """Load prompts from the preprocessed CSV (T006)."""
    config = Config()
    prompts_path = config.processed_prompts_path
    
    if not os.path.exists(prompts_path):
        raise FileNotFoundError(f"Prompts file not found at {prompts_path}. Run T006 first.")
    
    prompts = []
    with open(prompts_path, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row)
    
    logger.info(f"Loaded {len(prompts)} prompts from {prompts_path}")
    return prompts

def run_baseline_evaluation(prompts: List[Dict[str, Any]], config: Config) -> Dict[str, Any]:
    """Run static baseline inference and compute metrics."""
    logger.info("Starting Baseline (Static Rotation) evaluation...")
    
    # Initialize models and engines
    model_loader = ModelLoader(config)
    dit_wrapper = model_loader.load_model()
    baseline_engine = StaticRotationBaseline(config, dit_wrapper)
    
    # Run inference
    start_time = time.time()
    baseline_results = baseline_engine.run_inference(prompts)
    baseline_time = time.time() - start_time
    
    logger.info(f"Baseline inference completed in {baseline_time:.2f}s")
    
    # Compute metrics
    metrics = compute_metrics_batch(baseline_results, config)
    metrics['inference_time'] = baseline_time
    metrics['method'] = 'static_baseline'
    
    # Save intermediate results
    output_path = config.baseline_metrics_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_metrics_to_json(metrics, output_path)
    logger.info(f"Saved baseline metrics to {output_path}")
    
    return metrics

def run_dynamic_evaluation(prompts: List[Dict[str, Any]], config: Config) -> Dict[str, Any]:
    """Run dynamic router inference and compute metrics."""
    logger.info("Starting Dynamic (Router-based) evaluation...")
    
    # Initialize models and engines
    model_loader = ModelLoader(config)
    dit_wrapper = model_loader.load_model()
    w2a4_engine = W2A4Engine(config, dit_wrapper)
    router = EntropyRouter(config)
    
    # Run inference
    start_time = time.time()
    dynamic_results = w2a4_engine.run_inference_with_router(prompts, router)
    dynamic_time = time.time() - start_time
    
    logger.info(f"Dynamic inference completed in {dynamic_time:.2f}s")
    
    # Compute metrics
    metrics = compute_metrics_batch(dynamic_results, config)
    metrics['inference_time'] = dynamic_time
    metrics['method'] = 'dynamic_router'
    
    # Save intermediate results
    output_path = config.dynamic_metrics_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_metrics_to_json(metrics, output_path)
    logger.info(f"Saved dynamic metrics to {output_path}")
    
    return metrics

def run_timing_analysis(prompts: List[Dict[str, Any]], config: Config) -> Dict[str, Any]:
    """Run detailed timing analysis for both methods."""
    logger.info("Running timing analysis...")
    
    timing_results = {
        'static': {},
        'dynamic': {},
        'overhead_percentage': 0.0
    }
    
    # Static timing
    static_times = run_static_inference(prompts, config)
    timing_results['static'] = compute_statistics(static_times)
    
    # Dynamic timing
    dynamic_times = run_dynamic_inference(prompts, config)
    timing_results['dynamic'] = compute_statistics(dynamic_times)
    
    # Calculate overhead
    static_mean = timing_results['static']['mean']
    dynamic_mean = timing_results['dynamic']['mean']
    if static_mean > 0:
        timing_results['overhead_percentage'] = ((dynamic_mean - static_mean) / static_mean) * 100
    
    # Save timing results
    output_path = config.timing_results_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_timing_results(timing_results, output_path)
    logger.info(f"Saved timing results to {output_path}")
    
    return timing_results

def run_statistical_comparison(baseline_metrics: Dict[str, Any], 
                               dynamic_metrics: Dict[str, Any], 
                               config: Config) -> Dict[str, Any]:
    """Run statistical tests comparing baseline and dynamic methods."""
    logger.info("Running statistical tests...")
    
    # Prepare data for comparison
    # Assuming metrics contain lists of per-sample scores
    comparisons = {}
    
    metric_keys = ['fid', 'clip_score', 'mse']
    for key in metric_keys:
        if key in baseline_metrics and key in dynamic_metrics:
            baseline_vals = baseline_metrics[key] if isinstance(baseline_metrics[key], list) else [baseline_metrics[key]]
            dynamic_vals = dynamic_metrics[key] if isinstance(dynamic_metrics[key], list) else [dynamic_metrics[key]]
            
            if len(baseline_vals) == len(dynamic_vals) and len(baseline_vals) > 1:
                t_stat, p_value = perform_paired_ttest(baseline_vals, dynamic_vals)
                comparisons[key] = {
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significant_before_correction': p_value < 0.05
                }
            elif len(baseline_vals) > 0:
                comparisons[key] = {
                    't_statistic': 0.0,
                    'p_value': 1.0,
                    'significant_before_correction': False,
                    'note': 'Insufficient samples for paired test'
                }
    
    # Apply Bonferroni correction
    corrected_results = apply_bonferroni_correction(comparisons)
    
    # Save statistical results
    output_path = config.statistical_results_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_stats_results(corrected_results, output_path)
    logger.info(f"Saved statistical results to {output_path}")
    
    return corrected_results

def generate_final_report(baseline_metrics: Dict[str, Any],
                          dynamic_metrics: Dict[str, Any],
                          timing_results: Dict[str, Any],
                          statistical_results: Dict[str, Any],
                          config: Config) -> Dict[str, Any]:
    """Generate the final evaluation report (T035 artifact)."""
    logger.info("Generating final evaluation report...")
    
    report = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'config': {
            'device': config.device,
            'num_samples': len(baseline_metrics.get('sample_ids', [])),
            'quantization_bits': 'W2A4'
        },
        'baseline': {
            'fid': baseline_metrics.get('fid'),
            'clip_score': baseline_metrics.get('clip_score'),
            'mse': baseline_metrics.get('mse'),
            'inference_time': baseline_metrics.get('inference_time')
        },
        'dynamic': {
            'fid': dynamic_metrics.get('fid'),
            'clip_score': dynamic_metrics.get('clip_score'),
            'mse': dynamic_metrics.get('mse'),
            'inference_time': dynamic_metrics.get('inference_time')
        },
        'timing_analysis': timing_results,
        'statistical_tests': statistical_results,
        'summary': {}
    }
    
    # Generate summary
    baseline_fid = baseline_metrics.get('fid', 0)
    dynamic_fid = dynamic_metrics.get('fid', 0)
    if baseline_fid > 0:
        fid_improvement = ((baseline_fid - dynamic_fid) / baseline_fid) * 100
        report['summary']['fid_improvement_percent'] = fid_improvement
        report['summary']['fid_gained'] = dynamic_fid < baseline_fid
    
    # Check statistical significance
    significant_tests = 0
    for metric, results in statistical_results.get('comparisons', {}).items():
        if results.get('significant_after_correction', False):
            significant_tests += 1
    
    report['summary']['statistically_significant_improvements'] = significant_tests
    report['summary']['overall_success'] = significant_tests > 0 and report['summary'].get('fid_gained', False)
    
    # Save report
    output_path = config.final_evaluation_report_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved final evaluation report to {output_path}")
    return report

def main():
    """Main orchestration entry point."""
    logger.info("Starting Phase 3 Evaluation (T034)...")
    
    config = Config()
    
    # Step 1: Load Prompts
    prompts = load_prompts_for_evaluation()
    if not prompts:
        logger.error("No prompts loaded. Exiting.")
        sys.exit(1)
    
    # Step 2: Run Baseline Evaluation
    baseline_metrics = run_baseline_evaluation(prompts, config)
    
    # Step 3: Run Dynamic Evaluation
    dynamic_metrics = run_dynamic_evaluation(prompts, config)
    
    # Step 4: Run Timing Analysis
    timing_results = run_timing_analysis(prompts, config)
    
    # Step 5: Run Statistical Tests
    statistical_results = run_statistical_comparison(baseline_metrics, dynamic_metrics, config)
    
    # Step 6: Generate Final Report (T035 artifact)
    final_report = generate_final_report(
        baseline_metrics, 
        dynamic_metrics, 
        timing_results, 
        statistical_results, 
        config
    )
    
    logger.info("Phase 3 Evaluation completed successfully.")
    logger.info(f"Final Report Summary: {final_report['summary']}")
    
    return final_report

if __name__ == "__main__":
    main()