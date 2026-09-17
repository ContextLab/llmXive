"""
Preprocessing module for molecular feature extraction and dimensionality reduction.
Handles conversion of reaction data to feature matrices and saves them to Parquet.
"""
import pandas as pd
import hashlib
import logging
import os
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
import numpy as np

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import register_artifact, update_stage_status
from src.modeling.config import load_config

# --- Configuration & Constants ---
FEATURE_COLUMNS = [
    'molecular_weight', 'num_atoms', 'num_bonds', 'num_rings',
    'num_aromatic_rings', 'num_aliphatic_rings', 'num_h_bond_donors',
    'num_h_bond_acceptors', 'logP', 'tpsa', 'num_rotatable_bonds',
    'num_heavy_atoms', 'fraction_csp3', 'num_saturated_rings',
    'num_heteroatoms', 'num_carbon_atoms', 'num_nitrogen_atoms',
    'num_oxygen_atoms', 'num_sulfur_atoms', 'num_phosphorus_atoms',
    'num_halogens', 'num_chiral_centers', 'max_ring_size', 'min_ring_size',
    'avg_bond_order', 'ring_count', 'complexity', 'qed', 'sa_score'
]

# Map standard RDKit descriptors to our column names
DESCRIPTOR_MAP = {
    'MW': 'molecular_weight',
    'NumAtoms': 'num_atoms',
    'NumBonds': 'num_bonds',
    'NumRings': 'num_rings',
    'NumAromaticRings': 'num_aromatic_rings',
    'NumAliphaticRings': 'num_aliphatic_rings',
    'NumHDonors': 'num_h_bond_donors',
    'NumHAcceptors': 'num_h_bond_acceptors',
    'MolLogP': 'logP',
    'TPSA': 'tpsa',
    'NumRotatableBonds': 'num_rotatable_bonds',
    'NumHeavyAtoms': 'num_heavy_atoms',
    'FracNumSP3Carbons': 'fraction_csp3',
    'NumSaturatedRings': 'num_saturated_rings',
    'NumHeteroatoms': 'num_heteroatoms',
    'NumCarbonAtoms': 'num_carbon_atoms',
    'NumNitrogenAtoms': 'num_nitrogen_atoms',
    'NumOxygenAtoms': 'num_oxygen_atoms',
    'NumSulfurAtoms': 'num_sulfur_atoms',
    'NumPhosphorusAtoms': 'num_phosphorus_atoms',
    'NumHalogens': 'num_halogens',
    'NumChiralCenters': 'num_chiral_centers',
    'MaxRingSize': 'max_ring_size',
    'MinRingSize': 'min_ring_size',
    'Complexity': 'complexity',
    'QED': 'qed',
    'SA': 'sa_score'
}

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging for the preprocessing module."""
    logger = get_logger(__name__)
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_features_from_smiles(smiles: str) -> Dict[str, float]:
    """
    Extract molecular features from a SMILES string using RDKit.
    
    Args:
        smiles: SMILES string of the molecule
        
    Returns:
        Dictionary of feature values
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {col: np.nan for col in FEATURE_COLUMNS}
    
    features = {}
    
    # Standard descriptors
    features['molecular_weight'] = Descriptors.MolWt(mol)
    features['num_atoms'] = mol.GetNumAtoms()
    features['num_bonds'] = mol.GetNumBonds()
    features['num_rings'] = rdMolDescriptors.CalcNumRings(mol)
    features['num_aromatic_rings'] = rdMolDescriptors.CalcNumAromaticRings(mol)
    features['num_aliphatic_rings'] = rdMolDescriptors.CalcNumAliphaticRings(mol)
    features['num_h_bond_donors'] = rdMolDescriptors.CalcNumHBD(mol)
    features['num_h_bond_acceptors'] = rdMolDescriptors.CalcNumHBA(mol)
    features['logP'] = Descriptors.MolLogP(mol)
    features['tpsa'] = Descriptors.TPSA(mol)
    features['num_rotatable_bonds'] = rdMolDescriptors.CalcNumRotatableBonds(mol)
    features['num_heavy_atoms'] = rdMolDescriptors.CalcNumHeavyAtoms(mol)
    features['fraction_csp3'] = rdMolDescriptors.CalcFractionCSP3(mol)
    features['num_saturated_rings'] = rdMolDescriptors.CalcNumSaturatedRings(mol)
    features['num_heteroatoms'] = rdMolDescriptors.CalcNumHeteroatoms(mol)
    features['num_carbon_atoms'] = rdMolDescriptors.CalcNumCarbonAtoms(mol)
    features['num_nitrogen_atoms'] = rdMolDescriptors.CalcNumNitrogenAtoms(mol)
    features['num_oxygen_atoms'] = rdMolDescriptors.CalcNumOxygenAtoms(mol)
    features['num_sulfur_atoms'] = rdMolDescriptors.CalcNumSulfurAtoms(mol)
    features['num_phosphorus_atoms'] = rdMolDescriptors.CalcNumPhosphorusAtoms(mol)
    features['num_halogens'] = rdMolDescriptors.CalcNumHalogens(mol)
    features['num_chiral_centers'] = rdMolDescriptors.CalcNumAtomStereoCenters(mol)
    
    # Ring size analysis
    ring_info = mol.GetRingInfo()
    if ring_info.NumRings() > 0:
        ring_sizes = [len(ring) for ring in ring_info.AtomRings()]
        features['max_ring_size'] = max(ring_sizes)
        features['min_ring_size'] = min(ring_sizes)
    else:
        features['max_ring_size'] = 0
        features['min_ring_size'] = 0
    
    # Complexity and other metrics
    try:
        features['complexity'] = Descriptors.BertzCT(mol)
    except:
        features['complexity'] = np.nan
        
    try:
        features['qed'] = Descriptors.QED(mol)
    except:
        features['qed'] = np.nan
        
    try:
        features['sa_score'] = rdMolDescriptors.CalcSyntheticAccessibilityScore(mol)[0]
    except:
        features['sa_score'] = np.nan
        
    # Average bond order (simplified)
    bond_orders = []
    for bond in mol.GetBonds():
        bond_orders.append(bond.GetBondType().real)
    features['avg_bond_order'] = np.mean(bond_orders) if bond_orders else 0.0
    
    features['ring_count'] = rdMolDescriptors.CalcNumRings(mol)
    
    return features

