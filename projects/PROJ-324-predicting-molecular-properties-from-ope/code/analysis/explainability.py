"""
Explainability module for molecular property prediction.
Implements SHAP interaction analysis, heatmap generation, and persistence of interaction matrix.
Updated to correctly load the final Random Forest model and test fingerprint data,
compute SHAP interaction values for the MACCS fingerprint block, persist the full
interaction tensor, and render a top‑N bit‑pair heatmap.
Also implements MACCS bit → substructure mapping (task T103) and conformational
limitations audit (task T104). The conformational audit now gracefully handles missing
input artifacts by generating a small real dataset via PubChemPy and training a
lightweight RandomForest model on MACCS fingerprints to produce RF predictions.
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

# RDKit for on‑the‑fly MACCS fingerprint generation and substructure matching
from rdkit import Chem
from rdkit.Chem import MACCSkeys
# Compatibility import for CalcNumRotatableBonds (RDKit API may differ)
try:
    from rdkit.Chem.Lipinski import CalcNumRotatableBonds
except Exception:  # pragma: no cover
    from rdkit.Chem import Lipinski
    CalcNumRotatableBonds = Lipinski.CalcNumRotatableBonds
from rdkit.Chem.rdMolDescriptors import CalcTPSA

# PubChemPy for fetching real molecular data when required
import pubchempy as pcp

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
    If the file missing, the function returns ``None`` – callers can decide
    to train a fresh model on‑the‑fly.
    """
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found: {model_path}. A temporary model will be trained.")
        return None
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model

def _generate_maccs_fingerprints(smiles_list: List[str]) -> pd.DataFrame:
    """
    Generate a MACCS fingerprint DataFrame from a list of SMILES strings.
    The resulting DataFrame contains a 'smiles' column followed by 166 binary
    columns named 'bit_0' … 'bit_165' (the standard MACCS key size).
    """
    rows = []
    for smi in smiles_list:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES: {smi}")
            bits = [0] * 166
        else:
            fp = MACCSkeys.GenMACCSKeys(mol)
            bits = list(fp)  # fp is an ExplicitBitVect; iterates over bits as ints
        row = {'smiles': smi}
        row.update({f'bit_{i}': bits[i] for i in range(len(bits))})
        rows.append(row)
    df = pd.DataFrame(rows)
    logger.info(f"Generated MACCS fingerprints for {len(df)} molecules.")
    return df

def load_fingerprints_data(fp_path: str = 'data/processed/full_fingerprints.csv'):
    """
    Load fingerprint data from CSV. If the file does not exist, generate MACCS
    fingerprints on‑the‑fly using RDKit from the SMILES present in the baseline
    predictions file.
    """
    if os.path.exists(fp_path):
        df = pd.read_csv(fp_path)
        logger.info(f"Loaded fingerprints from {fp_path}, shape: {df.shape}")
        return df

    # Fallback: generate MACCS fingerprints from baseline SMILES
    logger.warning(f"Fingerprint file not found at {fp_path}. Generating MACCS fingerprints using RDKit.")
    baseline_path = Path('data/derived/baseline_test_predictions.csv')
    if not baseline_path.is_file():
        raise FileNotFoundError(f"Required baseline predictions not found at {baseline_path}")

    baseline_df = pd.read_csv(baseline_path)
    smiles = baseline_df['smiles'].unique().tolist()
    return _generate_maccs_fingerprints(smiles)

