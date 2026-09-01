"""
Single-seed runner for UQ pipeline.
Loads data, trains baseline, runs UQ inference (Deep Ensemble, MC Dropout, Sparse GP),
and outputs predictions with uncertainty intervals.
"""
import os
import sys
import json
import logging
import argparse
import signal
import time
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np
import torch

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models.baseline_nn import train_model as train_baseline, HeteroscedasticNN, load_config as load_baseline_config
from models.deep_ensemble import train_ensemble, DeepEnsemble, load_config as load_ensemble_config
from models.mc_dropout import train_mc_dropout, MCDropoutModel, load_config as load_mc_config
from models.sparse_gp import train_sparse_gp, SparseGPModel, load_config as load_gp_config
from data.preprocess import load_config as load_data_config, load_data
from utils.logging_config import setup_logging, log_metric

# Configure logging
logger = setup_logging()

# Timeout handler
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Seed execution timed out")

def run_single_seed(seed: int, timeout_hours: float = 2.0) -> pd.DataFrame:
    """
    Run the full pipeline for a single seed.
    
    Args:
        seed: Random seed for reproducibility
        timeout_hours: Maximum allowed runtime in hours
        
    Returns:
        DataFrame with predictions and uncertainty intervals
    """
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(timeout_hours * 3600))
    
    try:
        logger.info(f"Starting seed {seed}")
        start_time = time.time()
        
        # Set global seeds
        torch.manual_seed(seed)
        np.random.seed(seed)
        
        # Load configurations
        data_config = load_data_config()
        baseline_config = load_baseline_config()
        ensemble_config = load_ensemble_config()
        mc_config = load_mc_config()
        gp_config = load_gp_config()
        
        # Update configs with seed
        baseline_config['seed'] = seed
        ensemble_config['seed'] = seed
        mc_config['seed'] = seed
        gp_config['seed'] = seed
        
        # Load processed data
        logger.info("Loading processed data...")
        train_df = pd.read_csv('data/processed/features_train_20pca.csv')
        val_df = pd.read_csv('data/processed/features_val_20pca.csv')
        test_df = pd.read_csv('data/processed/features_test_20pca.csv')
        
        # Extract features and targets
        feature_cols = [col for col in train_df.columns if col not in ['sample_id', 'formation_energy']]
        X_train = train_df[feature_cols].values
        y_train = train_df['formation_energy'].values
        X_val = val_df[feature_cols].values
        y_val = val_df['formation_energy'].values
        X_test = test_df[feature_cols].values
        y_test = test_df['formation_energy'].values
        sample_ids = test_df['sample_id'].values
        
        # Train Baseline Model
        logger.info(f"Training baseline model with seed {seed}...")
        baseline_model = train_model(X_train, y_train, X_val, y_val, baseline_config)
        
        # Train Deep Ensemble
        logger.info(f"Training deep ensemble with seed {seed}...")
        ensemble_model = train_ensemble(X_train, y_train, X_val, y_val, ensemble_config)
        
        # Train MC Dropout Model
        logger.info(f"Training MC Dropout model with seed {seed}...")
        mc_model = train_mc_dropout(X_train, y_train, X_val, y_val, mc_config)
        
        # Train Sparse GP Model
        logger.info(f"Training Sparse GP model with seed {seed}...")
        gp_model = train_sparse_gp(X_train, y_train, X_val, y_val, gp_config)
        
        # Run Inference
        logger.info("Running inference...")
        predictions = []
        
        # Baseline predictions (use variance from heteroscedastic head)
        baseline_preds, baseline_vars = run_baseline_inference(baseline_model, X_test)
        for i, (pred, var) in enumerate(zip(baseline_preds, baseline_vars)):
            predictions.append({
                'sample_id': int(sample_ids[i]),
                'method': 'baseline',
                'prediction': float(pred),
                'variance': float(var),
                'lower_50': float(pred - 0.674 * np.sqrt(var)),
                'upper_50': float(pred + 0.674 * np.sqrt(var)),
                'lower_90': float(pred - 1.645 * np.sqrt(var)),
                'upper_90': float(pred + 1.645 * np.sqrt(var))
            })
        
        # Deep Ensemble predictions
        ens_preds, ens_vars = run_ensemble_inference(ensemble_model, X_test)
        for i, (pred, var) in enumerate(zip(ens_preds, ens_vars)):
            predictions.append({
                'sample_id': int(sample_ids[i]),
                'method': 'deep_ensemble',
                'prediction': float(pred),
                'variance': float(var),
                'lower_50': float(pred - 0.674 * np.sqrt(var)),
                'upper_50': float(pred + 0.674 * np.sqrt(var)),
                'lower_90': float(pred - 1.645 * np.sqrt(var)),
                'upper_90': float(pred + 1.645 * np.sqrt(var))
            })
        
        # MC Dropout predictions
        mc_preds, mc_vars = run_mc_dropout_inference(mc_model, X_test)
        for i, (pred, var) in enumerate(zip(mc_preds, mc_vars)):
            predictions.append({
                'sample_id': int(sample_ids[i]),
                'method': 'mc_dropout',
                'prediction': float(pred),
                'variance': float(var),
                'lower_50': float(pred - 0.674 * np.sqrt(var)),
                'upper_50': float(pred + 0.674 * np.sqrt(var)),
                'lower_90': float(pred - 1.645 * np.sqrt(var)),
                'upper_90': float(pred + 1.645 * np.sqrt(var))
            })
        
        # Sparse GP predictions
        gp_preds, gp_vars = run_gp_inference(gp_model, X_test)
        for i, (pred, var) in enumerate(zip(gp_preds, gp_vars)):
            predictions.append({
                'sample_id': int(sample_ids[i]),
                'method': 'sparse_gp',
                'prediction': float(pred),
                'variance': float(var),
                'lower_50': float(pred - 0.674 * np.sqrt(var)),
                'upper_50': float(pred + 0.674 * np.sqrt(var)),
                'lower_90': float(pred - 1.645 * np.sqrt(var)),
                'upper_90': float(pred + 1.645 * np.sqrt(var))
            })
        
        # Create DataFrame
        result_df = pd.DataFrame(predictions)
        
        # Ensure column order
        result_df = result_df[['sample_id', 'method', 'prediction', 'variance', 
                               'lower_50', 'upper_50', 'lower_90', 'upper_90']]
        
        # Save output
        output_path = f'results/uq_predictions_seed_{seed}.csv'
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved predictions to {output_path}")
        
        elapsed = time.time() - start_time
        logger.info(f"Seed {seed} completed in {elapsed:.2f} seconds")
        
        return result_df
        
    except TimeoutError:
        logger.error(f"Seed {seed} timed out after {timeout_hours} hours")
        raise
    finally:
        signal.alarm(0)  # Cancel the alarm

