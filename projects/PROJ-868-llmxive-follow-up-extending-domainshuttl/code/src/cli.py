import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the training function from the existing module
from src.models.training import train_autoencoder
from src.config.settings import get_config

# Define the dimensions to sweep as per FR-003
DIMENSIONS_TO_SWEEP: List[int] = [16, 32, 64, 128, 256]

def run_training_sweep(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    Executes the dimensionality sweep for Autoencoder training.
    
    Iterates over the predefined set of target dimensions [16, 32, 64, 128, 256],
    calling the training function for each. Aggregates logs into a single JSON file.
    
    Args:
        args: Optional argparse namespace. If None, uses default config.
        
    Returns:
        A dictionary containing the sweep results and log file path.
    """
    config = get_config()
    output_dir = Path(config["paths"]["processed"])
    models_dir = output_dir / "compressed_models"
    logs_dir = output_dir
    
    # Ensure output directories exist
    models_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    sweep_results: List[Dict[str, Any]] = []
    start_time = time.time()
    
    print(f"Starting dimensionality sweep for dimensions: {DIMENSIONS_TO_SWEEP}")
    
    for dim in DIMENSIONS_TO_SWEEP:
        print(f"--- Training Autoencoder for dimension {dim} ---")
        try:
            result = train_autoencoder(
                target_dimension=dim,
                models_dir=models_dir
            )
            
            # Log the result
            sweep_results.append({
                "target_dimension": dim,
                "status": "success",
                "checkpoint_path": result.get("checkpoint_path"),
                "final_loss": result.get("final_loss"),
                "training_time": result.get("training_time"),
                "timestamp": time.strftime("%Y-%m-%dT%H-%M-%S")
            })
            print(f"Completed dimension {dim}. Loss: {result.get('final_loss', 'N/A'):.4f}")
            
        except Exception as e:
            # Log failure but continue to next dimension
            error_msg = str(e)
            sweep_results.append({
                "target_dimension": dim,
                "status": "failed",
                "error": error_msg,
                "timestamp": time.strftime("%Y-%m-%dT%H-%M-%S")
            })
            print(f"FAILED dimension {dim}: {error_msg}", file=sys.stderr)
    
    total_time = time.time() - start_time
    
    # Aggregate logs
    final_log = {
        "sweep_start_time": time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime(start_time)),
        "sweep_end_time": time.strftime("%Y-%m-%dT%H-%M-%S"),
        "total_duration_seconds": total_time,
        "dimensions_processed": DIMENSIONS_TO_SWEEP,
        "results": sweep_results
    }
    
    # Save aggregate logs
    log_file_path = logs_dir / "sweep_logs.json"
    with open(log_file_path, "w", encoding="utf-8") as f:
        json.dump(final_log, f, indent=2)
    
    print(f"Sweep completed. Logs saved to {log_file_path}")
    
    return final_log

def setup_parser(subparsers: argparse._SubParsersAction) -> None:
    """Setup the CLI argument parser for the training sweep command."""
    parser = subparsers.add_parser(
        "sweep",
        help="Run the dimensionality sweep for autoencoder training."
    )
    parser.set_defaults(func=run_training_sweep)

def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive DomainShuttle Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    setup_parser(subparsers)
    
    # Add other commands here if needed (e.g., data, validate)
    # For this task, we focus on 'sweep'
    
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()