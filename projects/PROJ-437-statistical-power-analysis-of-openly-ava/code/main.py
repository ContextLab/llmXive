"""
Main entry point for the Statistical Power Analysis pipeline.

This module orchestrates the download, preprocessing, noise estimation,
power analysis, sensitivity analysis, convergence monitoring, and finalization
of the research pipeline.
"""

import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("results/paper/pipeline_run.log")
    ]
)
logger = logging.getLogger(__name__)

from utils.seed_manager import set_global_seed, get_seed
from utils.timer import start_run, end_run, log_split, save_timing_report
from download.openneuro_fetcher import main as fetch_main
from download.data_validator import main as validate_main
from preprocess.roi_extractor import main as roi_extract_main
from preprocess.temporal_smoothing import main as temporal_smooth_main
from simulation.noise_estimator import main as noise_est_main
from analysis.glm_fitter import main as glm_fit_main
from analysis.split_half_validator import main as split_half_main
from analysis.power_curve_generator import main as power_curve_main
from analysis.temporal_sensitivity_orchestrator import main as sensitivity_main
from utils.convergence_monitor import main as convergence_monitor_main
from analysis.result_finalizer import main as finalizer_main
from utils.timer import save_timing_breakdown


def load_config(config_path: str) -> dict:
    """Load configuration from a YAML or JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        if config_path.endswith('.json'):
            return json.load(f)
        elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
            # Simple YAML parser for basic key-value pairs without external deps
            # In a full implementation, use PyYAML
            config = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        config[key.strip()] = value.strip().strip('"').strip("'")
            return config
    return {}


def create_config():
    """Create a default configuration file."""
    default_config = {
        "seed": 42,
        "datasets": ["ds000030"],
        "paradigm": "Motor",
        "sample_sizes": [10, 20, 30, 40, 50],
        "kernels": ["4s", "8s"],
        "num_iterations": 50,
        "alpha_levels": [0.01, 0.05, 0.1],
        "output_dir": "results/paper"
    }
    with open("config.yaml", 'w') as f:
        for k, v in default_config.items():
            if isinstance(v, list):
                f.write(f"{k}:\n")
                for item in v:
                    f.write(f"  - {item}\n")
            else:
                f.write(f"{k}: {v}\n")
    logger.info("Default config.yaml created.")


def run_download(config: dict):
    """Run the data download step."""
    logger.info("Starting data download...")
    start_run("download")
    # Pass config via environment or args if needed, simplified here
    os.environ['CONFIG_PATH'] = 'config.yaml'
    try:
        fetch_main()
        log_split("download", "fetch_complete")
        logger.info("Data download completed.")
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise
    finally:
        end_run("download")


def run_preprocess(config: dict):
    """Run the preprocessing steps (ROI extraction and smoothing)."""
    logger.info("Starting preprocessing...")
    start_run("preprocess")
    try:
        roi_extract_main()
        log_split("preprocess", "roi_extract_complete")
        temporal_smooth_main()
        log_split("preprocess", "smoothing_complete")
        logger.info("Preprocessing completed.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise
    finally:
        end_run("preprocess")


def run_noise_estimation(config: dict):
    """Run noise estimation."""
    logger.info("Starting noise estimation...")
    start_run("noise_estimation")
    try:
        noise_est_main()
        log_split("noise_estimation", "noise_estimated")
        logger.info("Noise estimation completed.")
    except Exception as e:
        logger.error(f"Noise estimation failed: {e}")
        raise
    finally:
        end_run("noise_estimation")


def run_power_analysis(config: dict):
    """Run the GLM fitting, split-half validation, and power curve generation."""
    logger.info("Starting power analysis...")
    start_run("power_analysis")
    try:
        glm_fit_main()
        log_split("power_analysis", "glm_fit_complete")
        split_half_main()
        log_split("power_analysis", "split_half_complete")
        power_curve_main()
        log_split("power_analysis", "power_curves_complete")
        logger.info("Power analysis completed.")
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise
    finally:
        end_run("power_analysis")


def run_sensitivity_analysis(config: dict):
    """Run temporal sensitivity analysis."""
    logger.info("Starting sensitivity analysis...")
    start_run("sensitivity_analysis")
    try:
        sensitivity_main()
        log_split("sensitivity_analysis", "sensitivity_complete")
        logger.info("Sensitivity analysis completed.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise
    finally:
        end_run("sensitivity_analysis")


def run_convergence_monitoring(config: dict):
    """Run convergence monitoring."""
    logger.info("Starting convergence monitoring...")
    start_run("convergence_monitoring")
    try:
        convergence_monitor_main()
        log_split("convergence_monitoring", "convergence_reported")
        logger.info("Convergence monitoring completed.")
    except Exception as e:
        logger.error(f"Convergence monitoring failed: {e}")
        raise
    finally:
        end_run("convergence_monitoring")


def run_finalization(config: dict):
    """Run result finalization."""
    logger.info("Starting result finalization...")
    start_run("finalization")
    try:
        finalizer_main()
        log_split("finalization", "report_generated")
        logger.info("Result finalization completed.")
    except Exception as e:
        logger.error(f"Result finalization failed: {e}")
        raise
    finally:
        end_run("finalization")


def run_validation(config: dict):
    """Run final validation of all output files."""
    logger.info("Running final validation...")
    required_files = [
        "data/aggregated/power_curves.json",
        "data/aggregated/sensitivity_report.md",
        "results/paper/timing_report.md",
        "results/paper/timing_breakdown.csv",
        "results/paper/convergence_report.md",
        "data/aggregated/split_half_results.json",
        "data/aggregated/convergence_log.json",
        "results/paper/final_analysis_report.md"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.warning(f"Missing required output: {file_path}")
        else:
            logger.info(f"Found required output: {file_path}")

    if missing_files:
        logger.error(f"Validation failed. Missing {len(missing_files)} files: {missing_files}")
        sys.exit(1)
    else:
        logger.info("All required output files present. Validation passed.")
        sys.exit(0)


def run_pipeline(config: dict):
    """Run the full pipeline."""
    logger.info("Starting full pipeline execution...")
    start_run("full_pipeline")
    try:
        run_download(config)
        run_preprocess(config)
        run_noise_estimation(config)
        run_power_analysis(config)
        run_sensitivity_analysis(config)
        run_convergence_monitoring(config)
        run_finalization(config)
        run_validation(config)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)
    finally:
        end_run("full_pipeline")


def main():
    parser = argparse.ArgumentParser(description="Statistical Power Analysis Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--action", type=str, choices=[
        "download", "preprocess", "estimate_noise", "analyze", "sensitivity", "convergence", "report", "validate", "all"
    ], default="all", help="Action to perform")
    parser.add_argument("--create-config", action="store_true", help="Create default config file")

    args = parser.parse_args()

    if args.create_config:
        create_config()
        return

    if not os.path.exists(args.config):
        logger.error(f"Config file {args.config} not found. Use --create-config to generate one.")
        sys.exit(1)

    config = load_config(args.config)
    set_global_seed(int(config.get("seed", 42)))

    try:
        if args.action == "all":
            run_pipeline(config)
        elif args.action == "download":
            run_download(config)
        elif args.action == "preprocess":
            run_preprocess(config)
        elif args.action == "estimate_noise":
            run_noise_estimation(config)
        elif args.action == "analyze":
            run_power_analysis(config)
        elif args.action == "sensitivity":
            run_sensitivity_analysis(config)
        elif args.action == "convergence":
            run_convergence_monitoring(config)
        elif args.action == "report":
            run_finalization(config)
        elif args.action == "validate":
            run_validation(config)
        else:
            logger.error(f"Unknown action: {args.action}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()