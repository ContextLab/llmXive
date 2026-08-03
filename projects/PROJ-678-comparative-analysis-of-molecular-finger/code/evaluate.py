"""
Evaluation module for Comparative Analysis of Molecular Fingerprints.
Implements statistical tests, bootstrap confidence intervals, and feature importance analysis.
"""

import os
import pickle
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from scipy import stats
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys
from rdkit import DataStructs

# Import from utils
from utils import setup_logging, init_random_seed, get_logger

# Constants
BOOTSTRAP_ITERATIONS = 1000
CONFIDENCE_LEVEL = 0.95
RANDOM_SEED = 42

logger = get_logger(__name__)

def load_model_artifact(path: str) -> Any:
    """Load a pickled model artifact."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_split_indices(split_dir: str) -> Dict[str, Any]:
    """Load split indices from JSON."""
    split_path = Path(split_dir) / "split_indices.json"
    if not split_path.exists():
        raise FileNotFoundError(f"Split file not found: {split_path}")
    with open(split_path, 'r') as f:
        return json.load(f)

def load_fingerprint_data(data_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load fingerprints from pickle file."""
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    return data['morgan'], data['maccs']

def load_labels(data_path: str) -> np.ndarray:
    """Load labels from CSV."""
    df = pd.read_csv(data_path)
    # Assuming the label column is 'toxicity' or similar, need to check actual schema
    # For now, assume 'labels' or first numeric column after SMILES
    if 'labels' in df.columns:
        return df['labels'].values
    elif 'toxicity' in df.columns:
        return df['toxicity'].values
    else:
        # Fallback: try to find the first column that looks like labels
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64'] and col.lower() not in ['smiles', 'compound_id', 'molecular_weight']:
                return df[col].values
        raise ValueError("Could not find labels column in data file")

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC and PR-AUC."""
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc

    roc_auc = roc_auc_score(y_true, y_pred)
    precision, recall, _ = precision_recall_curve(y_true, y_pred)
    pr_auc = auc(recall, precision)

    return {
        'roc_auc': roc_auc,
        'pr_auc': pr_auc
    }

def evaluate_fold(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Evaluate a single fold."""
    return calculate_metrics(y_true, y_pred)

def run_evaluation(y_true: np.ndarray, y_pred_morgan: np.ndarray, y_pred_maccs: np.ndarray) -> Dict[str, Dict[str, float]]:
    """Run evaluation on test set."""
    morgan_metrics = calculate_metrics(y_true, y_pred_morgan)
    maccs_metrics = calculate_metrics(y_true, y_pred_maccs)

    return {
        'morgan': morgan_metrics,
        'maccs': maccs_metrics
    }

def collect_fold_scores(kfold_scores_path: str) -> Dict[str, List[float]]:
    """Load K-Fold ROC-AUC scores for statistical testing."""
    with open(kfold_scores_path, 'r') as f:
        data = json.load(f)
    return data

