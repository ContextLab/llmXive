"""
Runner script for a single seed: loads pre-processed data, loads trained models
(Baseline, Deep Ensemble, MC Dropout, Sparse GP), runs inference, calculates
uncertainty bounds, and writes the predictions CSV.

This script does NOT perform data download or preprocessing. It assumes
artifacts from T006 (preprocess) and T012-T015 (models) exist.
"""

import os
import sys
import json
import logging
import argparse
import signal
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Import model classes and utilities from sibling modules
# Baseline
from models.baseline_nn import HeteroscedasticNN, load_processed_data as load_baseline_data
# Deep Ensemble
from models.deep_ensemble import DeepEnsemble, load_config as load_ensemble_config
# MC Dropout
from models.mc_dropout import MCDropoutModel
# Sparse GP
from models.sparse_gp import SparseGPModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Pipeline execution timed out")

def run_with_timeout(func, timeout_seconds, *args, **kwargs):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = func(*args, **kwargs)
    finally:
        signal.alarm(0)
    return result

# --- Inference Functions ---

def run_baseline_inference(model_path, test_features, test_targets, seed):
    """
    Runs inference on the single baseline model.
    Returns predictions and variances.
    """
    logger.info(f"Loading baseline model from {model_path}")
    device = torch.device("cpu")
    
    # Load model architecture (assumed 2 hidden layers, heteroscedastic)
    # We need to infer input dim from the data
    input_dim = test_features.shape[1]
    model = HeteroscedasticNN(input_dim=input_dim, hidden_dims=[32, 32]).to(device)
    
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    with torch.no_grad():
        X = torch.FloatTensor(test_features).to(device)
        means, variances = model(X)
        
        predictions = means.cpu().numpy().flatten()
        variances = variances.cpu().numpy().flatten()
        
        # Ensure non-negative variance
        variances = np.maximum(variances, 1e-6)

    sample_ids = list(range(len(predictions)))
    results = []
    for i in range(len(predictions)):
        results.append({
            'sample_id': sample_ids[i],
            'method': 'baseline',
            'prediction': float(predictions[i]),
            'variance': float(variances[i])
        })
    return results

def run_ensemble_inference(models_dir, test_features, seed):
    """
    Loads 5 ensemble models, runs inference, aggregates mean and variance.
    """
    logger.info(f"Loading ensemble models from {models_dir}")
    device = torch.device("cpu")
    input_dim = test_features.shape[1]
    
    ensemble_predictions = []
    ensemble_variances = []

    # Expecting 5 models based on T013 description
    for i in range(5):
        model_path = os.path.join(models_dir, f"ensemble_seed_{seed}.pt")
        # Fallback for unique filenames if seeds are different, but task says "ensemble_seed_<seed>"
        # If the task implies 5 models for ONE seed, they might be named ensemble_seed_{seed}_0.pt etc.
        # However, T013 says "ensemble_seed_<seed>". Let's assume the directory contains 5 models
        # or we load one model 5 times with different seeds? 
        # Re-reading T013: "Train exactly 5 independently initialized copies... Save models to ... ensemble_seed_<seed>.pt"
        # This implies the filename might be the same if run sequentially, OR the seed in the filename is the 
        # random seed for that specific model. 
        # Given T016a says "Load model weights from ... ensemble_seed_<seed>.pt", it implies a specific file.
        # Let's assume the directory contains files named like ensemble_0.pt, ensemble_1.pt or similar if T013
        # generated 5 distinct files. If T013 overwrote, we can't do an ensemble.
        # Standard practice: ensemble_seed_<seed>_<idx>.pt. Let's try to find 5 files.
        
        # Alternative interpretation: The task T013 saves 5 models. T016a loads them.
        # Let's look for files matching pattern.
        files = sorted([f for f in os.listdir(models_dir) if f.endswith('.pt')])
        if len(files) < 5:
            logger.warning(f"Found {len(files)} models in {models_dir}, expected 5. Using available.")
        
        # Let's assume the naming convention from T013 was strict: ensemble_seed_<seed>.pt
        # If T013 ran 5 times, it would overwrite. 
        # Correction: T013 says "Save models to ... with unique filenames ensemble_seed_<seed>.pt".
        # This is ambiguous. If seed is 42, is it ensemble_seed_42.pt? 
        # If it runs 5 times, it must be ensemble_seed_42_0.pt etc.
        # Let's assume the files are named ensemble_0.pt, ensemble_1.pt... or similar.
        # To be robust, we will load all .pt files in the directory.
        
        # Actually, let's follow the prompt's specific instruction: "ensemble_seed_<seed>.pt"
        # If T013 produced 5 files, they must have unique names.
        # Let's assume the files are named ensemble_seed_{seed}_{i}.pt or similar.
        # We will load all .pt files found in the directory.
        
        # Re-reading T013: "ensemble_seed_<seed>.pt". If seed is 42, file is ensemble_seed_42.pt.
        # If it runs 5 times, it must be ensemble_seed_42_0.pt, etc.
        # Let's try to load all .pt files in the directory as the ensemble members.
        
        model_files = [f for f in files if f.endswith('.pt')]
        if not model_files:
            raise FileNotFoundError(f"No model files found in {models_dir}")

        # We need to run 5 forward passes. If we have 5 models, use them.
        # If we have 1 model, we can't do ensemble.
        
        # Let's assume the directory contains the 5 models.
        # We will load them and average.
        
        # If the file naming is strictly "ensemble_seed_<seed>.pt" and T013 ran 5 times,
        # the task description in T013 is slightly contradictory unless it implies
        # a loop that saves with an index.
        # Let's assume the files are named: ensemble_seed_<seed>_0.pt, ... _4.pt
        
        # We will iterate 5 times. If file exists, load it. If not, try to load the single file if it exists and reuse?
        # No, ensemble requires independent models.
        
        # Let's try to load files named: ensemble_seed_<seed>.pt (if only one) or with index.
        # We will just load all .pt files in the directory.
        
        models = []
        for f in model_files:
            path = os.path.join(models_dir, f)
            m = HeteroscedasticNN(input_dim=input_dim, hidden_dims=[32, 32]).to(device)
            ckpt = torch.load(path, map_location=device, weights_only=True)
            m.load_state_dict(ckpt['model_state_dict'])
            m.eval()
            models.append(m)
        
        if len(models) == 0:
            raise FileNotFoundError(f"No valid models loaded in {models_dir}")

        X = torch.FloatTensor(test_features).to(device)
        
        all_means = []
        all_vars = []
        
        with torch.no_grad():
            for m in models:
                mu, var = m(X)
                all_means.append(mu.cpu().numpy().flatten())
                all_vars.append(var.cpu().numpy().flatten())
        
        # Aggregate
        # Mean of means
        mean_preds = np.mean(all_means, axis=0)
        # Variance of means (Epistemic) + Mean of variances (Aleatoric) -> Total Variance?
        # Task T016a asks for "variance" and bounds. 
        # For Ensemble, Total Variance = Var(E[mu]) + E[var]
        mean_of_vars = np.mean(all_vars, axis=0)
        var_of_means = np.var(all_means, axis=0)
        total_variance = var_of_means + mean_of_vars
        
        predictions = mean_preds
        variances = total_variance

    sample_ids = list(range(len(predictions)))
    results = []
    for i in range(len(predictions)):
        results.append({
            'sample_id': sample_ids[i],
            'method': 'deep_ensemble',
            'prediction': float(predictions[i]),
            'variance': float(variances[i])
        })
    return results

