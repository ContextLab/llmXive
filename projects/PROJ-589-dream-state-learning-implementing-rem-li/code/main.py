import argparse
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy.stats import ttest_rel
from sklearn.metrics import accuracy_score
from sklearn.utils.stats import var as sklearn_var

from config import Config
from data.loader import load_glue_subset
from models.trainer import Trainer, DreamScheduler
from utils.logger import get_logger, log_event
from utils.memory_monitor import MemoryMonitor, enforce_memory_limit
from utils.exceptions import TimeLimitExceeded
from eval.reporting import save_comparison_report
from eval.statistical_analysis import run_ttest_paired

logger = get_logger(__name__)

# Temperature sweep configuration
TEMPERATURES = [0.5, 0.7, 0.9]
SEEDS_PER_TEMP = 5
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_single_seed_experiment(
    seed: int,
    temperature: float,
    config: Config,
    dataset_name: str = "sst2"
) -> Dict[str, Any]:
    """
    Run a single training experiment with a specific seed and temperature.
    Re-initializes model weights, optimizer state, and random seed for isolation.
    """
    logger.info(f"Starting experiment: seed={seed}, temperature={temperature}")
    
    # Set random seeds for reproducibility within this run
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    try:
        # Load data
        dataset = load_glue_subset(dataset_name, split="train")
        if len(dataset) > config.max_samples:
            dataset = dataset.select(range(config.max_samples))
        
        # Initialize trainer with specific temperature for dream phase
        trainer = Trainer(
            model_name=config.model_name,
            dataset=dataset,
            config=config,
            dream_temperature=temperature
        )
        
        # Train
        history = trainer.train(
            num_epochs=config.epochs,
            batch_size=config.batch_size,
            device=config.device
        )
        
        # Evaluate
        final_accuracy = trainer.evaluate(dataset)
        
        result = {
            "seed": seed,
            "temperature": temperature,
            "final_accuracy": float(final_accuracy),
            "final_loss": float(history["loss"][-1]) if history["loss"] else 0.0,
            "steps": len(history["loss"]),
            "status": "completed"
        }
        
        logger.info(f"Experiment completed: seed={seed}, temp={temperature}, acc={final_accuracy:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Experiment failed: seed={seed}, temp={temperature}, error={str(e)}")
        return {
            "seed": seed,
            "temperature": temperature,
            "final_accuracy": None,
            "final_loss": None,
            "steps": 0,
            "status": "failed",
            "error": str(e)
        }

def run_temperature_sweep(config: Config, dataset_name: str = "sst2") -> Dict[str, Any]:
    """
    Execute grid search over temperature values with multiple seeds per temperature.
    Re-initializes model and random state for each run to ensure state isolation.
    """
    logger.info(f"Starting temperature sweep: temperatures={TEMPERATURES}, seeds_per_temp={SEEDS_PER_TEMP}")
    
    all_results = []
    sweep_start_time = time.time()
    
    for temperature in TEMPERATURES:
        logger.info(f"Processing temperature: {temperature}")
        temp_results = []
        
        for seed in range(SEEDS_PER_TEMP):
            # Ensure full re-initialization for each run
            result = run_single_seed_experiment(
                seed=seed,
                temperature=temperature,
                config=config,
                dataset_name=dataset_name
            )
            temp_results.append(result)
            all_results.append(result)
            
            # Check time limit
            elapsed = time.time() - sweep_start_time
            max_seconds = config.max_wall_clock_hours * 3600
            if elapsed > max_seconds:
                raise TimeLimitExceeded(f"Time limit exceeded: {elapsed:.1f}s > {max_seconds}s")
        
        logger.info(f"Completed temperature {temperature}: {len(temp_results)} runs")
    
    # Compute variance metrics
    variance_report = compute_variance_metrics(all_results)
    
    # Save results
    results_file = RESULTS_DIR / "temperature_sweep_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "sweep_results": all_results,
            "variance_report": variance_report,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "temperatures": TEMPERATURES,
                "seeds_per_temperature": SEEDS_PER_TEMP,
                "dataset": dataset_name
            }
        }, f, indent=2)
    
    logger.info(f"Sweep completed. Results saved to {results_file}")
    return {
        "results": all_results,
        "variance_report": variance_report
    }

