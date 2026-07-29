"""
Main entry point for the Dream-State Learning pipeline.
Orchestrates experimental (Wake/Dream) and baseline (Continuous SFT) runs,
performs statistical analysis, and generates comparative reports.
"""
import argparse
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, Any, List

import numpy as np
import torch

from config import Config
from utils.logger import get_logger, log_event
from utils.memory_monitor import MemoryMonitor
from data.loader import load_glue_subset
from models.trainer import Trainer, DreamScheduler
from eval.metrics import calculate_few_shot_accuracy, wilcoxon_test
from eval.statistical_analysis import run_wilcoxon_test, save_analysis_report
from eval.reporting import save_comparison_report

logger = get_logger(__name__)

def run_single_seed_experiment(config: Config, seed: int) -> Dict[str, Any]:
    """
    Run the full Wake/Dream training cycle for a single seed.
    Returns metrics including final accuracy and per-step losses.
    """
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    logger.info(f"Starting experimental run for seed {seed}")

    # Load data
    dataset = load_glue_subset(
        subset_name=config.dataset_name,
        max_samples=config.max_samples_per_seed
    )

    # Initialize model and trainer
    trainer = Trainer(config, seed=seed)

    # Run training loop
    history = trainer.train(
        dataset=dataset,
        total_steps=config.total_steps,
        is_baseline=False
    )

    # Evaluate on held-out set
    accuracy = calculate_few_shot_accuracy(trainer.model, dataset, config)

    return {
        "seed": seed,
        "final_accuracy": accuracy,
        "final_loss": history["final_loss"],
        "steps_completed": history["steps_completed"],
        "avg_loss": history["avg_loss"]
    }

def run_single_seed_baseline(config: Config, seed: int) -> Dict[str, Any]:
    """
    Run the continuous SFT baseline for a single seed.
    Returns metrics comparable to the experimental run.
    """
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    logger.info(f"Starting baseline run for seed {seed}")

    # Load data
    dataset = load_glue_subset(
        subset_name=config.dataset_name,
        max_samples=config.max_samples_per_seed
    )

    # Initialize model and trainer
    trainer = Trainer(config, seed=seed)

    # Run training loop in baseline mode
    history = trainer.train(
        dataset=dataset,
        total_steps=config.total_steps,
        is_baseline=True
    )

    # Evaluate on held-out set
    accuracy = calculate_few_shot_accuracy(trainer.model, dataset, config)

    return {
        "seed": seed,
        "final_accuracy": accuracy,
        "final_loss": history["final_loss"],
        "steps_completed": history["steps_completed"],
        "avg_loss": history["avg_loss"]
    }

def run_experiment(config: Config) -> Dict[str, Any]:
    """
    Run the full experimental pipeline across multiple seeds.
    """
    logger.info(f"Starting experimental pipeline with {config.num_seeds} seeds")

    all_results = []
    for seed in range(config.num_seeds):
        result = run_single_seed_experiment(config, seed)
        all_results.append(result)
        log_event("seed_completed", {"seed": seed, "accuracy": result["final_accuracy"]})

    return {
        "seeds": [r["final_accuracy"] for r in all_results],
        "mean_accuracy": np.mean([r["final_accuracy"] for r in all_results]),
        "std_accuracy": np.std([r["final_accuracy"] for r in all_results]),
        "details": all_results
    }

def run_baseline(config: Config) -> Dict[str, Any]:
    """
    Run the baseline pipeline across multiple seeds.
    """
    logger.info(f"Starting baseline pipeline with {config.num_seeds} seeds")

    all_results = []
    for seed in range(config.num_seeds):
        result = run_single_seed_baseline(config, seed)
        all_results.append(result)
        log_event("baseline_seed_completed", {"seed": seed, "accuracy": result["final_accuracy"]})

    return {
        "seeds": [r["final_accuracy"] for r in all_results],
        "mean_accuracy": np.mean([r["final_accuracy"] for r in all_results]),
        "std_accuracy": np.std([r["final_accuracy"] for r in all_results]),
        "details": all_results
    }

def main():
    parser = argparse.ArgumentParser(description="Dream-State Learning Pipeline")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    parser.add_argument("--run-experiment", action="store_true", help="Run experimental (Wake/Dream) mode")
    parser.add_argument("--run-baseline", action="store_true", help="Run baseline (Continuous SFT) mode")
    parser.add_argument("--run-comparison", action="store_true", help="Run full comparison pipeline")
    args = parser.parse_args()

    config = Config()

    # Initialize memory monitor
    memory_monitor = MemoryMonitor(limit_kb=config.max_memory_kb)
    memory_monitor.start()

    try:
        if args.run_comparison:
            logger.info("Running full comparison pipeline...")
            
            # Run experimental
            exp_results = run_experiment(config)
            
            # Run baseline
            base_results = run_baseline(config)
            
            # Statistical analysis
            stat_results = run_wilcoxon_test(
                exp_results["seeds"],
                base_results["seeds"],
                alpha=0.05
            )
            
            # Save analysis report
            analysis_path = save_analysis_report(
                exp_results=exp_results,
                base_results=base_results,
                stat_results=stat_results,
                output_path=config.analysis_output_path
            )
            
            # Generate and save final comparison report
            report_path = save_comparison_report(
                experimental_results=exp_results,
                baseline_results=base_results,
                statistical_analysis=stat_results,
                config=config,
                output_path=config.report_output_path
            )
            
            logger.info(f"Pipeline complete. Report saved to: {report_path}")
            
        elif args.run_experiment:
            results = run_experiment(config)
            logger.info(f"Experiment complete. Mean accuracy: {results['mean_accuracy']:.4f}")
            
        elif args.run_baseline:
            results = run_baseline(config)
            logger.info(f"Baseline complete. Mean accuracy: {results['mean_accuracy']:.4f}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        memory_monitor.stop()
        peak_rss = memory_monitor.get_peak_rss_kb()
        logger.info(f"Peak memory usage: {peak_rss / 1024:.2f} MB")

if __name__ == "__main__":
    main()