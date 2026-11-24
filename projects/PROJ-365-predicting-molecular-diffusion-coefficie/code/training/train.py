"""
Training loop with checkpointing for MPNN and Linear Regression Baseline.
Implements T011.
"""

import argparse
import json
import logging
import time
import psutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

# Local imports from the provided API surface
from models.baseline import LinearRegressionBaseline
from models.mpnn import SingleLayerMPNN, get_device
from training.cv_strategy import ConfigurationError, get_cv_splitter
from llmxive_toolkit import paths, get_logger

# Setup logger
log = get_logger(__name__)

def load_dataset() -> pd.DataFrame:
    """Load featurized data from JSONL into a pandas DataFrame."""
    dataset_path = paths.data("processed", "featurized_data.jsonl")
    if not dataset_path.is_file():
        log.error("Featurized dataset not found at %s", dataset_path)
        raise FileNotFoundError(f"Missing input: {dataset_path}")

    records = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    return pd.DataFrame(records)

def prepare_mpnn_batch(df: pd.DataFrame) -> List[Data]:
    """Convert DataFrame rows to PyTorch Geometric Data objects."""
    graphs = []
    device = get_device()
    for _, row in df.iterrows():
        # node_features: [atomic_num, hybridization, formal_charge] -> dim=3
        # edge_index: [src, dst] pairs
        x = torch.tensor(row["node_features"], dtype=torch.float, device=device)
        edge_index = torch.tensor(row["edge_index"], dtype=torch.long, device=device).t().contiguous()
        y = torch.tensor([row["target"]], dtype=torch.float, device=device)
        graphs.append(Data(x=x, edge_index=edge_index, y=y))
    return graphs

def train_mpnn(train_df: pd.DataFrame, fold_idx: int) -> None:
    """Train the SingleLayerMPNN and save a checkpoint."""
    device = get_device()
    train_graphs = prepare_mpnn_batch(train_df)
    loader = DataLoader(train_graphs, batch_size=32, shuffle=True)

    # Node features dim = 3 (atomic number, hybridization, formal charge)
    model = SingleLayerMPNN(in_dim=3, hidden_dim=16, out_dim=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(20):  # Small number of epochs for CI feasibility
        for batch in loader:
            optimizer.zero_grad()
            out = model(batch)
            # SingleLayerMPNN returns (num_nodes, out_dim). 
            # For a simple regression task, we global-mean-pool the node embeddings.
            pooled = torch.mean(out, dim=0, keepdim=True) if batch.batch is None else torch.mean(out, dim=0)
            # Note: The SingleLayerMPNN provided in the API surface does not 
            # implement pooling. We adapt by taking the mean of the node outputs.
            # Since we are processing one graph at a time in this simplified loop
            # or a batch, we need to align target shapes.
            
            # Correcting for batching:
            if batch.batch is not None:
                # Global mean pooling
                pooled = torch.zeros(batch.num_graphs, 1, device=device)
                for i in range(batch.num_graphs):
                    mask = (batch.batch == i)
                    pooled[i] = torch.mean(out[mask], dim=0)
            else:
                pooled = torch.mean(out, dim=0, keepdim=True)

            loss = criterion(pooled, batch.y.view(-1, 1))
            loss.backward()
            optimizer.step()

    ckpt_path = paths.path("artifacts", "models", f"mpnn_fold_{fold_idx}.pt")
    torch.save(model.state_dict(), ckpt_path)
    log.info("Saved MPNN checkpoint: %s", ckpt_path)

def train_baseline(train_df: pd.DataFrame, fold_idx: int) -> None:
    """Train the LinearRegressionBaseline and save a checkpoint."""
    # The baseline.py API: fit(df, target_column="diffusion_coeff")
    # We ensure target column is present.
    baseline = LinearRegressionBaseline()
    
    # Ensure target column matches baseline expectation
    df_copy = train_df.copy()
    if "target" in df_copy.columns:
        df_copy = df_copy.rename(columns={"target": "diffusion_coeff"})
    
    baseline.fit(df_copy, target_column="diffusion_coeff")
    
    ckpt_path = paths.path("artifacts", "models", f"baseline_fold_{fold_idx}.pt")
    joblib.dump(baseline, ckpt_path)
    log.info("Saved baseline checkpoint: %s", ckpt_path)

def main() -> None:
    """Main training orchestrator."""
    start_time = time.time()
    
    # 1. Load Data
    df = load_dataset()
    n_samples = len(df)
    
    # 2. CV Strategy
    try:
        splitter = get_cv_splitter(n_samples)
    except ConfigurationError as e:
        log.error("CV Configuration Error: %s", e)
        return

    # Stratify by solvent_type if available
    y_strat = df["solvent_type"].astype('category').cat.codes if "solvent_type" in df.columns else np.zeros(n_samples)
    
    # Setup logs
    log_file = paths.data("logs", "training.log")
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"--- Training Session Started: {time.ctime()} ---\n")

    # 3. Training Loop
    fold_idx = 0
    for train_idx, val_idx in splitter.split(np.arange(n_samples), y_strat):
        fold_start = time.time()
        log.info("Processing Fold %d...", fold_idx)
        
        train_df = df.iloc[train_idx]
        
        # Train models
        train_mpnn(train_df, fold_idx)
        train_baseline(train_df, fold_idx)
        
        fold_end = time.time()
        duration = fold_end - fold_start
        
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"Fold {fold_idx}: Start={time.ctime(fold_start)}, End={time.ctime(fold_end)}, Duration={duration:.2f}s\n")
        
        fold_idx += 1

    # 4. Memory Profiling
    process = psutil.Process()
    peak_mem = process.memory_info().rss / (1024 * 1024)  # MB
    
    mem_report = {"peak_memory_mb": peak_mem}
    mem_path = paths.data("artifacts", "reports", "memory_profile.json")
    with open(mem_path, "w", encoding="utf-8") as f:
        json.dump(mem_report, f, indent=2)
    
    log.info("Training complete. Peak memory: %.2f MB", peak_mem)
    
    total_duration = time.time() - start_time
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(f"Total pipeline runtime: {total_duration:.2f}s\n")

if __name__ == "__main__":
    main()