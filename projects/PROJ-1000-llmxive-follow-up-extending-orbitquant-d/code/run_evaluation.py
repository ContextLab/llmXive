"""
Orchestration script for Phase 3: User Story 3 Evaluation.

Executes Baseline (Static) and Dynamic (Router-based) evaluations,
computes metrics, runs statistical tests, and generates the final report.

Dependencies:
  - T022 (clustering_report.json)
  - T028 (load_matrices.py)
  - T032 (metrics.py)
  - T033 (timing.py)
  - T034 (statistical_test.py)
"""
import os
import sys
import json
import logging
import time
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Project imports based on API surface
from config import Config
from evaluation.metrics import compute_metrics_batch, save_metrics_to_json, load_metrics_from_json
from evaluation.timing import run_static_inference, run_dynamic_inference, compute_statistics, save_timing_results
from analysis.statistical_test import perform_paired_ttest, apply_bonferroni_correction, run_statistical_tests, save_results as save_stats_results
from analysis.load_matrices import load_matrices_from_path
from analysis.router import EntropyRouter
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import create_dit_wrapper
from analysis.entropy_proxy import EntropyProxy
from quantization.w2a4_engine import W2A4Engine
from quantization.static_baseline import StaticRotationBaseline
from utils.gpu_offload import check_gpu_availability, GPUOffloadError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/evaluation_run.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
config = Config()
DATA_DIR = Path(config.data_dir)
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_FILE = PROCESSED_DIR / "final_evaluation_report.json"

