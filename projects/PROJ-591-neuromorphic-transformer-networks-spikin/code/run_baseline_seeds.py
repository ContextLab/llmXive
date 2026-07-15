import os
import sys
import argparse
import time
import json
import hashlib
import pandas as pd

from main import TrainingConfig, run_baseline_training, setup_seed

def run_all_seeds(project_root: str = ".", seeds: list = None, epochs: int = 5, batch_size: int = 32, lr: float = 1e-3):
    """
    Run baseline training for multiple seeds.
    
    Args:
        project_root: Root directory of the project
        seeds: List of random seeds to run
        epochs: Number of epochs per seed
        batch_size: Batch size
        lr: Learning rate
    """
    if seeds is None:
        seeds = [1, 2, 3, 4, 5]
    
    os.makedirs(os.path.join(project_root, "data/processed"), exist_ok=True)
    
    all_results = []
    
    for seed in seeds:
        print(f"Running baseline training for seed {seed}...")
        config = TrainingConfig(
            seed=seed,
            batch_size=batch_size,
            learning_rate=lr,
            max_epochs=epochs,
            is_spiking=False,
            project_root=project_root
        )
        
        try:
            results = run_baseline_training(config)
            all_results.extend(results)
            print(f"Seed {seed} completed successfully.")
        except Exception as e:
            print(f"Seed {seed} failed: {e}")
            continue
    
    # Save combined results to CSV
    if all_results:
        df = pd.DataFrame([
            {
                "seed": r.seed,
                "epoch": r.epoch,
                "perplexity": r.perplexity,
                "energy_per_token_kWh": r.energy_per_token_kWh,
                "wall_clock_time": r.wall_clock_time,
                "estimated_energy": r.estimated_energy
            }
            for r in all_results
        ])
        output_path = os.path.join(project_root, "data/processed/baseline_metrics.csv")
        df.to_csv(output_path, index=False)
        print(f"Baseline metrics saved to {output_path}")
    else:
        print("No results to save.")

def main():
    parser = argparse.ArgumentParser(description="Run baseline training for multiple seeds")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--project-root", type=str, default=".")
    
    args = parser.parse_args()
    
    run_all_seeds(
        project_root=args.project_root,
        seeds=args.seeds,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )

if __name__ == "__main__":
    main()