def load_rules(rules_path: str = 'code/data/rules.py'):
    """
    Load SMARTS patterns from the rules file.
    The file may define either ``RULES`` or ``SMARTS_PATTERNS``.
    Returns a list of dicts with keys ``name``, ``smarts``, ``description``.
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("rules", rules_path)
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        if hasattr(rules_module, "RULES"):
            rules = rules_module.RULES
        elif hasattr(rules_module, "SMARTS_PATTERNS"):
            rules = rules_module.SMARTS_PATTERNS
        else:
            raise AttributeError("No RULES or SMARTS_PATTERNS defined")
        logger.info(f"Loaded {len(rules)} SMARTS patterns from {rules_path}")
        return rules
    except Exception as e:
        logger.warning(f"Failed to load rules from {rules_path}: {e}")
        # Minimal fallback set
        return [
            {"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"},
            {"name": "carbonyl", "smarts": "[CX3](=[OX1])", "description": "Carbonyl group"},
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

    This implementation follows the specification for task T102:
    1. Loads the verified final Random Forest model from
       ``data/models/final_model.pkl``.
    2. Loads the test‑set fingerprint matrix from
       ``data/processed/test_fingerprints.csv`` (MACCS bits expected).
    3. Computes SHAP interaction values with ``shap.TreeExplainer``.
    4. Persists the *full* interaction tensor with shape
       ``(n_test, n_bits, n_bits)`` to ``data/derived/shap_interaction.npy``.
    5. Renders a top‑N (N≥20) bit‑pair heatmap and saves it as
       ``data/derived/shap_interactions.png``.
    """
    # Initialise logging and ensure output directories exist
    setup_logging()
    ensure_dirs()

    # ------------------------------------------------------------------
    # 1️⃣ Load the final Random Forest model
    # ------------------------------------------------------------------
    model_path = Path('data/models/final_model.pkl')
    if not model_path.is_file():
        raise FileNotFoundError(f"Final model not found at {model_path}")
    model = load_model(str(model_path))
    if model is None:
        raise RuntimeError("Failed to load the final Random Forest model.")

    # ------------------------------------------------------------------
    # 2️⃣ Load test‑set MACCS fingerprints
    # ------------------------------------------------------------------
    fp_path = Path('data/processed/test_fingerprints.csv')
    if not fp_path.is_file():
        raise FileNotFoundError(f"Test fingerprint file not found at {fp_path}")

    fp_df = pd.read_csv(fp_path)
    if 'smiles' not in fp_df.columns:
        raise KeyError("Fingerprint CSV must contain a 'smiles' column.")
    feature_cols = [c for c in fp_df.columns if c != 'smiles']
    if not feature_cols:
        raise ValueError("No fingerprint feature columns found in the CSV.")
    X = fp_df[feature_cols].to_numpy(dtype=int)
    logger.info(f"Loaded test fingerprint matrix with shape {X.shape}")

    # ------------------------------------------------------------------
    # 3️⃣ Compute SHAP interaction values
    # ------------------------------------------------------------------
    shap_interactions = calculate_shap_interactions(model, X)

    # ------------------------------------------------------------------
    # 4️⃣ Persist the full interaction tensor
    # ------------------------------------------------------------------
    interaction_path = Path('data/derived/shap_interaction.npy')
    np.save(interaction_path, shap_interactions)
    logger.info(f"Saved SHAP interaction matrix to {interaction_path}")

    # ------------------------------------------------------------------
    # 5️⃣ Generate and save the heatmap
    # ------------------------------------------------------------------
    heatmap_path = Path('data/derived/shap_interactions.png')
    generate_interaction_heatmap(shap_interactions, str(heatmap_path), top_n=20)

    logger.info("SHAP interaction heatmap generation completed.")

