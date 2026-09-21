import os
import sys
import logging
import json
import gc
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from config import get_default_config, ensure_directories, set_random_seed
from utils.logger import get_logger, setup_logging
from utils.checkpoint import CheckpointManager, save_state, load_state
from data.models import VideoClip, MetricRecord
from data.processor import load_processed_clips
from data.flow import compute_flow_magnitude_for_video
from metrics.resource import MemoryProfiler
from metrics.ssim import (
    compute_ssim,
    compute_temporal_gradient_variance,
    compute_background_stability_score,
    compute_flow_statistics
)
from models.baseline import run_baseline_inference
from models.flow_coherence import run_flow_coherence_inference

# Setup logging
logger = get_logger(__name__)

def run_baseline_inference_pipeline(
    output_dir: str,
    clip_subset: Optional[List[str]] = None,
    force_recompute: bool = False
) -> List[MetricRecord]:
    """
    Run baseline LiveEdit inference on processed clips.
    
    Args:
        output_dir: Directory to write metrics JSON files.
        clip_subset: Optional list of clip IDs to process.
        force_recompute: If True, recompute metrics even if files exist.
        
    Returns:
        List of MetricRecord objects containing results.
    """
    ensure_directories(output_dir)
    config = get_default_config()
    set_random_seed(config.get("seed", 42))
    
    logger.info(f"Starting baseline inference pipeline. Output: {output_dir}")
    
    # Load clips
    clips = load_processed_clips()
    if clip_subset:
        clips = [c for c in clips if c.id in clip_subset]
        
    if not clips:
        logger.warning("No clips found to process.")
        return []
        
    logger.info(f"Processing {len(clips)} clips.")
    
    profiler = MemoryProfiler()
    results = []
    
    for i, clip in enumerate(clips):
        logger.info(f"[{i+1}/{len(clips)}] Processing clip: {clip.id}")
        
        # Memory profiling context
        profiler.start()
        
        # Run inference
        try:
            inference_result = run_baseline_inference(clip)
        except Exception as e:
            logger.error(f"Error during inference for clip {clip.id}: {e}")
            continue
            
        peak_memory = profiler.get_peak_memory()
        profiler.stop()
        
        # Compute metrics
        bss = compute_background_stability_score(clip, inference_result.frames)
        ssim = compute_ssim(inference_result.frames, mask=clip.mask)
        grad = compute_temporal_gradient_variance(inference_result.frames, mask=clip.mask)
        
        # Create record
        record = MetricRecord(
            clip_id=clip.id,
            model_variant="baseline",
            peak_memory=peak_memory,
            inference_time=inference_result.time,
            bss_score=bss.get("score", 0.0),
            consecutive_ssim=ssim.get("score", 0.0),
            temporal_gradient_variance=grad.get("variance", 0.0)
        )
        results.append(record)
        
        # Write intermediate files
        output_path = Path(output_dir)
        with open(output_path / f"baseline_bss_{clip.id}.json", "w") as f:
            json.dump(bss, f)
        with open(output_path / f"baseline_ssim_{clip.id}.json", "w") as f:
            json.dump(ssim, f)
        with open(output_path / f"baseline_grad_{clip.id}.json", "w") as f:
            json.dump(grad, f)
            
        gc.collect()
        
    # Write aggregate results
    results_path = Path(output_dir) / "baseline_results.json"
    with open(results_path, "w") as f:
        json.dump([r.__dict__ for r in results], f, indent=2)
        
    logger.info(f"Baseline pipeline complete. Results written to {results_path}")
    return results

