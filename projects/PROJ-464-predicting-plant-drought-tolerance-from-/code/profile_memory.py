import os
import sys
import time
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing pipeline modules to profile
# Note: These imports assume the modules are in the code/ directory and added to sys.path
# The main entry point is expected to be run from the project root or code/
try:
    from download_images import main as download_main
    from preprocess_images import main as preprocess_main
except ImportError as e:
    # Fallback for execution context if not in code/ directory
    sys.path.insert(0, str(Path(__file__).parent))
    from download_images import main as download_main
    from preprocess_images import main as preprocess_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_current_memory_mb() -> float:
    """Get current memory usage in MB."""
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def run_pipeline_with_profiling() -> Dict[str, float]:
    """
    Run the image loading and preprocessing pipeline with memory profiling.
    
    Returns:
        Dict containing peak memory usage at various stages.
    """
    stats = {
        'start_memory_mb': 0.0,
        'download_peak_mb': 0.0,
        'preprocess_peak_mb': 0.0,
        'end_memory_mb': 0.0
    }

    # Start tracking
    tracemalloc.start()
    stats['start_memory_mb'] = get_current_memory_mb()
    logger.info(f"Initial memory: {stats['start_memory_mb']:.2f} MB")

    try:
        # Profile Download Images
        logger.info("Starting image download profiling...")
        download_main()
        stats['download_peak_mb'] = get_peak_memory_mb()
        logger.info(f"Download peak memory: {stats['download_peak_mb']:.2f} MB")

        # Profile Preprocess Images
        logger.info("Starting image preprocessing profiling...")
        preprocess_main()
        stats['preprocess_peak_mb'] = get_peak_memory_mb()
        logger.info(f"Preprocess peak memory: {stats['preprocess_peak_mb']:.2f} MB")

    except Exception as e:
        logger.error(f"Pipeline execution failed during profiling: {e}")
        raise
    finally:
        # Stop tracking
        tracemalloc.stop()
        stats['end_memory_mb'] = get_current_memory_mb()

    return stats

def generate_memory_report(stats: Dict[str, float]) -> None:
    """
    Generate a markdown report of the memory profiling results.
    Writes to state/memory_profile.md as per T039b specification.
    """
    # T039b explicitly requests output to state/memory_profile.md
    output_path = Path("state/memory_profile.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    peak_memory = max(
        stats['download_peak_mb'],
        stats['preprocess_peak_mb']
    )
    limit = 7.0  # 7GB limit as per task spec
    limit_mb = limit * 1024

    status = "PASS" if peak_memory < limit_mb else "FAIL"
    
    content = f"""# Memory Profiling Report

## Summary
- **Status**: {status}
- **Peak Memory Usage**: {peak_memory:.2f} MB
- **Constraint**: < {limit_mb} MB (7 GB)

## Detailed Metrics
| Stage | Memory Usage (MB) |
|-------|-------------------|
| Start | {stats['start_memory_mb']:.2f} |
| Download Peak | {stats['download_peak_mb']:.2f} |
| Preprocess Peak | {stats['preprocess_peak_mb']:.2f} |
| End | {stats['end_memory_mb']:.2f} |

## Analysis
The image loading and preprocessing pipeline was executed with memory profiling enabled.
The peak memory usage observed was **{peak_memory:.2f} MB**.

{'The pipeline successfully stayed within the 7GB memory limit.' if peak_memory < limit_mb else 'WARNING: The pipeline exceeded the 7GB memory limit. Optimization (e.g., streaming) is required.'}

## Methodology
- Used Python's `tracemalloc` module for accurate memory tracking.
- Profiled the full execution of `download_images.py` and `preprocess_images.py`.
- Measured peak memory consumption during the most intensive phases.
- Output written to: {output_path}
"""

    with open(output_path, 'w') as f:
        f.write(content)

    logger.info(f"Memory profile report generated at {output_path}")

def main():
    """Main entry point for memory profiling."""
    logger.info("Starting memory profiling for image loading pipeline...")
    
    # Ensure required directories exist
    Path("state").mkdir(exist_ok=True)
    Path("docs").mkdir(exist_ok=True)

    try:
        stats = run_pipeline_with_profiling()
        generate_memory_report(stats)
        logger.info("Memory profiling completed successfully.")
    except Exception as e:
        logger.error(f"Memory profiling failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()