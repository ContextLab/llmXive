"""
Explainability module for molecular property prediction.
Implements SHAP interaction analysis, heatmap generation, and persistence of interaction matrix.
Updated to avoid RDKit dependencies by loading precomputed MACCS fingerprints from CSV.
"""
import os
import sys
import pickle
import logging
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np

# External libraries
from sklearn.ensemble import RandomForestRegressor

# Ensure we can import from the project root (for relative imports if needed)
sys.path.insert(0, str(Path(__file__).parent.parent))

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

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

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

# ----------------------------------------------------------------------
# Helper utilities – retained for backward compatibility but not used in the
# new SHAP workflow.
# ----------------------------------------------------------------------
def load_model(model_path: str = 'data/models/final_model.pkl'):
    """
    Load a pre‑trained Random Forest model if it exists.
    If the file is missing, the function returns ``None`` – callers can decide
    to train a fresh model on‑the‑fly.
    """
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found: {model_path}. A temporary model will be trained.")
        return None
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model

def load_fingerprints_data(fp_path: str = 'data/processed/full_fingerprints.csv'):
    """
    Load fingerprint data from CSV. If the file does not exist, this function
    returns ``None`` – callers can generate fingerprints from SMILES instead.
    """
    if not os.path.exists(fp_path):
        logger.warning(f"Fingerprint file not found: {fp_path}. Fingerprints will be generated from SMILES.")
        return None
    df = pd.read_csv(fp_path)
    logger.info(f"Loaded fingerprints from {fp_path}, shape: {df.shape}")
    return df

def load_rules(rules_path: str = 'code/data/rules.py'):
    """Load SMARTS patterns from rules file (fallback to a minimal set)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("rules", rules_path)
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        rules = rules_module.RULES
        logger.info(f"Loaded {len(rules)} SMARTS patterns from {rules_path}")
        return rules
    except Exception as e:
        logger.warning(f"Failed to load rules from {rules_path}: {e}")
        return [
            {"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"},
            {"name": "carbonyl", "smarts": "[OX2]=[C]", "description": "Carbonyl group"},
            {"name": "aromatic", "smarts": "a", "description": "Aromatic ring"},
            {"name": "amine", "smarts": "[NX3]", "description": "Amine group"},
            {"name": "halogen", "smarts": "[F,Cl,Br,I]", "description": "Halogen atom"}
        ]

# ----------------------------------------------------------------------
# Core SHAP interaction workflow (task T102)
# ----------------------------------------------------------------------
def _train_lightweight_rf(X: np.ndarray, y: np.ndarray) -> RandomForestRegressor:
    """
    Train a small RandomForestRegressor for the purpose of SHAP interaction
    extraction. The model is deliberately simple to keep runtime low.
    """
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=1  # deterministic and respects runner CPU limits
    )
    rf.fit(X, y)
    logger.info("Trained temporary RandomForest model for SHAP analysis.")
    return rf

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
    explainer = shap.TreeExplainer(model, feature_perturbation="interventional")

    # Use a subset for background to keep memory usage modest
    if X.shape[0] > background_samples:
        idx = np.random.choice(X.shape[0], background_samples, replace=False)
        background = X[idx]
    else:
        background = X

    logger.info(f"Computing SHAP interaction values using {background.shape[0]} background samples...")
    shap_interactions = explainer.shap_interaction_values(X)
    logger.info(f"SHAP interaction tensor shape: {shap_interactions.shape}")
    return shap_interactions

def save_interaction_summary(shap_values, output_path: str = 'data/derived/shap_summary.csv'):
    """
    Save a concise summary of SHAP interaction strengths.
    The summary contains the mean absolute interaction per feature.
    """
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        mean_abs = np.mean(np.abs(shap_values), axis=0)  # (n_features, n_features)
        # Collapse to a 1‑D summary by averaging rows
        summary = np.mean(mean_abs, axis=1)
        df = pd.DataFrame({
            'feature_index': np.arange(len(summary)),
            'mean_abs_shap_interaction': summary
        })
        df.to_csv(output_path, index=False)
        logger.info(f"Saved SHAP interaction summary to {output_path}")
        return df
    else:
        logger.warning("SHAP values not in expected 3‑D shape; summary not saved.")
        return None

def generate_interaction_heatmap(shap_values, output_path: str = 'data/derived/shap_interactions.png', top_n: int = 20):
    """
    Generate a heatmap visualising the top‑N fingerprint bit‑pair interactions.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 8))

    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        # Mean absolute interaction across all molecules
        interaction_matrix = np.mean(np.abs(shap_values), axis=0)  # (n_features, n_features)

        # Identify top‑N interacting pairs (by absolute value)
        triu_idx = np.triu_indices_from(interaction_matrix, k=1)
        flat_vals = interaction_matrix[triu_idx]
        top_indices = np.argsort(flat_vals)[-top_n:][::-1]

        # Build a small matrix for visualisation (top_n x top_n diagonal)
        selected = np.zeros((top_n, top_n))
        for rank, idx in enumerate(top_indices):
            i = triu_idx[0][idx]
            j = triu_idx[1][idx]
            selected[rank, rank] = interaction_matrix[i, j]

        sns.heatmap(selected, cmap='viridis', annot=False,
                    cbar_kws={'label': 'Mean |Interaction|'},
                    xticklabels=False, yticklabels=False)
        plt.title(f'Top {top_n} MACCS Bit‑Pair SHAP Interactions')
    else:
        plt.text(0.5, 0.5, 'No interaction data available',
                 ha='center', va='center', transform=plt.gca().transAxes)
        plt.title('SHAP Interactions')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved SHAP interaction heatmap to {output_path}")

