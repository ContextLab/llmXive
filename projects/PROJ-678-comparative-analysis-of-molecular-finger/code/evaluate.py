import os
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem
from typing import Dict, List, Tuple, Any, Optional

# Import from sibling modules based on API surface
from utils import setup_logging, init_random_seed, get_logger
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, TANIMOTO_THRESHOLD, N_FOLDS

logger = get_logger(__name__)

def load_model_artifact(path: Path) -> Any:
    """Load a pickled model artifact."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_split_indices(path: Path) -> Dict[int, Dict[str, List[int]]]:
    """Load split indices for all folds."""
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_fingerprint_data(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Load Morgan and MACCS fingerprints."""
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data['morgan'], data['maccs']

def load_labels(path: Path) -> np.ndarray:
    """Load toxicity labels."""
    df = pd.read_csv(path)
    # Assuming label column is 'Toxicity' or similar based on Tox21 structure
    # We will look for the specific endpoint column used in training
    # For this implementation, we assume the label column is named 'label' or derived from context
    if 'label' in df.columns:
        return df['label'].values
    elif 'Toxicity' in df.columns:
        return df['Toxicity'].values
    else:
        # Fallback to first numeric column if specific name not found
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            return df[numeric_cols[0]].values
        raise ValueError("No suitable label column found in data")

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, PR-AUC, and Balanced Accuracy."""
    from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score
    
    metrics = {}
    try:
        metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
    except Exception as e:
        logger.warning(f"Could not calculate ROC-AUC: {e}")
        metrics['roc_auc'] = np.nan
    
    try:
        metrics['pr_auc'] = average_precision_score(y_true, y_proba)
    except Exception as e:
        logger.warning(f"Could not calculate PR-AUC: {e}")
        metrics['pr_auc'] = np.nan
    
    try:
        metrics['balanced_accuracy'] = balanced_accuracy_score(y_true, y_pred)
    except Exception as e:
        logger.warning(f"Could not calculate Balanced Accuracy: {e}")
        metrics['balanced_accuracy'] = np.nan
    
    return metrics

def evaluate_fold(fold_idx: int, model_data: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """Evaluate a single fold's model."""
    from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score, confusion_matrix
    
    model = model_data['model']
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if model.predict_proba(X_test).shape[1] > 1 else model.predict_proba(X_test)
    
    # Ensure y_test is binary for metrics
    if len(np.unique(y_test)) < 2:
        logger.warning(f"Fold {fold_idx} has only one class in test set. Skipping metrics.")
        return {
            'fold': fold_idx,
            'roc_auc': np.nan,
            'pr_auc': np.nan,
            'balanced_accuracy': np.nan,
            'confusion_matrix': None
        }

    metrics = {
        'fold': fold_idx,
        'roc_auc': roc_auc_score(y_test, y_proba),
        'pr_auc': average_precision_score(y_test, y_proba),
        'balanced_accuracy': balanced_accuracy_score(y_test, y_pred),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
    }
    
    return metrics

def run_evaluation(models_dir: Path, splits_path: Path, fingerprints_path: Path, labels_path: Path) -> List[Dict[str, Any]]:
    """Run evaluation for all folds."""
    splits = load_split_indices(splits_path)
    morgan_fps, maccs_fps = load_fingerprint_data(fingerprints_path)
    labels = load_labels(labels_path)
    
    results = []
    
    for fold_idx in range(N_FOLDS):
        if fold_idx not in splits:
            logger.warning(f"Fold {fold_idx} not found in splits, skipping.")
            continue
        
        test_indices = splits[fold_idx]['test']
        X_test_morgan = morgan_fps[test_indices]
        X_test_maccs = maccs_fps[test_indices]
        y_test = labels[test_indices]
        
        # Load Morgan model
        morgan_model_path = models_dir / f"fold_{fold_idx}_morgan.pkl"
        if morgan_model_path.exists():
            morgan_data = load_model_artifact(morgan_model_path)
            morgan_metrics = evaluate_fold(fold_idx, morgan_data, X_test_morgan, y_test)
            morgan_metrics['fingerprint_type'] = 'Morgan'
            results.append(morgan_metrics)
        
        # Load MACCS model
        maccs_model_path = models_dir / f"fold_{fold_idx}_maccs.pkl"
        if maccs_model_path.exists():
            maccs_data = load_model_artifact(maccs_model_path)
            maccs_metrics = evaluate_fold(fold_idx, maccs_data, X_test_maccs, y_test)
            maccs_metrics['fingerprint_type'] = 'MACCS'
            results.append(maccs_metrics)
    
    return results

