import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import kendalltau
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Local imports matching the provided API surface
from config import TrainingConfig, DataConfig, AnalysisConfig, ensure_dirs
from models.mpnn import MPNN, create_mpnn_from_config, MPNNConfig
from utils.logger import setup_logging, get_logger
from data.descriptors import compute_gasteiger_charges, compute_topological_indices
from utils.checksum import compute_file_checksum

# SHAP dependency
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not installed. Install with 'pip install shap' for consistency analysis.")

# Constants
SEEDS = [42, 123, 456]
TOP_N_FEATURES = 5
MIN_KENDALL_TAU = 0.7
ARTIFACTS_DIR = Path("artifacts")
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
CLEANED_DATA_PATH = PROCESSED_DIR / "cleaned_sn1.csv"
HYPERPARAM_PATH = ARTIFACTS_DIR / "hyperparameter_search.csv"
REPORT_PATH = ARTIFACTS_DIR / "shap_consistency_report.md"

def load_model_config() -> Dict[str, Any]:
    """Load the best hyperparameters from T023."""
    if not HYPERPARAM_PATH.exists():
        raise FileNotFoundError(f"Hyperparameter search results not found at {HYPERPARAM_PATH}. "
                                "Run T023 first.")
    
    df = pd.read_csv(HYPERPARAM_PATH)
    # Sort by R2_val descending and take the top row
    best_row = df.sort_values(by='r2_val', ascending=False).iloc[0]
    
    config = {
        'learning_rate': float(best_row['learning_rate']),
        'hidden_dim': int(best_row['hidden_dim']),
        'dropout': float(best_row['dropout']),
        'num_layers': int(best_row.get('num_layers', 2)), # Default to 2 if not present
    }
    return config

def load_processed_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Load cleaned data and prepare features/targets."""
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {CLEANED_DATA_PATH}. "
                                "Run T016 first.")
    
    df = pd.read_csv(CLEANED_DATA_PATH)
    
    # Extract features: Gasteiger charges and topological indices
    # Assuming columns exist based on T013 implementation
    feature_cols = [col for col in df.columns if col.startswith('gasteiger') or col.startswith('topo')]
    if not feature_cols:
        raise ValueError("No descriptor columns found in dataset. Run T013 first.")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df['rate_constant'].values.astype(np.float32)
    
    return df, X, y

def prepare_mpnn_data(X: np.ndarray, y: np.ndarray, seed: int) -> Tuple[DataLoader, DataLoader]:
    """Prepare DataLoader for training."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Simple split for validation within the full set for this specific task
    # In a real scenario, we might use the split from T014, but T035 says "full cleaned dataset"
    # We will use a simple train/val split for the training loop to work
    n = len(X)
    indices = np.random.permutation(n)
    train_size = int(0.8 * n)
    
    train_idx = indices[:train_size]
    val_idx = indices[train_size:]
    
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    
    train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train).unsqueeze(1))
    val_dataset = TensorDataset(torch.tensor(X_val), torch.tensor(y_val).unsqueeze(1))
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    return train_loader, val_loader