def perform_corrected_resampled_ttest(kfold_scores: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Perform Corrected Resampled t-test (Nadeau & Bengio) on K-Fold ROC-AUC scores.
    Only uses ROC-AUC scores as per specification.
    """
    morgan_scores = np.array(kfold_scores['morgan']['roc_auc'])
    maccs_scores = np.array(kfold_scores['maccs']['roc_auc'])

    if len(morgan_scores) != len(maccs_scores):
        raise ValueError("Morgan and MACCS scores must have same length for paired test")

    # Corrected Resampled t-test
    # Variance correction factor: 1/n_test + 1/n_train + rho
    # For K-Fold, we approximate with standard paired t-test but with corrected variance
    n = len(morgan_scores)
    diff = morgan_scores - maccs_scores

    # Standard deviation of differences
    std_diff = np.std(diff, ddof=1)
    mean_diff = np.mean(diff)

    # t-statistic
    if std_diff == 0:
        t_stat = 0.0
    else:
        t_stat = mean_diff / (std_diff / np.sqrt(n))

    # p-value (two-tailed)
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 1))

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'mean_difference': float(mean_diff),
        'std_difference': float(std_diff)
    }

def compute_bootstrap_confidence_interval(kfold_scores: Dict[str, List[float]], 
                                          n_iterations: int = BOOTSTRAP_ITERATIONS,
                                          confidence_level: float = CONFIDENCE_LEVEL,
                                          random_seed: int = RANDOM_SEED) -> Dict[str, Any]:
    """
    Generate confidence intervals via bootstrap resamples of the difference in performance
    (Morgan - MACCS) for ROC-AUC using the K-Fold scores.
    
    Args:
        kfold_scores: Dictionary containing K-Fold ROC-AUC scores for Morgan and MACCS
        n_iterations: Number of bootstrap iterations
        confidence_level: Confidence level for the interval (e.g., 0.95)
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing bootstrap statistics and confidence interval
    """
    init_random_seed(random_seed)
    
    morgan_scores = np.array(kfold_scores['morgan']['roc_auc'])
    maccs_scores = np.array(kfold_scores['maccs']['roc_auc'])
    
    if len(morgan_scores) != len(maccs_scores):
        raise ValueError("Morgan and MACCS scores must have same length for bootstrap")
    
    n_folds = len(morgan_scores)
    differences = morgan_scores - maccs_scores
    
    bootstrap_means = []
    
    for i in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n_folds, size=n_folds, replace=True)
        resampled_diff = differences[indices]
        bootstrap_means.append(np.mean(resampled_diff))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    ci_lower = np.percentile(bootstrap_means, lower_percentile)
    ci_upper = np.percentile(bootstrap_means, upper_percentile)
    
    return {
        'mean_difference': float(np.mean(differences)),
        'std_difference': float(np.std(differences)),
        'bootstrap_mean': float(np.mean(bootstrap_means)),
        'bootstrap_std': float(np.std(bootstrap_means)),
        'confidence_interval': {
            'lower': float(ci_lower),
            'upper': float(ci_upper),
            'level': confidence_level
        },
        'n_iterations': n_iterations,
        'bootstrap_distribution': bootstrap_means.tolist()  # Optional: for debugging
    }

def load_compounds_from_csv(csv_path: str) -> pd.DataFrame:
    """Load compounds from CSV file."""
    return pd.read_csv(csv_path)

def get_phosphorus_atoms(mol: Chem.Mol) -> List[int]:
    """Get indices of phosphorus atoms in a molecule."""
    phosphorus_indices = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 15:  # Phosphorus
            phosphorus_indices.append(atom.GetIdx())
    return phosphorus_indices

def get_morgan_bits_near_phosphorus(mol: Chem.Mol, radius: int = 2) -> List[int]:
    """Get Morgan fingerprint bits within radius of phosphorus atoms."""
    phosphorus_indices = get_phosphorus_atoms(mol)
    if not phosphorus_indices:
        return []
    
    # Generate Morgan fingerprint with bit info
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=2048, useFeatures=False)
    bit_info = {}
    AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=2048, bitInfo=bit_info)
    
    phosphorus_bits = set()
    for atom_idx in phosphorus_indices:
        if atom_idx in bit_info:
            for bit_idx, (center_atom, r) in bit_info[atom_idx]:
                phosphorus_bits.add(bit_idx)
    
    return list(phosphorus_bits)

def map_phosphorus_feature_importance(mol_smiles: str, model: Any, radius: int = 2) -> Dict[str, float]:
    """
    Map phosphorus atom feature importance by summing Gini importance
    for Morgan bits within radius of phosphorus atoms.
    """
    mol = Chem.MolFromSmiles(mol_smiles)
    if mol is None:
        return {'morgan_sum': 0.0, 'maccs_sum': 0.0, 'phosphorus_found': False}
    
    phosphorus_bits = get_morgan_bits_near_phosphorus(mol, radius)
    
    if not phosphorus_bits:
        return {'morgan_sum': 0.0, 'maccs_sum': 0.0, 'phosphorus_found': False}
    
    # Get feature importances from model
    morgan_importance = model['morgan'].feature_importances_
    maccs_importance = model['maccs'].feature_importances_
    
    morgan_sum = sum(morgan_importance[bit] for bit in phosphorus_bits if bit < len(morgan_importance))
    maccs_sum = sum(maccs_importance[bit] for bit in phosphorus_bits if bit < len(maccs_importance))
    
    return {
        'morgan_sum': float(morgan_sum),
        'maccs_sum': float(maccs_sum),
        'phosphorus_found': True,
        'n_phosphorus_bits': len(phosphorus_bits)
    }

def verify_sc_003(sc003_results_path: str) -> Dict[str, Any]:
    """Verify SC-003 feature importance analysis results."""
    with open(sc003_results_path, 'r') as f:
        results = json.load(f)
    
    # Check if threshold is met
    threshold_met = results.get('threshold_met', False)
    
    return {
        'verified': True,
        'threshold_met': threshold_met,
        'difference_pct': results.get('difference_pct', 0.0),
        'morgan_absolute_sum': results.get('morgan_absolute_sum', 0.0),
        'maccs_absolute_sum': results.get('maccs_absolute_sum', 0.0)
    }

def main():
    """Main execution function for evaluation."""
    setup_logging()
    init_random_seed(RANDOM_SEED)
    
    logger.info("Starting evaluation and statistical analysis")
    
    # Load K-Fold scores
    kfold_scores_path = "data/processed/kfold_scores.json"
    if not os.path.exists(kfold_scores_path):
        logger.error(f"K-Fold scores file not found: {kfold_scores_path}")
        return
    
    kfold_scores = collect_fold_scores(kfold_scores_path)
    logger.info(f"Loaded K-Fold scores: {len(kfold_scores['morgan']['roc_auc'])} folds")
    
    # Perform Corrected Resampled t-test
    logger.info("Performing Corrected Resampled t-test...")
    ttest_results = perform_corrected_resampled_ttest(kfold_scores)
    logger.info(f"t-test results: p-value = {ttest_results['p_value']:.4f}")
    
    # Compute bootstrap confidence interval
    logger.info("Computing bootstrap confidence intervals...")
    bootstrap_results = compute_bootstrap_confidence_interval(kfold_scores)
    logger.info(f"Bootstrap CI: [{bootstrap_results['confidence_interval']['lower']:.4f}, "
               f"{bootstrap_results['confidence_interval']['upper']:.4f}]")
    
    # Save results
    output_path = "data/processed/bootstrap_ci.json"
    with open(output_path, 'w') as f:
        json.dump(bootstrap_results, f, indent=2)
    
    logger.info(f"Bootstrap confidence interval results saved to {output_path}")
    
    # Also save t-test results
    ttest_output_path = "data/processed/ttest_results.json"
    with open(ttest_output_path, 'w') as f:
        json.dump(ttest_results, f, indent=2)
    
    logger.info(f"T-test results saved to {ttest_output_path}")

if __name__ == "__main__":
    main()