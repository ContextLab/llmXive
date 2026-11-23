"""
Training module for molecular permeability prediction.
Implements scaffold-split cross-validation with timeout enforcement.
"""

import os
import sys
import signal
import time
import logging
import random
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

# Local imports based on API surface
from config import load_config
from models.gcn import MolecularGCN, create_model
from models.trainer import EarlyStopping, GCNTrainer
from models.baselines import BaselineTrainer
from utils.metrics import calculate_metrics, aggregate_metrics, save_predictions
from utils.logger import setup_logging, log_timeout
from utils.memory_monitor import get_memory_usage_mb, check_memory_limit

# Constants
TIMEOUT_MESSAGE = "TIMEOUT: Training exceeded 5 minutes"
DEFAULT_TIMEOUT = 300  # 5 minutes in seconds

class TrainingTimeoutError(Exception):
    """Custom exception for training timeout."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise TrainingTimeoutError(TIMEOUT_MESSAGE)

def setup_timeout_handler(timeout_seconds: int = DEFAULT_TIMEOUT):
    """
    Setup signal alarm for timeout enforcement.
    
    Args:
        timeout_seconds: Maximum allowed execution time in seconds
    """
    if sys.platform != 'win32':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    else:
        logging.warning("Signal-based timeout not supported on Windows. Using alternative monitoring.")

def cancel_timeout_handler():
    """Cancel the timeout alarm."""
    if sys.platform != 'win32':
        signal.alarm(0)

def get_murcko_scaffold(smiles: str) -> str:
    """
    Extract Murcko scaffold from SMILES string.
    
    Args:
        smiles: Input SMILES string
        
    Returns:
        Scaffold SMILES string
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return smiles
        
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logging.warning(f"Failed to extract scaffold for {smiles}: {e}")
        return smiles

