"""
Explainability module for analyzing Random Forest model predictions on molecular properties.

This module implements SHAP-based interaction analysis, bit-to-substructure mapping,
and conformational limitation detection to interpret model behavior.
"""
import os
import sys
import pickle
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np
import pandas as pd
import shap
from rdkit import Chem
from rdkit.Chem import Descriptors, Fragments, rdMolDescriptors
from rdkit import DataStructs
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect

# Configure logging
logger = logging.getLogger(__name__)

def load_model(model_path: str) -> Any:
    """
    Load a pickled Random Forest model.

    Args:
        model_path: Path to the pickle file containing the trained model.

    Returns:
        The loaded model object.
    """
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_fingerprints_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load fingerprints and target values from a Parquet file.

    Args:
        data_path: Path to the Parquet file containing fingerprints and targets.

    Returns:
        Tuple of (fingerprints DataFrame, target Series).
    """
    df = pd.read_parquet(data_path)
    # Assume first column is SMILES, last is target, rest are fingerprints
    smiles_col = df.columns[0]
    target_col = df.columns[-1]
    fingerprint_cols = df.columns[1:-1]

    fingerprints = df[fingerprint_cols]
    targets = df[target_col]
    return fingerprints, targets

def get_smiles_for_bit(smiles_list: List[str], bit_index: int, fingerprint_size: int = 2048) -> List[str]:
    """
    Identify SMILES strings that have a specific bit set in their fingerprint.

    Args:
        smiles_list: List of SMILES strings.
        bit_index: The bit index to check.
        fingerprint_size: Size of the fingerprint (default 2048 for ECFP4).

    Returns:
        List of SMILES strings where the bit is set.
    """
    matching_smiles = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        fp = GetMorganFingerprintAsBitVect(mol, radius=2, nBits=fingerprint_size)
        if fp.GetBit(bit_index):
            matching_smiles.append(smiles)
    return matching_smiles

def map_bits_to_substructures(smiles_list: List[str], bit_indices: List[int], fingerprint_size: int = 2048) -> Dict[int, List[str]]:
    """
    Map fingerprint bits to representative substructures using RDKit.

    Args:
        smiles_list: List of SMILES strings.
        bit_indices: List of bit indices to map.
        fingerprint_size: Size of the fingerprint.

    Returns:
        Dictionary mapping bit indices to lists of representative SMILES.
    """
    bit_to_smiles = {}
    for bit in bit_indices:
        matching = get_smiles_for_bit(smiles_list, bit, fingerprint_size)
        if matching:
            # Return up to 5 representative examples
            bit_to_smiles[bit] = matching[:5]
    return bit_to_smiles

def calculate_shap_interactions(model: Any, fingerprints: np.ndarray, background_data: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate SHAP interaction values for the model.

    Args:
        model: Trained Random Forest model.
        fingerprints: 2D array of fingerprint features.
        background_data: Optional background data for SHAP explainer.

    Returns:
        Tuple of (SHAP interaction values, SHAP main values).
    """
    if background_data is None:
        # Use a small sample as background
        n_samples = min(100, len(fingerprints))
        indices = np.random.choice(len(fingerprints), n_samples, replace=False)
        background_data = fingerprints[indices]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(fingerprints)
    # For regression, shap_values is a single array
    if not isinstance(shap_values, list):
        shap_interactions = explainer.shap_interaction_values(fingerprints)
        return shap_interactions, shap_values
    else:
        # For multi-output, take mean across outputs
        shap_interactions = np.mean([explainer.shap_interaction_values(fingerprints, y_class=i) for i in range(len(shap_values))], axis=0)
        shap_main = np.mean(shap_values, axis=0)
        return shap_interactions, shap_main

def get_top_interacting_bits(shap_interactions: np.ndarray, n_top: int = 20) -> List[Tuple[int, int]]:
    """
    Identify the top interacting bit pairs based on SHAP interaction values.

    Args:
        shap_interactions: 3D array of SHAP interaction values (samples, features, features).
        n_top: Number of top interactions to return.

    Returns:
        List of tuples (bit_i, bit_j) representing top interactions.
    """
    # Aggregate interactions across samples (mean absolute value)
    aggregated = np.abs(shap_interactions).mean(axis=0)
    # Set diagonal to zero (self-interactions are not interesting)
    np.fill_diagonal(aggregated, 0)

    # Get indices of top interactions
    flat_indices = np.unravel_index(np.argsort(aggregated.flatten())[-n_top:], aggregated.shape)
    top_pairs = list(zip(flat_indices[0], flat_indices[1]))

    # Sort by interaction strength
    top_pairs_sorted = sorted(top_pairs, key=lambda p: aggregated[p], reverse=True)
    return top_pairs_sorted