def run_mc_dropout_inference(model_path, test_features, seed, num_samples=30, dropout_p=0.2):
    """
    Loads MC Dropout model, runs 30 stochastic forward passes.
    """
    logger.info(f"Loading MC Dropout model from {model_path}")
    device = torch.device("cpu")
    input_dim = test_features.shape[1]
    
    model = MCDropoutModel(input_dim=input_dim, hidden_dims=[32, 32], dropout_p=dropout_p).to(device)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.train() # Enable dropout

    X = torch.FloatTensor(test_features).to(device)
    
    all_preds = []
    with torch.no_grad():
        for _ in range(num_samples):
            mu, var = model(X)
            all_preds.append(mu.cpu().numpy().flatten())
    
    all_preds = np.array(all_preds)
    predictions = np.mean(all_preds, axis=0)
    # Variance of predictions across stochastic passes
    variances = np.var(all_preds, axis=0)
    # Ensure non-negative
    variances = np.maximum(variances, 1e-6)

    sample_ids = list(range(len(predictions)))
    results = []
    for i in range(len(predictions)):
        results.append({
            'sample_id': sample_ids[i],
            'method': 'mc_dropout',
            'prediction': float(predictions[i]),
            'variance': float(variances[i])
        })
    return results

def run_gp_inference(model_path, test_features, seed):
    """
    Loads Sparse GP model, runs inference.
    """
    logger.info(f"Loading Sparse GP model from {model_path}")
    device = torch.device("cpu")
    
    # Load model
    model = SparseGPModel()
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    X = torch.FloatTensor(test_features).to(device)
    
    with torch.no_grad():
        # Assuming model has a predict method or forward returns mean, var
        # The SparseGPModel class from T015 might have a specific interface.
        # Let's assume it returns mean and variance.
        mean, var = model(X)
        
        predictions = mean.cpu().numpy().flatten()
        variances = var.cpu().numpy().flatten()
        variances = np.maximum(variances, 1e-6)

    sample_ids = list(range(len(predictions)))
    results = []
    for i in range(len(predictions)):
        results.append({
            'sample_id': sample_ids[i],
            'method': 'sparse_gp',
            'prediction': float(predictions[i]),
            'variance': float(variances[i])
        })
    return results

