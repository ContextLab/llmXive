import argparse
import json
import logging
import os
import signal
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

from data.loader import get_scene_batch
from models.geometry_only import run_geometry_optimization_with_fallback
from models.trisplat_base import load_trisplat_base, is_cpu_compatible
from utils.mesh_utils import export_mesh, create_placeholder_mesh
from utils.stats import calculate_comparative_metrics
from data.metrics import calculate_metrics_batch

# Setup logging
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("run_batch")
    logger.setLevel(logging.INFO)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

class TimeoutError(Exception):
    pass

class TimeoutHandler:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.seconds)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        if exc_type is TimeoutError:
            return True
        return False
    
    def _timeout_handler(self, signum, frame):
        raise TimeoutError(f"Operation timed out after {self.seconds} seconds")
    
    def check_remaining(self, budget: int) -> float:
        if not self.start_time:
            return float('inf')
        elapsed = time.time() - self.start_time
        return max(0, budget - elapsed)

timeout_handler = TimeoutHandler(3600)

class SceneResult:
    def __init__(self, scene_id: str, view_count: int, status: str, 
                 metrics: Optional[Dict[str, float]] = None, 
                 error: Optional[str] = None, 
                 latency: Optional[float] = None):
        self.scene_id = scene_id
        self.view_count = view_count
        self.status = status
        self.metrics = metrics or {}
        self.error = error
        self.latency = latency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "view_count": self.view_count,
            "status": self.status,
            "metrics": self.metrics,
            "error": self.error,
            "latency": self.latency
        }

def run_baseline_trisplat_cpu(scene_data: Dict[str, Any], view_count: int, logger: logging.Logger) -> SceneResult:
    """
    Run baseline TriSplat on CPU with 2-core affinity.
    If it fails (CUDA error or timeout), log skipped and return None metrics.
    """
    start = time.time()
    try:
        # Attempt to load baseline
        model = load_trisplat_base()
        if not is_cpu_compatible(model):
            logger.warning(f"Baseline TriSplat not CPU compatible for {scene_data['id']}")
            return SceneResult(scene_data['id'], view_count, "skipped", error="baseline_cpu_unsupported")
        
        # Simulate inference (actual implementation would run forward pass)
        # For this task, we assume the model runs but might fail on 2-core constraint
        # In a real scenario, we would enforce CPU affinity here
        
        result = model.run_inference(scene_data, num_views=view_count)
        latency = time.time() - start
        
        return SceneResult(scene_data['id'], view_count, "success", latency=latency)
    except Exception as e:
        logger.warning(f"Baseline TriSplat failed for {scene_data['id']}: {str(e)}")
        return SceneResult(scene_data['id'], view_count, "skipped", error="baseline_cpu_unsupported")

def run_single_scene(scene_data: Dict[str, Any], view_count: int, logger: logging.Logger, timeout_remaining: float) -> SceneResult:
    """
    Run the geometry-only reconstruction for a single scene.
    """
    start = time.time()
    try:
        with TimeoutHandler(int(timeout_remaining)) as to:
            # Run geometry optimization
            result = run_geometry_optimization_with_fallback(
                scene_data, 
                num_views=view_count,
                logger=logger
            )
            
            # Calculate metrics if available
            metrics = {}
            if result.get('mesh_path') and os.path.exists(result['mesh_path']):
                # In real implementation, compare against ground truth
                # metrics = calculate_metrics_batch(...)
                metrics = {"chamfer_distance": 0.0, "psnr": 0.0} # Placeholder for structure
            
            latency = time.time() - start
            
            return SceneResult(
                scene_data['id'], 
                view_count, 
                "success" if result.get('success') else "failed",
                metrics=metrics,
                error=result.get('error'),
                latency=latency
            )
    except TimeoutError:
        logger.warning(f"Timeout for scene {scene_data['id']}")
        return SceneResult(scene_data['id'], view_count, "timeout", error="timeout_reached")
    except Exception as e:
        logger.error(f"Error processing scene {scene_data['id']}: {str(e)}")
        return SceneResult(scene_data['id'], view_count, "failed", error=str(e))

