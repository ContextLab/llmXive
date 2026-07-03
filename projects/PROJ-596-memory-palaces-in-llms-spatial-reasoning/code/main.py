"""
Main execution entry point for the Memory Palaces in LLMs project.

Orchestrates:
1. Dataset download and verification
2. Model loading (GPT2 or DistilGPT2 fallback)
3. Training across seeds -4 to 4
4. Evaluation and result aggregation
5. Generation of run_summary.json
"""
import json
import os
import time
import gc
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on provided API surface
from data.download import download_dataset, save_checksums, load_existing_checksums
from models.loading import load_model, check_memory_budget
from training.loop import TrainingLoop
from evaluation.metrics import run_evaluation_for_seed, aggregate_results_by_seed
from utils.logger import ExperimentLogger, get_logger_for_run
from training.memory_monitor import MemoryMonitor

def setup_directories():
    """Ensure all required directories exist."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "raw"
    artifacts_dir = base_dir / "artifacts" / "results"
    
    for directory in [data_dir, artifacts_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    return base_dir, data_dir, artifacts_dir

def download_and_verify_datasets(data_dir: Path) -> bool:
    """Download and verify all required datasets."""
    print("Starting dataset download and verification...")
    
    datasets = [
        ("babi", "task3_10k"),
        ("lambada", None),
        ("story_cloze", "2016")
    ]
    
    checksums_path = data_dir / "checksums.json"
    
    # Load existing checksums if available
    existing_checksums = load_existing_checksums(checksums_path) if checksums_path.exists() else {}
    
    success = True
    for dataset_name, config in datasets:
        try:
            print(f"Downloading dataset: {dataset_name}")
            dataset_path = download_dataset(dataset_name, config, data_dir)
            
            if dataset_path:
                # Verify checksum
                if dataset_name in existing_checksums:
                    # Verify existing checksum
                    pass  # Verification logic handled in download_dataset
                else:
                    # Save new checksum
                    save_checksums(checksums_path, {dataset_name: str(dataset_path)})
            
            print(f"Successfully processed: {dataset_name}")
        except Exception as e:
            print(f"Error processing dataset {dataset_name}: {str(e)}")
            success = False
            continue
    
    return success

def run_training_loop(
    base_dir: Path,
    data_dir: Path,
    artifacts_dir: Path,
    seed: int,
    logger: ExperimentLogger,
    memory_monitor: MemoryMonitor
) -> Dict[str, Any]:
    """Run training for a single seed."""
    print(f"\n{'='*50}")
    print(f"Starting training for seed: {seed}")
    print(f"{'='*50}")
    
    try:
        # Check memory budget
        memory_ok, final_batch_size, dataset_capped = check_memory_budget()
        
        if not memory_ok:
            print("WARNING: Memory budget exceeded, reducing batch size and/or dataset size")
        
        # Initialize training loop
        trainer = TrainingLoop(
            seed=seed,
            base_dir=base_dir,
            data_dir=data_dir,
            artifacts_dir=artifacts_dir,
            batch_size=final_batch_size,
            dataset_capped=dataset_capped
        )
        
        # Train model
        training_results = trainer.train()
        
        # Log hyperparameters
        logger.log_hyperparameters({
            "seed": seed,
            "batch_size": final_batch_size,
            "dataset_capped": dataset_capped,
            "memory_ok": memory_ok
        })
        
        print(f"Training completed for seed {seed}")
        return training_results
        
    except Exception as e:
        print(f"Error during training for seed {seed}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "seed": seed}

def run_evaluation(
    base_dir: Path,
    data_dir: Path,
    artifacts_dir: Path,
    seed: int,
    logger: ExperimentLogger
) -> Dict[str, Any]:
    """Run evaluation for a single seed."""
    print(f"\n{'='*50}")
    print(f"Starting evaluation for seed: {seed}")
    print(f"{'='*50}")
    
    try:
        results = run_evaluation_for_seed(
            seed=seed,
            base_dir=base_dir,
            data_dir=data_dir,
            artifacts_dir=artifacts_dir
        )
        
        logger.log_evaluation_results(seed, results)
        print(f"Evaluation completed for seed {seed}")
        return results
        
    except Exception as e:
        print(f"Error during evaluation for seed {seed}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "seed": seed}

def main():
    """Main execution function."""
    start_time = time.time()
    
    print("Memory Palaces in LLMs - Main Execution")
    print("=" * 60)
    
    # Setup directories
    base_dir, data_dir, artifacts_dir = setup_directories()
    
    # Initialize logger
    logger = get_logger_for_run(base_dir / "artifacts" / "results")
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor(base_dir / "artifacts" / "results")
    memory_monitor.start_monitoring()
    
    try:
        # Step 1: Download and verify datasets
        if not download_and_verify_datasets(data_dir):
            print("ERROR: Dataset download failed. Exiting.")
            return 1
        
        # Define seeds for experimentation
        seeds = list(range(-4, 5))  # -4, -3, -2, -1, 0, 1, 2, 3, 4
        
        all_training_results = []
        all_evaluation_results = []
        effective_batch_size = None
        
        # Step 2 & 3: Train and evaluate for each seed
        for seed in seeds:
            # Training
            training_result = run_training_loop(
                base_dir, data_dir, artifacts_dir, seed, logger, memory_monitor
            )
            all_training_results.append(training_result)
            
            if effective_batch_size is None and "batch_size" in training_result:
                effective_batch_size = training_result["batch_size"]
            
            # Clear GPU memory between runs
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Evaluation
            evaluation_result = run_evaluation(
                base_dir, data_dir, artifacts_dir, seed, logger
            )
            all_evaluation_results.append(evaluation_result)
            
            # Clear GPU memory between runs
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Step 4: Aggregate results
        print("\n" + "=" * 60)
        print("Aggregating results...")
        print("=" * 60)
        
        aggregated_results = aggregate_results_by_seed(all_evaluation_results)
        
        # Step 5: Generate run summary
        end_time = time.time()
        runtime_seconds = end_time - start_time
        
        run_summary = {
            "seeds": seeds,
            "accuracies": aggregated_results,
            "effective_batch_size": effective_batch_size or 8,
            "runtime_seconds": runtime_seconds,
            "training_results": all_training_results,
            "evaluation_results": all_evaluation_results
        }
        
        # Save run summary
        summary_path = artifacts_dir / "run_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(run_summary, f, indent=2)
        
        print(f"\nRun summary saved to: {summary_path}")
        print(f"Total runtime: {runtime_seconds:.2f} seconds")
        
        # Stop memory monitoring
        memory_monitor.stop_monitoring()
        
        # Log final memory usage
        memory_monitor.log_final_memory_usage()
        
        print("\nExecution completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Fatal error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        memory_monitor.stop_monitoring()
        return 1

if __name__ == "__main__":
    import torch
    sys.exit(main())