def preprocess_batch(df: pd.DataFrame, smiles_column: str = 'smiles') -> pd.DataFrame:
    """
    Preprocess a batch of reactions by extracting features from SMILES.
    
    Args:
        df: DataFrame containing reaction data
        smiles_column: Name of the column containing SMILES strings
        
    Returns:
        DataFrame with extracted features
    """
    logger = get_logger(__name__)
    logger.info(f"Extracting features from {len(df)} molecules...")
    
    feature_data = []
    failed_count = 0
    
    for idx, row in df.iterrows():
        smiles = row[smiles_column]
        features = extract_features_from_smiles(smiles)
        
        # Add reaction metadata
        features['reaction_id'] = row.get('reaction_id', idx)
        features['reaction_type'] = row.get('reaction_type', 'Unknown')
        features['yield_pct'] = row.get('yield_pct', np.nan)
        features['success_flag'] = row.get('success_flag', np.nan)
        
        feature_data.append(features)
        
        if idx % 1000 == 0:
            logger.info(f"Processed {idx}/{len(df)} molecules")
    
    logger.info(f"Feature extraction complete. {failed_count} failures.")
    return pd.DataFrame(feature_data)

def apply_dimensionality_reduction(X: np.ndarray, k: int = 100) -> Tuple[np.ndarray, Any]:
    """
    Apply variance threshold and SelectKBest for dimensionality reduction.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        k: Number of features to select
        
    Returns:
        Reduced feature matrix and the fitted selector
    """
    logger = get_logger(__name__)
    logger.info(f"Applying dimensionality reduction (k={k})...")
    
    # Variance threshold
    vt = VarianceThreshold(threshold=0.01)
    X_var = vt.fit_transform(X)
    logger.info(f"After variance threshold: {X_var.shape[1]} features")
    
    # SelectKBest
    selector = SelectKBest(score_func=f_regression, k=min(k, X_var.shape[1]))
    X_selected = selector.fit_transform(X_var, X_var[:, 0])  # Dummy target for unsupervised-like selection
    
    logger.info(f"After SelectKBest: {X_selected.shape[1]} features")
    return X_selected, selector

def save_feature_matrix(df: pd.DataFrame, output_path: str, checksum: str) -> Dict[str, Any]:
    """
    Save feature matrix to Parquet file with metadata.
    
    Args:
        df: DataFrame containing features
        output_path: Path to save the Parquet file
        checksum: SHA256 checksum of the file
        
    Returns:
        Metadata dictionary
    """
    logger = get_logger(__name__)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False, engine='pyarrow')
    
    # Create metadata
    metadata = {
        'file_path': output_path,
        'checksum': checksum,
        'num_rows': len(df),
        'num_features': len(df.columns),
        'columns': list(df.columns),
        'timestamp': datetime.now().isoformat(),
        'schema': 'FeatureVector'
    }
    
    logger.info(f"Saved feature matrix to {output_path} ({len(df)} rows, {len(df.columns)} features)")
    return metadata