def bootstrap_confidence_interval(scores: np.ndarray, n_iterations: int = 1000, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate bootstrap confidence interval for a set of scores."""
    if len(scores) == 0:
        return (np.nan, np.nan)
    
    n = len(scores)
    boot_means = []
    for _ in range(n_iterations):
        sample = np.random.choice(scores, size=n, replace=True)
        boot_means.append(np.mean(sample))
    
    boot_means = np.array(boot_means)
    lower = np.percentile(boot_means, (1 - confidence) / 2 * 100)
    upper = np.percentile(boot_means, (1 + confidence) / 2 * 100)
    return (lower, upper)

def compute_bootstrap_ci_for_metrics(results: List[Dict[str, Any]], metric_name: str, fingerprint_type: str) -> Tuple[float, float]:
    """Compute bootstrap CI for a specific metric and fingerprint type."""
    scores = np.array([r[metric_name] for r in results if r['fingerprint_type'] == fingerprint_type and not np.isnan(r[metric_name])])
    return bootstrap_confidence_interval(scores)

def map_phosphorus_feature_importance(model: Any, mol: Chem.Mol, radius: int = MORGAN_RADIUS) -> Dict[str, float]:
    """
    Map Morgan fingerprint bits to phosphorus-centered substructures.
    1) Identify phosphorus atom.
    2) Use RDKit GetBitInfo to find bits within radius of P.
    3) Sum Gini importance for these bits.
    4) Compare to total Gini importance.
    """
    if model is None or mol is None:
        return {'phosphorus_importance_sum': 0.0, 'total_importance_sum': 0.0, 'ratio': 0.0}
    
    # Find phosphorus atoms (atomic number 15)
    phosphorus_atoms = [atom.GetIdx() for atom in mol.GetAtoms() if atom.GetAtomicNum() == 15]
    
    if not phosphorus_atoms:
        logger.warning("No phosphorus atom found in molecule.")
        return {'phosphorus_importance_sum': 0.0, 'total_importance_sum': 0.0, 'ratio': 0.0}
    
    # Generate fingerprint with bit info
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=MORGAN_BITS, useChirality=True)
    bit_info = {}
    fp.GetBitInfo(bit_info)
    
    # Get feature importances from the Random Forest model
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        logger.warning("Model does not have feature_importances_ attribute.")
        return {'phosphorus_importance_sum': 0.0, 'total_importance_sum': 0.0, 'ratio': 0.0}
    
    total_importance = np.sum(importances)
    if total_importance == 0:
        return {'phosphorus_importance_sum': 0.0, 'total_importance_sum': 0.0, 'ratio': 0.0}
    
    # Sum importance for bits associated with phosphorus atoms
    phosphorus_importance_sum = 0.0
    for p_idx in phosphorus_atoms:
        # Find bits where this atom contributes
        for bit_idx, contributions in bit_info.items():
            for atom_idx, _ in contributions:
                if atom_idx == p_idx:
                    phosphorus_importance_sum += importances[bit_idx]
                    break # Avoid double counting if multiple contributions map to same bit from same atom
    
    ratio = phosphorus_importance_sum / total_importance if total_importance > 0 else 0.0
    
    return {
        'phosphorus_importance_sum': float(phosphorus_importance_sum),
        'total_importance_sum': float(total_importance),
        'ratio': float(ratio)
    }

def verify_sc_003(models_dir: Path, splits_path: Path, fingerprints_path: Path, labels_path: Path, 
                  processed_data_path: Path) -> Dict[str, Any]:
    """
    Verify SC-003: Check if sum of Gini importance for Morgan bits (radius 2) 
    exceeds sum for MACCS keys by >= 15%.
    """
    import json
    
    logger.info("Starting SC-003 verification...")
    
    splits = load_split_indices(splits_path)
    morgan_fps, maccs_fps = load_fingerprint_data(fingerprints_path)
    labels = load_labels(labels_path)
    
    # Load raw data to get SMILES for molecule reconstruction
    raw_df = pd.read_csv(processed_data_path)
    smiles_col = 'smiles' if 'smiles' in raw_df.columns else 'SMILES'
    if smiles_col not in raw_df.columns:
        logger.error("SMILES column not found in processed data. Cannot reconstruct molecules for feature importance.")
        return {'status': 'failed', 'reason': 'SMILES column missing'}
    
    morgan_importance_sums = []
    maccs_importance_sums = []
    
    # We need to aggregate importance across all folds or use a representative model
    # For SC-003, we will aggregate the total importance from all trained models
    # Since we have 5 folds, we can sum the importance of all trees across all folds
    
    # However, the task asks to compare the "sum of Gini importance" for the bits.
    # In a Random Forest, the total importance is the sum of importances of all trees.
    # We will calculate the average importance per bit across all trees in all folds for Morgan
    # and compare it to the average importance per bit for MACCS.
    
    # Actually, the task says: "sum of Gini importance for Morgan bits ... exceeds ... MACCS keys by >= 15%"
    # This implies comparing the total magnitude of importance captured by the Morgan bits vs MACCS bits.
    # Since the number of bits is different (2048 vs 166), a direct sum might be biased.
    # But the instruction is explicit: "sum of Gini importance".
    # We will compute the sum of importances for the Morgan model and the MACCS model
    # across all folds and compare.
    
    # Let's assume we want to compare the TOTAL importance captured by the Morgan fingerprint
    # vs the TOTAL importance captured by the MACCS fingerprint.
    # Since the models are trained on different feature sets, the total sum of importances
    # for each model should be roughly 1.0 per tree (or normalized).
    # The "sum of Gini importance for Morgan bits" might refer to the sum of importances
    # of the specific bits that are 'on' in the molecules of interest?
    # Re-reading: "sum of Gini importance for Morgan bits (radius 2) exceeds the sum for MACCS keys by >= 15%"
    # This likely means: Compare the total predictive power (importance) assigned to the Morgan features
    # vs the MACCS features.
    # But in a standard RF, the sum of importances is 1.0.
    # Perhaps it means: For the specific compounds in the dataset, which fingerprint type
    # has higher total importance in the models?
    
    # Let's interpret it as: Calculate the average feature importance across all trees
    # for the Morgan model and the MACCS model. Then compare the sums.
    # Since the sum of importances is 1.0 for each tree, the total sum for 100 trees is 100.
    # This doesn't make sense to compare directly if they are normalized.
    
    # Alternative interpretation: The "sum of Gini importance" refers to the importance
    # of the bits that are actually set to 1 in the dataset.
    # Let's calculate the mean importance of bits that are active in the test sets.
    
    # We will iterate through all folds, get the test set, and calculate the
    # sum of importances for the active bits in Morgan vs MACCS.
    
    total_morgan_active_importance = 0.0
    total_maccs_active_importance = 0.0
    count = 0
    
    for fold_idx in range(N_FOLDS):
        if fold_idx not in splits:
            continue
        
        test_indices = splits[fold_idx]['test']
        y_test = labels[test_indices]
        
        if len(np.unique(y_test)) < 2:
            continue
        
        # Load Morgan model
        morgan_model_path = models_dir / f"fold_{fold_idx}_morgan.pkl"
        if morgan_model_path.exists():
            morgan_model = load_model_artifact(morgan_model_path)
            if hasattr(morgan_model, 'feature_importances_'):
                # Calculate active bits for test set
                # We need to generate fingerprints for test set again or load them
                X_test_morgan = morgan_fps[test_indices]
                # Sum of importances for bits that are 1 in any test sample?
                # Or sum of importances weighted by the number of times a bit is 1?
                # Let's use the mean importance of bits that are active in the test set.
                active_morgan_bits = np.any(X_test_morgan > 0, axis=0)
                morgan_active_sum = np.sum(morgan_model.feature_importances_[active_morgan_bits])
                total_morgan_active_importance += morgan_active_sum
                count += 1
        
        # Load MACCS model
        maccs_model_path = models_dir / f"fold_{fold_idx}_maccs.pkl"
        if maccs_model_path.exists():
            maccs_model = load_model_artifact(maccs_model_path)
            if hasattr(maccs_model, 'feature_importances_'):
                X_test_maccs = maccs_fps[test_indices]
                active_maccs_bits = np.any(X_test_maccs > 0, axis=0)
                maccs_active_sum = np.sum(maccs_model.feature_importances_[active_maccs_bits])
                total_maccs_active_importance += maccs_active_sum
                count += 1
    
    if count == 0:
        logger.error("No valid folds found for SC-003 verification.")
        return {'status': 'failed', 'reason': 'No valid folds'}
    
    avg_morgan = total_morgan_active_importance / count
    avg_maccs = total_maccs_active_importance / count
    
    logger.info(f"Average active importance (Morgan): {avg_morgan}")
    logger.info(f"Average active importance (MACCS): {avg_maccs}")
    
    if avg_maccs == 0:
        ratio = float('inf') if avg_morgan > 0 else 0.0
    else:
        ratio = (avg_morgan - avg_maccs) / avg_maccs
    
    threshold = 0.15
    passed = ratio >= threshold
    
    result = {
        'status': 'passed' if passed else 'failed',
        'morgan_avg_active_importance': avg_morgan,
        'maccs_avg_active_importance': avg_maccs,
        'ratio_percent': ratio * 100,
        'threshold_percent': threshold * 100,
        'passed_threshold': passed
    }
    
    logger.info(f"SC-003 Verification Result: {result}")
    return result

def main():
    """Main entry point for evaluation and SC-003 verification."""
    init_random_seed(42)
    setup_logging()
    
    # Define paths
    base_path = Path("projects/PROJ-678-comparative-analysis-of-molecular-finger")
    models_dir = base_path / "data/processed/models"
    splits_path = base_path / "data/processed/splits/splits.pkl"
    fingerprints_path = base_path / "data/processed/fingerprints.pkl"
    labels_path = base_path / "data/processed/organophosphates_filtered.csv"
    processed_data_path = base_path / "data/processed/organophosphates_filtered.csv"
    
    if not models_dir.exists():
        logger.error(f"Models directory not found: {models_dir}")
        return
    
    # Run standard evaluation
    results = run_evaluation(models_dir, splits_path, fingerprints_path, labels_path)
    
    # Verify SC-003
    sc003_result = verify_sc_003(models_dir, splits_path, fingerprints_path, labels_path, processed_data_path)
    
    # Log results
    logger.info("Evaluation Results:")
    for res in results:
        logger.info(f"  Fold {res['fold']} ({res['fingerprint_type']}): ROC-AUC={res['roc_auc']:.4f}, PR-AUC={res['pr_auc']:.4f}")
    
    logger.info(f"SC-003 Result: {sc003_result['status']} (Ratio: {sc003_result['ratio_percent']:.2f}%)")

if __name__ == "__main__":
    main()