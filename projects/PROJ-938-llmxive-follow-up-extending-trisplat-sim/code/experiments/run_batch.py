import argparse
import json
import logging
import os
import signal
import sys
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import scipy.stats as stats
from utils.stats import apply_variance_stabilization, check_normality, run_statistical_analysis_batch

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class TimeoutHandler:
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.timer = None

    def start(self):
        if sys.platform != 'win32':
            signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self.seconds)
        else:
            # Fallback for Windows
            self.timer = time.time() + self.seconds

    def _handle_timeout(self, signum, frame):
        raise TimeoutError("SCENE_TIMEOUT_EXCEEDED")

    def stop(self):
        if sys.platform != 'win32':
            signal.alarm(0)

class SceneResult:
    def __init__(self, scene_id: str, view_count: int, success: bool, latency: float, chamfer: float, psnr: float, error_flag: Optional[str] = None):
        self.scene_id = scene_id
        self.view_count = view_count
        self.success = success
        self.latency = latency
        self.chamfer = chamfer
        self.psnr = psnr
        self.error_flag = error_flag

def setup_logging(log_file: str = None):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file) if log_file else logging.getLogger(),
            logging.StreamHandler(sys.stdout)
        ]
    )

def enforce_cpu_affinity(num_cores: int = 2):
    """Enforce CPU affinity for the process."""
    if hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, list(range(num_cores)))
        logger.info(f"CPU affinity set to {num_cores} cores.")
    else:
        logger.warning("sched_setaffinity not available; skipping CPU affinity enforcement.")

def run_baseline_trisplat_cpu(scene_data: Dict[str, Any], view_count: int) -> Tuple[float, float, float]:
    """Run baseline TriSplat on CPU and return (latency, chamfer, psnr)."""
    # Placeholder for actual implementation
    # In real scenario, this would call the TriSplat model
    start = time.perf_counter()
    # Simulate computation
    time.sleep(0.1)
    end = time.perf_counter()
    latency = end - start
    # Simulate metrics
    chamfer = 0.5 + np.random.rand() * 0.1
    psnr = 25.0 + np.random.rand() * 2.0
    return latency, chamfer, psnr

def run_single_scene(scene_data: Dict[str, Any], view_count: int, timeout: int) -> SceneResult:
    """Run a single scene with timeout handling."""
    try:
        handler = TimeoutHandler(timeout)
        handler.start()
        start = time.perf_counter()
        latency, chamfer, psnr = run_baseline_trisplat_cpu(scene_data, view_count)
        end = time.perf_counter()
        actual_latency = end - start
        handler.stop()
        return SceneResult(
            scene_id=scene_data['id'],
            view_count=view_count,
            success=True,
            latency=actual_latency,
            chamfer=chamfer,
            psnr=psnr
        )
    except TimeoutError as e:
        logger.error(str(e))
        return SceneResult(
            scene_id=scene_data['id'],
            view_count=view_count,
            success=False,
            latency=timeout,
            chamfer=0.0,
            psnr=0.0,
            error_flag="SCENE_TIMEOUT_EXCEEDED"
        )
    except Exception as e:
        logger.error(f"Scene processing failed: {e}")
        return SceneResult(
            scene_id=scene_data['id'],
            view_count=view_count,
            success=False,
            latency=0.0,
            chamfer=0.0,
            psnr=0.0,
            error_flag="PROCESSING_ERROR"
        )

def generate_summary_report(results: List[SceneResult]) -> Dict[str, Any]:
    """Generate a summary report from scene results."""
    summary = {
        "total_scenes": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": [
            {
                "scene_id": r.scene_id,
                "view_count": r.view_count,
                "latency": r.latency,
                "chamfer": r.chamfer,
                "psnr": r.psnr,
                "success": r.success,
                "error_flag": r.error_flag
            }
            for r in results
        ]
    }
    return summary

def run_batch_orchestration(
    scenes: List[Dict[str, Any]],
    view_counts: List[int],
    scene_timeout: int = 270,
    batch_timeout: int = 3600,
    output_dir: str = "data/processed"
) -> List[SceneResult]:
    """Orchestrate batch processing with timeouts."""
    results = []
    start_batch = time.time()
    
    for scene in scenes:
        if time.time() - start_batch > batch_timeout:
            logger.warning("BATCH_TIMEOUT_EXCEEDED")
            break
        
        for vc in view_counts:
            result = run_single_scene(scene, vc, scene_timeout)
            results.append(result)
    
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenes', type=str, required=True, help='Path to scene list JSON')
    parser.add_argument('--view-counts', type=int, nargs='+', default=[2, 3, 4, 5], help='View counts to test')
    parser.add_argument('--scene-timeout', type=int, default=270, help='Per-scene timeout in seconds')
    parser.add_argument('--batch-timeout', type=int, default=3600, help='Batch timeout in seconds')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    args = parser.parse_args()

    setup_logging()
    enforce_cpu_affinity(2)

    # Load scenes
    with open(args.scenes, 'r') as f:
        scenes = json.load(f)

    # Run batch
    results = run_batch_orchestration(
        scenes=scenes,
        view_counts=args.view_counts,
        scene_timeout=args.scene_timeout,
        batch_timeout=args.batch_timeout,
        output_dir=args.output_dir
    )

    # Check normality of latency data and apply variance-stabilizing transformation if needed
    latency_data = [r.latency for r in results if r.success]
    if latency_data:
        normality = check_normality(latency_data)
        if not normality['is_normal']:
            logger.warning("Latency data is non-normal. Applying variance-stabilizing transformation (Box-Cox).")
            transformed_latencies, lam = apply_variance_stabilization(latency_data)
            logger.info(f"Transformed latency data. Lambda: {lam}")
            # Update results with transformed latencies for statistical analysis
            for i, r in enumerate(results):
                if r.success:
                    r.latency = transformed_latencies[i]

    # Generate report
    report = generate_summary_report(results)
    output_path = Path(args.output_dir) / "batch_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Batch results saved to {output_path}")

if __name__ == "__main__":
    main()