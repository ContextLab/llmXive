import argparse
import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import yaml
import torch
import pandas as pd

from utils.config import load_config, get_project_root, get_artifacts_dir, get_data_dir
from utils.logging import setup_logging, get_logger, info, error, warning, critical
from utils.monitor import get_ram_usage_gb, check_ram_threshold, get_resource_snapshot
from training.train_loop import train_loop
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model
from training.callbacks import create_logging_callback

# RAM Threshold for T038b
RAM_THRESHOLD_GB = 6.5

def load_config_yaml(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = str(project_root / "code" / "config.yaml")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_single_model_training(
    model_type: str,
    config: Dict[str, Any],
    seed_id: int,
    logger: Any
) -> Dict[str, Any]:
    """
    Run training for a single model instance with monitoring.
    
    This function implements T038b: It monitors RAM usage during training
    and halts if the threshold (6.5 GB) is exceeded.
    """
    info(f"Starting training for {model_type} with seed {seed_id}")
    
    # Initialize model based on type
    if model_type == "AR":
        model = create_autoregressive_model()
    elif model_type == "Diffusion":
        model = create_diffusion_model()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Create logging callback
    callback = create_logging_callback(seed_id, model_type)
    
    # Training loop with RAM monitoring
    try:
        logs = train_loop(
            model=model,
            model_type=model_type,
            seed_id=seed_id,
            config=config,
            callbacks=[callback],
            ram_threshold=RAM_THRESHOLD_GB,
            logger=logger
        )
        
        # Final RAM check
        final_ram = get_ram_usage_gb()
        if final_ram > RAM_THRESHOLD_GB:
            warning(f"Final RAM usage ({final_ram:.2f} GB) exceeded threshold ({RAM_THRESHOLD_GB} GB)")
        
        return {
            "status": "success",
            "model_type": model_type,
            "seed_id": seed_id,
            "logs": logs,
            "peak_ram_gb": callback.get_peak_ram()
        }
        
    except MemoryError as e:
        error(f"OOM Error during {model_type} training (seed {seed_id}): {e}")
        return {
            "status": "oom",
            "model_type": model_type,
            "seed_id": seed_id,
            "error": str(e)
        }
    except Exception as e:
        error(f"Unexpected error during {model_type} training (seed {seed_id}): {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "model_type": model_type,
            "seed_id": seed_id,
            "error": str(e)
        }

def save_logs_to_csv(logs: List[Dict[str, Any]], output_path: str) -> None:
    """Save training logs to CSV."""
    if not logs:
        warning("No logs to save")
        return
    
    # Flatten logs for CSV
    flat_logs = []
    for log in logs:
        flat_log = {
            'epoch': log.get('epoch', 0),
            'model_type': log.get('model_type', ''),
            'seed_id': log.get('seed_id', 0),
            'train_loss': log.get('train_loss', 0.0),
            'val_loss': log.get('val_loss', 0.0),
            'gap': log.get('gap', 0.0),
            'time': log.get('time', 0.0),
            'ram_gb': log.get('ram_gb', 0.0),
            'seed_id': log.get('seed_id', 0)
        }
        flat_logs.append(flat_log)
    
    df = pd.DataFrame(flat_logs)
    df.to_csv(output_path, index=False)
    info(f"Logs saved to {output_path}")

def main():
    """
    Main entry point for running the experiment.
    
    Implements T038b: Verifies peak RAM < 6.5 GB via monitoring.
    """
    parser = argparse.ArgumentParser(description="Run LLMXive Training Experiment")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5], 
                      help="List of seed IDs to run")
    parser.add_argument("--models", type=str, nargs="+", default=["AR", "Diffusion"],
                      help="List of model types to train")
    args = parser.parse_args()
    
    # Setup logging
    log_dir = get_project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_file=log_dir / "experiment.log")
    
    info("=" * 60)
    info("Starting LLMXive Training Experiment")
    info(f"RAM Threshold: {RAM_THRESHOLD_GB} GB (T038b)")
    info("=" * 60)
    
    # Load configuration
    config = load_config_yaml(args.config)
    
    # Check scope approval
    if not config.get("approved", False):
        critical("Scope change not approved. Halting.")
        sys.exit(1)
    
    # Run experiments
    all_results = []
    all_logs = []
    
    for model_type in args.models:
        for seed_id in args.seeds:
            info(f"--- Running {model_type} seed {seed_id} ---")
            result = run_single_model_training(model_type, config, seed_id, logger)
            all_results.append(result)
            
            if result["status"] == "success":
                all_logs.extend(result["logs"])
            else:
                warning(f"Training failed for {model_type} seed {seed_id}: {result.get('error', 'Unknown')}")
    
    # Save results
    artifacts_dir = get_artifacts_dir()
    results_path = artifacts_dir / "experiment_results.json"
    logs_path = artifacts_dir / "training_logs.csv"
    
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    save_logs_to_csv(all_logs, str(logs_path))
    
    # Summary
    info("=" * 60)
    info("Experiment Summary")
    info("=" * 60)
    for res in all_results:
        status = res["status"]
        peak_ram = res.get("peak_ram_gb", "N/A")
        info(f"{res['model_type']} (seed {res['seed_id']}): {status} | Peak RAM: {peak_ram} GB")
    
    # Verify T038b: Check if any run exceeded threshold
    exceeded = [r for r in all_results if r.get("peak_ram_gb", 0) > RAM_THRESHOLD_GB]
    if exceeded:
        critical(f"WARNING: {len(exceeded)} runs exceeded RAM threshold of {RAM_THRESHOLD_GB} GB!")
        for r in exceeded:
            critical(f"  - {r['model_type']} (seed {r['seed_id']}): {r['peak_ram_gb']:.2f} GB")
    else:
        info(f"SUCCESS: All runs stayed below RAM threshold of {RAM_THRESHOLD_GB} GB")
    
    info("Experiment completed.")

if __name__ == "__main__":
    main()