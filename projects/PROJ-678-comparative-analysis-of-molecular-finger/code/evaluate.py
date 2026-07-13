import os
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

from utils import setup_logging, init_random_seed, get_logger
from fingerprints import get_fingerprint_bit_info

# Initialize logger
logger = get_logger(__name__)

def load_model_artifact(path: Path) -> Any:
    """Load a trained model artifact from a pickle file."""
    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found at {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_split_indices(path: Path) -> Dict[int, Dict[str, List[int]]]:
    """Load split indices from a pickle file."""
    if not path.exists():
        raise FileNotFoundError(f"Split indices not found at {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_fingerprint_data(path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load fingerprint data, labels, and molecule IDs from a pickle file."""
    if not path.exists():
        raise FileNotFoundError(f"Fingerprint data not found at {path}")
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data['fingerprints'], data['labels'], data['mol_ids']

def load_labels(path: Path) -> pd.DataFrame:
    """Load the labels dataframe."""
    if not path.exists():
        raise FileNotFoundError(f"Labels file not found at {path}")
    return pd.read_csv(path)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, PR-AUC, and Balanced Accuracy."""
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, balanced_accuracy_score
    
    metrics = {}
    try:
        metrics['roc_auc'] = roc_auc_score(y_true, y_prob)
    except Exception as e:
        logger.warning(f"Could not calculate ROC-AUC: {e}")
        metrics['roc_auc'] = np.nan

    try:
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        metrics['pr_auc'] = auc(recall, precision)
    except Exception as e:
        logger.warning(f"Could not calculate PR-AUC: {e}")
        metrics['pr_auc'] = np.nan

    try:
        metrics['balanced_accuracy'] = balanced_accuracy_score(y_true, y_pred)
    except Exception as e:
        logger.warning(f"Could not calculate Balanced Accuracy: {e}")
        metrics['balanced_accuracy'] = np.nan

    return metrics

def evaluate_fold(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate a single model on a test set."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return calculate_metrics(y_test, y_pred, y_prob)

def run_evaluation(models: Dict[str, Any], splits: Dict[int, Dict[str, List[int]]], 
                   fingerprints: np.ndarray, labels: np.ndarray) -> Dict[int, Dict[str, Dict[str, float]]]:
    """Run evaluation for all folds and models."""
    results = {}
    for fold_idx in range(5):
        test_indices = splits[fold_idx]['test']
        y_test = labels[test_indices]
        X_test = fingerprints[test_indices]
        
        fold_results = {}
        for model_name, model in models.items():
            fold_results[model_name] = evaluate_fold(model, X_test, y_test)
        results[fold_idx] = fold_results
    return results

def bootstrap_confidence_interval(data: np.ndarray, n_bootstrap: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for a metric."""
    rng = np.random.default_rng(42)
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = rng.choice(data, size=len(data), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    lower = np.percentile(bootstrap_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(bootstrap_means, (1 + confidence) / 2 * 100)
    return lower, upper

def compute_bootstrap_ci_for_metrics(metrics_list: List[float], n_bootstrap: int = 1000) -> Dict[str, float]:
    """Compute bootstrap CI for a list of metrics."""
    arr = np.array(metrics_list)
    lower, upper = bootstrap_confidence_interval(arr, n_bootstrap)
    return {'lower': lower, 'upper': upper, 'mean': np.mean(arr)}

def map_phosphorus_feature_importance(model: Any, mol: Chem.Mol, radius: int = 2) -> Dict[str, Any]:
    """
    Map Morgan fingerprint bits to phosphorus-centered substructures.
    
    1. Identify phosphorus atom (atomic number 15).
    2. Use RDKit GetBitInfo to find bits within a defined radius of the phosphorus atom.
    3. Sum the Gini importance for these specific bits.
    4. Compare this sum to the total Gini importance.
    
    Args:
        model: Trained Random Forest model (sklearn.ensemble.RandomForestClassifier)
        mol: RDKit Mol object
        radius: Radius for Morgan fingerprint (default 2)
        
    Returns:
        Dictionary with 'p_bits_importance', 'total_importance', 'ratio', and 'bit_indices'
    """
    # 1. Identify Phosphorus atoms
    p_atoms = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetAtomicNum() == 15]
    
    if not p_atoms:
        logger.warning("No Phosphorus atoms found in molecule. Returning zero importance.")
        return {
            'p_bits_importance': 0.0,
            'total_importance': 0.0,
            'ratio': 0.0,
            'bit_indices': [],
            'p_atom_indices': []
        }
    
    # 2. Generate Morgan fingerprint and get bit info
    # We need the fingerprint used for training to map back to importances
    # Assuming the model was trained with radius=2, bits=2048
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=2048)
    
    # Get bit info: dict mapping bit_id -> list of (atom_idx, radius)
    bit_info = {}
    fp.GetBitInfo(bit_info)
    
    # 3. Find bits associated with Phosphorus atoms
    p_bit_indices = set()
    for bit_id, info_list in bit_info.items():
        for atom_idx, r in info_list:
            if atom_idx in p_atoms:
                p_bit_indices.add(bit_id)
                break # Found a P atom for this bit, move to next bit
    
    p_bit_indices = sorted(list(p_bit_indices))
    
    # 4. Extract Gini Importances from the model
    # Assuming model is a RandomForestClassifier
    if not hasattr(model, 'feature_importances_'):
        raise ValueError("Model does not have feature_importances_ attribute.")
    
    feature_importances = model.feature_importances_
    total_importance = float(np.sum(feature_importances))
    
    p_importance_sum = 0.0
    for idx in p_bit_indices:
        if idx < len(feature_importances):
            p_importance_sum += feature_importances[idx]
    
    ratio = p_importance_sum / total_importance if total_importance > 0 else 0.0
    
    return {
        'p_bits_importance': p_importance_sum,
        'total_importance': total_importance,
        'ratio': ratio,
        'bit_indices': p_bit_indices,
        'p_atom_indices': p_atoms
    }

def main():
    """Main entry point for evaluation and phosphorus mapping."""
    setup_logging()
    init_random_seed(42)
    
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed'
    models_dir = data_dir / 'models'
    splits_dir = data_dir / 'splits'
    
    # Load data
    # Assuming fingerprints and labels are combined in a single pickle from train step or separate
    # For this implementation, we assume standard paths derived from T019/T020
    # We need to load the specific model and the corresponding molecule data to map bits
    
    # This function is designed to be called per fold/model to generate specific reports
    # For a full run, we iterate through folds
    
    logger.info("Starting Phosphorus Feature Importance Mapping")
    
    # Example: Process fold 0, Morgan model
    # In a real scenario, this would be part of a loop over all folds/models
    fold_idx = 0
    model_path = models_dir / f"rf_morgan_fold_{fold_idx}.pkl"
    split_path = splits_dir / f"split_{fold_idx}.pkl"
    
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Skipping.")
        return

    model = load_model_artifact(model_path)
    splits = load_split_indices(split_path)
    
    # We need the original molecules to map bits. 
    # Typically, the filtered CSV contains SMILES.
    filtered_csv_path = data_dir / 'organophosphates_filtered.csv'
    if not filtered_csv_path.exists():
        logger.error(f"Filtered CSV not found at {filtered_csv_path}.")
        return
    
    df = pd.read_csv(filtered_csv_path)
    # Assuming 'smiles' column exists
    if 'smiles' not in df.columns:
        logger.error("SMILES column not found in filtered CSV.")
        return
    
    results = []
    
    test_indices = splits[fold_idx]['test']
    # We only need to analyze test set molecules for feature importance relative to prediction
    # Or we could analyze all. Let's analyze all for a comprehensive view per fold.
    
    logger.info(f"Analyzing {len(df)} molecules for fold {fold_idx}...")
    
    for idx in range(len(df)):
        smiles = df.loc[idx, 'smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
            
        try:
            importance_data = map_phosphorus_feature_importance(model, mol, radius=2)
            results.append({
                'mol_idx': idx,
                'smiles': smiles,
                'p_importance': importance_data['p_bits_importance'],
                'total_importance': importance_data['total_importance'],
                'ratio': importance_data['ratio']
            })
        except Exception as e:
            logger.warning(f"Error processing molecule {idx}: {e}")
            continue
    
    if results:
        result_df = pd.DataFrame(results)
        output_path = data_dir / f'phosphorus_importance_fold_{fold_idx}.csv'
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved phosphorus importance results to {output_path}")
        logger.info(f"Average P-bits importance ratio: {result_df['ratio'].mean():.4f}")
    else:
        logger.warning("No valid results to save.")

if __name__ == "__main__":
    main()