def run_flow_coherence_inference_pipeline(
    output_dir: str,
    checkpoint_id: str,
    clip_subset: Optional[List[str]] = None,
    force_recompute: bool = False
) -> List[MetricRecord]:
    """
    Run Flow-Coherence inference on processed clips with checkpointing support.
    
    Args:
        output_dir: Directory to write metrics JSON files.
        checkpoint_id: Unique identifier for this run to manage checkpoints.
        clip_subset: Optional list of clip IDs to process.
        force_recompute: If True, recompute metrics even if files exist.
        
    Returns:
        List of MetricRecord objects containing results.
    """
    ensure_directories(output_dir)
    config = get_default_config()
    set_random_seed(config.get("seed", 42))
    
    logger.info(f"Starting flow-coherence inference pipeline. Output: {output_dir}")
    
    # Initialize checkpoint manager
    checkpoint_dir = Path(output_dir) / "checkpoints"
    ensure_directories(str(checkpoint_dir))
    checkpoint_mgr = CheckpointManager(checkpoint_dir, checkpoint_id)
    
    # Load clips
    clips = load_processed_clips()
    if clip_subset:
        clips = [c for c in clips if c.id in clip_subset]
        
    if not clips:
        logger.warning("No clips found to process.")
        return []
        
    # Filter out already processed clips unless force_recompute
    if not force_recompute:
        clips = [c for c in clips if not checkpoint_mgr.is_processed(c.id)]
        
    if not clips:
        logger.info("All clips already processed. Skipping.")
        # Still need to load and merge previous results
        # For now, return empty and let reporter handle aggregation
        return []
        
    logger.info(f"Processing {len(clips)} clips (excluding {len(load_processed_clips()) - len(clips)} completed).")
    
    profiler = MemoryProfiler()
    results = []
    
    for i, clip in enumerate(clips):
        logger.info(f"[{i+1}/{len(clips)}] Processing clip: {clip.id}")
        
        # Memory profiling context
        profiler.start()
        
        # Run inference
        try:
            inference_result = run_flow_coherence_inference(clip)
        except Exception as e:
            logger.error(f"Error during inference for clip {clip.id}: {e}")
            checkpoint_mgr.mark_failed(clip.id, str(e))
            continue
            
        peak_memory = profiler.get_peak_memory()
        profiler.stop()
        
        # Compute metrics
        bss = compute_background_stability_score(clip, inference_result.frames)
        ssim = compute_ssim(inference_result.frames, mask=clip.mask)
        grad = compute_temporal_gradient_variance(inference_result.frames, mask=clip.mask)
        flow_stats = compute_flow_statistics(inference_result.flow_fields)
        
        # Create record
        record = MetricRecord(
            clip_id=clip.id,
            model_variant="flow_coherence",
            peak_memory=peak_memory,
            inference_time=inference_result.time,
            bss_score=bss.get("score", 0.0),
            consecutive_ssim=ssim.get("score", 0.0),
            temporal_gradient_variance=grad.get("variance", 0.0),
            invalid_flow_count=inference_result.invalid_flow_count,
            flow_magnitude_mean=flow_stats.get("mean_magnitude", 0.0)
        )
        results.append(record)
        
        # Update checkpoint
        checkpoint_mgr.mark_processed(clip.id)
        
        # Write intermediate files
        output_path = Path(output_dir)
        with open(output_path / f"flow_bss_{clip.id}.json", "w") as f:
            json.dump(bss, f)
        with open(output_path / f"flow_ssim_{clip.id}.json", "w") as f:
            json.dump(ssim, f)
        with open(output_path / f"flow_grad_{clip.id}.json", "w") as f:
            json.dump(grad, f)
        with open(output_path / f"flow_stats_{clip.id}.json", "w") as f:
            json.dump(flow_stats, f)
            
        gc.collect()
        
    # Write aggregate results
    results_path = Path(output_dir) / "flow_results.json"
    with open(results_path, "w") as f:
        json.dump([r.__dict__ for r in results], f, indent=2)
        
    logger.info(f"Flow-coherence pipeline complete. Results written to {results_path}")
    return results

