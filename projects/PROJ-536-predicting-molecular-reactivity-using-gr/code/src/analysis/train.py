"""
Training module for molecular reactivity prediction.
Implements k-Fold Cross-Validation orchestration for GNN, RF, and LR models.
"""
import os
import sys
import json
import logging
import pickle
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd

# Local imports matching API surface
from src.utils.logging import get_logger, log_message
from src.utils.seeding import set_seed, get_seed_hash, DeterministicContext
from src.data.preprocess import get_burcko_scaffold, calculate_scaffold_split
from src.models.baselines import train_and_save_baselines, RandomForestBaseline, LinearRegressionBaseline
from src.models.mpnn import MPNN, train_mpnn, load_mpnn_model

# Configure logging
logger = get_logger("train")

def load_preprocessed_data(data_path: str) -> pd.DataFrame:
    """Load the preprocessed reaction dataframe."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    return pd.read_csv(data_path)

def run_gnn_fold(
    fold_idx: int,
    train_idx: List[int],
    test_idx: List[int],
    data: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: str
) -> Dict[str, Any]:
    """
    Run a single fold of GNN training and evaluation.
    Returns metrics for this fold.
    """
    logger.info(f"Running GNN Fold {fold_idx}")
    
    train_data = data.iloc[train_idx].reset_index(drop=True)
    test_data = data.iloc[test_idx].reset_index(drop=True)

    # Prepare features and targets
    # Assuming 'graph_features' column exists with pre-computed graph data or we parse on fly
    # For MPNN, we usually need the raw SMILES to build graphs dynamically or pre-built graphs
    # Based on parse.py API, we assume 'product_smiles' and 'reactants_smiles' are available
    
    X_train_smiles = train_data['product_smiles'].tolist()
    y_train = train_data['yield'].values
    X_test_smiles = test_data['product_smiles'].tolist()
    y_test = test_data['yield'].values

    # Initialize Model
    model = MPNN(
        node_dim=config['model']['node_dim'],
        edge_dim=config['model']['edge_dim'],
        hidden_dim=config['model']['hidden_dim'],
        output_dim=1,
        num_layers=config['model']['num_layers']
    )

    # Train
    metrics = train_mpnn(
        model=model,
        smiles_train=X_train_smiles,
        y_train=y_train,
        smiles_test=X_test_smiles,
        y_test=y_test,
        epochs=config['training']['max_epochs'],
        patience=config['training']['patience'],
        batch_size=config['training']['batch_size'],
        lr=config['training']['lr'],
        device='cpu', # Enforce CPU as per constraints
        output_path=os.path.join(output_dir, f"gnn_fold_{fold_idx}.pt")
    )
    
    logger.info(f"Fold {fold_idx} GNN Metrics: {metrics}")
    return metrics

def run_baselines_fold(
    fold_idx: int,
    train_idx: List[int],
    test_idx: List[int],
    data: pd.DataFrame,
    config: Dict[str, Any],
    output_dir: str
) -> Dict[str, Any]:
    """
    Run a single fold of Baseline (RF, LR) training and evaluation.
    Returns metrics for this fold.
    """
    logger.info(f"Running Baselines Fold {fold_idx}")

    train_data = data.iloc[train_idx].reset_index(drop=True)
    test_data = data.iloc[test_idx].reset_index(drop=True)

    # Prepare data for baselines
    # RF needs Morgan Fingerprints, LR needs Descriptors
    # We assume these are pre-calculated in 'fp_features' and 'descriptor_features' columns
    # or we calculate them here if not present.
    # For robustness, we check columns.
    
    if 'fp_features' not in train_data.columns:
        from src.models.baselines import prepare_fp_features
        train_data = prepare_fp_features(train_data)
        test_data = prepare_fp_features(test_data)
    
    if 'descriptor_features' not in train_data.columns:
        from src.models.baselines import prepare_descriptor_features
        train_data = prepare_descriptor_features(train_data)
        test_data = prepare_descriptor_features(test_data)

    X_train_fp = np.vstack(train_data['fp_features'].values)
    y_train = train_data['yield'].values
    X_test_fp = np.vstack(test_data['fp_features'].values)
    y_test = test_data['yield'].values

    X_train_desc = np.vstack(train_data['descriptor_features'].values)
    X_test_desc = np.vstack(test_data['descriptor_features'].values)

    # Train and save baselines
    results = train_and_save_baselines(
        X_train_fp=X_train_fp,
        y_train=y_train,
        X_test_fp=X_test_fp,
        y_test=y_test,
        X_train_desc=X_train_desc,
        X_test_desc=X_test_desc,
        output_dir=output_dir,
        fold_idx=fold_idx
    )

    logger.info(f"Fold {fold_idx} Baseline Metrics: {results}")
    return results

def orchestrate_kfold_cross_validation(
    data_path: str,
    config_path: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Main orchestration function for k-Fold Cross-Validation.
    Runs GNN, RF, and LR on the same scaffold splits.
    """
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    data = load_preprocessed_data(data_path)
    logger.info(f"Loaded {len(data)} reactions for cross-validation.")

    # Setup seeds
    seed = config.get('seeding', {}).get('seed', 42)
    set_seed(seed)
    logger.info(f"Seed set to {seed}")

    # Perform Scaffold Split for k-folds
    # We need to group by scaffold and then split into k folds
    # calculate_scaffold_split returns train/val/test indices for one split.
    # For k-fold, we need to implement a loop or use sklearn's StratifiedKFold on scaffolds.
    
    # Add scaffold column
    logger.info("Computing Murcko Scaffolds for splitting...")
    data['scaffold'] = data['product_smiles'].apply(get_burcko_scaffold)
    
    # Drop rows with invalid scaffolds (None)
    valid_mask = data['scaffold'].notna()
    data_valid = data[valid_mask].reset_index(drop=True)
    logger.info(f"Retained {len(data_valid)} reactions with valid scaffolds.")

    # K-Fold Logic
    k = config['training'].get('k_folds', 5)
    
    # Simple K-Fold on scaffold groups
    # Group by scaffold, then shuffle groups, then assign to folds
    scaffolds = data_valid['scaffold'].unique()
    np.random.shuffle(scaffolds)
    
    fold_indices = {i: {'train': [], 'test': []} for i in range(k)}
    
    # Assign scaffolds to folds
    scaffold_to_fold = {}
    for i, scaffold in enumerate(scaffolds):
        fold_idx = i % k
        scaffold_to_fold[scaffold] = fold_idx

    # Assign rows to folds based on scaffold
    for idx, row in data_valid.iterrows():
        fold_idx = scaffold_to_fold[row['scaffold']]
        # We need to distinguish train vs test per fold
        # In k-fold, fold i is test, others are train
        # But we need to store the global indices
        fold_indices[fold_idx]['test'].append(idx)
    
    # Now populate train indices for each fold
    all_indices = data_valid.index.tolist()
    for i in range(k):
        test_set = set(fold_indices[i]['test'])
        fold_indices[i]['train'] = [idx for idx in all_indices if idx not in test_set]

    # Run training for each fold
    all_results = {
        'gnn': [],
        'rf': [],
        'lr': []
    }

    for i in range(k):
        logger.info(f"--- Starting Fold {i+1}/{k} ---")
        train_idx = fold_indices[i]['train']
        test_idx = fold_indices[i]['test']
        
        # Run GNN
        gnn_metrics = run_gnn_fold(i, train_idx, test_idx, data_valid, config, output_dir)
        all_results['gnn'].append(gnn_metrics)
        
        # Run Baselines
        baseline_metrics = run_baselines_fold(i, train_idx, test_idx, data_valid, config, output_dir)
        # baseline_metrics likely contains 'rf' and 'lr' keys
        if 'rf' in baseline_metrics:
            all_results['rf'].append(baseline_metrics['rf'])
        if 'lr' in baseline_metrics:
            all_results['lr'].append(baseline_metrics['lr'])

    # Save aggregated results
    results_path = os.path.join(output_dir, "kfold_results.json")
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"Cross-validation complete. Results saved to {results_path}")
    return all_results

def main():
    """Entry point for training script."""
    # Default paths
    data_path = os.getenv('DATA_PATH', 'data/preprocessed_reactions.csv')
    config_path = os.getenv('CONFIG_PATH', 'src/config/defaults.yaml') # Assuming yaml or json
    output_dir = os.getenv('OUTPUT_DIR', 'results/training')
    
    # If config is yaml, we might need to load it differently, but json is standard for this flow
    # Adjusting to match typical project structure if config is yaml
    if not os.path.exists(config_path):
        config_path = 'code/src/config/defaults.json' # Fallback or specific path
    
    # If config is yaml, we need to load it. 
    # For now, assuming JSON for simplicity in this script or converting.
    # Let's assume the config is passed as JSON or we load YAML if available.
    import yaml
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        # Save as JSON for the function if needed, or just pass dict
        config_dict = config
    else:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

    results = orchestrate_kfold_cross_validation(
        data_path=data_path,
        config_path=config_path, # Passing path to reload inside function or use dict
        output_dir=output_dir
    )
    
    print("Training completed successfully.")

if __name__ == "__main__":
    main()