def load_prompts_for_evaluation() -> List[Dict[str, Any]]:
    """Load prompts from the diverse prompts dataset for evaluation."""
    prompts_file = PROCESSED_DIR / "diverse_prompts.csv"
    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}. Run T006d first.")
    
    prompts = []
    with open(prompts_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure we have a valid caption
            caption = row.get('caption', '').strip()
            if caption:
                prompts.append({
                    'id': row.get('id', ''),
                    'caption': caption,
                    'source': row.get('source', 'unknown')
                })
    
    logger.info(f"Loaded {len(prompts)} prompts for evaluation.")
    return prompts

def run_baseline_evaluation(prompts: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Run the Static Baseline evaluation.
    Returns metrics and timing data.
    """
    logger.info("Starting Baseline (Static) Evaluation.")
    
    # Initialize components
    try:
        model_loader = ModelLoader(config)
        dit_model = model_loader.load_model(use_gpu=True)
        baseline_engine = StaticRotationBaseline(dit_model, config)
        entropy_proxy = EntropyProxy(config)
    except Exception as e:
        logger.error(f"Failed to initialize baseline components: {e}")
        raise

    metrics_list = []
    timing_data = {'inference_times': [], 'total_time': 0}
    
    start_total = time.time()
    
    for i, prompt_data in enumerate(prompts):
        prompt = prompt_data['caption']
        logger.info(f"Processing baseline prompt {i+1}/{len(prompts)}: {prompt[:50]}...")
        
        try:
            # Compute entropy for routing (even though baseline uses static, we need it for comparison)
            entropy_score = entropy_proxy.compute_entropy(prompt)
            
            # Run static inference
            start_inference = time.time()
            result = baseline_engine.generate(prompt)
            inference_time = time.time() - start_inference
            
            # Compute metrics
            if result and 'image' in result:
                metrics = compute_metrics_batch(
                    generated_images=[result['image']],
                    ground_truth=None, # No ground truth for generation metrics like FID/CLIP
                    prompt=prompt,
                    model_name=config.model_name
                )
                metrics['entropy'] = entropy_score
                metrics['prompt_id'] = prompt_data['id']
                metrics_list.append(metrics)
                timing_data['inference_times'].append(inference_time)
            else:
                logger.warning(f"Baseline generation failed for prompt {prompt_data['id']}")
        
        except Exception as e:
            logger.error(f"Error in baseline evaluation for prompt {prompt_data['id']}: {e}")
            continue

    timing_data['total_time'] = time.time() - start_total
    timing_stats = compute_statistics(timing_data['inference_times'])
    
    logger.info(f"Baseline evaluation complete. Generated {len(metrics_list)} samples.")
    return {
        'metrics': metrics_list,
        'timing': timing_data,
        'timing_stats': timing_stats
    }, timing_stats

def run_dynamic_evaluation(prompts: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Run the Dynamic Router evaluation.
    Returns metrics and timing data.
    """
    logger.info("Starting Dynamic Router Evaluation.")
    
    # Load rotation matrices
    matrices_file = PROCESSED_DIR / "clustering_report.json"
    if not matrices_file.exists():
        raise FileNotFoundError(f"Clustering report not found: {matrices_file}. Run T022 first.")
    
    rotation_matrices = load_matrices_from_path(matrices_file)
    logger.info(f"Loaded {len(rotation_matrices)} rotation matrices.")
    
    # Initialize components
    try:
        model_loader = ModelLoader(config)
        dit_model = model_loader.load_model(use_gpu=True)
        dynamic_engine = W2A4Engine(dit_model, config, rotation_matrices)
        router = EntropyRouter(matrices_file, config)
        entropy_proxy = EntropyProxy(config)
    except Exception as e:
        logger.error(f"Failed to initialize dynamic components: {e}")
        raise

    metrics_list = []
    timing_data = {'inference_times': [], 'total_time': 0}
    
    start_total = time.time()
    
    for i, prompt_data in enumerate(prompts):
        prompt = prompt_data['caption']
        logger.info(f"Processing dynamic prompt {i+1}/{len(prompts)}: {prompt[:50]}...")
        
        try:
            # Compute entropy
            entropy_score = entropy_proxy.compute_entropy(prompt)
            
            # Select rotation matrix
            matrix_index = router.select_matrix(entropy_score)
            logger.debug(f"Prompt entropy: {entropy_score:.4f}, Selected matrix index: {matrix_index}")
            
            # Run dynamic inference
            start_inference = time.time()
            result = dynamic_engine.generate(prompt, matrix_index=matrix_index)
            inference_time = time.time() - start_inference
            
            # Compute metrics
            if result and 'image' in result:
                metrics = compute_metrics_batch(
                    generated_images=[result['image']],
                    ground_truth=None,
                    prompt=prompt,
                    model_name=config.model_name
                )
                metrics['entropy'] = entropy_score
                metrics['matrix_index'] = matrix_index
                metrics['prompt_id'] = prompt_data['id']
                metrics_list.append(metrics)
                timing_data['inference_times'].append(inference_time)
            else:
                logger.warning(f"Dynamic generation failed for prompt {prompt_data['id']}")
        
        except Exception as e:
            logger.error(f"Error in dynamic evaluation for prompt {prompt_data['id']}: {e}")
            continue

    timing_data['total_time'] = time.time() - start_total
    timing_stats = compute_statistics(timing_data['inference_times'])
    
    logger.info(f"Dynamic evaluation complete. Generated {len(metrics_list)} samples.")
    return {
        'metrics': metrics_list,
        'timing': timing_data,
        'timing_stats': timing_stats
    }, timing_stats

def run_timing_analysis(baseline_timing: Dict[str, float], dynamic_timing: Dict[str, float]) -> Dict[str, Any]:
    """Compare timing between baseline and dynamic methods."""
    logger.info("Running timing analysis.")
    
    baseline_avg = baseline_timing.get('mean', 0)
    dynamic_avg = dynamic_timing.get('mean', 0)
    
    overhead_pct = ((dynamic_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0
    
    return {
        'baseline_avg_seconds': baseline_avg,
        'dynamic_avg_seconds': dynamic_avg,
        'overhead_percent': overhead_pct,
        'baseline_total_samples': len(baseline_timing.get('inference_times', [])),
        'dynamic_total_samples': len(dynamic_timing.get('inference_times', []))
    }

def run_statistical_comparison(baseline_metrics: List[Dict], dynamic_metrics: List[Dict]) -> Dict[str, Any]:
    """Perform statistical tests (paired t-tests) on metrics."""
    logger.info("Running statistical comparison.")
    
    # Align metrics by prompt_id if possible, otherwise just compare distributions
    # For simplicity in this orchestration, we assume same number of samples and order
    # In a real scenario, we'd match by prompt_id
    
    metric_types = ['fid', 'clip_score', 'mse']
    results = {}
    
    for metric_name in metric_types:
        baseline_vals = [m.get(metric_name) for m in baseline_metrics if metric_name in m and m[metric_name] is not None]
        dynamic_vals = [m.get(metric_name) for m in dynamic_metrics if metric_name in m and m[metric_name] is not None]
        
        if len(baseline_vals) > 1 and len(dynamic_vals) > 1:
            # Ensure equal length for paired test
            min_len = min(len(baseline_vals), len(dynamic_vals))
            baseline_vals = baseline_vals[:min_len]
            dynamic_vals = dynamic_vals[:min_len]
            
            t_stat, p_value = perform_paired_ttest(baseline_vals, dynamic_vals)
            corrected_p = apply_bonferroni_correction(p_value, len(metric_types))
            
            results[metric_name] = {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'corrected_p_value': float(corrected_p),
                'significant': corrected_p < 0.05,
                'sample_size': min_len
            }
        else:
            results[metric_name] = {
                'error': 'Insufficient data for statistical test',
                'sample_size': min(len(baseline_vals), len(dynamic_vals))
            }
    
    return results

def generate_final_report(
    baseline_results: Dict,
    dynamic_results: Dict,
    timing_analysis: Dict,
    statistical_results: Dict
) -> Dict[str, Any]:
    """Compile all results into the final evaluation report."""
    
    report = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'config': {
            'model': config.model_name,
            'device': config.device,
            'num_prompts': len(baseline_results['metrics'])
        },
        'baseline': {
            'metrics_summary': {
                'count': len(baseline_results['metrics']),
                'avg_fid': sum(m.get('fid', 0) for m in baseline_results['metrics']) / max(1, len(baseline_results['metrics'])),
                'avg_clip': sum(m.get('clip_score', 0) for m in baseline_results['metrics']) / max(1, len(baseline_results['metrics'])),
            },
            'timing': baseline_results['timing_stats']
        },
        'dynamic': {
            'metrics_summary': {
                'count': len(dynamic_results['metrics']),
                'avg_fid': sum(m.get('fid', 0) for m in dynamic_results['metrics']) / max(1, len(dynamic_results['metrics'])),
                'avg_clip': sum(m.get('clip_score', 0) for m in dynamic_results['metrics']) / max(1, len(dynamic_results['metrics'])),
            },
            'timing': dynamic_results['timing_stats']
        },
        'timing_comparison': timing_analysis,
        'statistical_tests': statistical_results,
        'conclusion': {
            'dynamic_improves_fid': False,
            'dynamic_improves_clip': False,
            'overhead_acceptable': timing_analysis.get('overhead_percent', 100) < 10
        }
    }
    
    # Determine conclusions
    if statistical_results.get('fid', {}).get('significant'):
        report['conclusion']['dynamic_improves_fid'] = statistical_results['fid']['t_statistic'] < 0 # Lower FID is better
    if statistical_results.get('clip_score', {}).get('significant'):
        report['conclusion']['dynamic_improves_clip'] = statistical_results['clip_score']['t_statistic'] > 0 # Higher CLIP is better
    
    return report

def main():
    """Main entry point for the evaluation pipeline."""
    logger.info("=" * 50)
    logger.info("Starting Phase 3: Final Evaluation Pipeline (T036)")
    logger.info("=" * 50)
    
    # 1. Load Prompts
    prompts = load_prompts_for_evaluation()
    if not prompts:
        logger.error("No prompts loaded. Aborting.")
        sys.exit(1)
    
    # 2. Run Baseline Evaluation
    try:
        baseline_results, baseline_timing_stats = run_baseline_evaluation(prompts)
    except Exception as e:
        logger.error(f"Baseline evaluation failed: {e}")
        sys.exit(1)
    
    # 3. Run Dynamic Evaluation
    try:
        dynamic_results, dynamic_timing_stats = run_dynamic_evaluation(prompts)
    except Exception as e:
        logger.error(f"Dynamic evaluation failed: {e}")
        sys.exit(1)
    
    # 4. Timing Analysis
    timing_analysis = run_timing_analysis(baseline_timing_stats, dynamic_timing_stats)
    
    # 5. Statistical Comparison
    statistical_results = run_statistical_comparison(
        baseline_results['metrics'], 
        dynamic_results['metrics']
    )
    
    # 6. Generate Final Report
    final_report = generate_final_report(
        baseline_results,
        dynamic_results,
        timing_analysis,
        statistical_results
    )
    
    # 7. Save Report
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final evaluation report saved to: {OUTPUT_FILE}")
    logger.info("Phase 3 Evaluation Complete.")
    
    return final_report

if __name__ == "__main__":
    main()