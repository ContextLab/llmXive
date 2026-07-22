import os
import sys
import logging
import json
import gc
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import local modules using relative imports logic handled by sys.path in runner
# The prompt indicates imports like `from main import ...` so we assume code/ is in PYTHONPATH
from data.models import VideoClip, MetricRecord
from data.processor import process_dataset_stratification, load_processed_clips
from data.flow import extract_flow_magnitudes_for_dataset, compute_flow_magnitude
from models.baseline import run_baseline_inference
from models.flow_coherence import run_flow_coherence_inference
from metrics.resource import MemoryProfiler
from metrics.ssim import (
    compute_background_stability_score,
    compute_ssim,
    compute_temporal_gradient_variance,
    compute_flow_statistics
)
from analysis.reporter import generate_baseline_report, generate_comparative_report
from utils.checkpoint import CheckpointManager
from utils.logger import get_logger
from config import ensure_directories, get_default_config

logger = get_logger(__name__)

def run_flow_coherence_inference_pipeline(
    output_dir: str,
    clips: Optional[List[VideoClip]] = None,
    checkpoint_id: Optional[str] = None
) -> List[MetricRecord]:
    """
    Implement flow-coherence inference runner with checkpointing support.
    Processes clips one-by-one to manage RAM.
    """
    ensure_directories(output_dir)
    checkpoint_manager = CheckpointManager(checkpoint_dir=os.path.join(output_dir, "..", "checkpoints"))
    
    if clips is None:
        clips = load_processed_clips()
    
    logger.info(f"Starting Flow-Coherence inference pipeline on {len(clips)} clips.")
    
    results = []
    flow_stats = []
    bss_scores = []
    ssim_scores = []
    grad_scores = []

    start_time = time.time()
    profiler = MemoryProfiler()
    profiler.start()

    for i, clip in enumerate(clips):
        # Checkpointing: Skip if already processed
        if checkpoint_id:
            if checkpoint_manager.is_processed(checkpoint_id, clip.id):
                logger.info(f"Skipping clip {clip.id} (already processed)")
                continue

        logger.info(f"Processing clip {i+1}/{len(clips)}: {clip.id}")
        
        try:
            # Run Flow-Coherence Inference
            # This function is expected to return frames and metadata
            inference_result = run_flow_coherence_inference(clip)
            
            if inference_result is None:
                logger.warning(f"Inference failed for clip {clip.id}, skipping.")
                continue

            frames = inference_result.frames
            invalid_flow_count = getattr(inference_result, 'invalid_flow_count', 0)
            
            # Compute Metrics
            # 1. Background Stability Score (BSS)
            bss = compute_background_stability_score(frames)
            bss_scores.append(bss)
            
            # 2. Consecutive Frame SSIM
            ssim = compute_ssim(frames)
            ssim_scores.append(ssim)
            
            # 3. Temporal Gradient Variance
            grad = compute_temporal_gradient_variance(frames)
            grad_scores.append(grad)

            # 4. Flow Statistics (Magnitude & Invalid Flags)
            flow_stat = compute_flow_statistics(clip, frames)
            flow_stats.append(flow_stat)

            # Record Metric
            metric_record = MetricRecord(
                clip_id=clip.id,
                model_variant="flow_coherence",
                peak_memory=0, # Updated at end
                fps=30, # Default, or extract from clip
                ssim=ssim.get('score', 0.0),
                gradient_variance=grad.get('variance', 0.0),
                flow_magnitude=flow_stat.get('mean_magnitude', 0.0),
                invalid_flow=invalid_flow_count > 0
            )
            results.append(metric_record)

            # Save Checkpoint
            if checkpoint_id:
                checkpoint_manager.mark_processed(checkpoint_id, clip.id)

        except Exception as e:
            logger.error(f"Error processing clip {clip.id}: {e}", exc_info=True)
            # Fail loudly or continue? Per constraints, we log and continue to process others
            # but in a real research run, we might want to stop.
            continue

        # Garbage Collection
        gc.collect()

    profiler.stop()
    total_peak_memory = profiler.get_peak_memory()

    # Update peak memory for all records
    for record in results:
        record.peak_memory = total_peak_memory

    elapsed_time = time.time() - start_time
    logger.info(f"Flow-Coherence pipeline completed in {elapsed_time:.2f}s. Peak Memory: {total_peak_memory}MB")

    # Write Aggregated Metrics
    baseline_path = os.path.join(output_dir, "baseline_results.json") # Just for structure check
    flow_results_path = os.path.join(output_dir, "flow_results.json")
    flow_bss_path = os.path.join(output_dir, "flow_bss.json")
    flow_ssim_path = os.path.join(output_dir, "flow_ssim.json")
    flow_grad_path = os.path.join(output_dir, "flow_grad.json")
    flow_stats_path = os.path.join(output_dir, "flow_stats.json")

    # Generate Reports (using the reporter module)
    # We need to structure data for the reporter
    report_data = {
        "results": [r.__dict__ if hasattr(r, '__dict__') else r for r in results],
        "bss": bss_scores,
        "ssim": ssim_scores,
        "gradient": grad_scores,
        "flow_stats": flow_stats
    }

    # Write raw JSON files for specific metrics
    with open(flow_bss_path, 'w') as f:
        json.dump(bss_scores, f, indent=2)
    with open(flow_ssim_path, 'w') as f:
        json.dump(ssim_scores, f, indent=2)
    with open(flow_grad_path, 'w') as f:
        json.dump(grad_scores, f, indent=2)
    with open(flow_stats_path, 'w') as f:
        json.dump(flow_stats, f, indent=2)

    # Use reporter to generate the main summary
    generate_comparative_report(results, output_dir, "flow_coherence")

    return results