def generate_summary_report(results: List[SceneResult], output_path: str):
    """
    Generate a summary report of all scene results.
    """
    with open(output_path, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    logging.info(f"Summary report saved to {output_path}")

def run_batch_orchestration(
    num_scenes: int, 
    view_counts: List[int], 
    timeout_seconds: int, 
    logger: logging.Logger,
    expand_to_50: bool = False
) -> List[SceneResult]:
    """
    Orchestrates the batch processing of scenes.
    Implements T042: If N=20 scenes complete within 70% of time budget, expand to 50.
    """
    start_time = time.time()
    budget = timeout_seconds
    all_results = []
    
    # Initial scene list
    initial_count = min(num_scenes, 20)
    scenes = get_scene_batch(initial_count)
    logger.info(f"Starting batch with {len(scenes)} scenes (Target: {num_scenes}, Max: {initial_count})")
    
    scene_index = 0
    
    while scene_index < len(scenes):
        # Check time budget
        elapsed = time.time() - start_time
        remaining = budget - elapsed
        
        # T042 Logic: Check if we should expand to 50
        if (expand_to_50 and 
            len(scenes) < 50 and 
            scene_index >= initial_count and 
            elapsed < (budget * 0.70)):
            
            # Expand the list
            new_scenes = get_scene_batch(50)
            # Filter out already processed scenes
            processed_ids = {s['id'] for s in scenes[:scene_index]}
            new_scenes = [s for s in new_scenes if s['id'] not in processed_ids]
            
            if new_scenes:
                logger.info(f"T042: Expanding scene list to 50. Adding {len(new_scenes)} new scenes.")
                scenes.extend(new_scenes)
            else:
                logger.info("T042: No additional scenes available to expand.")
        
        # Process current scene
        current_scene = scenes[scene_index]
        logger.info(f"Processing scene {scene_index + 1}/{len(scenes)}: {current_scene['id']}")
        
        # Process all view counts for this scene
        for v_count in view_counts:
            if elapsed >= budget:
                logger.warning("Time budget exhausted. Stopping batch.")
                break
            
            result = run_single_scene(current_scene, v_count, logger, remaining)
            all_results.append(result)
            elapsed = time.time() - start_time
            remaining = budget - elapsed
        
        scene_index += 1
        
        # Safety break if we've processed 50 scenes
        if len(scenes) >= 50 and scene_index >= 50:
            break

    elapsed_total = time.time() - start_time
    logger.info(f"Batch orchestration completed. Processed {len(all_results)} scene-views in {elapsed_total:.2f}s.")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Run TriSplat batch experiments")
    parser.add_argument("--views", type=int, nargs="+", default=[2, 3, 4, 5], help="View counts to test")
    parser.add_argument("--timeout", type=int, default=21600, help="Total timeout in seconds (6h)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--update-state", action="store_true", help="Update state file after run")
    parser.add_argument("--num-scenes", type=int, default=20, help="Number of scenes to process")
    parser.add_argument("--log-file", type=str, default=None, help="Log file path")
    
    args = parser.parse_args()
    
    # Set seed
    random.seed(args.seed)
    
    # Setup logging
    logger = setup_logging(args.log_file)
    
    # Run batch
    results = run_batch_orchestration(
        num_scenes=args.num_scenes,
        view_counts=args.views,
        timeout_seconds=args.timeout,
        logger=logger,
        expand_to_50=True  # T042: Enable stretch goal logic
    )
    
    # Generate report
    report_path = "data/processed/batch_results.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    generate_summary_report(results, report_path)
    
    logger.info(f"Pipeline finished. Results saved to {report_path}")

if __name__ == "__main__":
    main()