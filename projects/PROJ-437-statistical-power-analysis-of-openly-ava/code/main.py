import argparse
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Import existing modules from the project API surface
from utils.execution_order_validator import ExecutionOrderValidator, TaskOrderError
from utils.timer import start_run, end_run, log_split, save_timing_report, save_timing_breakdown
from utils.seed_manager import set_global_seed, get_seed
from utils.memory_monitor import monitor_and_ensure_memory
from download.openneuro_fetcher import main as fetch_main
from download.data_validator import main as validate_main
from preprocess.roi_extractor import main as roi_main
from preprocess.temporal_smoothing import main as smooth_main
from simulation.noise_estimator import main as noise_main
from simulation.synthetic_data_gen import main as synth_main
from analysis.glm_fitter import main as glm_main
from analysis.split_half_validator import main as split_half_main
from analysis.power_curve_generator import main as power_main
from analysis.temporal_sensitivity_orchestrator import main as sensitivity_main
from utils.convergence_monitor import main as convergence_monitor_main
from analysis.result_finalizer import main as finalizer_main
from analysis.alpha_sweep_analyzer import main as alpha_sweep_main
from download.paradigm_loader import main as paradigm_loader_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/paper/pipeline_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Load configuration from a YAML or JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.endswith('.json'):
            return json.load(f)
        else:
            # Simple YAML parser for basic key-value pairs
            config = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip().strip('"\'')
            return config

