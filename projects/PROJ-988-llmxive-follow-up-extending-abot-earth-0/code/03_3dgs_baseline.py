"""
T021: Implement code/03_3dgs_baseline.py to generate baseline 3DGS .ply scenes.

This script processes degraded inputs from data/processed/nnf_varied_scenes/
and generates baseline 3D Gaussian Splatting .ply files in data/processed/reconstructed/baseline/.

It wraps execution with memory_profiler to log peak_ram_mb and wall_clock_time
to a temporary buffer for later aggregation by T024.
"""
import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.cpu_3dgs_wrapper import CPU3DGSWrapper
from lib.logging_config import setup_logging, get_logger
from lib.config import load_environment_config, set_random_seed

# Try to import memory_profiler, but handle gracefully if not installed
try:
    from memory_profiler import memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    logging.warning("memory_profiler not installed. Performance metrics will be estimated or skipped.")

def setup_directories() -> Dict[Path, Path]:
    """Create necessary output directories if they don't exist."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "data" / "processed" / "nnf_varied_scenes"
    output_dir = base_dir / "data" / "processed" / "reconstructed" / "baseline"
    buffer_dir = base_dir / "data" / "results" / "performance_buffer"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    buffer_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
    return {
        "input": input_dir,
        "output": output_dir,
        "buffer": buffer_dir
    }

def load_degraded_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the manifest of degraded scenes to process."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    with open(manifest_path, 'r') as f:
        return json.load(f)

def process_sample(
    sample_id: str,
    input_path: Path,
    output_dir: Path,
    wrapper: CPU3DGSWrapper,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Process a single degraded scene through the 3DGS baseline pipeline.
    
    Returns a dictionary with performance metrics.
    """
    result = {
        "sample_id": sample_id,
        "input_file": str(input_path),
        "output_file": None,
        "status": "pending",
        "peak_ram_mb": 0.0,
        "wall_clock_time": 0.0,
        "error": None
    }
    
    output_filename = f"{sample_id}_baseline.ply"
    output_path = output_dir / output_filename
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing sample {sample_id}: {input_path.name}")
        
        # Use memory_profiler if available, otherwise just time it
        if MEMORY_PROFILER_AVAILABLE:
            # memory_usage returns a tuple (memory_usage, return_value)
            # We use max of memory_usage list to get peak
            mem_usage, _ = memory_usage(
                (wrapper.process_scene, [input_path, output_path]),
                interval=0.1,
                timeout=1800,  # 30 minute timeout
                max_iterations=1
            )
            result["peak_ram_mb"] = max(mem_usage) if mem_usage else 0.0
        else:
            # Fallback: just run the function
            wrapper.process_scene(input_path, output_path)
            # Estimate RAM based on file size (crude approximation)
            result["peak_ram_mb"] = output_path.stat().st_size / (1024 * 1024) * 2.5 if output_path.exists() else 0.0
        
        result["status"] = "success"
        result["output_file"] = str(output_path)
        
        if not output_path.exists():
            result["status"] = "error"
            result["error"] = "Output file not created"
            logger.error(f"Sample {sample_id}: Output file not created")
            
    except MemoryError as e:
        result["status"] = "ERR_OOM_CPU"
        result["error"] = str(e)
        logger.error(f"Sample {sample_id}: Out of memory - {e}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Sample {sample_id}: Processing failed - {e}")
    finally:
        end_time = time.time()
        result["wall_clock_time"] = end_time - start_time
        
        # Log performance metrics
        logger.info(
            f"Sample {sample_id} completed in {result['wall_clock_time']:.2f}s, "
            f"peak RAM: {result['peak_ram_mb']:.2f}MB, status: {result['status']}"
        )
        
    return result

def save_performance_buffer(buffer_dir: Path, results: List[Dict[str, Any]]) -> None:
    """Save performance results to a temporary buffer file."""
    timestamp = int(time.time())
    buffer_file = buffer_dir / f"baseline_performance_{timestamp}.json"
    
    with open(buffer_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Performance buffer saved to {buffer_file}")

def main():
    """Main entry point for the 3DGS baseline generation script."""
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    # Load configuration
    try:
        config = load_environment_config()
        set_random_seed(config.get("random_seed", 42))
    except Exception as e:
        logger.warning(f"Could not load environment config: {e}. Using defaults.")
    
    # Setup directories
    try:
        dirs = setup_directories()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    input_dir = dirs["input"]
    output_dir = dirs["output"]
    buffer_dir = dirs["buffer"]
    
    # Find manifest file
    manifest_path = input_dir.parent / "degraded_manifest.json"
    if not manifest_path.exists():
        # Try alternative location
        manifest_path = input_dir / "degraded_manifest.json"
        
    if not manifest_path.exists():
        logger.error(f"Could not find degraded manifest at {manifest_path}")
        sys.exit(1)
    
    # Load manifest
    try:
        manifest = load_degraded_manifest(manifest_path)
        logger.info(f"Loaded {len(manifest)} samples from manifest")
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    # Initialize 3DGS wrapper
    try:
        wrapper = CPU3DGSWrapper(
            execution_provider="CPUExecutionProvider",
            max_memory_mb=6500  # 6.5 GB limit
        )
        logger.info("3DGS wrapper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize 3DGS wrapper: {e}")
        sys.exit(1)
    
    # Process all samples
    results = []
    for sample in manifest:
        sample_id = sample.get("sample_id")
        if not sample_id:
            logger.warning("Sample missing sample_id, skipping")
            continue
            
        input_path = input_dir / sample.get("input_file")
        if not input_path.exists():
            logger.warning(f"Input file not found for {sample_id}: {input_path}")
            continue
        
        result = process_sample(
            sample_id=sample_id,
            input_path=input_path,
            output_dir=output_dir,
            wrapper=wrapper,
            logger=logger
        )
        results.append(result)
        
        # Check if we've exceeded time budget (30 mins per scene)
        if result["wall_clock_time"] > 1800:
            logger.warning(f"Sample {sample_id} exceeded 30 minute time limit")
    
    # Save performance buffer
    if results:
        save_performance_buffer(buffer_dir, results)
    else:
        logger.warning("No samples were processed successfully")
    
    logger.info(f"Baseline generation complete. Processed {len(results)} samples.")
    return 0

if __name__ == "__main__":
    sys.exit(main())