def bootstrap_stability_analysis(
    shap_interactions: np.ndarray,
    top_bits: List[Tuple[int, int]],
    n_bootstrap: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform bootstrap resampling to assess stability of top interacting bits.

    Args:
        shap_interactions: 3D array of SHAP interaction values.
        top_bits: List of top interacting bit pairs.
        n_bootstrap: Number of bootstrap resamples.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with stability metrics for each bit pair.
    """
    np.random.seed(seed)
    n_samples = shap_interactions.shape[0]
    bit_pairs = [f"({i},{j})" for i, j in top_bits]
    stability_data = {pair: [] for pair in bit_pairs}

    for b in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, n_samples, replace=True)
        sampled_interactions = shap_interactions[indices]
        aggregated = np.abs(sampled_interactions).mean(axis=0)
        np.fill_diagonal(aggregated, 0)

        # Get top bits for this resample
        flat_indices = np.unravel_index(np.argsort(aggregated.flatten())[-len(top_bits):], aggregated.shape)
        resample_top = set(zip(flat_indices[0], flat_indices[1]))

        # Check which original top bits are in this resample
        for i, j in top_bits:
            if (i, j) in resample_top or (j, i) in resample_top:
                stability_data[f"({i},{j})"].append(1)
            else:
                stability_data[f"({i},{j})"].append(0)

    # Calculate Jaccard-like stability (frequency of appearance)
    stability_df = pd.DataFrame(stability_data)
    stability_df['mean_stability'] = stability_df.mean(axis=1)
    return stability_df

def save_stability_analysis(stability_df: pd.DataFrame, output_path: str) -> None:
    """
    Save stability analysis results to CSV.

    Args:
        stability_df: DataFrame with stability metrics.
        output_path: Path to save the CSV file.
    """
    stability_df.to_csv(output_path, index=False)
    logger.info(f"Stability analysis saved to {output_path}")

def save_substructure_mapping(mapping: Dict[int, List[str]], output_path: str) -> None:
    """
    Save bit-to-substructure mapping to CSV.

    Args:
        mapping: Dictionary mapping bit indices to SMILES lists.
        output_path: Path to save the CSV file.
    """
    rows = []
    for bit, smiles_list in mapping.items():
        rows.append({
            'bit_index': bit,
            'representative_smiles': ';'.join(smiles_list),
            'count': len(smiles_list)
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Substructure mapping saved to {output_path}")

def validate_topological_nature(smiles: str) -> bool:
    """
    Validate that a molecule's properties are primarily topological.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        True if the molecule is likely topological, False otherwise.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False

    # Check for high flexibility (long chains)
    n_atoms = mol.GetNumAtoms()
    n_rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    if n_rotatable > n_atoms * 0.5:
        return False

    # Check for complex 3D features (stereocenters)
    n_stereocenters = rdMolDescriptors.CalcNumStereoCenters(mol)
    if n_stereocenters > 5:
        return False

    return True

def cross_reference_with_functional_groups(smiles_list: List[str], bit_mapping: Dict[int, List[str]]) -> pd.DataFrame:
    """
    Cross-reference identified substructures with RDKit's functional group detection.

    Args:
        smiles_list: List of SMILES strings.
        bit_mapping: Dictionary mapping bit indices to SMILES lists.

    Returns:
        DataFrame with functional group annotations.
    """
    results = []
    for bit, smiles_examples in bit_mapping.items():
        for smiles in smiles_examples:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue

            # Use RDKit's Fragments module for functional group detection
            fragments = {}
            fragments['num_carbonyl'] = Fragments.fr_COO(mol)
            fragments['num_hydroxyl'] = Fragments.fr_Al_OH(mol)
            fragments['num_amine'] = Fragments.fr_AlNH2(mol)
            fragments['num_ether'] = Fragments.fr_ether(mol)
            fragments['num_ester'] = Fragments.fr_ester(mol)

            # Add global descriptors as context (but not in final output)
            mw = Descriptors.MolWt(mol)
            tpsa = Descriptors.TPSA(mol)

            results.append({
                'bit_index': bit,
                'smiles': smiles,
                'MW': mw,
                'TPSA': tpsa,
                'num_carbonyl': fragments['num_carbonyl'],
                'num_hydroxyl': fragments['num_hydroxyl'],
                'num_amine': fragments['num_amine'],
                'num_ether': fragments['num_ether'],
                'num_ester': fragments['num_ester']
            })

    return pd.DataFrame(results)

def generate_associational_report(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a report framing findings as associational correlations.

    Args:
        results_df: DataFrame with analysis results.
        output_path: Path to save the report.
    """
    with open(output_path, 'w') as f:
        f.write("# Associational Correlation Report\n\n")
        f.write("This report identifies statistical associations between fingerprint bits and molecular properties.\n")
        f.write("These findings represent correlations observed in the training data and should not be interpreted\n")
        f.write("as causal mechanisms. The relationships identified are based on topological fingerprints which\n")
        f.write("are abstractions of molecular structure and may not capture solution-phase conformational effects.\n\n")
        f.write("## Key Findings\n\n")
        f.write(f"Total bit pairs analyzed: {len(results_df)}\n")
        f.write(f"Functional groups detected: {results_df[['num_carbonyl', 'num_hydroxyl', 'num_amine', 'num_ether', 'num_ester']].sum().sum()}\n")
        f.write("\n## Limitations\n\n")
        f.write("- 2D fingerprints cannot capture 3D conformational ensembles\n")
        f.write("- Correlations do not imply causation\n")
        f.write("- Results are specific to the dataset and model used\n")

def detect_conformational_limitations(smiles_list: List[str]) -> pd.DataFrame:
    """
    Identify molecules where 2D topology likely fails to capture conformational effects.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        DataFrame with conformational limitation flags.
    """
    results = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        n_atoms = mol.GetNumAtoms()
        n_rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
        n_rings = rdMolDescriptors.CalcNumRings(mol)

        # Heuristic: long flexible chains or high ring strain
        is_flexible = n_rotatable > n_atoms * 0.4
        is_rigid = n_rings > 3 and n_rotatable < n_atoms * 0.1
        has_steric_clash = False  # Would need 3D conformation analysis

        results.append({
            'smiles': smiles,
            'n_atoms': n_atoms,
            'n_rotatable_bonds': n_rotatable,
            'n_rings': n_rings,
            'is_flexible_chain': is_flexible,
            'is_rigid_ring_system': is_rigid,
            'potential_3d_failure': is_flexible or has_steric_clash
        })

    return pd.DataFrame(results)

def generate_conformational_limitation_report(limitations_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a report on conformational limitations of the 2D fingerprint approach.

    Args:
        limitations_df: DataFrame with limitation flags.
        output_path: Path to save the report.
    """
    with open(output_path, 'w') as f:
        f.write("# Conformational Limitation Report\n\n")
        f.write("This report identifies molecules where 2D topological fingerprints may fail to capture\n")
        f.write("solution-phase conformational ensembles, as noted by reviewer Rosalind Franklin.\n\n")

        n_flexible = limitations_df['is_flexible_chain'].sum()
        n_total = len(limitations_df)
        f.write(f"## Summary\n\n")
        f.write(f"Total molecules analyzed: {n_total}\n")
        f.write(f"Molecules with long flexible chains: {n_flexible} ({100*n_flexible/n_total:.1f}%)\n")
        f.write(f"These molecules may exhibit significant conformational diversity in solution\n")
        f.write(f"that is not captured by static 2D fingerprints.\n\n")

        f.write("## Methodology\n\n")
        f.write("Flexibility is assessed using the ratio of rotatable bonds to total atoms.\n")
        f.write("Molecules with >40% rotatable bonds are flagged as potentially problematic.\n")
        f.write("\n## Implications\n\n")
        f.write("For these molecules, the model's predictions may be less reliable as the\n")
        f.write("topological abstraction cannot capture the dynamic conformational ensemble.\n")

def main() -> None:
    """
    Main entry point for the explainability analysis pipeline.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    model_path = project_root / 'data' / 'derived' / 'final_model.pkl'
    fingerprints_path = project_root / 'data' / 'derived' / 'fingerprints.parquet'
    output_dir = project_root / 'data' / 'derived'

    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        sys.exit(1)

    if not fingerprints_path.exists():
        logger.error(f"Fingerprints file not found: {fingerprints_path}")
        sys.exit(1)

    # Load model and data
    logger.info("Loading model and fingerprints...")
    model = load_model(str(model_path))
    fingerprints, targets = load_fingerprints_data(str(fingerprints_path))
    fingerprints_np = fingerprints.values

    # Calculate SHAP interactions
    logger.info("Calculating SHAP interactions...")
    shap_interactions, shap_main = calculate_shap_interactions(model, fingerprints_np)

    # Get top interacting bits
    top_bits = get_top_interacting_bits(shap_interactions, n_top=20)
    logger.info(f"Top {len(top_bits)} interacting bit pairs identified")

    # Stability analysis
    logger.info("Performing bootstrap stability analysis...")
    stability_df = bootstrap_stability_analysis(shap_interactions, top_bits, n_bootstrap=100, seed=42)
    save_stability_analysis(stability_df, str(output_dir / 'stability_analysis.csv'))

    # Map bits to substructures
    smiles_list = fingerprints.index.tolist() if hasattr(fingerprints, 'index') else []
    if not smiles_list:
        # Try to load SMILES from a separate file or assume first column
        logger.warning("No SMILES found in fingerprints index, skipping substructure mapping")
    else:
        bit_mapping = map_bits_to_substructures(smiles_list, [i for i, j in top_bits])
        save_substructure_mapping(bit_mapping, str(output_dir / 'shap_substructure_mapping.csv'))

    # Cross-reference with functional groups
    if bit_mapping:
        functional_groups_df = cross_reference_with_functional_groups(smiles_list, bit_mapping)
        # Save without global descriptors to final output
        final_output = functional_groups_df[['bit_index', 'smiles', 'num_carbonyl', 'num_hydroxyl', 'num_amine', 'num_ether', 'num_ester']]
        final_output.to_csv(output_dir / 'shap_substructure_mapping.csv', index=False)

    # Generate associational report
    generate_associational_report(final_output, str(output_dir / 'associational_report.txt'))

    # Conformational limitation analysis
    limitations_df = detect_conformational_limitations(smiles_list)
    generate_conformational_limitation_report(limitations_df, str(output_dir / 'conformational_limitation_report.txt'))

    logger.info("Explainability analysis complete")

if __name__ == "__main__":
    main()