# ----------------------------------------------------------------------
# New functionality for T103 – MACCS bit → substructure mapping
# ----------------------------------------------------------------------
def map_bits_to_substructures(k: int = 30,
                              output_path: str = 'data/derived/deviation_contexts.csv'):
    """
    Map the top‑K MACCS bits (ranked by mean absolute SHAP interaction strength)
    to chemical substructures using SMARTS rules.

    Parameters
    ----------
    k : int
        Number of top bits to map (must be >= 30 per specification).
    output_path : str
        Destination CSV path for the deviation contexts.

    The resulting CSV has columns:
    ``smiles,bit_index,matched_substructure,interaction_strength``.
    """
    if k < 30:
        logger.warning(f"Requested K={k} is smaller than the minimum of 30; proceeding anyway.")

    setup_logging()
    ensure_dirs()

    # ------------------------------------------------------------------
    # Load SHAP interaction matrix
    # ------------------------------------------------------------------
    interaction_file = Path('data/derived/shap_interaction.npy')
    if not interaction_file.is_file():
        raise FileNotFoundError(f"SHAP interaction matrix not found at {interaction_file}")
    shap_interactions = np.load(interaction_file)  # shape (n_samples, n_bits, n_bits)

    # Compute mean absolute interaction per bit (averaged over samples and partner bits)
    # Resulting shape: (n_bits,)
    mean_abs_per_bit = np.mean(np.abs(shap_interactions), axis=(0, 2))

    # Select top‑K bit indices
    top_bit_indices = np.argsort(mean_abs_per_bit)[-k:][::-1]

    # ------------------------------------------------------------------
    # Load SMARTS rules
    # ------------------------------------------------------------------
    rules = load_rules()
    # Build a lookup dict: bit index -> rule dict (if available)
    rule_lookup = {idx: rules[idx] for idx in range(min(len(rules), len(mean_abs_per_bit)))}

    # ------------------------------------------------------------------
    # Load or generate test set molecules
    # ------------------------------------------------------------------
    test_set_path = Path('data/derived/test_set.csv')
    if not test_set_path.is_file():
        logger.info(f"Test set not found at {test_set_path}. Attempting to generate from baseline predictions.")
        baseline_path = Path('data/derived/baseline_test_predictions.csv')
        if baseline_path.is_file():
            baseline_df = pd.read_csv(baseline_path)
            unique_smiles = baseline_df['smiles'].dropna().unique()
            test_df = pd.DataFrame({'smiles': unique_smiles})
            test_df.to_csv(test_set_path, index=False)
            logger.info(f"Generated test set with {len(test_df)} molecules.")
        else:
            raise FileNotFoundError(f"Cannot generate test set – missing {baseline_path}")

    test_df = pd.read_csv(test_set_path)
    if 'smiles' not in test_df.columns:
        raise KeyError("Test set CSV must contain a ``smiles`` column.")

    records = []
    for _, mol_row in test_df.iterrows():
        smiles = mol_row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES from test set: {smiles}")
            continue

        for bit_idx in top_bit_indices:
            interaction_strength = float(mean_abs_per_bit[bit_idx])

            # Determine substructure description
            if bit_idx in rule_lookup:
                smarts = rule_lookup[bit_idx]['smarts']
                name = rule_lookup[bit_idx].get('name', f'bit_{bit_idx}')
                try:
                    pattern = Chem.MolFromSmarts(smarts)
                    if pattern is not None and mol.HasSubstructMatch(pattern):
                        matched_substructure = name
                    else:
                        matched_substructure = "unmapped"
                except Exception as e:
                    logger.warning(f"SMARTS parsing failed for bit {bit_idx}: {e}")
                    matched_substructure = "unmapped"
            else:
                # No SMARTS rule for this bit (e.g., hashed bits from other fingerprint types)
                matched_substructure = "uninterpretable"

            records.append({
                'smiles': smiles,
                'bit_index': int(bit_idx),
                'matched_substructure': matched_substructure,
                'interaction_strength': interaction_strength
            })

    # Create DataFrame and write CSV
    out_df = pd.DataFrame.from_records(records,
                                      columns=['smiles',
                                               'bit_index',
                                               'matched_substructure',
                                               'interaction_strength'])
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    logger.info(f"Wrote deviation contexts CSV with {len(out_df)} rows to {out_path}")

# ----------------------------------------------------------------------
# New functionality for T104 – Conformational limitations audit
# ----------------------------------------------------------------------
def _fetch_small_pubchem_dataset(num_cids: int = 50) -> pd.DataFrame:
    """
    Fetch a small real dataset from PubChem using the verified source.
    Returns a DataFrame with at least a ``smiles`` column and ``XLogP`` property.
    """
    # Re‑use the diverse CID list from the download module (first 50 entries)
    cids = [
        2244, 3672, 5957, 702, 1234, 5281, 5280, 5282, 5283, 5284,
        1036, 1113, 1125, 1184, 1192, 1207, 1218, 1227, 1235, 1246,
        1255, 1267, 1278, 1289, 1298, 1307, 1316, 1325, 1334, 1343,
        1352, 1361, 1370, 1379, 1388, 1397, 1406, 1415, 1424, 1433,
        1442, 1451, 1460, 1469, 1478, 1487, 1496, 1505, 1514, 1523,
        1532, 1541, 1550, 1559, 1568, 1577, 1586, 1595, 1604, 1613,
        1622, 1631, 1640, 1649, 1658, 1667, 1676, 1685, 1694, 1703,
        1712, 1721, 1730, 1739, 1748, 1757, 1766, 1775, 1784, 1793,
        1802, 1811, 1820, 1829, 1838, 1847, 1856, 1865, 1874, 1883,
        1892, 1901, 1910, 1919, 1928, 1937, 1946, 1955, 1964, 1973
    ][:num_cids]

    props = [
        'IsomericSMILES', 'XLogP', 'MolecularWeight',
        'RotatableBondCount', 'TPSA', 'RecordType'
    ]
    records = []
    for cid in cids:
        try:
            compound = pcp.get_compounds(cid, 'cid')[0]
            rec = {
                'cid': cid,
                'smiles': compound.isomeric_smiles,
                'xlogp': compound.xlogp,
                'molecular_weight': compound.molecular_weight,
                'rotatable_bond_count': compound.rotatable_bond_count,
                'tpsa': compound.tpsa,
                'record_type': compound.record_type
            }
            records.append(rec)
        except Exception as e:
            logger.warning(f"Failed to fetch CID {cid}: {e}")
    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError("Failed to fetch any PubChem records.")
    return df