def train_model(config: Dict[str, Any], seed: int, train_loader: DataLoader, val_loader: DataLoader) -> Tuple[MPNN, float]:
    """Train a shallow MPNN model."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Create MPNN config
    mpnn_config = MPNNConfig(
        input_dim=train_loader.dataset.tensors[0].shape[1],
        hidden_dim=config['hidden_dim'],
        num_layers=min(max(config['num_layers'], 1), 4), # Enforce 1-4 bound
        dropout=config['dropout'],
        output_dim=1
    )
    
    model = create_mpnn_from_config(mpnn_config)
    optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    criterion = nn.MSELoss()
    
    best_val_r2 = -np.inf
    best_state = None
    epochs = 50 # Shallow training for speed in consistency check
    
    for epoch in range(epochs):
        model.train()
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
        
        # Validation
        model.eval()
        val_preds = []
        val_true = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                preds = model(batch_x)
                val_preds.extend(preds.numpy().flatten())
                val_true.extend(batch_y.numpy().flatten())
        
        val_preds = np.array(val_preds)
        val_true = np.array(val_true)
        
        # Calculate R2
        ss_res = np.sum((val_true - val_preds) ** 2)
        ss_tot = np.sum((val_true - np.mean(val_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        if r2 > best_val_r2:
            best_val_r2 = r2
            best_state = model.state_dict().copy()
    
    if best_state:
        model.load_state_dict(best_state)
    
    return model, best_val_r2

def get_shap_rankings(model: MPNN, X: np.ndarray, seed: int) -> List[Tuple[str, float]]:
    """
    Run SHAP analysis to extract feature rankings.
    Since MPNN takes graph inputs, we approximate SHAP on the tabular feature vector
    by treating the model as a black box over the input features X.
    """
    if not SHAP_AVAILABLE:
        raise RuntimeError("SHAP library is required for this analysis.")
    
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    model.eval()
    X_tensor = torch.tensor(X, dtype=torch.float32)
    
    # Define a wrapper function for SHAP
    def model_wrapper(x):
        # x is numpy, convert to tensor
        with torch.no_grad():
            out = model(torch.tensor(x, dtype=torch.float32))
        return out.numpy().flatten()
    
    # Use KernelExplainer as it works with any model and input type
    # Use a subset for background data to save time
    background_size = min(100, len(X))
    background_indices = np.random.choice(len(X), background_size, replace=False)
    background_data = X[background_indices]
    
    explainer = shap.KernelExplainer(model_wrapper, background_data)
    
    # Calculate SHAP values for the whole dataset (or a sample if too large)
    # For consistency check, we might need to sample to keep it fast
    sample_size = min(500, len(X))
    sample_indices = np.random.choice(len(X), sample_size, replace=False)
    X_sample = X[sample_indices]
    
    shap_values = explainer.shap_values(X_sample, nsamples=100) # nsamples for speed
    
    # Aggregate to global feature importance (mean absolute SHAP)
    # shap_values shape: (n_samples, n_features)
    if isinstance(shap_values, list):
        shap_values = shap_values[0] # Handle case where explainer returns list
        
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Get feature names (assuming order matches columns in X)
    # We need to map indices to actual column names if we had them, 
    # but here we just return indices or generic names for ranking
    feature_names = [f"feature_{i}" for i in range(len(mean_abs_shap))]
    
    rankings = list(zip(feature_names, mean_abs_shap))
    rankings.sort(key=lambda x: x[1], reverse=True)
    
    return rankings

def compute_kendall_tau_consistency(rankings_list: List[List[Tuple[str, float]]]) -> Tuple[float, Dict[str, float]]:
    """Compute Kendall's Tau correlation between rankings."""
    if len(rankings_list) < 2:
        return 0.0, {}
    
    # Extract top N features for comparison
    top_features = set()
    for r in rankings_list:
        for feat, _ in r[:TOP_N_FEATURES]:
            top_features.add(feat)
    
    # We need to align rankings. Since features might differ slightly due to randomness in SHAP sampling,
    # we compare the rank order of the union of top features.
    # However, for a robust consistency check, we usually compare the rank of the *same* features.
    # Let's assume the feature space is fixed (X columns).
    # We compare the full ranking vectors.
    
    # Flatten rankings to rank vectors
    # Create a map from feature name to rank for each seed
    all_features = [f"feature_{i}" for i in range(len(rankings_list[0]))] # Assuming same length
    
    rank_vectors = []
    for r in rankings_list:
        feat_to_rank = {name: i for i, (name, _) in enumerate(r)}
        rank_vec = [feat_to_rank.get(f, len(all_features)) for f in all_features]
        rank_vectors.append(rank_vec)
    
    correlations = {}
    for i in range(len(rank_vectors)):
        for j in range(i + 1, len(rank_vectors)):
            tau, pval = kendalltau(rank_vectors[i], rank_vectors[j])
            key = f"seed_{SEEDS[i]}_vs_seed_{SEEDS[j]}"
            correlations[key] = tau
    
    # Average correlation
    avg_tau = np.mean(list(correlations.values()))
    
    return avg_tau, correlations