def compute_variance_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute variance metrics for the temperature sweep results.
    Uses scikit-learn's var function as required.
    """
    # Group results by temperature
    temp_groups = {}
    for result in results:
        if result["status"] != "completed" or result["final_accuracy"] is None:
            continue
        temp = result["temperature"]
        if temp not in temp_groups:
            temp_groups[temp] = []
        temp_groups[temp].append(result["final_accuracy"])
    
    # Compute variance for each temperature
    variance_by_temp = {}
    for temp, accuracies in temp_groups.items():
        if len(accuracies) > 1:
            # Use scikit-learn's var function (population variance by default)
            var_value = float(sklearn_var(accuracies))
            variance_by_temp[str(temp)] = {
                "variance": var_value,
                "std": float(np.sqrt(var_value)),
                "mean": float(np.mean(accuracies)),
                "count": len(accuracies),
                "values": accuracies
            }
        else:
            variance_by_temp[str(temp)] = {
                "variance": 0.0,
                "std": 0.0,
                "mean": float(accuracies[0]) if accuracies else None,
                "count": len(accuracies),
                "values": accuracies
            }
    
    # Overall variance across all temperatures
    all_accuracies = [r["final_accuracy"] for r in results 
                    if r["status"] == "completed" and r["final_accuracy"] is not None]
    overall_variance = float(sklearn_var(all_accuracies)) if len(all_accuracies) > 1 else 0.0
    
    return {
        "variance_by_temperature": variance_by_temp,
        "overall_variance": overall_variance,
        "overall_std": float(np.sqrt(overall_variance)),
        "total_completed_runs": len(all_accuracies),
        "total_temperatures": len(temp_groups)
    }

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple experiments.
    """
    if not results:
        return {"status": "no_results"}
    
    completed = [r for r in results if r["status"] == "completed"]
    failed = [r for r in results if r["status"] == "failed"]
    
    if not completed:
        return {
            "status": "all_failed",
            "failed_count": len(failed),
            "errors": [r.get("error", "Unknown error") for r in failed]
        }
    
    accuracies = [r["final_accuracy"] for r in completed]
    
    return {
        "status": "partial_success" if failed else "all_completed",
        "completed_count": len(completed),
        "failed_count": len(failed),
        "accuracy_stats": {
            "mean": float(np.mean(accuracies)),
            "std": float(np.std(accuracies)),
            "min": float(np.min(accuracies)),
            "max": float(np.max(accuracies)),
            "variance": float(sklearn_var(accuracies))
        },
        "results": completed
    }

def main():
    """
    Main entry point for the temperature sweep experiment.
    """
    parser = argparse.ArgumentParser(description="Dream-State Learning Temperature Sweep")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--dataset", type=str, default="sst2", help="GLUE dataset name")
    parser.add_argument("--temperatures", type=str, 
                      default="0.5,0.7,0.9", 
                      help="Comma-separated list of temperatures")
    parser.add_argument("--seeds-per-temp", type=int, default=5, help="Seeds per temperature")
    args = parser.parse_args()
    
    # Update global settings
    global TEMPERATURES, SEEDS_PER_TEMP
    TEMPERATURES = [float(t) for t in args.temperatures.split(",")]
    SEEDS_PER_TEMP = args.seeds_per_temp
    
    # Load configuration
    config = Config.load(args.config)
    
    logger.info(f"Starting Dream-State Learning Temperature Sweep")
    logger.info(f"Temperatures: {TEMPERATURES}")
    logger.info(f"Seeds per temperature: {SEEDS_PER_TEMP}")
    logger.info(f"Dataset: {args.dataset}")
    
    try:
        result = run_temperature_sweep(config, args.dataset)
        
        # Log summary
        logger.info(f"Sweep completed successfully")
        logger.info(f"Total runs: {result['variance_report']['total_completed_runs']}")
        logger.info(f"Overall variance: {result['variance_report']['overall_variance']:.6f}")
        
        for temp, metrics in result['variance_report']['variance_by_temperature'].items():
            logger.info(f"Temperature {temp}: variance={metrics['variance']:.6f}, "
                      f"mean={metrics['mean']:.4f}, count={metrics['count']}")
        
        return result
        
    except TimeLimitExceeded as e:
        logger.error(f"Time limit exceeded: {e}")
        return {"status": "time_limit_exceeded", "error": str(e)}
    except Exception as e:
        logger.error(f"Sweep failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    main()