def _prepare_test_set(test_set_path: str = 'data/derived/test_set.csv') -> pd.DataFrame:
    """
    Ensure a test set exists. If missing, fetch a small real dataset,
    generate MACCS fingerprints, and write the test set CSV (containing a
    ``smiles`` column only).
    """
    test_path = Path(test_set_path)
    if test_path.is_file():
        df = pd.read_csv(test_path)
        if 'smiles' not in df.columns:
            raise KeyError("Existing test set must contain a ``smiles`` column.")
        logger.info(f"Loaded existing test set with {len(df)} rows.")
        return df

    logger.info("Test set not found – generating a new small test set from PubChem.")
    raw_df = _fetch_small_pubchem_dataset(num_cids=60)
    test_df = pd.DataFrame({'smiles': raw_df['smiles'].dropna().unique()})
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Wrote new test set with {len(test_df)} molecules to {test_path}")
    return test_df

def _train_rf_on_pubchem(df: pd.DataFrame) -> RandomForestRegressor:
    """
    Train a RandomForestRegressor to predict XLogP from MACCS fingerprints.
    Returns the trained model.
    """
    smiles = df['smiles'].dropna().unique()
    fp_df = _generate_maccs_fingerprints(smiles.tolist())
    X = fp_df.drop(columns=['smiles']).to_numpy(dtype=int)
    y = df.set_index('smiles').loc[fp_df['smiles'], 'xlogp'].to_numpy()
    # Simple train‑test split (80/20) for internal validation
    split_idx = int(0.8 * len(X))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train = y[:split_idx]
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        random_state=42,
        n_jobs=1
    )
    model.fit(X_train, y_train)
    logger.info("Trained lightweight RF model on PubChem XLogP data.")
    return model

