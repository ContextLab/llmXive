"""
Scaling analysis for the Cortical Column LLM project.
Implements T049a, T049b, and T049c: training single configs, running the loop,
and writing the scaling law results to CSV.
"""
import json
import logging
import os
import sys
import time
import csv
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from src.models.hybrid_network import HybridNetwork, create_hybrid_network, count_parameters
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_polynomial_test_data, load_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_RESULTS_DIR = Path("data/results")
DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class ScalingConfig:
    """Configuration for a single scaling experiment."""
    column_count: int
    hidden_dim: int = 64
    num_heads: int = 4
    num_layers: int = 3
    lr: float = 0.001
    epochs: int = 5
    batch_size: int = 32
    seed: int = 42
    name: str = field(default="", repr=False)

    def __post_init__(self):
        if not self.name:
            self.name = f"scaling_{self.column_count}x"

@dataclass
class ScalingResult:
    """Result of a single scaling experiment."""
    config_name: str
    column_count: int
    total_params: int
    mae: float
    time_sec: float
    success: bool
    error_msg: Optional[str] = None

def create_scaling_configs(base_columns: int = 1, multipliers: List[int] = [1, 2, 4]) -> List[ScalingConfig]:
    """
    Create a list of ScalingConfig objects for different column counts.
    T049b dependency: orchestrates the configurations for the loop.
    """
    configs = []
    for mult in multipliers:
        count = base_columns * mult
        cfg = ScalingConfig(
            column_count=count,
            name=f"scaling_{mult}x"
        )
        configs.append(cfg)
    return configs

def train_single_config(cfg: ScalingConfig) -> ScalingResult:
    """
    T049a: Train a single model configuration with specified column count.
    Performs a real, small-scale training run to measure MAE and time.
    Outputs: data/results/scaling_single_{config}.json
    """
    logger.info(f"Starting training for config: {cfg.name} (columns={cfg.column_count})")
    start_time = time.time()
    try:
        # Set seed for reproducibility
        torch.manual_seed(cfg.seed)
        np.random.seed(cfg.seed)

        # 1. Generate REAL data (Lorenz for training, Polynomial for test)
        # Using a small, deterministic dataset to fit within CPU/GPU limits
        train_data = generate_training_data(n_samples=500, seed=cfg.seed)
        test_data = generate_polynomial_test_data(n_samples=200, seed=cfg.seed)

        # Prepare tensors
        X_train = torch.FloatTensor(train_data['X'])
        y_train = torch.FloatTensor(train_data['y'])
        X_test = torch.FloatTensor(test_data['X'])
        y_test = torch.FloatTensor(test_data['y'])

        # 2. Create Model
        # The hybrid network takes column_count as an argument
        model = create_hybrid_network(
            column_count=cfg.column_count,
            hidden_dim=cfg.hidden_dim,
            num_heads=cfg.num_heads,
            num_layers=cfg.num_layers
        )
        total_params = count_parameters(model)
        logger.info(f"Model created with {total_params:,} parameters")

        # 3. Training Loop (Simplified for speed)
        optimizer = optim.Adam(model.parameters(), lr=cfg.lr)
        criterion = nn.MSELoss()
        model.train()

        # Small dataset, so one pass per epoch is fine
        dataset_size = len(X_train)
        indices = torch.randperm(dataset_size)

        for epoch in range(cfg.epochs):
            epoch_loss = 0.0
            # Shuffle indices
            current_indices = indices[epoch * dataset_size : (epoch + 1) * dataset_size]
            # In this small case, we just iterate the whole set shuffled
            for i in range(0, dataset_size, cfg.batch_size):
                batch_idx = current_indices[i : i + cfg.batch_size]
                if len(batch_idx) == 0: continue

                batch_X = X_train[batch_idx]
                batch_y = y_train[batch_idx]

                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / (dataset_size / cfg.batch_size)
            if (epoch + 1) % 2 == 0:
                logger.info(f"Epoch {epoch+1}/{cfg.epochs}, Loss: {avg_loss:.4f}")

        # 4. Evaluation
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test)
            mae = calculate_mae(test_outputs, y_test)

        end_time = time.time()
        duration = end_time - start_time

        # 5. Save single result
        result_dict = {
            "config": asdict(cfg),
            "total_params": total_params,
            "mae": float(mae),
            "time_sec": float(duration),
            "success": True
        }
        output_path = DATA_RESULTS_DIR / f"scaling_single_{cfg.name}.json"
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Saved single result to {output_path}")

        return ScalingResult(
            config_name=cfg.name,
            column_count=cfg.column_count,
            total_params=total_params,
            mae=float(mae),
            time_sec=float(duration),
            success=True
        )

    except Exception as e:
        end_time = time.time()
        logger.error(f"Training failed for {cfg.name}: {e}", exc_info=True)
        return ScalingResult(
            config_name=cfg.name,
            column_count=cfg.column_count,
            total_params=0,
            mae=-1.0,
            time_sec=end_time - start_time,
            success=False,
            error_msg=str(e)
        )

def run_scaling_loop(base_columns: int = 1, multipliers: List[int] = [1, 2, 4]) -> List[ScalingResult]:
    """
    T049b: Orchestrate training for column counts [x, 2x, 4x].
    Calls train_single_config for each config.
    """
    logger.info("Starting Scaling Loop")
    configs = create_scaling_configs(base_columns, multipliers)
    results = []
    for cfg in configs:
        res = train_single_config(cfg)
        results.append(res)
    return results

def write_scaling_results(results: List[ScalingResult], output_path: Optional[str] = None) -> bool:
    """
    T049c: Aggregate results into data/results/scaling_law.csv.
    Columns: columns, params, mae, time_sec.
    Includes verification step.
    """
    if output_path is None:
        output_path = str(DATA_RESULTS_DIR / "scaling_law.csv")

    logger.info(f"Writing scaling results to {output_path}")

    # Filter for successful runs only to ensure valid CSV
    valid_results = [r for r in results if r.success]
    if not valid_results:
        logger.error("No successful results to write. Aborting.")
        return False

    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Header
            writer.writerow(['columns', 'params', 'mae', 'time_sec'])
            # Data
            for res in valid_results:
                writer.writerow([
                    res.column_count,
                    res.total_params,
                    f"{res.mae:.6f}",
                    f"{res.time_sec:.2f}"
                ])

        # Verification Step
        if not os.path.exists(output_path):
            logger.error(f"Verification failed: {output_path} does not exist.")
            return False

        # Check file is not empty and has header
        with open(output_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                logger.error(f"Verification failed: {output_path} is empty or missing data rows.")
                return False

        logger.info(f"Verification passed: {output_path} exists and is valid.")
        return True

    except Exception as e:
        logger.error(f"Failed to write or verify scaling results: {e}", exc_info=True)
        return False

def main():
    """
    Entry point for the scaling analysis script.
    Runs the loop and writes the CSV.
    """
    logger.info("Running Scaling Analysis Main")
    # Run the loop with default multipliers [1, 2, 4]
    results = run_scaling_loop(base_columns=1, multipliers=[1, 2, 4])

    # Write the aggregated CSV
    success = write_scaling_results(results)

    if success:
        logger.info("Scaling analysis completed successfully.")
        sys.exit(0)
    else:
        logger.error("Scaling analysis failed to produce valid output.")
        sys.exit(1)

if __name__ == "__main__":
    main()
