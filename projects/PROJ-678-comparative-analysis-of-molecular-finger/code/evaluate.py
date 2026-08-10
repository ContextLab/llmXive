"""
Evaluation module for comparative analysis of molecular fingerprints.
Handles metric calculation, statistical tests, and report generation.
"""

import os
import pickle
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
from scipy import stats

# Import utilities from utils
from utils import setup_logging, init_random_seed, get_logger

# Import constants
from constants import N_FOLDS, MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"

def load_model_artifact(path: str) -> Any:
    """Load a pickled model artifact."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_split_indices(path: str) -> Dict:
    """Load split indices from JSON."""
    with open(path, 'r') as f:
        return json.load(f)

def load_fingerprint_data(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load fingerprint data from pickle."""
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data['fingerprints'], data['labels']

def load_labels(path: str) -> pd.DataFrame:
    """Load labels from CSV."""
    return pd.read_csv(path)

def calculate_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC and PR-AUC."""
    roc_auc = roc_auc_score(y_true, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    pr_auc = auc(recall, precision)
    return {"roc_auc": roc_auc, "pr_auc": pr_auc}

def evaluate_fold(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate a single fold."""
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    return calculate_metrics(y_test, y_pred_proba)

def run_evaluation(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Run evaluation on a test set."""
    return evaluate_fold(model, X_test, y_test)

def collect_fold_scores(fold_scores: List[Dict[str, Dict[str, float]]]) -> Dict[str, List[float]]:
    """Collect ROC-AUC scores from all folds."""
    morgan_scores = [f['morgan']['roc_auc'] for f in fold_scores]
    maccs_scores = [f['maccs']['roc_auc'] for f in fold_scores]
    return {"morgan": morgan_scores, "maccs": maccs_scores}

def perform_corrected_resampled_ttest(morgan_scores: List[float], maccs_scores: List[float], 
                                     n_iterations: int = 1000, random_seed: int = 42) -> Dict[str, float]:
    """
    Perform Corrected Resampled t-test (Nadeau & Bengio) on K-Fold ROC-AUC scores.
    
    Args:
        morgan_scores: List of ROC-AUC scores for Morgan fingerprints
        maccs_scores: List of ROC-AUC scores for MACCS fingerprints
        n_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with p-value and test statistics
    """
    init_random_seed(random_seed)
    
    if len(morgan_scores) != len(maccs_scores):
        raise ValueError("Score lists must have the same length")
    
    n_folds = len(morgan_scores)
    if n_folds < 2:
        raise ValueError("At least 2 folds required for t-test")
    
    # Calculate differences
    differences = np.array(morgan_scores) - np.array(maccs_scores)
    mean_diff = np.mean(differences)
    
    # Corrected Resampled t-test
    # This accounts for the overlap in training sets
    n = n_folds
    gamma = 1/n + 1/n  # n1=n2=n for K-fold
    
    # Bootstrap resampling of differences
    bootstrap_means = []
    for _ in range(n_iterations):
        resampled_diff = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(np.mean(resampled_diff))
    
    bootstrap_means = np.array(bootstrap_means)
    std_diff = np.std(bootstrap_means, ddof=1)
    
    if std_diff == 0:
        p_value = 1.0
    else:
        t_stat = mean_diff / (std_diff / np.sqrt(n))
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    
    return {
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "n_folds": n_folds
    }

def compute_bootstrap_confidence_interval(morgan_scores: List[float], maccs_scores: List[float],
                                         n_iterations: int = 1000, random_seed: int = 42,
                                         confidence_level: float = 0.95) -> Dict[str, float]:
    """
    Compute bootstrap confidence interval for the difference in performance.
    
    Args:
        morgan_scores: List of ROC-AUC scores for Morgan fingerprints
        maccs_scores: List of ROC-AUC scores for MACCS fingerprints
        n_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        confidence_level: Confidence level (default 0.95)
        
    Returns:
        Dictionary with confidence interval bounds
    """
    init_random_seed(random_seed)
    
    if len(morgan_scores) != len(maccs_scores):
        raise ValueError("Score lists must have the same length")
    
    # Calculate differences
    differences = np.array(morgan_scores) - np.array(maccs_scores)
    
    # Bootstrap resampling
    bootstrap_means = []
    n = len(differences)
    for _ in range(n_iterations):
        resampled_diff = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(np.mean(resampled_diff))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_bound = np.percentile(bootstrap_means, 100 * alpha / 2)
    upper_bound = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return {
        "lower_bound": float(lower_bound),
        "upper_bound": float(upper_bound),
        "confidence_level": confidence_level,
        "n_iterations": n_iterations
    }

def load_compounds_from_csv(path: str) -> pd.DataFrame:
    """Load compounds from filtered CSV."""
    return pd.read_csv(path)

def get_phosphorus_atoms(smiles: str) -> List[int]:
    """
    Find indices of phosphorus atoms in a molecule.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        List of atom indices for phosphorus atoms
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    
    phosphorus_indices = []
    for i, atom in enumerate(mol.GetAtoms()):
        if atom.GetAtomicNum() == 15:  # Phosphorus
            phosphorus_indices.append(i)
    
    return phosphorus_indices

def get_morgan_bits_near_phosphorus(smiles: str, phosphorus_indices: List[int], 
                                   radius: int = 2) -> List[int]:
    """
    Find Morgan fingerprint bits within radius of phosphorus atoms.
    
    Args:
        smiles: SMILES string
        phosphorus_indices: List of phosphorus atom indices
        radius: Radius for Morgan fingerprint (default 2)
        
    Returns:
        List of bit indices near phosphorus atoms
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return []
    
    # Generate Morgan fingerprint with bit info
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=MORGAN_BITS)
    bit_info = {}
    AllChem.GetMorganFingerprint(mol, radius, bitInfo=bit_info)
    
    phosphorus_bits = set()
    for p_idx in phosphorus_indices:
        if p_idx in bit_info:
            for bit_idx, (atom_idx, radius_used) in bit_info[p_idx]:
                phosphorus_bits.add(bit_idx)
    
    return list(phosphorus_bits)

def map_phosphorus_feature_importance(model: Any, smiles_list: List[str], 
                                     radius: int = 2) -> Dict[str, float]:
    """
    Map feature importance to phosphorus center bits.
    
    Args:
        model: Trained Random Forest model
        smiles_list: List of SMILES strings
        radius: Radius for Morgan fingerprint (default 2)
        
    Returns:
        Dictionary with importance statistics
    """
    if not hasattr(model, 'feature_importances_'):
        raise ValueError("Model does not have feature_importances_ attribute")
    
    importance_vector = model.feature_importances_
    total_importance = np.sum(importance_vector)
    
    phosphorus_importance = 0.0
    phosphorus_bits_count = 0
    
    for smiles in smiles_list:
        phosphorus_indices = get_phosphorus_atoms(smiles)
        if not phosphorus_indices:
            continue
        
        bits = get_morgan_bits_near_phosphorus(smiles, phosphorus_indices, radius)
        for bit in bits:
            if bit < len(importance_vector):
                phosphorus_importance += importance_vector[bit]
                phosphorus_bits_count += 1
    
    if phosphorus_bits_count > 0:
        mean_phosphorus_importance = phosphorus_importance / phosphorus_bits_count
    else:
        mean_phosphorus_importance = 0.0
    
    mean_total_importance = total_importance / len(importance_vector)
    
    return {
        "total_importance": float(total_importance),
        "phosphorus_importance": float(phosphorus_importance),
        "mean_phosphorus_importance": float(mean_phosphorus_importance),
        "mean_total_importance": float(mean_total_importance),
        "phosphorus_bits_count": phosphorus_bits_count
    }

def verify_sc_003(morgan_importance: Dict[str, float], maccs_importance: Dict[str, float]) -> Dict[str, Any]:
    """
    Verify SC-003: Check if Morgan improvement exceeds 15% of MACCS importance.
    
    Args:
        morgan_importance: Morgan importance statistics
        maccs_importance: MACCS importance statistics
        
    Returns:
        Dictionary with verification result
    """
    morgan_mean = morgan_importance.get("mean_phosphorus_importance", 0.0)
    maccs_mean = maccs_importance.get("mean_phosphorus_importance", 0.0)
    
    if maccs_mean == 0:
        difference_pct = 0.0
        threshold_met = False
    else:
        difference = morgan_mean - maccs_mean
        difference_pct = (difference / maccs_mean) * 100
        threshold_met = difference_pct >= 15.0
    
    return {
        "morgan_mean_importance": float(morgan_mean),
        "maccs_mean_importance": float(maccs_mean),
        "difference_pct": float(difference_pct),
        "threshold_met": threshold_met
    }

def write_descriptive_metrics(morgan_metrics: Dict[str, float], maccs_metrics: Dict[str, float], 
                             output_path: str) -> None:
    """
    Write descriptive metrics to JSON file.
    
    Args:
        morgan_metrics: Morgan model metrics (roc_auc, pr_auc)
        maccs_metrics: MACCS model metrics (roc_auc, pr_auc)
        output_path: Path to output JSON file
    """
    data = {
        "morgan": {
            "roc_auc": round(morgan_metrics["roc_auc"], 4),
            "pr_auc": round(morgan_metrics["pr_auc"], 4)
        },
        "maccs": {
            "roc_auc": round(maccs_metrics["roc_auc"], 4),
            "pr_auc": round(maccs_metrics["pr_auc"], 4)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logging.info(f"Descriptive metrics written to {output_path}")

def main():
    """Main entry point for evaluation."""
    logger = setup_logging()
    init_random_seed(42)
    
    # Paths
    metrics_path = PROCESSED_DIR / "final_test_metrics.json"
    output_path = PROCESSED_DIR / "test_set_descriptive.json"
    
    # Check if metrics file exists
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        logger.error("Please run T020b (Evaluate Final Model) first.")
        return
    
    # Load final test metrics
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    # Extract metrics
    morgan_metrics = metrics_data.get("morgan", {})
    maccs_metrics = metrics_data.get("maccs", {})
    
    # Validate metrics
    if not morgan_metrics or not maccs_metrics:
        logger.error("Invalid metrics format in final_test_metrics.json")
        return
    
    # Write descriptive metrics
    write_descriptive_metrics(morgan_metrics, maccs_metrics, str(output_path))
    
    logger.info("T024b completed successfully")

if __name__ == "__main__":
    main()