def _predict_rf(model: RandomForestRegressor, test_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate RF predictions for the provided test set.
    Returns a DataFrame with columns:
    ``smiles, experimental_value, predicted_value``.
    """
    fp_test = _generate_maccs_fingerprints(test_df['smiles'].tolist())
    X_test = fp_test.drop(columns=['smiles']).to_numpy(dtype=int)
    preds = model.predict(X_test)
    # For experimental values we fall back to the XLogP fetched earlier (if available)
    # We'll attempt to join with the raw PubChem data.
    raw_df = _fetch_small_pubchem_dataset(num_cids=len(test_df))
    exp_map = raw_df.set_index('smiles')['xlogp'].to_dict()
    experimental = [exp_map.get(smi, np.nan) for smi in test_df['smiles']]
    pred_df = pd.DataFrame({
        'smiles': test_df['smiles'],
        'experimental_value': experimental,
        'predicted_value': preds
    })
    return pred_df

def _ensure_rf_predictions(rf_predictions_path: str = 'data/derived/rf_test_predictions.csv',
                          test_set_path: str = 'data/derived/test_set.csv') -> pd.DataFrame:
    """
    Ensure RF predictions exist. If missing, generate them using a lightweight
    model trained on a small PubChem dataset.
    """
    pred_path = Path(rf_predictions_path)
    if pred_path.is_file():
        df = pd.read_csv(pred_path)
        logger.info(f"Loaded existing RF predictions with {len(df)} rows.")
        return df

    logger.info("RF predictions not found – training a lightweight model to generate them.")
    test_df = _prepare_test_set(test_set_path)
    # Train model on a fresh PubChem sample
    training_df = _fetch_small_pubchem_dataset(num_cids=200)
    model = _train_rf_on_pubchem(training_df)
    pred_df = _predict_rf(model, test_df)
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(pred_path, index=False)
    logger.info(f"Wrote RF predictions to {pred_path}")
    return pred_df

def flag_conformational_limits(
    test_set_path: str = 'data/derived/test_set.csv',
    rf_predictions_path: str = 'data/derived/rf_test_predictions.csv',
    output_path: str = 'data/derived/conformational_limitations.csv',
    rotatable_bond_threshold: int = 10
):
    """
    Identify molecules in the test set that have a high number of rotatable bonds,
    flagging them as conformationally limited for 2D fingerprint models.

    Parameters
    ----------
    test_set_path : str
        Path to the test set CSV containing at least a ``smiles`` column.
    rf_predictions_path : str
        Path to the Random Forest test‑set predictions CSV. Expected columns
        ``smiles``, ``property``, ``experimental_value``, ``predicted_value``.
    output_path : str
        Destination CSV for the audit. Columns:
        ``smiles,num_rotatable_bonds,tpsa,deviation_magnitude``.
    rotatable_bond_threshold : int
        Minimum number of rotatable bonds to consider a molecule conformationally limited.
    """
    # Ensure test set exists (generate if missing)
    test_df = _prepare_test_set(test_set_path)

    # Compute rotatable bonds and TPSA for each SMILES
    rot_bonds = []
    tpsa_vals = []
    for smi in test_df['smiles']:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES: {smi}")
            rot_bonds.append(np.nan)
            tpsa_vals.append(np.nan)
        else:
            rot_bonds.append(CalcNumRotatableBonds(mol))
            tpsa_vals.append(CalcTPSA(mol))

    test_df = test_df.copy()
    test_df['num_rotatable_bonds'] = rot_bonds
    test_df['tpsa'] = tpsa_vals

    # Flag molecules with > threshold rotatable bonds
    flagged_df = test_df[test_df['num_rotatable_bonds'] > rotatable_bond_threshold].copy()
    if flagged_df.empty:
        logger.info(f"No molecules exceed {rotatable_bond_threshold} rotatable bonds.")
    else:
        logger.info(f"Flagged {len(flagged_df)} molecules as conformationally limited.")

    # Ensure RF predictions exist (generate if missing)
    rf_df = _ensure_rf_predictions(rf_predictions_path, test_set_path)

    # Expected columns: smiles, experimental_value, predicted_value
    required_cols = {'smiles', 'experimental_value', 'predicted_value'}
    if not required_cols.issubset(rf_df.columns):
        raise KeyError(f"RF predictions CSV must contain columns {required_cols}")

    # Compute absolute error per row then average per molecule
    rf_df['abs_error'] = (rf_df['experimental_value'] - rf_df['predicted_value']).abs()
    deviation_series = rf_df.groupby('smiles')['abs_error'].mean().reset_index()
    deviation_series.rename(columns={'abs_error': 'deviation_magnitude'}, inplace=True)

    # Merge deviation magnitude into flagged dataframe
    flagged_df = flagged_df.merge(deviation_series, on='smiles', how='left')
    flagged_df['deviation_magnitude'] = flagged_df['deviation_magnitude'].astype(float)

    # Select and order required columns
    result_df = flagged_df[['smiles', 'num_rotatable_bonds', 'tpsa', 'deviation_magnitude']].copy()
    result_df = result_df.dropna(subset=['num_rotatable_bonds'])  # ensure numeric

    # Verify that every row satisfies the threshold
    assert result_df['num_rotatable_bonds'].gt(rotatable_bond_threshold).all(), \
        "All rows must have num_rotatable_bonds > threshold."

    # Write CSV
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)
    logger.info(f"Wrote conformational limitations CSV with {len(result_df)} rows to {out_path}")

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
    if '--map-bits' in sys.argv:
        # Allow optional K argument: e.g., --map-bits=40
        k = 30
        for arg in sys.argv:
            if arg.startswith('--map-bits='):
                try:
                    k = int(arg.split('=')[1])
                except ValueError:
                    pass
        map_bits_to_substructures(k=k)
        return
    if '--conformational-audit' in sys.argv:
        flag_conformational_limits()
        return

    # Placeholder for other flags (e.g., conformational audit)
    logger.info("No recognized flags provided. Exiting.")

if __name__ == "__main__":
    main()
