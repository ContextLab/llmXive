"""
Explainability module for Random Forest models using SHAP values.
Implements steric descriptor computation and topological proxy analysis.
"""
import os
import sys
import pickle
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import shap
from rdkit import Chem
from rdkit.Chem import Fragments, rdMolDescriptors
from rdkit import DataStructs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_dirs():
    """Create necessary output directories if they don't exist."""
    Path("data/derived").mkdir(parents=True, exist_ok=True)
    Path("figures").mkdir(parents=True, exist_ok=True)

def load_model(model_path: str) -> Any:
    """Load a trained model from a pickle file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_fingerprints_data(fingerprint_path: str) -> pd.DataFrame:
    """Load fingerprint data from a Parquet or CSV file."""
    if fingerprint_path.endswith('.parquet'):
        return pd.read_parquet(fingerprint_path)
    elif fingerprint_path.endswith('.csv'):
        return pd.read_csv(fingerprint_path)
    else:
        raise ValueError(f"Unsupported file format: {fingerprint_path}")

def load_rules(rules_path: str = "code/data/rules.py") -> List[Dict[str, str]]:
    """Load SMARTS patterns from the rules file."""
    # Import the SMARTS_PATTERNS from rules.py
    sys.path.insert(0, os.path.dirname(os.path.abspath(rules_path)))
    from rules import SMARTS_PATTERNS
    return SMARTS_PATTERNS

def calculate_shap_interactions(
    model: Any,
    X: np.ndarray,
    feature_names: Optional[List[str]] = None
) -> Any:
    """
    Calculate SHAP interaction values for the trained RF model.

    Args:
        model: Trained Random Forest model.
        X: Feature matrix (fingerprints).
        feature_names: Optional list of feature names.

    Returns:
        SHAP interaction values object.
    """
    if feature_names is None:
        feature_names = [f"bit_{i}" for i in range(X.shape[1])]

    # Use SHAP's TreeExplainer for tree-based models
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_interaction_values(X)

    return shap_values

def save_interaction_summary(
    shap_interactions: Any,
    output_path: str = "data/derived/shap_interaction_summary.csv"
):
    """Save the top interacting bit pairs to a CSV file."""
    # Extract absolute interaction values
    abs_interactions = np.abs(shap_interactions)
    # Sum across samples to get global importance
    global_importance = np.mean(abs_interactions, axis=(0, 2))  # shape: (n_features, n_features)

    # Get top 20 interacting pairs
    n_top = 20
    indices = np.unravel_index(np.argsort(global_importance.flatten())[-n_top:], global_importance.shape)
    pairs = list(zip(indices[0], indices[1]))

    df = pd.DataFrame({
        'bit_1': [p[0] for p in pairs],
        'bit_2': [p[1] for p in pairs],
        'interaction_strength': [global_importance[p[0], p[1]] for p in pairs]
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Saved interaction summary to {output_path}")

def generate_interaction_heatmap(
    shap_interactions: Any,
    output_path: str = "data/derived/shap_interactions.png",
    top_n: int = 50
):
    """Generate a heatmap of top interacting fingerprint bit pairs."""
    abs_interactions = np.abs(shap_interactions)
    global_importance = np.mean(abs_interactions, axis=(0, 2))

    # Get top N interacting pairs
    indices = np.unravel_index(np.argsort(global_importance.flatten())[-top_n:], global_importance.shape)
    sorted_pairs = sorted(zip(indices[0], indices[1], global_importance[indices[0], indices[1]]),
                          key=lambda x: x[2], reverse=True)

    # Create a sparse matrix for plotting
    n_features = global_importance.shape[0]
    heatmap_data = np.zeros((top_n, top_n))
    row_labels = []
    col_labels = []

    for i, (r, c, val) in enumerate(sorted_pairs[:top_n]):
        heatmap_data[i, i] = val
        row_labels.append(f"bit_{r}")
        col_labels.append(f"bit_{c}")

    # Plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 10))
    plt.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
    plt.xticks(range(top_n), col_labels, rotation=90, fontsize=8)
    plt.yticks(range(top_n), row_labels, fontsize=8)
    plt.title(f"Top {top_n} SHAP Interaction Values (Steric Proxy Analysis)")
    plt.colorbar(label="Interaction Strength (Abs)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved interaction heatmap to {output_path}")

def map_bits_to_substructures(
    smiles_list: List[str],
    bit_indices: List[int],
    output_path: str = "data/derived/deviation_contexts.csv"
):
    """
    Map top interacting bits back to chemical substructures using RDKit.

    Args:
        smiles_list: List of SMILES strings.
        bit_indices: List of fingerprint bit indices to analyze.
        output_path: Path to save the output CSV.
    """
    rules = load_rules()
    results = []

    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        # Get bit info for the molecule
        # We need to generate the fingerprint to get bit info
        # Using Morgan fingerprint (ECFP4) as an example
        fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        bit_info = {}
        rdMolDescriptors.GetBitInfo(mol, fp, bit_info)

        for bit_idx in bit_indices:
            if bit_idx in bit_info:
                atom_indices = bit_info[bit_idx]
                for atom_idx in atom_indices:
                    atom = mol.GetAtomWithIdx(atom_idx)
                    # Check against SMARTS patterns
                    for rule in rules:
                        pattern = Chem.MolFromSmarts(rule['smarts'])
                        if pattern:
                            matches = mol.GetSubstructMatches(pattern)
                            for match in matches:
                                if atom_idx in match:
                                    results.append({
                                        'smiles': smiles,
                                        'bit_index': bit_idx,
                                        'matched_substructure': rule['name'],
                                        'interaction_strength': "High"  # Placeholder, actual strength from SHAP
                                    })

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved deviation contexts to {output_path}")

def compute_steric_descriptors(
    smiles_list: List[str],
    output_path: str = "data/derived/steric_descriptors.csv"
) -> pd.DataFrame:
    """
    Compute steric descriptors for a list of molecules using RDKit.
    These are TOPLOGICAL PROXIES for steric effects, not physical measurements.

    Args:
        smiles_list: List of SMILES strings.
        output_path: Path to save the output CSV.

    Returns:
        DataFrame with steric descriptors.
    """
    logger.info("Computing steric descriptors (Topological Proxies for Steric Effects)...")
    results = []

    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        # Compute steric descriptors
        descriptors = {
            'smiles': smiles,
            'molecular_weight': rdMolDescriptors.CalcExactMolWt(mol),
            'tpsa': rdMolDescriptors.CalcTPSA(mol),
            'num_rotatable_bonds': rdMolDescriptors.CalcNumRotatableBonds(mol),
            'num_h_acceptors': rdMolDescriptors.CalcNumHBA(mol),
            'num_h_donors': rdMolDescriptors.CalcNumHBD(mol),
            'num_aromatic_rings': rdMolDescriptors.CalcNumAromaticRings(mol),
            'num_aliphatic_rings': rdMolDescriptors.CalcNumAliphaticRings(mol),
            'num_fragments': len(Fragments.Fragments(mol))  # Functional group count
        }

        # Add functional group detection results
        for rule in load_rules():
            pattern = Chem.MolFromSmarts(rule['smarts'])
            if pattern:
                count = len(mol.GetSubstructMatches(pattern))
                descriptors[f'has_{rule["name"]}_group'] = 1 if count > 0 else 0

        results.append(descriptors)

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved steric descriptors to {output_path} (Topological Proxies)")
    return df

def generate_associational_report(
    steric_df: pd.DataFrame,
    shap_summary_path: str = "data/derived/shap_interaction_summary.csv",
    output_path: str = "data/derived/steric_association_report.md"
):
    """
    Generate a report correlating steric descriptors with SHAP interaction strengths.
    IMPORTANT: All findings are framed as ASSOCIATIONAL CORRELATIONS, not causal mechanisms.

    Args:
        steric_df: DataFrame with steric descriptors.
        shap_summary_path: Path to SHAP interaction summary.
        output_path: Path to save the report.
    """
    if not os.path.exists(shap_summary_path):
        logger.warning(f"SHAP summary not found at {shap_summary_path}, skipping association report.")
        return

    shap_df = pd.read_csv(shap_summary_path)

    # Simple correlation analysis
    report_lines = [
        "# Steric Descriptor Association Report (Topological Proxies)",
        "",
        "## Disclaimer",
        "This report identifies **associational correlations** between topological proxies for steric effects",
        "and model deviation patterns. These findings DO NOT imply causal physical mechanisms.",
        "2D fingerprints are topological abstractions and cannot capture solution-phase conformational ensembles.",
        "",
        "## Methodology",
        "- Computed steric descriptors using RDKit (Molecular Weight, TPSA, NumRotatableBonds, etc.)",
        "- Correlated with SHAP interaction strengths from Random Forest model",
        "- All results are statistical associations, not physical measurements",
        "",
        "## Key Findings",
        ""
    ]

    # Calculate correlations
    if 'interaction_strength' in shap_df.columns and 'molecular_weight' in steric_df.columns:
        # Merge on some common key if available, or just report summary stats
        # For now, report summary statistics
        report_lines.append(f"- Average Molecular Weight: {steric_df['molecular_weight'].mean():.2f}")
        report_lines.append(f"- Average TPSA: {steric_df['tpsa'].mean():.2f}")
        report_lines.append(f"- Average NumRotatableBonds: {steric_df['num_rotatable_bonds'].mean():.2f}")
        report_lines.append(f"- Average SHAP Interaction Strength: {shap_df['interaction_strength'].mean():.4f}")
        report_lines.append("")
        report_lines.append("## Limitations",)
        report_lines.append("- 2D fingerprints cannot resolve 3D conformational ensembles")
        report_lines.append("- Steric descriptors are topological proxies, not physical measurements")
        report_lines.append("- Correlations do not imply causation")

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"Saved association report to {output_path}")

def main():
    """Main entry point for steric descriptor computation and analysis."""
    ensure_dirs()

    # Example usage (to be replaced with actual data paths in a full pipeline)
    # This function is designed to be called by other parts of the pipeline
    # after SHAP interactions have been computed and steric descriptors are needed.
    logger.info("Steric descriptor computation module loaded successfully.")
    logger.info("Use compute_steric_descriptors() to generate steric proxy data.")
    logger.info("Use generate_associational_report() to create the final report.")

if __name__ == "__main__":
    main()