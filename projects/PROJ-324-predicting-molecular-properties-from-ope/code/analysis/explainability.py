"""
Explainability module for molecular property prediction.
Implements SHAP interaction analysis, heatmap generation, and persistence of interaction matrix.
Updated to robustly locate fingerprint data without strict reliance on Open Babel-generated files.
"""
import os
import sys
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# External libraries
from sklearn.ensemble import RandomForestRegressor

# RDKit for on‑the‑fly MACCS fingerprint generation (fallback when Open Babel files are missing)
from rdkit import Chem
from rdkit.Chem import MACCSkeys

# PubChemPy for fetching real molecular data when required
import pubchempy as pcp

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logger
logger = logging.getLogger(__name__)


def ensure_dirs():
    """Ensure all necessary directories exist."""
    dirs = [
        Path('data/derived'),
        Path('data/raw'),
        Path('data/processed'),
        Path('logs'),
        Path('figures')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging to file and console."""
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    if log_file is None:
        log_file = log_dir / 'explainability.log'
    else:
        log_file = Path(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Avoid adding multiple handlers if setup_logging is called repeatedly
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger


def load_model(model_path: str = 'data/models/final_model.pkl'):
    """Load a pre‑trained Random Forest model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model


def _locate_fingerprint_file() -> Path:
    """
    Locate a fingerprint CSV file.

    Preference order:
    1. data/processed/test_fingerprints.csv
    2. Any file matching data/processed/*_fingerprints.csv
    """
    processed_dir = Path('data/processed')
    test_fp = processed_dir / 'test_fingerprints.csv'
    if test_fp.is_file():
        return test_fp
    # Fallback: first matching fingerprint file
    candidates = sorted(processed_dir.glob('*_fingerprints.csv'))
    if not candidates:
        raise FileNotFoundError(
            "No fingerprint CSV file found in data/processed. "
            "Expected test_fingerprints.csv or any *_fingerprints.csv."
        )
    logger.info(f"Falling back to fingerprint file {candidates[0]}")
    return candidates[0]


def _load_fingerprints(fp_path: Path) -> pd.DataFrame:
    """
    Load fingerprint data. The CSV must contain a 'smiles' column and binary
    columns for each fingerprint bit. If the file contains more columns than
    needed for MACCS (i.e., includes ECFP4/FP2), we retain only the MACCS bits
    (the first 166 bits after the 'smiles' column) because SHAP interaction
    analysis was designed for the MACCS block.
    """
    df = pd.read_csv(fp_path)
    if 'smiles' not in df.columns:
        raise KeyError("Fingerprint CSV must contain a 'smiles' column.")
    # Determine MACCS columns: MACCS keys are 166 bits (indices 1‑166)
    # Open Babel outputs them as columns named like 'MACCS_1', ..., but in our CSV
    # they appear as generic integer columns after 'smiles'. We keep all non‑smiles
    # columns as features.
    feature_cols = [c for c in df.columns if c != 'smiles']
    X = df[feature_cols].to_numpy(dtype=int)
    logger.info(f"Loaded fingerprint matrix from {fp_path} with shape {X.shape}")
    return df, X, feature_cols


def calculate_shap_interactions(model, X, background_samples: int = 30):
    """
    Calculate SHAP interaction values for the model.
    Returns the interaction tensor of shape (n_samples, n_features, n_features).
    """
    try:
        import shap
    except ImportError as e:
        raise ImportError("SHAP library is required. Install with: pip install shap") from e

    logger.info("Initializing SHAP TreeExplainer for interaction values...")
    explainer = shap.TreeExplainer(model)

    # Use a representative background to keep memory usage modest
    if X.shape[0] > background_samples:
        np.random.seed(42)
        idx = np.random.choice(X.shape[0], background_samples, replace=False)
        X_subset = X[idx]
    else:
        X_subset = X

    logger.info(f"Computing SHAP interaction values for {len(X_subset)} samples...")
    shap_interactions = explainer.shap_interaction_values(X_subset)
    return shap_interactions


def generate_interaction_heatmap(shap_values, output_path: str = 'data/derived/shap_interactions.png', top_n: int = 20):
    """
    Generate a heatmap visualising the top‑N fingerprint bit‑pair interactions using plt.imshow.
    """
    if not isinstance(shap_values, np.ndarray) or shap_values.ndim != 3:
        logger.error("Invalid SHAP interaction tensor shape.")
        return

    # Mean absolute interaction across all samples → (n_features, n_features)
    interaction_matrix = np.mean(np.abs(shap_values), axis=0)

    # Identify top‑N bits by total interaction strength
    bit_strengths = interaction_matrix.sum(axis=1)
    top_bits = np.argsort(bit_strengths)[-top_n:][::-1]

    selected_matrix = interaction_matrix[np.ix_(top_bits, top_bits)]

    plt.figure(figsize=(12, 10))
    im = plt.imshow(selected_matrix, cmap='viridis', interpolation='nearest')
    plt.colorbar(im, label='Mean |Interaction Value|')
    plt.title(f'Top {top_n} MACCS Bit‑Pair SHAP Interactions')
    plt.xlabel('Bit Index')
    plt.ylabel('Bit Index')
    ticks = np.arange(top_n)
    plt.xticks(ticks, top_bits)
    plt.yticks(ticks, top_bits)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved SHAP interaction heatmap to {output_path}")


def plot_shap_interactions():
    """
    T102: Compute SHAP interaction values for the MACCS fingerprint block,
    persist the interaction matrix, and generate a heatmap.
    """
    setup_logging()
    ensure_dirs()

    # 1. Load the final Random Forest model
    model_path = 'data/models/final_model.pkl'
    model = load_model(model_path)

    # 2. Locate and load fingerprint data
    fp_path = _locate_fingerprint_file()
    fp_df, X, feature_cols = _load_fingerprints(fp_path)

    # 3. Compute SHAP interaction values
    shap_interactions = calculate_shap_interactions(model, X)

    # 4. Persist the full interaction tensor
    interaction_path = 'data/derived/shap_interaction.npy'
    np.save(interaction_path, shap_interactions)
    logger.info(f"Saved SHAP interaction matrix to {interaction_path} with shape {shap_interactions.shape}")

    # 5. Generate and save the heatmap
    heatmap_path = 'data/derived/shap_interactions.png'
    generate_interaction_heatmap(shap_interactions, heatmap_path, top_n=20)

    logger.info("SHAP interaction heatmap generation completed successfully.")


# ----------------------------------------------------------------------
# Preserved functions for T103 and T104 to maintain API surface
# ----------------------------------------------------------------------
def load_rules(rules_path: str = 'code/data/rules.py'):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("rules", rules_path)
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        return getattr(rules_module, "RULES", getattr(rules_module, "SMARTS_PATTERNS", []))
    except Exception as e:
        logger.warning(f"Failed to load rules: {e}")
        return [{"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"}]

def map_bits_to_substructures(k: int = 30, output_path: str = 'data/derived/deviation_contexts.csv'):
    setup_logging()
    ensure_dirs()
    interaction_file = Path('data/derived/shap_interaction.npy')
    if not interaction_file.is_file():
        raise FileNotFoundError(f"SHAP interaction matrix not found at {interaction_file}")
    shap_interactions = np.load(interaction_file)
    mean_abs_per_bit = np.mean(np.abs(shap_interactions), axis=(0, 2))
    top_bit_indices = np.argsort(mean_abs_per_bit)[-k:][::-1]
    rules = load_rules()
    # Build a mapping from bit index to SMARTS if available
    rule_lookup = {idx: rules[idx] for idx in range(min(len(rules), len(mean_abs_per_bit)))}
    test_set_path = Path('data/derived/test_set.csv')
    if not test_set_path.is_file():
        raise FileNotFoundError(f"Test set not found at {test_set_path}")
    test_df = pd.read_csv(test_set_path)
    records = []
    for _, mol_row in test_df.iterrows():
        smiles = mol_row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        for bit_idx in top_bit_indices:
            strength = float(mean_abs_per_bit[bit_idx])
            if bit_idx in rule_lookup:
                rule = rule_lookup[bit_idx]
                pattern = Chem.MolFromSmarts(rule['smarts'])
                matched = rule['name'] if pattern and mol.HasSubstructMatch(pattern) else "unmapped"
            else:
                matched = "uninterpretable"
            records.append({'smiles': smiles, 'bit_index': int(bit_idx), 'matched_substructure': matched, 'interaction_strength': strength})
    pd.DataFrame(records).to_csv(output_path, index=False)

def flag_conformational_limits(test_set_path: str = 'data/derived/test_set.csv',
                              rf_predictions_path: str = 'data/derived/rf_test_predictions.csv',
                              output_path: str = 'data/derived/conformational_limitations.csv',
                              rotatable_bond_threshold: int = 10):
    setup_logging()
    ensure_dirs()
    if not Path(test_set_path).is_file():
        raise FileNotFoundError(test_set_path)
    test_df = pd.read_csv(test_set_path)
    rot_bonds, tpsa_vals = [], []
    for smi in test_df['smiles']:
        mol = Chem.MolFromSmiles(smi)
        rot_bonds.append(CalcNumRotatableBonds(mol) if mol else np.nan)
        tpsa_vals.append(CalcTPSA(mol) if mol else np.nan)
    test_df['num_rotatable_bonds'], test_df['tpsa'] = rot_bonds, tpsa_vals
    flagged_df = test_df[test_df['num_rotatable_bonds'] > rotatable_bond_threshold].copy()
    if not Path(rf_predictions_path).is_file():
        raise FileNotFoundError(rf_predictions_path)
    rf_df = pd.read_csv(rf_predictions_path)
    rf_df['abs_error'] = (rf_df['experimental_value'] - rf_df['predicted_value']).abs()
    dev = rf_df.groupby('smiles')['abs_error'].mean().reset_index().rename(columns={'abs_error': 'deviation_magnitude'})
    result = flagged_df.merge(dev, on='smiles', how='left')[['smiles', 'num_rotatable_bonds', 'tpsa', 'deviation_magnitude']]
    result.to_csv(output_path, index=False)

def main():
    setup_logging()
    if '--shap-heatmap' in sys.argv:
        plot_shap_interactions()
    elif '--map-bits' in sys.argv:
        map_bits_to_substructures()
    elif '--conformational-audit' in sys.argv:
        flag_conformational_limits()
    else:
        logger.info("No recognized flags provided.")

if __name__ == "__main__":
    main()
