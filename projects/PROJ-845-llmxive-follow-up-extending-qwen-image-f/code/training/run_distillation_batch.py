import os
import sys
import json
import argparse
import time
import torch
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config, get_config
from utils.logger import get_logger
from utils.resource_monitor import ResourceMonitor
from training.distill_loop import run_distillation
from models.student import create_student_model
from models.teacher import Teacher

logger = get_logger("run_distillation_batch")

def run_single_distillation_run(
    dataset_path: str,
    run_id: str,
    output_dir: str,
    config: Config
) -> dict:
    """
    Execute a single distillation run for a specific dataset subset.
    
    Args:
        dataset_path: Path to the input CSV (high/low/target)
        run_id: Unique identifier for this run
        output_dir: Directory to save the DistillationRun JSON
        config: Configuration object containing seed, limits, etc.
        
    Returns:
        Dictionary containing the DistillationRun record
    """
    logger.info(f"Starting distillation run: {run_id} for dataset: {dataset_path}")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    monitor.start()
    
    start_time = time.time()
    run_result = {
        "run_id": run_id,
        "dataset_path": dataset_path,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "model_params": {},
        "training_loss_curve": [],
        "convergence_epoch": None,
        "final_accuracy": None,
        "resource_usage": {
            "peak_ram_gb": 0.0,
            "elapsed_hours": 0.0
        },
        "metadata": {
            "config_seed": config.seed,
            "max_ram_gb": config.max_ram_gb,
            "max_runtime_hours": config.max_runtime_hours
        }
    }
    
    try:
        # Check resource limits immediately
        if config.max_ram_gb is not None:
            # Initial check (will be updated during training)
            pass
        
        # Create student model
        logger.info(f"Creating student model for run {run_id}")
        student_model = create_student_model(config.seed)
        run_result["model_params"] = {
            "num_parameters": sum(p.numel() for p in student_model.parameters()),
            "architecture": "DistilBERT-base-uncased-like",
            "seed": config.seed
        }
        
        # Initialize teacher
        teacher = Teacher(seed=config.seed)
        
        # Run distillation
        logger.info(f"Running distillation loop for {run_id}")
        distillation_result = run_distillation(
            dataset_path=dataset_path,
            student_model=student_model,
            teacher=teacher,
            config=config,
            run_id=run_id
        )
        
        # Update run result with distillation output
        run_result["training_loss_curve"] = distillation_result.get("loss_curve", [])
        run_result["convergence_epoch"] = distillation_result.get("convergence_epoch")
        run_result["final_accuracy"] = distillation_result.get("final_accuracy")
        run_result["status"] = distillation_result.get("status", "completed")
        
        # Stop resource monitor and record usage
        monitor.stop()
        peak_ram = monitor.get_peak_ram_gb()
        elapsed_hours = (time.time() - start_time) / 3600.0
        
        run_result["resource_usage"] = {
            "peak_ram_gb": round(peak_ram, 3),
            "elapsed_hours": round(elapsed_hours, 3)
        }
        
        # Check constraints
        if peak_ram > config.max_ram_gb:
            run_result["status"] = "failed_ram_exceeded"
            logger.error(f"RAM limit exceeded: {peak_ram:.2f}GB > {config.max_ram_gb}GB")
            # We still save the result, but mark as failed
        
        if elapsed_hours > config.max_runtime_hours:
            run_result["status"] = "failed_timeout"
            logger.error(f"Runtime limit exceeded: {elapsed_hours:.2f}h > {config.max_runtime_hours}h")
        
        run_result["end_time"] = datetime.now().isoformat()
        
    except Exception as e:
        logger.error(f"Error during distillation run {run_id}: {str(e)}", exc_info=True)
        monitor.stop()
        run_result["status"] = "failed_error"
        run_result["error_message"] = str(e)
        run_result["end_time"] = datetime.now().isoformat()
        
        # Record partial resource usage
        run_result["resource_usage"] = {
            "peak_ram_gb": round(monitor.get_peak_ram_gb(), 3),
            "elapsed_hours": round((time.time() - start_time) / 3600.0, 3)
        }
    
    # Save result to JSON
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{run_id}_distillation_run.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(run_result, f, indent=2, default=str)
    
    logger.info(f"Saved distillation run result to {output_path}")
    return run_result

def main():
    """
    Main entry point to execute three independent distillation runs
    for High, Low, and Target entropy subsets.
    """
    parser = argparse.ArgumentParser(description="Run batch distillation for entropy subsets")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Directory containing the generated CSV datasets"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save DistillationRun JSON files"
    )
    parser.add_argument(
        "--max-ram-gb",
        type=float,
        default=7.0,
        help="Maximum RAM in GB"
    )
    parser.add_argument(
        "--max-runtime-hours",
        type=float,
        default=6.0,
        help="Maximum runtime in hours"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Initialize config
    config = Config(
        seed=args.seed,
        max_ram_gb=args.max_ram_gb,
        max_runtime_hours=args.max_runtime_hours
    )
    
    # Define dataset mappings
    dataset_configs = [
        {
            "name": "high_entropy",
            "filename": "high_entropy.csv",
            "run_id": "distill_high_entropy"
        },
        {
            "name": "low_entropy",
            "filename": "low_entropy.csv",
            "run_id": "distill_low_entropy"
        },
        {
            "name": "target_specific",
            "filename": "target_specific.csv",
            "run_id": "distill_target_specific"
        }
    ]
    
    logger.info(f"Starting batch distillation with {len(dataset_configs)} runs")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    all_results = []
    
    for dataset_cfg in dataset_configs:
        dataset_path = os.path.join(args.data_dir, dataset_cfg["filename"])
        
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset not found: {dataset_path}")
            # Create a failed result entry
            failed_result = {
                "run_id": dataset_cfg["run_id"],
                "dataset_path": dataset_path,
                "status": "failed_dataset_missing",
                "error_message": f"Dataset file not found: {dataset_path}",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }
            all_results.append(failed_result)
            continue
        
        result = run_single_distillation_run(
            dataset_path=dataset_path,
            run_id=dataset_cfg["run_id"],
            output_dir=args.output_dir,
            config=config
        )
        all_results.append(result)
    
    # Summary
    logger.info("Batch distillation completed")
    successful_runs = sum(1 for r in all_results if r.get("status") == "completed")
    failed_runs = len(all_results) - successful_runs
    logger.info(f"Successful runs: {successful_runs}, Failed runs: {failed_runs}")
    
    # Return non-zero exit code if any run failed
    if failed_runs > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