def run_baseline_inference(model, X):
    """Run inference on baseline heteroscedastic model."""
    model.eval()
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X)
        mean, log_var = model(X_tensor)
        return mean.numpy(), np.exp(log_var.numpy())

def run_ensemble_inference(ensemble, X):
    """Run inference on deep ensemble."""
    predictions = []
    for model in ensemble.models:
        model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            mean, log_var = model(X_tensor)
            predictions.append((mean.numpy(), np.exp(log_var.numpy())))
    
    # Aggregate predictions
    all_means = np.array([p[0] for p in predictions])
    all_vars = np.array([p[1] for p in predictions])
    
    # Mean of means is the prediction
    final_means = np.mean(all_means, axis=0)
    
    # Total variance = mean of variances + variance of means
    final_vars = np.mean(all_vars, axis=0) + np.var(all_means, axis=0)
    
    return final_means, final_vars

def run_mc_dropout_inference(model, X, n_samples=50):
    """Run MC Dropout inference."""
    model.eval()
    predictions = []
    
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X)
        for _ in range(n_samples):
            mean, log_var = model(X_tensor)
            predictions.append((mean.numpy(), np.exp(log_var.numpy())))
    
    all_means = np.array([p[0] for p in predictions])
    all_vars = np.array([p[1] for p in predictions])
    
    final_means = np.mean(all_means, axis=0)
    final_vars = np.mean(all_vars, axis=0) + np.var(all_means, axis=0)
    
    return final_means, final_vars

def run_gp_inference(model, X):
    """Run Sparse GP inference."""
    model.eval()
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X)
        # For GP, we get mean and variance directly
        predictive_mean, predictive_var = model(X_tensor)
        return predictive_mean.numpy(), predictive_var.numpy()

def main():
    parser = argparse.ArgumentParser(description='Run single seed UQ pipeline')
    parser.add_argument('--seed', type=int, required=True, help='Random seed')
    parser.add_argument('--timeout', type=float, default=2.0, help='Timeout in hours')
    args = parser.parse_args()
    
    run_single_seed(args.seed, args.timeout)

if __name__ == '__main__':
    main()