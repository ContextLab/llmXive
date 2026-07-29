"""
Orchestrator Entry Point - Single entry point for the entire pipeline.
"""
import json
import logging
import sys
import time
import tracemalloc
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.config import get_project_root, get_path, ensure_dir
from utils.runtime_logger import RuntimeLogger
from utils.memory_logger import get_peak_memory_gb, log_memory_usage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the pipeline."""
    project_root = get_project_root()
    processed_dir = get_path(project_root, "processed_data")
    ensure_dir(processed_dir)

    # Start timer and memory monitor
    tracemalloc.start()
    start_time = time.time()
    logger.info("Pipeline started")

    pipeline_success = True

    try:
        # Import and run analysis tasks as sub-routines
        # T013: Annotate graph
        logger.info("Running T013: Annotate graph...")
        from ingest.annotate_graph import main as t013_main
        t013_main()

        # T013b: Verify annotation coverage
        logger.info("Running T013b: Verify annotation coverage...")
        from ingest.calculate_annotation_coverage import main as t013b_main
        t013b_main()

        # T019: Stratify accuracy
        logger.info("Running T019: Stratify accuracy...")
        from analysis.stratify_accuracy import main as t019_main
        t019_main()

        # T020a: Bin preparation
        logger.info("Running T020a: Bin preparation...")
        from analysis.bin_utils import main as t020a_main
        t020a_main()

        # T020b: Threshold detection
        logger.info("Running T020b: Threshold detection...")
        from analysis.detect_threshold import main as t020b_main
        t020b_main()

        # T022: Visualization
        logger.info("Running T022: Visualization...")
        from analysis.visualize_continuous import main as t022_main
        t022_main()

        # T025: Sensitivity analysis
        logger.info("Running T025: Sensitivity analysis...")
        from analysis.sensitivity import main as t025_main
        t025_main()

        # T037: Generate final report
        logger.info("Running T037: Generate final report...")
        from analysis.generate_final_report import main as t037_main
        t037_main()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        pipeline_success = False
        error_log_path = processed_dir / "error_log.txt"
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Pipeline error: {str(e)}")

    # Stop timer and memory monitor
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_runtime = end_time - start_time
    peak_memory_gb = peak / (1024 ** 3)
    limit_exceeded = peak_memory_gb > 14  # 14 GB limit

    # Write runtime log
    runtime_log = {
        "total_runtime_seconds": total_runtime,
        "limit_exceeded": limit_exceeded,
        "peak_memory_gb": peak_memory_gb,
        "pipeline_success": pipeline_success
    }
    runtime_log_path = processed_dir / "runtime_log.json"
    with open(runtime_log_path, 'w', encoding='utf-8') as f:
        json.dump(runtime_log, f, indent=2)

    # Write memory log
    memory_log = {
        "peak_memory_gb": peak_memory_gb,
        "limit_exceeded": limit_exceeded
    }
    memory_log_path = processed_dir / "memory_log.json"
    with open(memory_log_path, 'w', encoding='utf-8') as f:
        json.dump(memory_log, f, indent=2)

    logger.info(f"Pipeline completed. Success: {pipeline_success}")
    logger.info(f"Total runtime: {total_runtime:.2f} seconds")
    logger.info(f"Peak memory: {peak_memory_gb:.2f} GB")

    if not pipeline_success:
        sys.exit(1)

if __name__ == "__main__":
    main()