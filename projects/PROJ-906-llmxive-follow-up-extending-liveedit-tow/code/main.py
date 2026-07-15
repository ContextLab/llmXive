import os
import sys
import logging
import json
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_default_config, ensure_directories
from utils.logger import get_logger, setup_logging
from utils.checkpoint import CheckpointManager
from data.models import VideoClip, MetricRecord
from data.processor import process_dataset_stratification, ProcessedClip
from models.baseline import run_baseline_inference
from models.flow_coherence import run_flow_coherence_inference
from metrics.ssim import compute_background_stability_score, compute_flow_normalized_ssim
from metrics.resource import MemoryProfiler
from analysis.reporter import generate_comparative_report

logger = get_logger(__name__)

def load_processed_clips(clip_dir: Path) -> List[ProcessedClip]:
    """Load processed clips from the data directory."""
    clips = []
    if not clip_dir.exists():
        logger.error(f"Clip directory does not exist: {clip_dir}")
        return clips
    
    for json_file in clip_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Reconstruct ProcessedClip from dict
                # Assuming the JSON structure matches the dataclass fields
                clip = ProcessedClip(**data)
                clips.append(clip)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")
    return clips

def run_flow_coherence_inference_pipeline(
    clip_dir: Path,
    output_dir: Path,
    config: Dict[str, Any],
    resume: bool = True
) -> List[MetricRecord]:
    """
    Run the Flow-Coherence inference pipeline on a list of processed clips.
    Implements T022: Flow-mode runner with checkpointing support.
    
    Args:
        clip_dir: Directory containing processed clip JSON files.
        output_dir: Directory to save metrics and results.
        config: Experiment configuration dictionary.
        resume: Whether to resume from checkpoint if available.
    
    Returns:
        List of MetricRecord objects.
    """
    ensure_directories(output_dir)
    
    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager(
        checkpoint_dir=output_dir / "checkpoints",
        run_id="flow_coherence_run"
    )
    
    # Load or resume state
    processed_clips = load_processed_clips(clip_dir)
    if not processed_clips:
        logger.warning(f"No processed clips found in {clip_dir}")
        return []
    
    start_idx = 0
    if resume:
        checkpoint_data = checkpoint_manager.load_checkpoint()
        if checkpoint_data and "processed_count" in checkpoint_data:
            start_idx = checkpoint_data["processed_count"]
            logger.info(f"Resuming from clip index {start_idx}")
        
        # Load existing metrics to append
        existing_metrics_file = output_dir / "flow_metrics.json"
        if existing_metrics_file.exists():
            with open(existing_metrics_file, 'r') as f:
                existing_records = json.load(f)
        else:
            existing_records = []
    else:
        existing_records = []
    
    # Initialize memory profiler
    memory_profiler = MemoryProfiler()
    
    results: List[MetricRecord] = []
    
    for idx, clip in enumerate(processed_clips):
        if idx < start_idx:
            logger.info(f"Skipping clip {idx} ({clip.clip_id}) - already processed")
            continue
        
        logger.info(f"Processing clip {idx}/{len(processed_clips)}: {clip.clip_id}")
        
        # Start memory tracking
        memory_profiler.start()
        
        try:
            # Run flow coherence inference
            result = run_flow_coherence_inference(
                processed_clip=clip,
                config=config
            )
            
            # Compute metrics
            bss = compute_background_stability_score(result.output_frames)
            flow_norm_ssim = compute_flow_normalized_ssim(
                result.output_frames, 
                clip.flow_data
            )
            
            # Get memory usage
            mem_usage = memory_profiler.get_peak_usage_mb()
            memory_profiler.stop()
            
            # Create metric record
            metric_record = MetricRecord(
                clip_id=clip.clip_id,
                method="flow_coherence",
                bss=bss,
                flow_normalized_ssim=flow_norm_ssim,
                peak_memory_mb=mem_usage,
                inference_time_sec=result.total_time,
                invalid_flow_count=result.invalid_flow_count,
                flow_magnitude_stats=result.flow_magnitude_stats
            )
            
            results.append(metric_record)
            
            # Save checkpoint after each clip
            checkpoint_manager.save_checkpoint({
                "processed_count": idx + 1,
                "last_clip_id": clip.clip_id
            })
            
            # Save intermediate metrics
            intermediate_metrics = [r.to_dict() for r in results]
            with open(output_dir / "flow_metrics.json", 'w') as f:
                json.dump(intermediate_metrics, f, indent=2)
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            logger.error(f"Failed to process clip {clip.clip_id}: {e}", exc_info=True)
            # Continue to next clip instead of crashing
            gc.collect()
            continue
    
    # Final report generation
    if results:
        logger.info(f"Generating comparative report for {len(results)} clips")
        generate_comparative_report(
            results=results,
            output_path=output_dir / "flow_results.json"
        )
    
    return results

def main():
    """Main entry point for the flow-coherence inference runner."""
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Load configuration
    config = get_default_config()
    config["mode"] = "flow_coherence"
    
    # Define paths
    project_root = Path(__file__).parent.parent
    clip_dir = project_root / "data" / "processed"
    output_dir = project_root / "data" / "metrics"
    
    # Ensure directories exist
    ensure_directories(output_dir)
    
    logger.info("Starting Flow-Coherence Inference Pipeline")
    logger.info(f"Clip directory: {clip_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Run pipeline
    metrics = run_flow_coherence_inference_pipeline(
        clip_dir=clip_dir,
        output_dir=output_dir,
        config=config,
        resume=True
    )
    
    logger.info(f"Pipeline completed. Processed {len(metrics)} clips.")
    
    # Print summary
    if metrics:
        avg_bss = sum(m.bss for m in metrics) / len(metrics)
        avg_mem = sum(m.peak_memory_mb for m in metrics) / len(metrics)
        logger.info(f"Average BSS: {avg_bss:.4f}")
        logger.info(f"Average Memory: {avg_mem:.2f} MB")
    
    return metrics

if __name__ == "__main__":
    main()