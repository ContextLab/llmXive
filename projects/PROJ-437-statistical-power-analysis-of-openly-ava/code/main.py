"""
Main entry point for the Statistical Power Analysis pipeline.
Orchestrates download, preprocess, noise estimation, power analysis, sensitivity analysis, and finalization.
"""
import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.seed_manager import set_global_seed, get_seed
from utils.timer import start_run, end_run, log_split, save_timing_report, save_timing_breakdown
from utils.memory_monitor import monitor_and_ensure_memory
from download.openneuro_fetcher import main as fetch_main
from download.data_validator import main as validate_main
from preprocess.roi_extractor import main as roi_main
from preprocess.temporal_smoothing import main as smooth_main
from simulation.noise_estimator import main as noise_main
from analysis.power_curve_generator import main as power_main
from analysis.temporal_sensitivity_orchestrator import main as sensitivity_main
from analysis.result_finalizer import main as finalizer_main
from analysis.convergence_monitor import main as convergence_monitor_main
from analysis.alpha_sweep_analyzer import main as alpha_sweep_main
from utils.bootstrap_aggregator import main as bootstrap_agg_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "results" / "paper" / "pipeline_run.log")
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Load configuration from a YAML or JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Simple YAML/JSON loader (assuming json for robustness or simple yaml)
    # In a real scenario, use pyyaml
    with open(path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            # Fallback for simple yaml if pyyaml not installed, otherwise import yaml
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                logger.warning("PyYAML not found. Attempting simple key-value parsing for YAML.")
                config = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            config[k.strip()] = v.strip()
                return config
        else:
            return json.load(f)

def create_config(output_path: str) -> None:
    """Create a default configuration file."""
    default_config = {
        "seed": 42,
        "dataset_ids": ["ds000030"],
        "paradigm": "Motor",
        "sample_sizes": [10, 20, 30, 40, 50],
        "kernels": ["4s", "8s"],
        "alpha_values": [0.01, 0.05, 0.1],
        "bootstrap_iterations": 10,
        "memory_threshold_gb": 6.0,
        "output_dir": "data/aggregated"
    }
    with open(output_path, 'w') as f:
        json.dump(default_config, f, indent=4)
    logger.info(f"Created default config at {output_path}")

def run_download(config: dict) -> None:
    """Run the download step."""
    logger.info("Starting download phase...")
    start_run("download")
    # Pass config to fetcher
    # Assuming fetcher expects args or reads from a standard location
    # For now, we simulate the call structure
    # In a real implementation, we would parse args or pass dict directly
    os.environ['PIPELINE_CONFIG'] = json.dumps(config)
    fetch_main()
    end_run("download")

def run_preprocess(config: dict) -> None:
    """Run the preprocessing steps (ROI extraction, smoothing)."""
    logger.info("Starting preprocessing phase...")
    start_run("preprocess")
    
    # ROI Extraction
    log_split("roi_extraction")
    roi_main()
    
    # Temporal Smoothing
    log_split("temporal_smoothing")
    smooth_main()
    
    end_run("preprocess")

def run_noise_estimation(config: dict) -> None:
    """Estimate noise characteristics."""
    logger.info("Starting noise estimation...")
    start_run("noise_estimation")
    noise_main()
    end_run("noise_estimation")

def run_power_analysis(config: dict) -> None:
    """Run the power curve generation."""
    logger.info("Starting power analysis...")
    start_run("power_analysis")
    
    # Bootstrap aggregation
    log_split("bootstrap_aggregation")
    bootstrap_agg_main()
    
    # Alpha sweep
    log_split("alpha_sweep")
    alpha_sweep_main()
    
    # Power curve generation
    log_split("power_curve_gen")
    power_main()
    
    end_run("power_analysis")

def run_sensitivity_analysis(config: dict) -> None:
    """Run sensitivity analysis across kernels."""
    logger.info("Starting sensitivity analysis...")
    start_run("sensitivity_analysis")
    sensitivity_main()
    end_run("sensitivity_analysis")

def run_convergence_monitoring(config: dict) -> None:
    """Monitor GLM convergence."""
    logger.info("Running convergence monitoring...")
    start_run("convergence_monitoring")
    convergence_monitor_main()
    end_run("convergence_monitoring")

def run_finalization(config: dict) -> None:
    """Finalize results and generate reports."""
    logger.info("Starting finalization...")
    start_run("finalization")
    finalizer_main()
    end_run("finalization")

def run_validation(config: dict) -> None:
    """Run validation checks."""
    logger.info("Running validation...")
    start_run("validation")
    # Validation logic would go here, checking output files
    # For now, just a placeholder
    end_run("validation")

def run_pipeline(config: dict) -> None:
    """Run the full pipeline."""
    logger.info("Starting full pipeline execution...")
    set_global_seed(config.get('seed', 42))
    
    run_download(config)
    run_preprocess(config)
    run_noise_estimation(config)
    run_power_analysis(config)
    run_sensitivity_analysis(config)
    run_convergence_monitoring(config)
    run_finalization(config)
    
    logger.info("Pipeline execution completed.")

def main():
    parser = argparse.ArgumentParser(description="Statistical Power Analysis Pipeline")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--action', type=str, choices=['download', 'preprocess', 'estimate_noise', 'generate_synthetic', 'analyze', 'report', 'validate', 'pipeline'], default='pipeline', help='Action to perform')
    parser.add_argument('--create-config', type=str, help='Create a default config file at the specified path')
    
    args = parser.parse_args()

    if args.create_config:
        create_config(args.create_config)
        return

    if not Path(args.config).exists():
        logger.error(f"Config file {args.config} not found.")
        sys.exit(1)

    config = load_config(args.config)
    
    # Ensure output directories exist
    (PROJECT_ROOT / "data" / "aggregated").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results" / "paper").mkdir(parents=True, exist_ok=True)

    try:
        if args.action == 'download':
            run_download(config)
        elif args.action == 'preprocess':
            run_preprocess(config)
        elif args.action == 'estimate_noise':
            run_noise_estimation(config)
        elif args.action == 'analyze':
            run_power_analysis(config)
            run_sensitivity_analysis(config)
        elif args.action == 'report':
            run_finalization(config)
        elif args.action == 'validate':
            run_validation(config)
        elif args.action == 'pipeline':
            run_pipeline(config)
        elif args.action == 'generate_synthetic':
            logger.warning("Synthetic generation is disabled. Use real data.")
            sys.exit(1)
        else:
            logger.error(f"Unknown action: {args.action}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
