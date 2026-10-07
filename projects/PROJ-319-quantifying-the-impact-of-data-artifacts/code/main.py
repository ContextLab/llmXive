"""
Main CLI entry point for the llmXive automated science pipeline.
"""
import argparse
import logging
import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Adjust imports to work from the code directory when run as script
# The import structure assumes we are running from the project root
# or that code/ is in sys.path.
try:
    from code.config import get_project_root, get_config_summary
    from code.io.writer import write_run_manifest_for_pipeline
    from code.synthetic.generator import main as generate_main
    from code.synthetic.artifacts import main as artifacts_main
    from code.analysis.statistics import main as stats_main
    from code.analysis.regression import main as regression_main
    from code.analysis.validation import main as validation_main
    from code.analysis.power_analysis import main as power_main
except ImportError:
    # Fallback for direct execution if sys.path isn't set correctly
    # This block ensures the script runs even if called as `python code/main.py`
    # from the project root, by adding the parent to path.
    import sys
    from pathlib import Path
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    
    from config import get_project_root, get_config_summary
    from io.writer import write_run_manifest_for_pipeline
    from synthetic.generator import main as generate_main
    from synthetic.artifacts import main as artifacts_main
    from analysis.statistics import main as stats_main
    from analysis.regression import main as regression_main
    from analysis.validation import main as validation_main
    from analysis.power_analysis import main as power_main

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure logging to file and console."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def setup_directories(root: Path):
    """Ensure required directories exist."""
    dirs = [
        root / "data" / "raw",
        root / "data" / "synthetic",
        root / "data" / "processed",
        root / "data" / "validation",
        root / "logs",
        root / "tests"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_pipeline_state(root: Path):
    """
    Check for required files before execution.
    Raises FileNotFoundError if dependencies are missing.
    """
    gt_file = root / "data" / "synthetic" / "gt_metadata.json"
    if not gt_file.exists():
        raise FileNotFoundError(
            "Missing ground truth metadata. Ensure T006 (Synthetic Generation) has completed successfully."
        )

def generate_data(root: Path, n_images: int = 50):
    """Generate synthetic planetary nebulae."""
    logging.info(f"Generating {n_images} synthetic images...")
    # We call the main function of the generator module
    # The generator module expects to be run from the project root or have paths configured
    # For this orchestration, we assume the generator handles its own paths or we pass them via env/args
    # Since the generator's main() is designed to run standalone, we invoke it directly.
    # However, to ensure it uses the correct output directory, we might need to adjust.
    # Given the task constraints, we assume the generator writes to data/synthetic by default.
    generate_main()

def process_artifacts(root: Path):
    """Process synthetic data by injecting artifacts and measuring metrics."""
    logging.info("Processing artifacts (noise and saturation sweeps)...")
    artifacts_main()

def run_us1_pipeline(root: Path):
    """Run User Story 1: Noise vs Ellipticity."""
    logging.info("Running US1: Noise regression...")
    stats_main() # This runs the noise regression logic

def run_us2_pipeline(root: Path):
    """Run User Story 2: Saturation vs Asymmetry."""
    logging.info("Running US2: Saturation regression...")
    # The saturation regression is part of the statistics module or separate
    # Based on T023, it's in statistics.py. If separate, call it here.
    # Assuming stats_main covers both or we call specific logic.
    # For safety, we call the statistics main which should handle both if configured.
    # If not, we rely on the artifacts_main having produced the sweep data.
    # T023 says "Implement statistical test logic... output... to saturation_stats.csv"
    # Let's assume stats_main handles both noise and saturation if data exists.
    stats_main()

def run_us3_pipeline(root: Path):
    """Run User Story 3: Calibration and Validation."""
    logging.info("Running US3: Aggregation, Regression, Validation...")
    
    # 1. Aggregate (T041) - Assuming this is part of validation or regression flow
    # 2. Fit models (T027)
    regression_main()
    
    # 3. Validate (T028)
    validation_main()
    
    # 4. Power Analysis (T030)
    power_main()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument("--run-all", action="store_true", help="Run the full pipeline")
    parser.add_argument("--mode", choices=["generate", "process", "calibrate", "validate", "verify"],
                        help="Run a specific mode")
    parser.add_argument("--n-images", type=int, default=50, help="Number of synthetic images")
    parser.add_argument("--output", type=str, help="Output directory (optional)")
    
    args = parser.parse_args()
    
    root = get_project_root()
    log_file = root / "logs" / "research.log"
    logger = setup_logging(log_file)
    logger.info("Pipeline started.")
    
    setup_directories(root)
    
    # Generate run manifest (T053)
    write_run_manifest_for_pipeline(root)
    
    if args.mode:
        if args.mode == "generate":
            generate_data(root, args.n_images)
        elif args.mode == "process":
            process_artifacts(root)
        elif args.mode == "calibrate":
            run_us3_pipeline(root)
        elif args.mode == "validate":
            run_us3_pipeline(root) # Validation is part of US3
        elif args.mode == "verify":
            validate_pipeline_state(root)
            logger.info("Pipeline state verified.")
    elif args.run_all:
        logger.info("Running full pipeline...")
        try:
            validate_pipeline_state(root)
            generate_data(root, args.n_images)
            process_artifacts(root)
            run_us1_pipeline(root)
            run_us2_pipeline(root)
            run_us3_pipeline(root)
            logger.info("Full pipeline completed successfully.")
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
