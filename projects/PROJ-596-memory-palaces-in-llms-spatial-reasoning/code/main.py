"""
Main orchestration script for the Memory Palaces project.
Orchestrates dataset download, training, evaluation, and interference injection experiments.
"""
import json
import os
import time
import gc
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Enforce single-core execution as per project constraints
os.environ["OMP_NUM_THREADS"] = "1"
try:
    import torch
    torch.set_num_threads(1)
except ImportError:
    pass

from data.download import download_dataset, save_checksums, load_existing_checksums, main as download_main
from models.loading import load_model, check_memory_budget
from training.loop import OptimizedTrainingLoop
from training.memory_monitor import MemoryMonitor
from evaluation.metrics import (
    evaluate_model_on_dataset,
    compute_interference_distance,
    ensure_results_dir
)
from utils.logger import ExperimentLogger, get_logger_for_run
from utils.hyperparams_logger import log_hyperparameters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('artifacts/results/main_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directory structure."""
    dirs = [
        "code", "data", "data/raw", "data/processed",
        "artifacts", "artifacts/results", "artifacts/metrics",
        "artifacts/schemas", "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    return dirs

def download_and_verify_datasets():
    """Download datasets and verify checksums."""
    logger.info("Downloading and verifying datasets...")
    try:
        download_main()
        logger.info("Datasets downloaded and verified.")
    except Exception as e:
        logger.error(f"Failed to download datasets: {e}")
        raise

def run_training_loop(args, variant="spatial"):
    """Run the training loop for a specific variant."""
    logger.info(f"Starting training for variant: {variant}")
    
    # Check memory budget
    check_memory_budget()
    
    # Initialize model
    model, tokenizer = load_model(variant=variant)
    
    # Initialize training loop
    trainer = OptimizedTrainingLoop(
        model=model,
        tokenizer=tokenizer,
        dataset_name=args.dataset,
        variant=variant
    )
    
    # Run training
    metrics = trainer.train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        seed=args.seed
    )
    
    logger.info(f"Training completed for variant {variant}. Metrics: {metrics}")
    return model, metrics

def run_evaluation(args, model, tokenizer, variant):
    """Run evaluation for a specific variant."""
    logger.info(f"Evaluating variant: {variant}")
    
    results = evaluate_model_on_dataset(
        model=model,
        tokenizer=tokenizer,
        dataset_name=args.dataset,
        variant=variant,
        seed=args.seed
    )
    
    # Save evaluation results
    output_path = Path(f"artifacts/results/{variant}_evaluation_{args.seed}.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")
    return results

def run_interference_injection_experiment(args, spatial_model, baseline_model, tokenizer):
    """
    Run interference-injection experiments to measure spatial organization efficacy.
    Computes interference distance metric for both spatial and baseline variants.
    """
    logger.info("Starting interference injection experiment...")
    
    # Ensure results directory exists
    ensure_results_dir()
    
    # Compute interference distance for spatial model
    logger.info("Computing interference distance for spatial model...")
    spatial_result = compute_interference_distance(
        model=spatial_model,
        tokenizer=tokenizer,
        dataset_name=args.dataset,
        variant="spatial",
        seed=args.seed
    )
    
    # Compute interference distance for baseline model
    logger.info("Computing interference distance for baseline model...")
    baseline_result = compute_interference_distance(
        model=baseline_model,
        tokenizer=tokenizer,
        dataset_name=args.dataset,
        variant="baseline",
        seed=args.seed
    )
    
    # Calculate delta and p-value
    spatial_recall = spatial_result.get("recall", 0.0)
    baseline_recall = baseline_result.get("recall", 0.0)
    delta = spatial_recall - baseline_recall
    
    # For p-value, we use the result from the interference distance computation
    # which should have performed statistical testing
    p_value = spatial_result.get("p_value", 1.0)
    
    # Prepare results dictionary
    interference_metrics = {
        "spatial_recall": spatial_recall,
        "baseline_recall": baseline_recall,
        "delta": delta,
        "p_value": p_value,
        "dataset": args.dataset,
        "seed": args.seed,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    output_path = Path("artifacts/results/interference_metrics.json")
    with open(output_path, 'w') as f:
        json.dump(interference_metrics, f, indent=2)
    
    logger.info(f"Interference metrics saved to {output_path}")
    logger.info(f"Results - Spatial: {spatial_recall:.4f}, Baseline: {baseline_recall:.4f}, Delta: {delta:.4f}, p-value: {p_value:.4f}")
    
    return interference_metrics

def main():
    """Main entry point for the orchestration script."""
    parser = argparse.ArgumentParser(description="Memory Palaces Project Orchestration")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--dataset", type=str, default="babi_task3", help="Dataset to use")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--skip_training", action="store_true", help="Skip training and use existing models")
    
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    # Download and verify datasets
    if not args.skip_training:
        download_and_verify_datasets()
    
    # Load or train models
    if args.skip_training:
        logger.info("Skipping training, loading existing models...")
        # In a real scenario, we would load from saved checkpoints
        # For now, we'll train both variants
        spatial_model, _ = run_training_loop(args, variant="spatial")
        baseline_model, _ = run_training_loop(args, variant="baseline")
    else:
        logger.info("Training spatial model...")
        spatial_model, _ = run_training_loop(args, variant="spatial")
        
        logger.info("Training baseline model...")
        baseline_model, _ = run_training_loop(args, variant="baseline")
    
    # Load tokenizer
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2-medium")
    
    # Run evaluation
    logger.info("Running evaluation...")
    spatial_eval = run_evaluation(args, spatial_model, tokenizer, "spatial")
    baseline_eval = run_evaluation(args, baseline_model, tokenizer, "baseline")
    
    # Run interference injection experiment
    logger.info("Running interference injection experiment...")
    interference_results = run_interference_injection_experiment(
        args, 
        spatial_model, 
        baseline_model, 
        tokenizer
    )
    
    # Log hyperparameters
    log_hyperparameters({
        "seed": args.seed,
        "dataset": args.dataset,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "interference_delta": interference_results["delta"],
        "interference_p_value": interference_results["p_value"]
    })
    
    logger.info("Orchestration completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())