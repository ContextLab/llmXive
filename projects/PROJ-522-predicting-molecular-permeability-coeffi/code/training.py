import os
import sys
import signal
import time
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

# Import from project modules based on API surface
from config import load_config
from models.gcn import MolecularGCN, create_model
from models.baselines import RandomForestBaseline, LinearRegressionBaseline
from models.trainer import EarlyStopping, GCNTrainer
from utils.memory_monitor import get_memory_usage_mb, check_memory_limit
from utils.logger import setup_logging, log_timeout, log_missing_data

# Custom exception for training timeouts
class TrainingTimeoutError(Exception):
    """Raised when training exceeds the configured time limit."""
    pass

# Global flag for timeout handler
_timeout_handler_active = False
_timeout_start_time = None
_timeout_duration = None

def _timeout_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    global _timeout_handler_active
    log_timeout("Training exceeded configured time limit")
    _timeout_handler_active = False
    raise TrainingTimeoutError("Training exceeded the configured time limit")

def setup_timeout_handler(duration_seconds: int):
    """
    Setup the timeout handler for the current process.
    
    Args:
        duration_seconds: Maximum duration in seconds before timeout.
    """
    global _timeout_handler_active, _timeout_start_time, _timeout_duration
    _timeout_start_time = time.time()
    _timeout_duration = duration_seconds
    _timeout_handler_active = True
    
    # Only setup signal handler on Unix-like systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(duration_seconds)
        logging.info(f"Timeout handler set for {duration_seconds} seconds")
    else:
        logging.warning("SIGALRM not available on this platform (likely Windows). "
                      "Timeout enforcement disabled. Use an external watchdog if needed.")

def cancel_timeout_handler():
    """Cancel the active timeout handler."""
    global _timeout_handler_active
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)  # Cancel the alarm
    _timeout_handler_active = False
    logging.debug("Timeout handler cancelled")

