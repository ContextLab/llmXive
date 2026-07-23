import os
import sys
import json
import logging
import argparse
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

# Import from project modules
from config import TrainingConfig, DataConfig, AnalysisConfig, ensure_dirs
from data.split import stratified_split
from models.mpnn import MPNN, MPNNConfig, create_mpnn_from_config
from utils.logger import setup_logging

def load_processed_data_for_sampling(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset from T016."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run T016 first.")
    return pd.read_csv(data_path)

def prepare_features_for_model(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract feature matrix X and target y from the dataframe.
    Assumes the dataframe has been processed by T013 (descriptors) and T012 (cleaning).
    """
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ['smiles', 'rate_constant', 'substrate_class', 'source_id']
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        raise ValueError("No numeric feature columns found in the dataset.")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df['rate_constant'].values.astype(np.float32)
    return X, y

def create_random_mpnn_config(base_config: MPNNConfig, override: Dict[str, Any]) -> MPNNConfig:
    """Create a new MPNN config by overriding specific parameters."""
    config_dict = base_config.__dict__.copy()
    config_dict.update(override)
    # Ensure layers are within bounds [1, 4] as per T019 constraint
    if 'num_layers' in config_dict:
        config_dict['num_layers'] = max(1, min(4, config_dict['num_layers']))
    return MPNNConfig(**config_dict)

def train_and_evaluate_subset(
    X: np.ndarray,
    y: np.ndarray,
    split_ratio: float = 0.8,
    mpnn_config: Optional[MPNNConfig] = None,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.01,
    dropout: float = 0.1,
    num_layers: int = 2,
    seed: int = 42
) -> Dict[str, float]:
    """
    Train a shallow MPNN on a subset and evaluate R2 and MAE.
    This function simulates the training loop for the sensitivity analysis.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    n_samples = len(X)
    indices = np.random.permutation(n_samples)
    split_idx = int(n_samples * split_ratio)
    train_idx, val_idx = indices[:split_idx], indices[split_idx:]

    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    # Convert to tensors
    train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    val_dataset = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Create model
    if mpnn_config is None:
        # Default shallow config for sensitivity analysis
        mpnn_config = MPNNConfig(
            input_dim=X_train.shape[1],
            hidden_dim=64,
            num_layers=num_layers,
            dropout=dropout,
            out_dim=1
        )
    else:
        # Override specific params if passed
        mpnn_config.dropout = dropout
        mpnn_config.num_layers = num_layers
        mpnn_config.input_dim = X_train.shape[1]
        mpnn_config.out_dim = 1

    model = create_mpnn_from_config(mpnn_config)
    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X).squeeze()
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

    # Evaluation
    model.eval()
    val_predictions = []
    val_targets = []
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            outputs = model(batch_X).squeeze()
            val_predictions.extend(outputs.numpy())
            val_targets.extend(batch_y.numpy())

    val_predictions = np.array(val_predictions)
    val_targets = np.array(val_targets)

    # Calculate metrics
    mse = np.mean((val_predictions - val_targets) ** 2)
    mae = np.mean(np.abs(val_predictions - val_targets))
    
    # R2 calculation
    ss_res = np.sum((val_targets - val_predictions) ** 2)
    ss_tot = np.sum((val_targets - np.mean(val_targets)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return {"r2": float(r2), "mae": float(mae)}

def run_hyperparameter_sensitivity(
    data_path: str,
    output_path: str,
    sample_size: int = 2000,
    num_configs: int = 5,
    baseline_r2: float = 0.85 # Placeholder for T022 baseline, will be loaded if available
) -> None:
    """
    Run the hyperparameter sensitivity analysis.
    1. Load and sample data.
    2. Sweep hyperparameters (learning rate, dropout, layers).
    3. Train shallow MPNN for each config.
    4. Calculate variance in R2.
    5. Compare against baseline.
    6. Save report.
    """
    ensure_dirs()
    logger = setup_logging("hyperparameter_sensitivity")
    logger.info(f"Starting hyperparameter sensitivity analysis for {sample_size} samples.")

    # 1. Load data
    df = load_processed_data_for_sampling(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}.")

    # Stratified sample by substrate_class if available
    if 'substrate_class' in df.columns:
        sample_df = df.groupby('substrate_class', group_keys=False).apply(
            lambda x: x.sample(n=min(sample_size // len(df['substrate_class'].unique()), len(x)), random_state=42)
        )
    else:
        sample_df = df.sample(n=min(sample_size, len(df)), random_state=42)
    
    logger.info(f"Selected {len(sample_df)} rows for sensitivity analysis.")

    X, y = prepare_features_for_model(sample_df)
    logger.info(f"Prepared features: {X.shape}")

    # 2. Define sweep ranges
    learning_rates = [0.001, 0.01, 0.1]
    dropouts = [0.0, 0.2, 0.5]
    layers = [1, 2, 3] # Shallow models

    # We need max 5 configurations total as per task description
    # Select a representative set
    configs_to_test = [
        {"learning_rate": 0.01, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.001, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.1, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.01, "dropout": 0.0, "num_layers": 2},
        {"learning_rate": 0.01, "dropout": 0.2, "num_layers": 2},
    ]
    # If we need to vary layers, we can swap one in, but keeping it simple for 5 configs
    # Let's ensure we cover the requested sweep logic: "For each hyperparameter ... sweep a range"
    # The task says "max 5 configurations total". We will pick 5 that cover the ranges.
    configs_to_test = [
        {"learning_rate": 0.001, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.01, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.1, "dropout": 0.1, "num_layers": 2},
        {"learning_rate": 0.01, "dropout": 0.0, "num_layers": 2},
        {"learning_rate": 0.01, "dropout": 0.2, "num_layers": 1}, # Vary layers here
    ]

    results = []
    r2_scores = []

    for i, cfg in enumerate(configs_to_test):
        logger.info(f"Training config {i+1}/{len(configs_to_test)}: {cfg}")
        metrics = train_and_evaluate_subset(
            X, y,
            mpnn_config=None, # Let function create default shallow config
            epochs=50,
            learning_rate=cfg['learning_rate'],
            dropout=cfg['dropout'],
            num_layers=cfg['num_layers'],
            seed=42 + i # Different seed for each to capture variance
        )
        results.append({
            "config_id": i + 1,
            "learning_rate": cfg['learning_rate'],
            "dropout": cfg['dropout'],
            "num_layers": cfg['num_layers'],
            "r2": metrics['r2'],
            "mae": metrics['mae']
        })
        r2_scores.append(metrics['r2'])

    # 5. Calculate variance
    variance_r2 = np.var(r2_scores)
    mean_r2 = np.mean(r2_scores)

    # 6. Compare against baseline (from T022)
    # Try to load T022 baseline if available
    baseline_path = "artifacts/metrics.json"
    baseline_r2_actual = baseline_r2
    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, 'r') as f:
                baseline_data = json.load(f)
                baseline_r2_actual = baseline_data.get('r2', baseline_r2)
        except Exception as e:
            logger.warning(f"Could not load baseline from {baseline_path}: {e}")

    robustness_score = abs(mean_r2 - baseline_r2_actual)

    # 7. Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["config_id", "learning_rate", "dropout", "num_layers", "r2", "mae", "variance_r2", "robustness_vs_baseline"])
        writer.writeheader()
        for res in results:
            writer.writerow({
                "config_id": res["config_id"],
                "learning_rate": res["learning_rate"],
                "dropout": res["dropout"],
                "num_layers": res["num_layers"],
                "r2": f"{res['r2']:.4f}",
                "mae": f"{res['mae']:.4f}",
                "variance_r2": f"{variance_r2:.6f}",
                "robustness_vs_baseline": f"{robustness_score:.4f}"
            })

    logger.info(f"Sensitivity analysis complete. Variance: {variance_r2:.6f}. Report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Hyperparameter Sensitivity Analysis for SN1 Rate Prediction")
    parser.add_argument("--data-path", type=str, default="data/processed/cleaned_sn1.csv", help="Path to cleaned dataset")
    parser.add_argument("--output-path", type=str, default="artifacts/hyperparameter_sensitivity_report.csv", help="Output path for report")
    parser.add_argument("--sample-size", type=int, default=2000, help="Size of stratified sample")
    args = parser.parse_args()

    run_hyperparameter_sensitivity(
        data_path=args.data_path,
        output_path=args.output_path,
        sample_size=args.sample_size
    )

if __name__ == "__main__":
    main()