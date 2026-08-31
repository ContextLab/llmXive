import json
import logging
import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr

# Import from existing metrics module
from metrics import calculate_mae, calculate_r2, calculate_spearman_rho, calculate_deviation_index

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PARAM_LIMIT = 1_000_000
DEFAULT_SEED = 42
SENSITIVITY_SEEDS = [42, 123, 999]

def count_model_parameters(model: Any) -> int:
    """
    Count the total number of trainable parameters in a scikit-learn model.
    For ensemble models, this sums parameters of base estimators.
    """
    total_params = 0
    if hasattr(model, 'estimators_'):
        # For ensemble models (RandomForest, etc.)
        base_estimator_params = 0
        if hasattr(model.estimators_[0], 'tree_'):
            # Count nodes in trees as a proxy for parameters (simplified)
            for tree in model.estimators_:
                total_params += tree.tree_.node_count
        elif hasattr(model.estimators_[0], 'coef_'):
            for tree in model.estimators_:
                if hasattr(tree, 'coef_'):
                    total_params += np.prod(tree.coef_.shape)
        return total_params
    elif hasattr(model, 'coef_'):
        return int(np.prod(model.coef_.shape))
    elif hasattr(model, 'n_features_in_'):
        # Fallback for simple linear models
        return model.n_features_in_ + 1 # weights + bias
    return 0