def get_murcko_scaffold(smiles: str) -> str:
    """
    Extract the Murcko scaffold from a SMILES string.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Canonical SMILES of the Murcko scaffold.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return ""
        
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logging.warning(f"Failed to extract scaffold for SMILES '{smiles}': {e}")
        return ""

def scaffold_split(
    data: pd.DataFrame,
    scaffold_column: str = 'scaffold',
    n_folds: int = 5,
    seed: int = 42
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Split data into k folds based on molecular scaffolds to prevent data leakage.
    
    Args:
        data: DataFrame containing molecules and targets.
        scaffold_column: Column name containing scaffold SMILES.
        n_folds: Number of folds for cross-validation.
        seed: Random seed for reproducibility.
        
    Returns:
        List of (train_idx, val_idx) tuples.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Group by scaffold
    scaffold_groups = data.groupby(scaffold_column).indices
    scaffold_keys = list(scaffold_groups.keys())
    random.shuffle(scaffold_keys)
    
    folds = []
    fold_size = len(scaffold_keys) // n_folds
    
    for i in range(n_folds):
        start_idx = i * fold_size
        if i == n_folds - 1:
            end_idx = len(scaffold_keys)
        else:
            end_idx = (i + 1) * fold_size
        
        val_scaffolds = scaffold_keys[start_idx:end_idx]
        train_scaffolds = [s for s in scaffold_keys if s not in val_scaffolds]
        
        val_idx = []
        train_idx = []
        
        for scaffold in val_scaffolds:
            val_idx.extend(scaffold_groups[scaffold])
        
        for scaffold in train_scaffolds:
            train_idx.extend(scaffold_groups[scaffold])
        
        folds.append((np.array(train_idx), np.array(val_idx)))
        
    return folds

def train_and_evaluate_fold(
    train_data: pd.DataFrame,
    val_data: pd.DataFrame,
    fold_idx: int,
    config: Dict,
    device: str = 'cpu'
) -> Dict:
    """
    Train and evaluate a single fold of cross-validation.
    
    Args:
        train_data: Training dataset.
        val_data: Validation dataset.
        fold_idx: Current fold index.
        config: Configuration dictionary.
        device: Device to run training on ('cpu' or 'cuda').
        
    Returns:
        Dictionary containing fold metrics and predictions.
    """
    logging.info(f"Starting fold {fold_idx}")
    
    # Setup timeout for this fold
    fold_timeout = config.get('TRAINING_TIMEOUT_SECONDS', 7200)  # Default 2 hours
    setup_timeout_handler(fold_timeout)
    
    try:
        # Prepare features and targets
        X_train = train_data[config['FEATURE_COLUMNS']].values
        y_train = train_data[config['TARGET_COLUMN']].values
        X_val = val_data[config['FEATURE_COLUMNS']].values
        y_val = val_data[config['TARGET_COLUMN']].values
        
        # Train GCN model
        gcn_model = create_model(config)
        gcn_model = gcn_model.to(device)
        
        early_stopping = EarlyStopping(patience=config.get('EARLY_STOPPING_PATIENCE', 10))
        trainer = GCNTrainer(
            model=gcn_model,
            device=device,
            lr=config.get('LEARNING_RATE', 0.001),
            weight_decay=config.get('WEIGHT_DECAY', 1e-4)
        )
        
        # Train the model (simplified for baseline implementation)
        # In a full implementation, this would use graph data
        best_model_state = trainer.train(
            X_train, y_train, X_val, y_val,
            epochs=config.get('MAX_EPOCHS', 100),
            early_stopping=early_stopping
        )
        
        # Evaluate
        metrics = trainer.evaluate(X_val, y_val)
        predictions = trainer.predict(X_val)
        
        # Train baselines for comparison
        rf_model = RandomForestBaseline()
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_val)
        rf_metrics = trainer._calculate_metrics(y_val, rf_pred)
        
        lr_model = LinearRegressionBaseline()
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_val)
        lr_metrics = trainer._calculate_metrics(y_val, lr_pred)
        
        results = {
            'fold': fold_idx,
            'gcn_metrics': metrics,
            'gcn_predictions': predictions.tolist(),
            'rf_metrics': rf_metrics,
            'rf_predictions': rf_pred.tolist(),
            'lr_metrics': lr_metrics,
            'lr_predictions': lr_pred.tolist()
        }
        
        cancel_timeout_handler()
        return results
        
    except TrainingTimeoutError:
        cancel_timeout_handler()
        logging.error(f"Fold {fold_idx} timed out after {fold_timeout} seconds")
        return {
            'fold': fold_idx,
            'error': 'TIMEOUT',
            'gcn_metrics': None,
            'rf_metrics': None,
            'lr_metrics': None
        }
    except Exception as e:
        cancel_timeout_handler()
        logging.error(f"Fold {fold_idx} failed with error: {e}")
        return {
            'fold': fold_idx,
            'error': str(e),
            'gcn_metrics': None,
            'rf_metrics': None,
            'lr_metrics': None
        }

def run_scaffold_cv(
    data: pd.DataFrame,
    n_folds: int = 5,
    config: Optional[Dict] = None
) -> List[Dict]:
    """
    Run scaffold-based cross-validation.
    
    Args:
        data: Full dataset.
        n_folds: Number of folds.
        config: Configuration dictionary.
        
    Returns:
        List of results for each fold.
    """
    if config is None:
        config = load_config()
    
    # Ensure scaffold column exists
    if 'scaffold' not in data.columns:
        logging.info("Computing Murcko scaffolds for dataset")
        data['scaffold'] = data['smiles'].apply(get_murcko_scaffold)
    
    # Split data
    folds = scaffold_split(data, n_folds=n_folds)
    
    results = []
    for i, (train_idx, val_idx) in enumerate(folds):
        train_data = data.iloc[train_idx]
        val_data = data.iloc[val_idx]
        
        fold_result = train_and_evaluate_fold(
            train_data, val_data, i, config
        )
        results.append(fold_result)
        
    return results

def main():
    """Main entry point for training pipeline with timeout enforcement."""
    # Setup logging
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    setup_logging(log_file=log_dir / 'training.log')
    
    # Load configuration
    config = load_config()
    
    # Load dataset
    data_path = Path(config.get('DATA_PATH', 'data/processed/deduplicated.csv'))
    if not data_path.exists():
        logging.error(f"Dataset not found at {data_path}")
        sys.exit(1)
        
    data = pd.read_csv(data_path)
    logging.info(f"Loaded {len(data)} samples")
    
    # Run cross-validation
    results = run_scaffold_cv(data, n_folds=5, config=config)
    
    # Save results
    output_dir = Path('data/processed')
    output_dir.mkdir(exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / 'cv_results.csv', index=False)
    
    logging.info("Training pipeline completed")

if __name__ == '__main__':
    main()