def scaffold_split(
    df: pd.DataFrame,
    smiles_col: str = 'smiles',
    n_splits: int = 5,
    seed: int = 42
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Perform scaffold-based cross-validation split.
    
    Args:
        df: Input dataframe with SMILES and target
        smiles_col: Column name for SMILES strings
        n_splits: Number of folds
        seed: Random seed for reproducibility
        
    Returns:
        List of (train_df, val_df) tuples for each fold
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # Extract scaffolds
    df = df.copy()
    df['scaffold'] = df[smiles_col].apply(get_murcko_scaffold)
    
    # Group by scaffold
    scaffold_groups = df.groupby('scaffold').indices
    scaffold_list = list(scaffold_groups.keys())
    random.shuffle(scaffold_list)
    
    # Split scaffolds into folds
    fold_size = len(scaffold_list) // n_splits
    folds = []
    
    for i in range(n_splits):
        start_idx = i * fold_size
        end_idx = (i + 1) * fold_size if i < n_splits - 1 else len(scaffold_list)
        
        val_scaffolds = set(scaffold_list[start_idx:end_idx])
        train_scaffolds = set(scaffold_list) - val_scaffolds
        
        train_df = df[df['scaffold'].isin(train_scaffolds)].drop(columns=['scaffold'])
        val_df = df[df['scaffold'].isin(val_scaffolds)].drop(columns=['scaffold'])
        
        folds.append((train_df, val_df))
    
    return folds

def smiles_to_graph(smiles: str) -> Optional[Data]:
    """
    Convert SMILES string to PyTorch Geometric Data object.
    
    Args:
        smiles: SMILES string
        
    Returns:
        PyTorch Geometric Data object or None if conversion fails
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Add hydrogens
        mol = Chem.AddHs(mol)
        
        # Node features: atom properties
        node_features = []
        for atom in mol.GetAtoms():
            feat = [
                atom.GetAtomicNum(),
                atom.GetDegree(),
                atom.GetFormalCharge(),
                atom.GetIsAromatic(),
                atom.GetTotalNumHs()
            ]
            node_features.append(feat)
        
        node_features = torch.tensor(node_features, dtype=torch.float)
        
        # Edge index
        edge_list = []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            edge_list.append([i, j])
            edge_list.append([j, i])  # Undirected graph
        
        if not edge_list:
            edge_index = torch.tensor([], dtype=torch.long).view(2, 0)
        else:
            edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        
        # Graph label (target) - will be added later
        data = Data(x=node_features, edge_index=edge_index)
        return data
    except Exception as e:
        logging.warning(f"Failed to convert SMILES to graph: {smiles}, error: {e}")
        return None

def train_and_evaluate_fold(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    fold_idx: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Train and evaluate a single fold of cross-validation.
    
    Args:
        train_df: Training dataframe
        val_df: Validation dataframe
        fold_idx: Fold index
        config: Configuration dictionary
        
    Returns:
        Dictionary containing fold results
    """
    logging.info(f"Processing fold {fold_idx + 1}")
    
    # Check memory usage
    mem_usage = get_memory_usage_mb()
    check_memory_limit(mem_usage, config.get('memory_limit_mb', 2048))
    
    # Prepare data
    train_graphs = []
    train_targets = []
    for idx, row in train_df.iterrows():
        graph = smiles_to_graph(row['smiles'])
        if graph is not None:
            graph.y = torch.tensor([row['target']], dtype=torch.float)
            train_graphs.append(graph)
            train_targets.append(row['target'])
    
    val_graphs = []
    val_targets = []
    for idx, row in val_df.iterrows():
        graph = smiles_to_graph(row['smiles'])
        if graph is not None:
            graph.y = torch.tensor([row['target']], dtype=torch.float)
            val_graphs.append(graph)
            val_targets.append(row['target'])
    
    if len(train_graphs) == 0 or len(val_graphs) == 0:
        logging.warning(f"Fold {fold_idx + 1}: Insufficient data after graph conversion")
        return {
            'fold': fold_idx,
            'train_size': 0,
            'val_size': 0,
            'r2': float('nan'),
            'mae': float('nan'),
            'rmse': float('nan'),
            'status': 'insufficient_data'
        }
    
    # Create model
    model = create_model(
        input_dim=config.get('input_dim', 5),
        hidden_dim=config.get('hidden_dim', 64),
        output_dim=1,
        num_layers=config.get('num_layers', 3)
    )
    
    # Setup trainer
    trainer = GCNTrainer(
        model=model,
        device=config.get('device', 'cpu'),
        learning_rate=config.get('learning_rate', 0.001),
        weight_decay=config.get('weight_decay', 1e-4),
        patience=config.get('early_stopping_patience', 10)
    )
    
    # Train
    train_metrics = trainer.fit(
        train_graphs,
        train_targets,
        val_graphs,
        val_targets,
        epochs=config.get('epochs', 100),
        batch_size=config.get('batch_size', 32)
    )
    
    # Evaluate
    val_predictions, val_true = trainer.predict(val_graphs)
    
    metrics = calculate_metrics(val_true, val_predictions)
    
    result = {
        'fold': fold_idx,
        'train_size': len(train_graphs),
        'val_size': len(val_graphs),
        'r2': metrics['r2'],
        'mae': metrics['mae'],
        'rmse': metrics['rmse'],
        'status': 'completed'
    }
    
    logging.info(f"Fold {fold_idx + 1} completed: R²={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}")
    
    return result

def run_scaffold_cv(
    data_path: str,
    output_path: str,
    model_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run scaffold-based cross-validation.
    
    Args:
        data_path: Path to input dataset
        output_path: Path to save predictions and metrics
        model_path: Path to save trained model
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing overall results
    """
    # Load configuration
    if config is None:
        config = load_config()
    
    # Setup logging
    setup_logging(config.get('logging_config', 'code/config/logging.yaml'))
    
    # Load data
    logging.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Validate data
    if 'smiles' not in df.columns or 'target' not in df.columns:
        raise ValueError("Input data must contain 'smiles' and 'target' columns")
    
    # Remove rows with missing values
    initial_count = len(df)
    df = df.dropna(subset=['smiles', 'target'])
    excluded_count = initial_count - len(df)
    
    if excluded_count > 0:
        logging.warning(f"Excluded {excluded_count} rows with missing values")
    
    if len(df) < 10:
        raise ValueError(f"Insufficient data after cleaning: {len(df)} rows")
    
    # Setup timeout
    timeout_seconds = config.get('timeout_graphs', DEFAULT_TIMEOUT)
    setup_timeout_handler(timeout_seconds)
    
    try:
        # Perform scaffold split
        n_splits = config.get('n_splits', 5)
        seed = config.get('random_seed', 42)
        folds = scaffold_split(df, n_splits=n_splits, seed=seed)
        
        logging.info(f"Running {n_splits}-fold scaffold cross-validation")
        
        # Train and evaluate each fold
        all_results = []
        all_predictions = []
        
        for fold_idx, (train_df, val_df) in enumerate(folds):
            fold_result = train_and_evaluate_fold(
                train_df, val_df, fold_idx, config
            )
            all_results.append(fold_result)
            
            # Collect predictions for this fold
            if fold_result['status'] == 'completed':
                # Re-run prediction to get actual values
                trainer = GCNTrainer(
                    model=create_model(
                        input_dim=config.get('input_dim', 5),
                        hidden_dim=config.get('hidden_dim', 64),
                        output_dim=1,
                        num_layers=config.get('num_layers', 3)
                    ),
                    device=config.get('device', 'cpu'),
                    learning_rate=config.get('learning_rate', 0.001),
                    weight_decay=config.get('weight_decay', 1e-4),
                    patience=config.get('early_stopping_patience', 10)
                )
                
                # Re-train for this fold to get predictions
                train_graphs = []
                train_targets = []
                for idx, row in train_df.iterrows():
                    graph = smiles_to_graph(row['smiles'])
                    if graph is not None:
                        graph.y = torch.tensor([row['target']], dtype=torch.float)
                        train_graphs.append(graph)
                        train_targets.append(row['target'])
                
                val_graphs = []
                val_targets = []
                val_smiles = []
                for idx, row in val_df.iterrows():
                    graph = smiles_to_graph(row['smiles'])
                    if graph is not None:
                        graph.y = torch.tensor([row['target']], dtype=torch.float)
                        val_graphs.append(graph)
                        val_targets.append(row['target'])
                        val_smiles.append(row['smiles'])
                
                if len(train_graphs) > 0 and len(val_graphs) > 0:
                    trainer.fit(
                        train_graphs, train_targets,
                        val_graphs, val_targets,
                        epochs=config.get('epochs', 100),
                        batch_size=config.get('batch_size', 32)
                    )
                    
                    predictions, true_vals = trainer.predict(val_graphs)
                    
                    for i, (pred, true_val, smiles) in enumerate(zip(predictions, true_vals, val_smiles)):
                        all_predictions.append({
                            'fold': fold_idx,
                            'model': 'gcn',
                            'smiles': smiles,
                            'prediction': float(pred),
                            'target': float(true_val)
                        })
        
        # Save results
        results_df = pd.DataFrame(all_results)
        predictions_df = pd.DataFrame(all_predictions)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics summary
        metrics_summary_path = str(Path(output_path).parent / 'metrics_summary.csv')
        results_df.to_csv(metrics_summary_path, index=False)
        logging.info(f"Saved metrics summary to {metrics_summary_path}")
        
        # Save predictions
        save_predictions(predictions_df, output_path)
        logging.info(f"Saved predictions to {output_path}")
        
        # Save model
        model_dir = Path(model_path).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the last trained model
        last_fold = len(folds) - 1
        if len(all_results) > 0 and all_results[last_fold]['status'] == 'completed':
            # Re-train on full data for final model
            train_graphs = []
            train_targets = []
            for idx, row in df.iterrows():
                graph = smiles_to_graph(row['smiles'])
                if graph is not None:
                    graph.y = torch.tensor([row['target']], dtype=torch.float)
                    train_graphs.append(graph)
                    train_targets.append(row['target'])
            
            final_model = create_model(
                input_dim=config.get('input_dim', 5),
                hidden_dim=config.get('hidden_dim', 64),
                output_dim=1,
                num_layers=config.get('num_layers', 3)
            )
            
            final_trainer = GCNTrainer(
                model=final_model,
                device=config.get('device', 'cpu'),
                learning_rate=config.get('learning_rate', 0.001),
                weight_decay=config.get('weight_decay', 1e-4),
                patience=config.get('early_stopping_patience', 10)
            )
            
            final_trainer.fit(
                train_graphs, train_targets,
                [], [],  # No validation for final model
                epochs=config.get('epochs', 100),
                batch_size=config.get('batch_size', 32)
            )
            
            torch.save(final_model.state_dict(), model_path)
            logging.info(f"Saved final model to {model_path}")
        
        overall_metrics = aggregate_metrics(results_df)
        
        return {
            'status': 'completed',
            'n_folds': n_splits,
            'overall_metrics': overall_metrics,
            'results_path': metrics_summary_path,
            'predictions_path': output_path,
            'model_path': model_path
        }
        
    except TrainingTimeoutError as e:
        logging.error(f"TIMEOUT: Training exceeded {timeout_seconds} seconds")
        log_timeout(f"TIMEOUT: Training exceeded {timeout_seconds} seconds")
        cancel_timeout_handler()
        
        return {
            'status': 'timeout',
            'error': str(e),
            'timeout_seconds': timeout_seconds
        }
    except Exception as e:
        logging.error(f"Training failed: {e}")
        cancel_timeout_handler()
        raise
    finally:
        cancel_timeout_handler()

def main():
    """Main entry point for training script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train molecular permeability model')
    parser.add_argument('--input', type=str, required=True, help='Path to input dataset')
    parser.add_argument('--output', type=str, required=True, help='Path to save predictions')
    parser.add_argument('--model_path', type=str, default='data/models/gcn_model.pt', help='Path to save model')
    parser.add_argument('--config', type=str, default='code/config/config.yaml', help='Path to config file')
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logging.warning(f"Could not load config from {args.config}: {e}. Using defaults.")
        config = load_config()
    
    # Run training
    result = run_scaffold_cv(
        data_path=args.input,
        output_path=args.output,
        model_path=args.model_path,
        config=config
    )
    
    # Log result
    if result['status'] == 'completed':
        logging.info(f"Training completed successfully. Metrics: {result['overall_metrics']}")
    else:
        logging.error(f"Training failed: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == '__main__':
    main()