def load_processed_data(data_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load processed data from CSV/Parquet in data/processed/.
    Returns DataFrame and metadata.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
    return df, {'source': str(data_path)}

def encode_smiles(smiles_list: List[str]) -> np.ndarray:
    """
    Simple molecular fingerprint encoding using RDKit (simulated here for standalone).
    In a real pipeline, this would use RDKit to generate Morgan fingerprints.
    For this implementation, we use a simple hash-based feature extraction.
    """
    # Simulated fingerprint: use character counts and simple hashes
    # In production, replace with actual RDKit fingerprint generation
    fingerprints = []
    for smi in smiles_list:
        # Simple feature extraction based on SMILES string
        features = [
            len(smi),
            smi.count('C'),
            smi.count('O'),
            smi.count('N'),
            smi.count('S'),
            smi.count('P'),
            smi.count('F'),
            smi.count('Cl'),
            smi.count('Br'),
            smi.count('('),
            smi.count(')'),
            smi.count('='),
            smi.count('#'),
        ]
        fingerprints.append(features)
    
    return np.array(fingerprints)

def train_model(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    seed: int,
    max_params: int = PARAM_LIMIT
) -> Tuple[Any, bool]:
    """
    Train a model on the provided data.
    Returns (model, is_substituted).
    If the original model exceeds max_params, a baseline model is used.
    """
    # Try to train a RandomForest (often used in chemistry)
    # Estimate parameters: n_estimators * (nodes_per_tree)
    # We'll start with a moderate size and check
    n_estimators = 100
    rf = RandomForestRegressor(
        n_estimators=n_estimators, 
        max_depth=10, 
        random_state=seed, 
        n_jobs=1
    )
    
    # Fit to estimate parameter count
    rf.fit(X_train, y_train)
    param_count = count_model_parameters(rf)
    
    is_substituted = False
    if param_count > max_params:
        logger.warning(f"Model has {param_count} parameters (> {max_params}). Substituting with Ridge regression.")
        # Substitute with a simpler model
        rf = Ridge(random_state=seed)
        rf.fit(X_train, y_train)
        is_substituted = True
        logger.info(f"Substituted model parameter count: {count_model_parameters(rf)}")
    
    return rf, is_substituted

def evaluate_model(
    model: Any, 
    X_test: np.ndarray, 
    y_test: np.ndarray, 
    reported_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """
    Evaluate the model and compute metrics.
    """
    y_pred = model.predict(X_test)
    
    mae = calculate_mae(y_test, y_pred)
    r2 = calculate_r2(y_test, y_pred)
    spearman, _ = calculate_spearman_rho(y_test, y_pred)
    
    # Calculate deviations
    dev_mae = abs(mae - reported_metrics.get('mae', mae))
    dev_r2 = abs(r2 - reported_metrics.get('r2', r2))
    dev_spearman = abs(spearman - reported_metrics.get('spearman', spearman))
    
    # Deviation Index S
    epsilon = 1e-6
    s_score = 1 - (
        (dev_mae / (abs(reported_metrics.get('mae', mae)) + epsilon)) +
        (dev_r2 / (abs(reported_metrics.get('r2', r2)) + epsilon)) +
        (dev_spearman / (abs(reported_metrics.get('spearman', spearman)) + epsilon))
    ) / 3
    
    return {
        'mae': mae,
        'r2': r2,
        'spearman': spearman,
        'deviation_index': s_score,
        'dev_mae': dev_mae,
        'dev_r2': dev_r2,
        'dev_spearman': dev_spearman,
        'predictions': y_pred.tolist(),
        'actuals': y_test.tolist()
    }

def run_sensitivity_analysis(
    X: np.ndarray, 
    y: np.ndarray, 
    seeds: List[int] = SENSITIVITY_SEEDS
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by training on multiple seeds.
    """
    results = {'seeds': seeds, 'metrics': {}}
    
    for seed in seeds:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed
        )
        
        model, _ = train_model(X_train, y_train, seed)
        y_pred = model.predict(X_test)
        
        mae = calculate_mae(y_test, y_pred)
        r2 = calculate_r2(y_test, y_pred)
        spearman, _ = calculate_spearman_rho(y_test, y_pred)
        
        results['metrics'][seed] = {
            'mae': mae,
            'r2': r2,
            'spearman': spearman
        }
    
    # Compute standard deviations
    metric_stds = {
        'mae': np.std([results['metrics'][s]['mae'] for s in seeds]),
        'r2': np.std([results['metrics'][s]['r2'] for s in seeds]),
        'spearman': np.std([results['metrics'][s]['spearman'] for s in seeds])
    }
    
    results['metric_std'] = metric_stds
    results['max_metric_std'] = max(metric_stds.values())
    
    return results

def run_reproducibility_assessment(
    paper_id: str,
    data_path: Path,
    reported_metrics: Dict[str, float],
    reported_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main function to run the reproducibility assessment for a single paper.
    """
    logger.info(f"Starting reproducibility assessment for paper: {paper_id}")
    
    # Load data
    try:
        df, metadata = load_processed_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return {
            'paper_id': paper_id,
            'status': 'failed',
            'error': str(e),
            'reason': 'Data Unavailable'
        }
    
    # Prepare features and target
    # Assuming standard columns: 'smiles', 'yield'
    if 'smiles' not in df.columns or 'yield' not in df.columns:
        logger.error("Missing required columns: smiles, yield")
        return {
            'paper_id': paper_id,
            'status': 'failed',
            'error': 'Missing required columns',
            'reason': 'Data Unavailable'
        }
    
    X_smiles = df['smiles'].tolist()
    y = df['yield'].values
    
    X = encode_smiles(X_smiles)
    
    # Split data
    seed = reported_seed if reported_seed is not None else DEFAULT_SEED
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    
    # Train model
    model, is_substituted = train_model(X_train, y_train, seed)
    
    # Evaluate
    eval_results = evaluate_model(model, X_test, y_test, reported_metrics)
    
    # Sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(X, y)
    
    # Compile result
    result = {
        'paper_id': paper_id,
        'status': 'success',
        'seed_used': seed,
        'model_substituted': is_substituted,
        'metrics': eval_results,
        'sensitivity_analysis': {
            'metric_std': sensitivity_results['metric_std'],
            'max_metric_std': sensitivity_results['max_metric_std']
        },
        'metadata': metadata
    }
    
    return result

def main():
    """
    Main entry point to run reproducibility assessment on all papers.
    Reads manifest, processes each paper, and writes results to JSON.
    """
    # Paths
    data_dir = Path("data/processed")
    manifest_path = Path("data/manifest.yaml")
    output_path = Path("artifacts/reports/repro_results.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    if not manifest_path.exists():
        logger.error("Manifest not found. Cannot proceed.")
        return
    
    import yaml
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)
    
    results = []
    
    for entry in manifest.get('papers', []):
        paper_id = entry.get('id')
        reported_metrics = entry.get('reported_metrics', {})
        reported_seed = entry.get('seed')
        data_file = entry.get('data_file')
        
        if not data_file:
            logger.warning(f"No data file specified for {paper_id}")
            continue
        
        data_path = data_dir / data_file
        
        result = run_reproducibility_assessment(
            paper_id=paper_id,
            data_path=data_path,
            reported_metrics=reported_metrics,
            reported_seed=reported_seed
        )
        results.append(result)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Reproducibility results written to {output_path}")
    
    # Return for testing
    return results

if __name__ == "__main__":
    main()
