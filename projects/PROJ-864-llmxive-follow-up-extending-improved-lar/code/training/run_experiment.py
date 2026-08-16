import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

# Local imports matching API surface
from utils.config import load_config, get_project_root, get_artifacts_dir, get_data_dir, get_processed_dir
from utils.monitor import get_ram_usage_gb, check_ram_threshold, get_resource_snapshot, resource_monitor
from utils.logging import setup_logging, get_logger, info, error, warning, critical
from training.train_loop import train_loop
from training.callbacks import create_logging_callback

def load_config_yaml(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "code" / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_single_model_training(
    model_type: str,
    config: Dict[str, Any],
    seed_id: int,
    logger: Any
) -> Dict[str, Any]:
    """
    Run training for a single model with a specific seed.
    
    Args:
        model_type: Either 'autoregressive' or 'diffusion'
        config: Configuration dictionary
        seed_id: Random seed identifier
        logger: Logger instance
    
    Returns:
        Dictionary containing training results and metrics
    """
    # Set random seed
    import torch
    import random
    random.seed(seed_id)
    torch.manual_seed(seed_id)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed_id)
    
    info(logger, f"Starting training for {model_type} model with seed {seed_id}")
    
    # Initialize logging callback
    log_callback = create_logging_callback(
        model_type=model_type,
        seed_id=seed_id,
        artifacts_dir=get_artifacts_dir(),
        logger=logger
    )
    
    # Track peak RAM during training
    peak_ram_gb = 0.0
    
    def ram_monitor_callback():
        nonlocal peak_ram_gb
        current_ram = get_ram_usage_gb()
        if current_ram > peak_ram_gb:
            peak_ram_gb = current_ram
        return current_ram
    
    # Run training loop with RAM monitoring
    try:
        results = train_loop(
            model_type=model_type,
            config=config,
            seed_id=seed_id,
            callbacks=[log_callback, ram_monitor_callback],
            logger=logger
        )
    except Exception as e:
        error(logger, f"Training failed for {model_type} with seed {seed_id}: {str(e)}")
        raise
    
    # Verify peak RAM constraint
    max_ram_gb = config.get('model_params', {}).get('max_ram_gb', 6.5)
    if peak_ram_gb > max_ram_gb:
        warning(logger, f"Peak RAM {peak_ram_gb:.2f} GB exceeded threshold {max_ram_gb} GB")
        # Log the violation but don't halt - this is a performance optimization check
        results['peak_ram_gb'] = peak_ram_gb
        results['ram_threshold_exceeded'] = True
    else:
        info(logger, f"Peak RAM {peak_ram_gb:.2f} GB within threshold {max_ram_gb} GB")
        results['peak_ram_gb'] = peak_ram_gb
        results['ram_threshold_exceeded'] = False
    
    info(logger, f"Completed training for {model_type} model with seed {seed_id}")
    return results

def save_logs_to_csv(all_logs: List[Dict[str, Any]], output_path: Path) -> None:
    """Save all training logs to a CSV file."""
    if not all_logs:
        warning(None, "No logs to save")
        return
    
    # Flatten nested dictionaries for CSV export
    flat_logs = []
    for log in all_logs:
        flat_log = {}
        for key, value in log.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_log[f"{key}_{sub_key}"] = sub_value
            else:
                flat_log[key] = value
        flat_logs.append(flat_log)
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        if flat_logs:
            writer = csv.DictWriter(f, fieldnames=flat_logs[0].keys())
            writer.writeheader()
            writer.writerows(flat_logs)
    
    info(None, f"Saved training logs to {output_path}")

def main():
    """Main entry point for running the experiment."""
    parser = argparse.ArgumentParser(description="Run comparative training experiment")
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456, 789, 1011],
                      help='List of seed IDs to run')
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging("run_experiment")
    
    try:
        # Load configuration
        config = load_config_yaml(args.config)
        
        # Check scope approval
        if not config.get('approved', False):
            error(logger, "Scope not approved. Halting execution.")
            sys.exit(1)
        
        regime = config.get('regime', '1M')
        info(logger, f"Running experiment for regime: {regime}")
        
        # Define model types to train
        model_types = ['autoregressive', 'diffusion']
        
        all_logs = []
        results_summary = []
        
        # Run training for each model type and seed
        for model_type in model_types:
            for seed_id in args.seeds:
                try:
                    result = run_single_model_training(
                        model_type=model_type,
                        config=config,
                        seed_id=seed_id,
                        logger=logger
                    )
                    all_logs.append(result)
                    results_summary.append({
                        'model_type': model_type,
                        'seed_id': seed_id,
                        'final_train_loss': result.get('final_train_loss'),
                        'final_val_loss': result.get('final_val_loss'),
                        'peak_ram_gb': result.get('peak_ram_gb'),
                        'ram_threshold_exceeded': result.get('ram_threshold_exceeded', False)
                    })
                except Exception as e:
                    error(logger, f"Failed to complete training for {model_type} seed {seed_id}: {str(e)}")
                    # Continue with other seeds/models
                    continue
        
        # Save logs to CSV
        artifacts_dir = get_artifacts_dir()
        logs_path = artifacts_dir / "training_logs.csv"
        save_logs_to_csv(all_logs, logs_path)
        
        # Save results summary
        summary_path = artifacts_dir / "experiment_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        info(logger, f"Experiment completed. Results saved to {summary_path}")
        
    except Exception as e:
        critical(logger, f"Experiment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()