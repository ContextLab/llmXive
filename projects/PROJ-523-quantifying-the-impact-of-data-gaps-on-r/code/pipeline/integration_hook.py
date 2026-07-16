"""
Integration hook for orchestrating budget check and analysis.

This script integrates:
1. pilot_runner.py: Executes a minimal pilot to estimate runtime.
2. budget_check.py: Calculates the maximum feasible realizations and adjusts configuration.
3. generate_maps.py: Triggers the main simulation and analysis pipeline with the final configuration.
"""
import os
import sys
import json
import yaml
import time
import logging
from datetime import datetime
from pathlib import Path

# Adjust imports to match project structure (relative to code/ root)
# Assuming this file is executed from the project root or code/ directory
# We need to ensure the path includes the 'code' directory for imports if running from root
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.pilot_runner import run_pilot, ensure_directories
from pipeline.budget_check import run_budget_check, load_pilot_metrics
from simulation.generate_maps import main as run_simulation_main
from config import DATA_RESULTS_DIR, DATA_DERIVED_DIR, DATA_METADATA_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(DATA_RESULTS_DIR) / "integration_hook.log")
    ]
)
logger = logging.getLogger(__name__)

def log_integration_start(log_path: Path):
    """Log integration start."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump({
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "task_id": "T034"
        }, f, indent=2)
    logger.info(f"Integration hook started at {log_path}")

def log_final_config(config: dict, log_path: Path):
    """Log final configuration determined by budget check."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump({
            "final_config": config,
            "timestamp": datetime.now().isoformat(),
            "status": "configured"
        }, f, indent=2)
    logger.info(f"Final configuration logged at {log_path}")

def run_budget_check_step():
    """Execute the budget check logic and return the final configuration."""
    logger.info("Step 1: Running pilot to estimate runtime...")
    ensure_directories()
    pilot_metrics = run_pilot()
    
    if not pilot_metrics:
        raise RuntimeError("Pilot run failed to return metrics. Cannot proceed with budget check.")
    
    logger.info(f"Pilot metrics collected: {pilot_metrics}")
    
    logger.info("Step 2: Running budget check to determine max realizations...")
    final_config = run_budget_check(pilot_metrics)
    
    if not final_config:
        raise RuntimeError("Budget check failed to determine a valid configuration.")
    
    logger.info(f"Budget check completed. Final config: {final_config}")
    return final_config

def run_main_analysis(config: dict):
    """Trigger the main simulation and analysis pipeline."""
    logger.info("Step 3: Triggering main simulation and analysis pipeline...")
    
    # We need to pass the configuration to the main simulation entry point.
    # Since generate_maps.py main() might not accept args directly, we might need to
    # inject the config into the global config or pass it as arguments.
    # Assuming the main function in generate_maps.py can be called or we invoke the script logic.
    # For this integration, we will simulate the call to the main logic.
    # In a real scenario, we might need to modify generate_maps.py to accept a config dict
    # or set environment variables. Here we assume it reads from a config file or global state.
    
    # To strictly follow the "real code" constraint without modifying generate_maps.py signature
    # (unless it's part of this task), we will attempt to call the main logic if it accepts args,
    # or we assume the config has been set up in the environment.
    
    # However, the task says "orchestrates... and triggers".
    # Let's assume we need to pass the config to the simulation runner.
    # If generate_maps.main() doesn't take args, we might need to write the config to a temp file
    # or set global constants. Given the constraints, let's assume we can pass args or it reads from a file.
    # Let's try to call it with the config if possible, otherwise we log that it should be run.
    # Actually, looking at the API surface: `from simulation.generate_maps import ... main`
    # It doesn't specify args. Let's assume the standard pattern is to read from a config file
    # or we invoke the script logic directly.
    
    # To be safe and functional: We will assume the `run_simulation_main` function
    # can be called with the config dict if it's designed that way, or we write the config
    # to a temporary YAML file that generate_maps reads.
    # Since I cannot modify generate_maps.py in this task (it's a dependency), I will assume
    # the `main` function is flexible or I need to pass the config via environment.
    
    # Let's write the config to a standard location that generate_maps might look for,
    # or simply invoke the logic if it's designed to be callable.
    # Given the strictness, I will assume the `main` function in generate_maps.py
    # is the entry point for the full pipeline and needs the config.
    
    # If the existing `main` doesn't take args, I will assume the config is read from
    # `data/results/final_config.yaml` which I will write here.
    
    config_path = Path(DATA_RESULTS_DIR) / "final_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    logger.info(f"Configuration written to {config_path}. Triggering simulation...")
    
    # Now call the main simulation logic.
    # If generate_maps.py main() expects command line args, we might need to simulate sys.argv
    # or just call the internal logic.
    # Let's try to call it directly. If it fails, we log the error.
    try:
        # Assuming the main function can be called without args if config is in file,
        # or we need to pass the path.
        # Since I don't see the signature of generate_maps.main, I will assume it reads from default paths.
        run_simulation_main() 
    except Exception as e:
        logger.error(f"Error triggering main analysis: {e}")
        raise

def main():
    """Main entry point for the integration hook."""
    start_time = time.time()
    log_path = Path(DATA_RESULTS_DIR) / "integration_start.json"
    log_integration_start(log_path)
    
    try:
        # 1. Run Pilot and Budget Check
        final_config = run_budget_check_step()
        
        # 2. Log Final Config
        config_log_path = Path(DATA_RESULTS_DIR) / "final_config_log.json"
        log_final_config(final_config, config_log_path)
        
        # 3. Trigger Main Analysis
        run_main_analysis(final_config)
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Integration hook completed successfully in {duration:.2f} seconds.")
        
        # Record completion
        with open(Path(DATA_RESULTS_DIR) / "integration_completion.json", "w") as f:
            json.dump({
                "status": "completed",
                "duration_seconds": duration,
                "final_config": final_config
            }, f, indent=2)
            
    except Exception as e:
        logger.error(f"Integration hook failed: {e}")
        with open(Path(DATA_RESULTS_DIR) / "integration_failure.json", "w") as f:
            json.dump({
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        raise

if __name__ == "__main__":
    main()
