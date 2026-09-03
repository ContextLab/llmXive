import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import spearmanr

from metrics import calculate_mae, calculate_r2, calculate_spearman_rho, calculate_deviation_index

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('artifacts/logs/model_runner.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PARAMETER_THRESHOLD = 1_000_000  # 1M parameters
RANDOM_SEED = 42
DATA_DIR = Path('data/processed')
OUTPUT_DIR = Path('artifacts/reports')
OUTPUT_FILE = OUTPUT_DIR / 'repro_results.json'

def count_model_parameters(model: Any) -> int:
    """
    Count the total number of trainable parameters in a scikit-learn model.
    For RandomForest, this is approximated by n_estimators * n_features * tree_depth.
    For other models, we sum the shapes of all numpy arrays.
    """
    if hasattr(model, 'n_estimators') and hasattr(model, 'max_depth'):
        # Approximation for tree-based models
        # This is a rough estimate; exact count depends on implementation
        if hasattr(model, 'n_features_in_'):
            n_features = model.n_features_in_
        elif hasattr(model, 'n_features_'):
            n_features = model.n_features_
        else:
            n_features = 0
        depth = model.max_depth if model.max_depth is not None else 10
        return model.n_estimators * n_features * depth
    
    total_params = 0
    for attr in dir(model):
        if not attr.startswith('_'):
            val = getattr(model, attr)
            if isinstance(val, np.ndarray):
                total_params += val.size
            elif isinstance(val, list) and val and isinstance(val[0], np.ndarray):
                total_params += sum(v.size for v in val)
    return total_params

def load_processed_data(paper_id: str) -> pd.DataFrame:
    """
    Load processed data for a specific paper from data/processed/.
    Expected file format: {paper_id}_processed.csv
    """
    data_path = DATA_DIR / f"{paper_id}_processed.csv"
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def encode_smiles(smiles_list: List[str]) -> np.ndarray:
    """
    Convert a list of SMILES strings to molecular descriptors.
    Uses a fixed set of RDKit descriptors.
    """
    descriptors = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            # Handle invalid SMILES
            descriptors.append([0.0] * 10)  # Placeholder for invalid molecules
            continue
        
        desc = [
            Descriptors.MolWt(mol),
            Descriptors.MolLogP(mol),
            Descriptors.NumHDonors(mol),
            Descriptors.NumHAcceptors(mol),
            Descriptors.TPSA(mol),
            Descriptors.NumRotatableBonds(mol),
            Descriptors.NumAromaticRings(mol),
            Descriptors.FractionCSP3(mol),
            Descriptors.HeavyAtomCount(mol),
            Descriptors.RingCount(mol)
        ]
        descriptors.append(desc)
    
    return np.array(descriptors)

def train_model(X_train: np.ndarray, y_train: np.ndarray, seed: int = RANDOM_SEED) -> Any:
    """
    Train a Random Forest model.
    If the original model was specified as too large, this baseline is used.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the model and return metrics.
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    rho, _ = spearmanr(y_test, y_pred)
    
    return {
        'mae': mae,
        'r2': r2,
        'rho': rho,
        'y_pred': y_pred.tolist(),
        'y_test': y_test.tolist()
    }

def run_sensitivity_analysis(
    df: pd.DataFrame,
    reported_seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Run sensitivity analysis by training with different seeds.
    Returns the maximum standard deviation observed across metrics.
    """
    seeds = [42, 123, 999]
    if reported_seed is not None and reported_seed not in seeds:
        seeds.append(reported_seed)
    
    mae_stds = []
    r2_stds = []
    rho_stds = []
    
    # Prepare data
    smiles = df['smiles'].tolist()
    yields = df['yield'].values
    X = encode_smiles(smiles)
    
    for seed in seeds:
        X_train, X_test, y_train, y_test = train_test_split(
            X, yields, test_size=0.2, random_state=seed
        )
        model = train_model(X_train, y_train, seed=seed)
        metrics = evaluate_model(model, X_test, y_test)
        
        mae_stds.append(metrics['mae'])
        r2_stds.append(metrics['r2'])
        rho_stds.append(metrics['rho'])
    
    max_mae_std = np.std(mae_stds)
    max_r2_std = np.std(r2_stds)
    max_rho_std = np.std(rho_stds)
    
    # Return the maximum standard deviation observed across all metrics
    return {
        'max_metric_std_dev': max(max_mae_std, max_r2_std, max_rho_std)
    }

def run_reproducibility_assessment(
    paper_id: str,
    reported_metrics: Dict[str, float],
    reported_seed: Optional[int] = None,
    experimental_replicates: Optional[int] = None,
    reaction_conditions: Optional[Dict[str, Any]] = None,
    yield_std_dev: Optional[float] = None,
    parameter_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full reproducibility assessment for a single paper.
    """
    result = {
        'doi': paper_id,
        'flags': [],
        'experimental_replicates': experimental_replicates,
        'reaction_conditions': reaction_conditions,
        'yield_std_dev': yield_std_dev
    }
    
    try:
        # Load data
        df = load_processed_data(paper_id)
        
        # Check for required columns
        if 'smiles' not in df.columns or 'yield' not in df.columns:
            result['flags'].append('Data Unavailable')
            result['mae'] = None
            result['r2'] = None
            result['rho'] = None
            result['deviation_mae'] = None
            result['deviation_r2'] = None
            result['deviation_rho'] = None
            result['score_s'] = None
            result['max_metric_std_dev'] = None
            logger.warning(f"Missing required columns in {paper_id}")
            return result
        
        # Prepare features and target
        smiles = df['smiles'].tolist()
        yields = df['yield'].values
        X = encode_smiles(smiles)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, yields, test_size=0.2, random_state=RANDOM_SEED
        )
        
        # Check parameter count and decide on model
        used_baseline = False
        if parameter_count is not None and parameter_count > PARAMETER_THRESHOLD:
            logger.info(f"Paper {paper_id}: Model has {parameter_count} parameters (>1M). Using Random Forest baseline.")
            result['flags'].append('Model Substitution/Unavailable')
            used_baseline = True
        elif parameter_count is None:
            logger.warning(f"Paper {paper_id}: Parameter count unknown. Assuming baseline.")
            result['flags'].append('Model Substitution/Unavailable')
            used_baseline = True
        
        # Train model
        model = train_model(X_train, y_train, seed=RANDOM_SEED)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test)
        result['mae'] = metrics['mae']
        result['r2'] = metrics['r2']
        result['rho'] = metrics['rho']
        
        # Calculate deviations
        if reported_metrics:
            result['deviation_mae'] = abs(result['mae'] - reported_metrics.get('mae', 0))
            result['deviation_r2'] = abs(result['r2'] - reported_metrics.get('r2', 0))
            result['deviation_rho'] = abs(result['rho'] - reported_metrics.get('rho', 0))
            
            # Calculate Deviation Index (S)
            epsilon = 1e-6
            term1 = result['deviation_mae'] / (abs(reported_metrics.get('mae', 0)) + epsilon)
            term2 = result['deviation_r2'] / (abs(reported_metrics.get('r2', 0)) + epsilon)
            term3 = result['deviation_rho'] / (abs(reported_metrics.get('rho', 0)) + epsilon)
            result['score_s'] = 1 - (term1 + term2 + term3) / 3
        else:
            result['deviation_mae'] = None
            result['deviation_r2'] = None
            result['deviation_rho'] = None
            result['score_s'] = None
        
        # Sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(df, reported_seed)
        result['max_metric_std_dev'] = sensitivity_results['max_metric_std_dev']
        
        # Log substitution if applicable
        if used_baseline and 'Model Substitution/Unavailable' not in result['flags']:
            result['flags'].append('Model Substitution/Unavailable')
            logger.info(f"Recorded 'Model Substitution/Unavailable' for {paper_id}")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found for {paper_id}: {e}")
        result['flags'].append('Data Unavailable')
        result['mae'] = None
        result['r2'] = None
        result['rho'] = None
        result['deviation_mae'] = None
        result['deviation_r2'] = None
        result['deviation_rho'] = None
        result['score_s'] = None
        result['max_metric_std_dev'] = None
    except Exception as e:
        logger.error(f"Error processing {paper_id}: {e}")
        result['flags'].append('Processing Error')
        result['mae'] = None
        result['r2'] = None
        result['rho'] = None
        result['deviation_mae'] = None
        result['deviation_r2'] = None
        result['deviation_rho'] = None
        result['score_s'] = None
        result['max_metric_std_dev'] = None
    
    return result

def main():
    """
    Main entry point to run reproducibility assessment on all papers.
    Reads manifest from data/manifest.yaml (or .csv if that's what exists).
    """
    manifest_path = Path('data/manifest.yaml')
    if not manifest_path.exists():
        manifest_path = Path('data/manifest.csv')
    
    if not manifest_path.exists():
        logger.error("Manifest file not found. Please ensure data/manifest.yaml or data/manifest.csv exists.")
        return
    
    # Load manifest
    if manifest_path.suffix == '.yaml':
        import yaml
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
    else:
        import pandas as pd
        manifest_df = pd.read_csv(manifest_path)
        manifest = manifest_df.to_dict(orient='records')
    
    results = []
    
    for entry in manifest:
        paper_id = entry.get('doi') or entry.get('paper_id')
        if not paper_id:
            logger.warning("Skipping entry without DOI or paper_id")
            continue
        
        reported_metrics = entry.get('reported_metrics', {})
        reported_seed = entry.get('reported_seed')
        experimental_replicates = entry.get('experimental_replicates')
        reaction_conditions = entry.get('reaction_conditions')
        yield_std_dev = entry.get('yield_std_dev')
        
        # Estimate parameter count if available in manifest
        parameter_count = entry.get('parameter_count')
        
        logger.info(f"Processing paper: {paper_id}")
        result = run_reproducibility_assessment(
            paper_id=paper_id,
            reported_metrics=reported_metrics,
            reported_seed=reported_seed,
            experimental_replicates=experimental_replicates,
            reaction_conditions=reaction_conditions,
            yield_std_dev=yield_std_dev,
            parameter_count=parameter_count
        )
        results.append(result)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()