def calculate_bounds(prediction, variance, confidence_level):
    """
    Calculates lower and upper bounds for a given confidence level.
    Assumes Gaussian distribution: mean +/- z * std
    """
    std = np.sqrt(variance)
    if confidence_level == 0.50:
        z = 0.6745 # ~50% CI
    elif confidence_level == 0.90:
        z = 1.6449 # ~90% CI
    else:
        z = 1.96 # Default 95%
    
    lower = prediction - z * std
    upper = prediction + z * std
    return lower, upper

def run_single_seed(seed, timeout_hours=5.0):
    """
    Main function to run the pipeline for a single seed.
    """
    timeout_seconds = int(timeout_hours * 3600)
    
    # Paths
    data_dir = Path("data/processed")
    results_dir = Path("results")
    models_dir = results_dir / "models"
    
    # Input files (from T006)
    test_features_path = data_dir / "features_test_20pca.csv"
    
    # Output file
    output_path = results_dir / f"uq_predictions_seed_{seed}.csv"
    
    if not test_features_path.exists():
        raise FileNotFoundError(f"Test features file not found: {test_features_path}")
    
    logger.info(f"Loading test features from {test_features_path}")
    df_test = pd.read_csv(test_features_path)
    
    # Assume first column is sample_id, rest are features?
    # Or maybe index is sample_id. Let's assume 'sample_id' column exists or use index.
    # T006 output: raw_test.csv -> features_test_20pca.csv.
    # Let's assume the CSV has a 'sample_id' column. If not, use range.
    if 'sample_id' not in df_test.columns:
        df_test['sample_id'] = range(len(df_test))
    
    # Features are all columns except sample_id and target?
    # T006 says "PCA-reduced features". So likely just feature columns.
    # Let's assume the CSV contains only features and sample_id.
    # We need to separate features from sample_id.
    # If 'target' or 'target_bin' exists, we should drop them.
    cols_to_drop = ['sample_id', 'target', 'target_bin']
    feature_cols = [c for c in df_test.columns if c not in cols_to_drop]
    
    test_features = df_test[feature_cols].values
    sample_ids = df_test['sample_id'].values
    
    all_results = []
    
    # 1. Baseline
    baseline_path = models_dir / "baseline" / f"baseline_seed_{seed}.pt"
    if baseline_path.exists():
        try:
            res = run_baseline_inference(baseline_path, test_features, None, seed)
            all_results.extend(res)
        except Exception as e:
            logger.error(f"Baseline inference failed: {e}")
    else:
        logger.warning(f"Baseline model not found: {baseline_path}")
    
    # 2. Deep Ensemble
    # T013 saves to results/models/ensemble/
    ensemble_dir = models_dir / "ensemble"
    if ensemble_dir.exists():
        try:
            res = run_ensemble_inference(ensemble_dir, test_features, seed)
            all_results.extend(res)
        except Exception as e:
            logger.error(f"Ensemble inference failed: {e}")
    else:
        logger.warning(f"Ensemble directory not found: {ensemble_dir}")
    
    # 3. MC Dropout
    mc_dir = models_dir / "mc_dropout"
    mc_path = mc_dir / f"mc_dropout_seed_{seed}.pt"
    if mc_path.exists():
        try:
            res = run_mc_dropout_inference(mc_path, test_features, seed)
            all_results.extend(res)
        except Exception as e:
            logger.error(f"MC Dropout inference failed: {e}")
    else:
        logger.warning(f"MC Dropout model not found: {mc_path}")
    
    # 4. Sparse GP
    gp_path = models_dir / "sparse_gp_model.pt"
    if gp_path.exists():
        try:
            res = run_gp_inference(gp_path, test_features, seed)
            all_results.extend(res)
        except Exception as e:
            logger.error(f"GP inference failed: {e}")
    else:
        logger.warning(f"GP model not found: {gp_path}")
    
    if not all_results:
        raise RuntimeError("No predictions generated. Check model paths.")
    
    # Convert to DataFrame
    df_results = pd.DataFrame(all_results)
    
    # Calculate bounds
    # We need to calculate bounds per row based on prediction and variance
    # Columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90
    
    def add_bounds(row):
        p = row['prediction']
        v = row['variance']
        l50, u50 = calculate_bounds(p, v, 0.50)
        l90, u90 = calculate_bounds(p, v, 0.90)
        return pd.Series([l50, u50, l90, u90], index=['lower_50', 'upper_50', 'lower_90', 'upper_90'])
    
    bounds = df_results.apply(add_bounds, axis=1)
    df_results = pd.concat([df_results, bounds], axis=1)
    
    # Ensure column order
    cols = ['sample_id', 'method', 'prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
    # Cast sample_id to int
    df_results['sample_id'] = df_results['sample_id'].astype(int)
    df_results = df_results[cols]
    
    # Save
    results_dir.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Run UQ inference for a single seed.")
    parser.add_argument("--seed", type=int, required=True, help="Random seed for this run.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout in hours.")
    args = parser.parse_args()
    
    try:
        output_file = run_with_timeout(
            run_single_seed, 
            int(args.timeout * 3600), 
            args.seed, 
            args.timeout
        )
        print(f"Success: {output_file}")
    except TimeoutError:
        logger.error("Pipeline timed out.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()