def run_baseline_inference_pipeline(
    output_dir: str,
    clips: Optional[List[VideoClip]] = None
) -> List[MetricRecord]:
    """
    Baseline inference runner (for completeness, though T015 covers it).
    """
    ensure_directories(output_dir)
    if clips is None:
        clips = load_processed_clips()
    
    logger.info(f"Starting Baseline inference pipeline on {len(clips)} clips.")
    results = []
    
    start_time = time.time()
    profiler = MemoryProfiler()
    profiler.start()

    for i, clip in enumerate(clips):
        logger.info(f"Processing clip {i+1}/{len(clips)}: {clip.id}")
        try:
            inference_result = run_baseline_inference(clip)
            if inference_result is None: continue
            
            frames = inference_result.frames
            bss = compute_background_stability_score(frames)
            ssim = compute_ssim(frames)
            grad = compute_temporal_gradient_variance(frames)

            metric_record = MetricRecord(
                clip_id=clip.id,
                model_variant="baseline",
                peak_memory=0,
                fps=30,
                ssim=ssim.get('score', 0.0),
                gradient_variance=grad.get('variance', 0.0),
                flow_magnitude=0.0,
                invalid_flow=False
            )
            results.append(metric_record)
        except Exception as e:
            logger.error(f"Error in baseline clip {clip.id}: {e}")
            continue
        gc.collect()

    profiler.stop()
    for r in results:
        r.peak_memory = profiler.get_peak_memory()

    generate_baseline_report(results, output_dir)
    return results

def run_analysis_pipeline(output_dir: str) -> Dict[str, Any]:
    """Run statistical analysis on baseline and flow results."""
    from analysis.stats import generate_analysis_summary
    return generate_analysis_summary(output_dir)

def main():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--stage", type=str, required=True, 
                        choices=["data_prep", "flow_compute", "inference", "analysis"],
                        help="Stage to run")
    parser.add_argument("--dataset", type=str, default="davis", help="Dataset name")
    parser.add_argument("--model", type=str, default="baseline", 
                        choices=["baseline", "flow_coherence"], help="Model variant for inference")
    parser.add_argument("--method", type=str, default="farneback", help="Flow method")
    parser.add_argument("--output", type=str, default="data/metrics", help="Output directory")
    parser.add_argument("--stratify", action="store_true", help="Enable stratification")
    
    args = parser.parse_args()
    output_dir = args.output
    ensure_directories(output_dir)

    if args.stage == "data_prep":
        logger.info("Running Data Prep...")
        # T013a/T013b logic
        process_dataset_stratification(dataset_name=args.dataset, stratify=args.stratify)
    
    elif args.stage == "flow_compute":
        logger.info("Running Flow Compute...")
        # T009a/T009 logic
        extract_flow_magnitudes_for_dataset(method=args.method, output_dir=output_dir)

    elif args.stage == "inference":
        logger.info(f"Running Inference ({args.model})...")
        clips = load_processed_clips()
        if args.model == "baseline":
            run_baseline_inference_pipeline(output_dir, clips)
        elif args.model == "flow_coherence":
            run_flow_coherence_inference_pipeline(output_dir, clips)
    
    elif args.stage == "analysis":
        logger.info("Running Analysis...")
        run_analysis_pipeline(output_dir)

    logger.info("Pipeline stage completed.")

if __name__ == "__main__":
    main()