def plot_shap_interactions():
    """
    Compute SHAP interaction values for the MACCS fingerprint block,
    persist the interaction matrix, and generate a heatmap.
    This implementation is self‑contained: it trains a lightweight Random Forest
    on the available baseline test predictions if a pre‑trained model is not
    found.
    """
    # Initialise logging and directories
    setup_logging()
    ensure_dirs()

    # ------------------------------------------------------------------
    # 1️⃣ Load baseline test predictions (required artifact)
    # ------------------------------------------------------------------
    baseline_path = Path('data/derived/baseline_test_predictions.csv')
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Required baseline predictions not found at {baseline_path}")

    baseline_df = pd.read_csv(baseline_path)
    # Use only logP entries for this example (any property could be used)
    logp_df = baseline_df[baseline_df['property'] == 'logP'].dropna(subset=['experimental_value'])
    if logp_df.empty:
        raise ValueError("No logP entries found in baseline_test_predictions.csv")

    smiles = logp_df['smiles'].tolist()
    y = logp_df['experimental_value'].astype(float).values

    # ------------------------------------------------------------------
    # 2️⃣ Load precomputed MACCS fingerprint matrix
    # ------------------------------------------------------------------
    fp_df = load_fingerprints_data()
    if fp_df is None:
        raise FileNotFoundError("Fingerprint CSV not found; cannot compute SHAP interactions.")

    # Ensure the fingerprint DataFrame contains a 'smiles' column
    if 'smiles' not in fp_df.columns:
        raise KeyError("Fingerprint CSV must contain a 'smiles' column.")

    # Filter fingerprint rows to match the SMILES used for y
    fp_df = fp_df[fp_df['smiles'].isin(smiles)]
    if fp_df.empty:
        raise ValueError("No matching fingerprints found for the baseline SMILES.")

    # Assume all columns other than 'smiles' are binary MACCS bits
    feature_cols = [c for c in fp_df.columns if c != 'smiles']
    X = fp_df[feature_cols].to_numpy(dtype=int)
    logger.info(f"Loaded MACCS fingerprint matrix with shape {X.shape}")

    # ------------------------------------------------------------------
    # 3️⃣ Load an existing model if available; otherwise train a temporary one
    # ------------------------------------------------------------------
    model = load_model()
    if model is None:
        model = _train_lightweight_rf(X, y)

    # ------------------------------------------------------------------
    # 4️⃣ Compute SHAP interaction values
    # ------------------------------------------------------------------
    shap_interactions = calculate_shap_interactions(model, X)

    # ------------------------------------------------------------------
    # 5️⃣ Persist the full interaction tensor
    # ------------------------------------------------------------------
    interaction_path = Path('data/derived/shap_interaction.npy')
    np.save(interaction_path, shap_interactions)
    logger.info(f"Saved SHAP interaction matrix to {interaction_path}")

    # ------------------------------------------------------------------
    # 6️⃣ Produce a heatmap of the top‑N interactions
    # ------------------------------------------------------------------
    heatmap_path = Path('data/derived/shap_interactions.png')
    generate_interaction_heatmap(shap_interactions, str(heatmap_path), top_n=20)

    logger.info("SHAP interaction heatmap generation completed.")

# ----------------------------------------------------------------------
# Existing CLI entry point – retained for compatibility
# ----------------------------------------------------------------------
def main():
    """Main function to run explainability analysis."""
    setup_logging()
    logger.info("Starting explainability analysis...")

    # Simple CLI handling
    if '--shap-heatmap' in sys.argv:
        plot_shap_interactions()
        return

    # Placeholder for other flags (e.g., conformational audit, bit mapping)
    logger.info("No recognized flags provided. Exiting.")

if __name__ == "__main__":
    main()