def generate_consistency_report(avg_tau: float, correlations: Dict[str, float], 
                                rankings_list: List[List[Tuple[str, float]]], 
                                r2_scores: List[float]) -> str:
    """Generate a markdown report."""
    report_lines = [
        "# SHAP Consistency Analysis Report (SC-004)",
        "",
        f"**Objective**: Verify stability of feature importance rankings across random seeds.",
        f"**Seeds Tested**: {SEEDS}",
        f"**Top N Features Analyzed**: {TOP_N_FEATURES}",
        f"**Consistency Threshold**: Kendall's Tau > {MIN_KENDALL_TAU}",
        "",
        "## Summary",
        f"- **Average Kendall's Tau**: {avg_tau:.4f}",
        f"- **Consistency Passed**: {'Yes' if avg_tau > MIN_KENDALL_TAU else 'No'}",
        "",
        "## Pairwise Correlations",
    ]
    
    for key, val in correlations.items():
        report_lines.append(f"- {key}: {val:.4f}")
    
    report_lines.append("")
    report_lines.append("## Model Performance (Validation R²)")
    for i, r2 in enumerate(r2_scores):
        report_lines.append(f"- Seed {SEEDS[i]}: {r2:.4f}")
        
    report_lines.append("")
    report_lines.append("## Top Feature Rankings by Seed")
    for i, rankings in enumerate(rankings_list):
        report_lines.append(f"### Seed {SEEDS[i]}")
        report_lines.append("| Rank | Feature | Importance |")
        report_lines.append("|---|---|---|")
        for rank, (feat, imp) in enumerate(rankings[:TOP_N_FEATURES], 1):
            report_lines.append(f"| {rank} | {feat} | {imp:.4f} |")
        report_lines.append("")
    
    return "\n".join(report_lines)

def run_consistency_analysis():
    """Main orchestration for T035."""
    logger = get_logger("consistency_analysis")
    logger.info("Starting SHAP Consistency Analysis (T035)...")
    
    ensure_dirs()
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    
    # 1. Load Config and Data
    logger.info("Loading best model configuration...")
    config = load_model_config()
    logger.info(f"Loaded config: {config}")
    
    logger.info("Loading cleaned dataset...")
    df, X, y = load_processed_data()
    logger.info(f"Dataset shape: {X.shape}")
    
    # 2. Train Models and Get Rankings
    rankings_list = []
    r2_scores = []
    
    for seed in SEEDS:
        logger.info(f"--- Processing Seed {seed} ---")
        train_loader, val_loader = prepare_mpnn_data(X, y, seed)
        
        logger.info(f"Training model for seed {seed}...")
        model, r2 = train_model(config, seed, train_loader, val_loader)
        r2_scores.append(r2)
        logger.info(f"Seed {seed} Validation R²: {r2:.4f}")
        
        logger.info(f"Calculating SHAP rankings for seed {seed}...")
        try:
            rankings = get_shap_rankings(model, X, seed)
            rankings_list.append(rankings)
            logger.info(f"Seed {seed} SHAP calculation complete.")
        except Exception as e:
            logger.error(f"SHAP calculation failed for seed {seed}: {e}")
            raise
    
    # 3. Compute Consistency
    logger.info("Computing Kendall's Tau consistency...")
    avg_tau, correlations = compute_kendall_tau_consistency(rankings_list)
    logger.info(f"Average Kendall's Tau: {avg_tau:.4f}")
    
    # 4. Generate Report
    logger.info("Generating report...")
    report_content = generate_consistency_report(avg_tau, correlations, rankings_list, r2_scores)
    
    with open(REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report saved to {REPORT_PATH}")
    
    if avg_tau <= MIN_KENDALL_TAU:
        logger.warning(f"Consistency check FAILED (Tau={avg_tau:.4f} <= {MIN_KENDALL_TAU}).")
        # Do not exit with error, as this is an analysis result, but log the warning
    else:
        logger.info(f"Consistency check PASSED (Tau={avg_tau:.4f} > {MIN_KENDALL_TAU}).")

def main():
    parser = argparse.ArgumentParser(description="Verify SHAP consistency across random seeds.")
    parser.parse_args()
    run_consistency_analysis()

if __name__ == "__main__":
    main()