def run_analysis_pipeline(
    output_dir: str,
    methods: List[str] = None,
    sensitivity_cutoffs: List[float] = None
) -> Dict[str, Any]:
    """
    Run statistical analysis pipeline comparing baseline and flow-coherence results.
    
    Args:
        output_dir: Directory to write analysis results.
        methods: List of analysis methods to run (e.g., 'ks_test', 'piecewise', 'sensitivity').
        sensitivity_cutoffs: Cutoff values for sensitivity analysis.
        
    Returns:
        Dictionary containing analysis results.
    """
    ensure_directories(output_dir)
    
    logger.info(f"Starting analysis pipeline. Output: {output_dir}")
    
    # Import stats module to trigger analysis
    from analysis.stats import (
        load_json_metrics,
        aggregate_metrics_to_pairs,
        compute_kolmogorov_smirnov_test,
        compute_piecewise_regression,
        run_sensitivity_analysis,
        generate_analysis_summary
    )
    
    baseline_path = Path(output_dir) / "baseline_results.json"
    flow_path = Path(output_dir) / "flow_results.json"
    
    if not baseline_path.exists() or not flow_path.exists():
        logger.error("Missing baseline or flow results. Cannot run analysis.")
        return {}
        
    # Load metrics
    baseline_metrics = load_json_metrics(baseline_path)
    flow_metrics = load_json_metrics(flow_path)
    
    # Aggregate pairs
    paired_data = aggregate_metrics_to_pairs(baseline_metrics, flow_metrics)
    paired_path = Path(output_dir) / "paired_metrics.json"
    with open(paired_path, "w") as f:
        json.dump(paired_data, f, indent=2)
        
    results = {}
    
    if not methods:
        methods = ['ks_test', 'piecewise', 'sensitivity']
        
    if 'ks_test' in methods:
        logger.info("Running Kolmogorov-Smirnov test...")
        ks_result = compute_kolmogorov_smirnov_test(paired_data)
        ks_path = Path(output_dir) / "ks_test.json"
        with open(ks_path, "w") as f:
            json.dump(ks_result, f, indent=2)
        results['ks_test'] = ks_result
        
    if 'piecewise' in methods:
        logger.info("Running piecewise regression...")
        pc_result = compute_piecewise_regression(paired_data)
        pc_path = Path(output_dir) / "pc_regression.json"
        with open(pc_path, "w") as f:
            json.dump(pc_result, f, indent=2)
        results['pc_regression'] = pc_result
        
    if 'sensitivity' in methods:
        if not sensitivity_cutoffs:
            sensitivity_cutoffs = [0.01, 0.05, 0.1]
        logger.info(f"Running sensitivity analysis with cutoffs: {sensitivity_cutoffs}")
        sens_result = run_sensitivity_analysis(paired_data, sensitivity_cutoffs)
        sens_path = Path(output_dir) / "sensitivity_analysis.json"
        with open(sens_path, "w") as f:
            json.dump(sens_result, f, indent=2)
        results['sensitivity_analysis'] = sens_result
        
    # Generate summary
    summary = generate_analysis_summary(results)
    summary_path = Path(output_dir) / "analysis_results.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Analysis pipeline complete. Summary written to {summary_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="llmXive Video Editing Analysis Pipeline")
    parser.add_argument("--stage", type=str, required=True, 
                      choices=["data_prep", "flow_compute", "inference", "analysis"],
                      help="Pipeline stage to execute")
    parser.add_argument("--dataset", type=str, default="davis",
                      help="Dataset to use (davis, youtube_vos)")
    parser.add_argument("--method", type=str, default=None,
                      help="Method for flow computation or analysis")
    parser.add_argument("--model", type=str, default="baseline",
                      choices=["baseline", "flow_coherence"],
                      help="Model variant for inference stage")
    parser.add_argument("--stratify", action="store_true",
                      help="Apply stratification during data prep")
    parser.add_argument("--output_dir", type=str, default="data/metrics",
                      help="Output directory for results")
    parser.add_argument("--checkpoint_id", type=str, default=None,
                      help="Checkpoint ID for flow-coherence inference")
    parser.add_argument("--sweep", type=str, default=None,
                      help="Comma-separated cutoff values for sensitivity analysis")
                      
    args = parser.parse_args()
    setup_logging()
    
    if args.stage == "data_prep":
        from data.downloader import download_dataset
        from data.processor import process_dataset_stratification
        
        logger.info(f"Running data prep for {args.dataset}")
        download_dataset(args.dataset, stratify=args.stratify)
        if args.stratify:
            process_dataset_stratification()
            
    elif args.stage == "flow_compute":
        from data.flow import compute_full_flow_field
        
        logger.info(f"Computing flow with method: {args.method}")
        compute_full_flow_field(method=args.method)
        
    elif args.stage == "inference":
        if args.model == "baseline":
            run_baseline_inference_pipeline(args.output_dir)
        elif args.model == "flow_coherence":
            if not args.checkpoint_id:
                args.checkpoint_id = "flow_run_001"
            run_flow_coherence_inference_pipeline(args.output_dir, args.checkpoint_id)
            
    elif args.stage == "analysis":
        cutoffs = None
        if args.sweep:
            cutoffs = [float(x) for x in args.sweep.split(",")]
        run_analysis_pipeline(args.output_dir, methods=[args.method] if args.method else None, 
                            sensitivity_cutoffs=cutoffs)
                            
if __name__ == "__main__":
    main()