def load_feature_matrix(input_path: str) -> pd.DataFrame:
    """
    Load feature matrix from Parquet file.
    
    Args:
        input_path: Path to the Parquet file
        
    Returns:
        DataFrame with features
    """
    logger = get_logger(__name__)
    logger.info(f"Loading feature matrix from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Feature matrix file not found: {input_path}")
    
    df = pd.read_parquet(input_path, engine='pyarrow')
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} features")
    return df

def preprocess_and_save_features(
    input_path: str,
    output_path: str,
    smiles_column: str = 'smiles',
    k_features: int = 100
) -> Dict[str, Any]:
    """
    Main pipeline: load data, extract features, reduce dimensions, and save.
    
    Args:
        input_path: Path to input reactions file (Parquet)
        output_path: Path to save output features (Parquet)
        smiles_column: Name of SMILES column
        k_features: Number of features to keep after selection
        
    Returns:
        Metadata dictionary
    """
    logger = setup_logging()
    logger.info(f"Starting feature extraction pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load input data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df_reactions = pd.read_parquet(input_path, engine='pyarrow')
    logger.info(f"Loaded {len(df_reactions)} reactions")
    
    # Extract features
    df_features = preprocess_batch(df_reactions, smiles_column)
    
    # Prepare feature matrix (exclude metadata columns)
    feature_cols = [col for col in df_features.columns if col not in ['reaction_id', 'reaction_type', 'yield_pct', 'success_flag']]
    X = df_features[feature_cols].values
    
    # Handle NaN values
    X = np.nan_to_num(X, nan=0.0)
    
    # Dimensionality reduction
    X_reduced, selector = apply_dimensionality_reduction(X, k=k_features)
    
    # Create output DataFrame
    df_output = df_features.copy()
    for i, col in enumerate(feature_cols[:X_reduced.shape[1]]):
        df_output[f'feature_{i}'] = X_reduced[:, i]
    
    # Remove original feature columns to save space
    cols_to_keep = ['reaction_id', 'reaction_type', 'yield_pct', 'success_flag'] + [f'feature_{i}' for i in range(X_reduced.shape[1])]
    df_output = df_output[cols_to_keep]
    
    # Compute checksum before saving
    temp_path = output_path + '.tmp'
    df_output.to_parquet(temp_path, index=False, engine='pyarrow')
    checksum = compute_file_checksum(temp_path)
    
    # Rename to final path
    os.rename(temp_path, output_path)
    
    # Save metadata
    metadata = {
        'file_path': output_path,
        'checksum': checksum,
        'num_rows': len(df_output),
        'num_features': X_reduced.shape[1],
        'original_features': len(feature_cols),
        'columns': list(df_output.columns),
        'timestamp': datetime.now().isoformat(),
        'schema': 'FeatureVector',
        'reduction_method': 'VarianceThreshold + SelectKBest',
        'k_features': k_features
    }
    
    # Register artifact with state manager
    try:
        register_artifact(
            project_id='PROJ-442-predicting-molecular-reactivity-using-ma',
            artifact_type='feature_matrix',
            file_path=output_path,
            checksum=checksum
        )
        update_stage_status(
            project_id='PROJ-442-predicting-molecular-reactivity-using-ma',
            stage='feature_extraction',
            status='completed',
            artifacts=[output_path]
        )
    except Exception as e:
        logger.warning(f"Failed to register artifact with state manager: {e}")
    
    logger.info(f"Feature extraction complete. Saved to {output_path}")
    logger.info(f"Checksum: {checksum}")
    
    return metadata

def main():
    """Main entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and save molecular features')
    parser.add_argument('--input', type=str, required=True, help='Input reactions file (Parquet)')
    parser.add_argument('--output', type=str, required=True, help='Output features file (Parquet)')
    parser.add_argument('--smiles-col', type=str, default='smiles', help='Name of SMILES column')
    parser.add_argument('--k-features', type=int, default=100, help='Number of features to keep')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info(f"Running feature extraction pipeline")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    
    try:
        metadata = preprocess_and_save_features(
            input_path=args.input,
            output_path=args.output,
            smiles_column=args.smiles_col,
            k_features=args.k_features
        )
        
        # Print summary
        print(json.dumps(metadata, indent=2))
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()