def run_download(config: dict):
    """Run the data download phase."""
    logger.info("Starting data download phase...")
    log_split("download_start")
    
    try:
        # Set seed from config
        if 'random_seed' in config:
            set_global_seed(int(config['random_seed']))
        
        # Run fetcher
        sys.argv = ['openneuro_fetcher'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        fetch_main()
        
        log_split("download_end")
        logger.info("Data download phase completed successfully.")
    except Exception as e:
        logger.error(f"Data download failed: {str(e)}")
        raise

def run_preprocess(config: dict):
    """Run the preprocessing phase."""
    logger.info("Starting preprocessing phase...")
    log_split("preprocess_start")
    
    try:
        # ROI extraction
        sys.argv = ['roi_extractor'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        roi_main()
        
        # Temporal smoothing
        sys.argv = ['temporal_smoothing'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        smooth_main()
        
        log_split("preprocess_end")
        logger.info("Preprocessing phase completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise

def run_noise_estimation(config: dict):
    """Run noise estimation."""
    logger.info("Starting noise estimation...")
    log_split("noise_estimation_start")
    
    try:
        sys.argv = ['noise_estimator'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        noise_main()
        
        log_split("noise_estimation_end")
        logger.info("Noise estimation completed successfully.")
    except Exception as e:
        logger.error(f"Noise estimation failed: {str(e)}")
        raise

def run_synthetic_generation(config: dict):
    """Run synthetic data generation."""
    logger.info("Starting synthetic data generation...")
    log_split("synthetic_generation_start")
    
    try:
        sys.argv = ['synthetic_data_gen'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        synth_main()
        
        log_split("synthetic_generation_end")
        logger.info("Synthetic data generation completed successfully.")
    except Exception as e:
        logger.error(f"Synthetic data generation failed: {str(e)}")
        raise

def run_power_analysis(config: dict):
    """Run power analysis including split-half validation and power curve generation."""
    logger.info("Starting power analysis...")
    log_split("power_analysis_start")
    
    try:
        # Run GLM fitting (this also generates convergence_log.json)
        sys.argv = ['glm_fitter'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        glm_main()
        
        # Run split-half validation (this generates split_half_results.json)
        sys.argv = ['split_half_validator'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        split_half_main()
        
        # Run power curve generation
        sys.argv = ['power_curve_generator'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        power_main()
        
        # Run alpha sweep analysis
        sys.argv = ['alpha_sweep_analyzer'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        alpha_sweep_main()
        
        log_split("power_analysis_end")
        logger.info("Power analysis completed successfully.")
    except Exception as e:
        logger.error(f"Power analysis failed: {str(e)}")
        raise

def run_sensitivity_analysis(config: dict):
    """Run sensitivity analysis across smoothing kernels."""
    logger.info("Starting sensitivity analysis...")
    log_split("sensitivity_analysis_start")
    
    try:
        sys.argv = ['temporal_sensitivity_orchestrator'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        sensitivity_main()
        
        log_split("sensitivity_analysis_end")
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {str(e)}")
        raise

def run_convergence_monitoring(config: dict):
    """Run convergence monitoring and generate report."""
    logger.info("Starting convergence monitoring...")
    log_split("convergence_monitoring_start")
    
    try:
        sys.argv = ['convergence_monitor'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        convergence_monitor_main()
        
        log_split("convergence_monitoring_end")
        logger.info("Convergence monitoring completed successfully.")
    except Exception as e:
        logger.error(f"Convergence monitoring failed: {str(e)}")
        raise

def run_finalization(config: dict):
    """Run result finalization to generate the final report."""
    logger.info("Starting result finalization...")
    log_split("finalization_start")
    
    try:
        sys.argv = ['result_finalizer'] + [f"--config={config.get('config_file', 'config.yaml')}"]
        finalizer_main()
        
        log_split("finalization_end")
        logger.info("Result finalization completed successfully.")
    except Exception as e:
        logger.error(f"Result finalization failed: {str(e)}")
        raise

def run_validation(config: dict):
    """Run final validation step to check for all required output files."""
    logger.info("Starting final validation...")
    log_split("validation_start")
    
    required_files = [
        "data/aggregated/power_curves.json",
        "results/paper/sensitivity_report.md",
        "results/paper/timing_breakdown.csv",
        "results/paper/convergence_report.md",
        "data/aggregated/split_half_results.json",
        "data/aggregated/convergence_log.json",
        "results/paper/final_analysis_report.md",
        "results/paper/success_criteria_status.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.warning(f"Missing required file: {file_path}")
        else:
            logger.info(f"Found required file: {file_path}")
    
    if missing_files:
        logger.error(f"Validation failed. Missing {len(missing_files)} required files:")
        for f in missing_files:
            logger.error(f"  - {f}")
        log_split("validation_end")
        raise FileNotFoundError(f"Missing required output files: {', '.join(missing_files)}")
    
    log_split("validation_end")
    logger.info("Final validation completed successfully. All required files present.")

def run_pipeline(config: dict):
    """Run the full pipeline."""
    logger.info("Starting full pipeline execution...")
    
    # Pre-flight check
    validator = ExecutionOrderValidator()
    try:
        validator.validate()
    except TaskOrderError as e:
        logger.error(f"Pre-flight validation failed: {str(e)}")
        sys.exit(1)
    
    # Run phases
    run_download(config)
    run_preprocess(config)
    run_noise_estimation(config)
    run_synthetic_generation(config)
    run_power_analysis(config)
    run_sensitivity_analysis(config)
    run_convergence_monitoring(config)
    run_finalization(config)
    
    # Final validation
    run_validation(config)
    
    logger.info("Full pipeline execution completed successfully.")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Statistical Power Analysis Pipeline')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--action', type=str, choices=['download', 'preprocess', 'noise', 'synthetic', 'analyze', 'sensitivity', 'convergence', 'report', 'validate', 'pipeline'], 
                      default='pipeline', help='Action to perform')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Override seed if provided
        if args.seed:
            config['random_seed'] = str(args.seed)
            set_global_seed(args.seed)
        
        # Execute requested action
        if args.action == 'download':
            run_download(config)
        elif args.action == 'preprocess':
            run_preprocess(config)
        elif args.action == 'noise':
            run_noise_estimation(config)
        elif args.action == 'synthetic':
            run_synthetic_generation(config)
        elif args.action == 'analyze':
            run_power_analysis(config)
        elif args.action == 'sensitivity':
            run_sensitivity_analysis(config)
        elif args.action == 'convergence':
            run_convergence_monitoring(config)
        elif args.action == 'report':
            run_finalization(config)
        elif args.action == 'validate':
            run_validation(config)
        elif args.action == 'pipeline':
            run_pipeline(config)
        
        logger.info(f"Action '{args.action}' completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()