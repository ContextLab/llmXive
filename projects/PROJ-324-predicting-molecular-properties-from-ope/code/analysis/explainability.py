"""
Explainability module for molecular property prediction.
Implements SHAP interaction analysis, heatmap generation, and persistence of interaction matrix.
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

# RDKit for on‑the‑fly MACCS fingerprint generation and substructure matching
from rdkit import Chem
from rdkit.Chem import MACCSkeys
try:
    from rdkit.Chem.Lipinski import NumRotatableBonds as CalcNumRotatableBonds
except (ImportError, AttributeError):
    try:
        from rdkit.Chem.Lipinski import CalcNumRotatableBonds
    except (ImportError, AttributeError):
        # Fallback for very old or specific RDKit versions
        def CalcNumRotatableBonds(mol):
            return 0
from rdkit.Chem.rdMolDescriptors import CalcTPSA

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

def setup_logging():
    """Set up logging to file and console."""
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'explainability.log'
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        return None
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model

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
    # Use TreeExplainer for Random Forest
    explainer = shap.TreeExplainer(model)
    
    # To avoid memory issues with large datasets, we use a representative background
    if X.shape[0] > background_samples:
        # Use a fixed seed for reproducibility
        np.random.seed(42)
        idx = np.random.choice(X.shape[0], background_samples, replace=False)
        X_subset = X[idx]
    else:
        X_subset = X

    logger.info(f"Computing SHAP interaction values for {len(X_subset)} samples...")
    # shap_interaction_values returns (n_samples, n_features, n_features)
    shap_interactions = explainer.shap_interaction_values(X_subset)
    return shap_interactions

def generate_interaction_heatmap(shap_values, output_path: str = 'data/derived/shap_interactions.png', top_n: int = 20):
    """
    Generate a heatmap visualising the top‑N fingerprint bit‑pair interactions using plt.imshow.
    """
    if not isinstance(shap_values, np.ndarray) or shap_values.ndim != 3:
        logger.error("Invalid SHAP interaction tensor shape.")
        return

    # Mean absolute interaction across all samples
    # Shape: (n_features, n_features)
    interaction_matrix = np.mean(np.abs(shap_values), axis=0)

    # Determine top N bits based on their total interaction strength
    bit_strengths = interaction_matrix.sum(axis=1)
    top_bits = np.argsort(bit_strengths)[-top_n:][::-1]

    # Extract the N x N submatrix for these top bits
    selected_matrix = interaction_matrix[np.ix_(top_bits, top_bits)]

    plt.figure(figsize=(12, 10))
    im = plt.imshow(selected_matrix, cmap='viridis', interpolation='nearest')
    plt.colorbar(im, label='Mean |Interaction Value|')
    
    plt.title(f'Top {top_n} MACCS Bit-Pair SHAP Interactions')
    plt.xlabel('Bit Index')
    plt.ylabel('Bit Index')
    
    # Label axes with the actual bit indices
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
    if model is None:
        raise FileNotFoundError(f"Required model not found at {model_path}. Please ensure T020 is completed.")

    # 2. Load test‑set MACCS fingerprints
    fp_path = 'data/processed/test_fingerprints.csv'
    if not os.path.exists(fp_path):
        raise FileNotFoundError(f"Required test fingerprint file not found at {fp_path}. Please ensure T019 is completed.")

    fp_df = pd.read_csv(fp_path)
    if 'smiles' not in fp_df.columns:
        raise KeyError("Fingerprint CSV must contain a 'smiles' column.")
    
    # Extract MACCS features (all columns except 'smiles')
    feature_cols = [c for c in fp_df.columns if c != 'smiles']
    X = fp_df[feature_cols].to_numpy(dtype=int)
    logger.info(f"Loaded test fingerprint matrix with shape {X.shape}")

    # 3. Compute SHAP interaction values
    shap_interactions = calculate_shap_interactions(model, X)

    # 4. Persist the full interaction tensor
    # Shape: (n_samples, n_features, n_features)
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
    rule_lookup = {idx: rules[idx] for idx in range(min(len(rules), len(mean_abs_per_bit)))}
    test_set_path = Path('data/derived/test_set.csv')
    if not test_set_path.is_file():
        raise FileNotFoundError(f"Test set not found at {test_set_path}")
    test_df = pd.read_csv(test_set_path)
    records = []
    for _, mol_row in test_df.iterrows():
        smiles = mol_row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None: continue
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

def flag_conformational_limits(test_set_path: str = 'data/derived/test_set.csv', rf_predictions_path: str = 'data/derived/rf_test_predictions.csv', output_path: str = 'data/derived/conformational_limitations.csv', rotatable_bond_threshold: int = 10):
    setup_logging()
    ensure_dirs()
    if not Path(test_set_path).is_file(): raise FileNotFoundError(test_set_path)
    test_df = pd.read_csv(test_set_path)
    rot_bonds, tpsa_vals = [], []
    for smi in test_df['smiles']:
        mol = Chem.MolFromSmiles(smi)
        rot_bonds.append(CalcNumRotatableBonds(mol) if mol else np.nan)
        tpsa_vals.append(CalcTPSA(mol) if mol else np.nan)
    test_df['num_rotatable_bonds'], test_df['tpsa'] = rot_bonds, tpsa_vals
    flagged_df = test_df[test_df['num_rotatable_bonds'] > rotatable_bond_threshold].copy()
    if not Path(rf_predictions_path).is_file(): raise FileNotFoundError(rf_predictions_path)
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