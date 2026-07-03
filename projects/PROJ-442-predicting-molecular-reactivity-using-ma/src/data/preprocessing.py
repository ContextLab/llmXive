"""
Preprocessing module for molecular reactivity prediction.
Handles feature extraction, dimensionality reduction, and data normalization.
"""
import logging
import os
import hashlib
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.stats import zscore
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression, mutual_info_regression
from sklearn.preprocessing import StandardScaler
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from src.utils.logging import get_logger
from src.utils.state_manager import register_artifact, update_stage_status
from src.modeling.config import load_config

logger = get_logger(__name__)


def extract_features_from_smiles(smiles: str) -> Dict[str, float]:
    """
    Extract molecular features from a SMILES string.
    Returns a dictionary of feature names and values.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}

        features = {}

        # Basic descriptors
        features['MolecularWeight'] = Descriptors.MolWt(mol)
        features['NumAtoms'] = mol.GetNumAtoms()
        features['NumBonds'] = mol.GetNumBonds()
        features['NumRings'] = rdMolDescriptors.CalcNumRings(mol)
        features['NumHDonors'] = rdMolDescriptors.CalcNumHBD(mol)
        features['NumHAcceptors'] = rdMolDescriptors.CalcNumHBA(mol)
        features['LogP'] = Descriptors.MolLogP(mol)
        features['TPSA'] = Descriptors.TPSA(mol)

        # Topological indices
        features['WienerIndex'] = rdMolDescriptors.CalcWienerIndex(mol)
        features['BalabanJ'] = rdMolDescriptors.CalcBalabanJ(mol)
        features['Kappa1'] = rdMolDescriptors.CalcKappa1(mol)
        features['Kappa2'] = rdMolDescriptors.CalcKappa2(mol)
        features['Kappa3'] = rdMolDescriptors.CalcKappa3(mol)

        # Atom type counts
        atom_counts = {}
        for atom in mol.GetAtoms():
            symbol = atom.GetSymbol()
            atom_counts[symbol] = atom_counts.get(symbol, 0) + 1
        
        for symbol, count in atom_counts.items():
            features[f'Num_{symbol}'] = count

        # Bond type counts
        bond_counts = {
            'Single': 0, 'Double': 0, 'Triple': 0, 'Aromatic': 0
        }
        for bond in mol.GetBonds():
            bond_type = bond.GetBondType().name
            if bond_type == 'SINGLE':
                bond_counts['Single'] += 1
            elif bond_type == 'DOUBLE':
                bond_counts['Double'] += 1
            elif bond_type == 'TRIPLE':
                bond_counts['Triple'] += 1
            elif bond_type == 'AROMATIC':
                bond_counts['Aromatic'] += 1
        
        for bond_type, count in bond_counts.items():
            features[f'Num_{bond_type}Bonds'] = count

        return features
    except Exception as e:
        logger.warning(f"Failed to extract features from SMILES: {smiles}, error: {e}")
        return {}


def batch_extract_features(df: pd.DataFrame, smiles_column: str = 'reactant_smiles') -> pd.DataFrame:
    """
    Extract features from a batch of SMILES strings in a DataFrame.
    Returns a new DataFrame with feature columns appended.
    """
    logger.info(f"Starting feature extraction for {len(df)} rows")
    
    all_features = []
    valid_count = 0
    invalid_count = 0

    for idx, row in df.iterrows():
        smiles = row[smiles_column]
        features = extract_features_from_smiles(smiles)
        
        if not features:
            invalid_count += 1
            continue
        
        valid_count += 1
        all_features.append(features)

    logger.info(f"Feature extraction complete: {valid_count} valid, {invalid_count} invalid")

    if not all_features:
        return pd.DataFrame()

    feature_df = pd.DataFrame(all_features)
    
    # Combine with original dataframe (drop the SMILES column if needed, or keep it)
    result_df = pd.concat([df.reset_index(drop=True), feature_df], axis=1)
    
    return result_df


def apply_variance_threshold(X: np.ndarray, threshold: float = 0.0) -> Tuple[np.ndarray, VarianceThreshold]:
    """
    Apply variance thresholding to remove low-variance features.
    """
    logger.info(f"Applying variance threshold with threshold={threshold}")
    selector = VarianceThreshold(threshold=threshold)
    X_reduced = selector.fit_transform(X)
    kept_features = selector.get_support(indices=True)
    logger.info(f"Variance threshold removed {X.shape[1] - X_reduced.shape[1]} features")
    return X_reduced, selector


def apply_select_kbest(X: np.ndarray, y: np.ndarray, k: int = 100, 
                      scoring_func: str = 'f_regression') -> Tuple[np.ndarray, SelectKBest]:
    """
    Apply SelectKBest for feature selection.
    
    Args:
        X: Feature matrix
        y: Target variable
        k: Number of features to select
        scoring_func: Scoring function ('f_regression' or 'mutual_info_regression')
    
    Returns:
        Tuple of (reduced feature matrix, fitted selector)
    """
    logger.info(f"Applying SelectKBest with k={k}, scoring={scoring_func}")
    
    if scoring_func == 'f_regression':
        selector = SelectKBest(score_func=f_regression, k=k)
    elif scoring_func == 'mutual_info_regression':
        selector = SelectKBest(score_func=mutual_info_regression, k=k)
    else:
        raise ValueError(f"Unknown scoring function: {scoring_func}")
    
    X_reduced = selector.fit_transform(X, y)
    kept_indices = selector.get_support(indices=True)
    logger.info(f"SelectKBest selected {len(kept_indices)} features from {X.shape[1]}")
    
    return X_reduced, selector


def normalize_features(X: np.ndarray) -> Tuple[np.ndarray, StandardScaler]:
    """
    Normalize features using Z-score standardization.
    """
    logger.info("Normalizing features with Z-score")
    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)
    return X_normalized, scaler


def process_features(input_path: str, output_path: str, config_path: str = None) -> Dict[str, Any]:
    """
    Main pipeline for feature processing:
    1. Load filtered reactions
    2. Extract molecular features
    3. Apply variance thresholding
    4. Apply SelectKBest
    5. Normalize features
    6. Save processed feature matrix
    
    Args:
        input_path: Path to filtered reactions CSV
        output_path: Path to save feature matrix parquet
        config_path: Path to config file (optional)
    
    Returns:
        Dictionary with processing metadata
    """
    logger.info(f"Starting feature processing pipeline")
    
    # Load config
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'modeling', 'config.yaml')
    config = load_config(config_path)
    
    # Load input data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Identify target column
    target_col = config.get('modeling', {}).get('target_column', 'yield_pct')
    if target_col not in df.columns:
        # Fallback to success_flag if yield_pct not available
        if 'success_flag' in df.columns:
            target_col = 'success_flag'
            logger.warning(f"Target column '{target_col}' not found, using 'success_flag' instead")
        else:
            raise ValueError(f"Neither 'yield_pct' nor 'success_flag' found in data")
    
    # Extract features
    df_features = batch_extract_features(df, smiles_column='reactant_smiles')
    
    if df_features.empty:
        raise ValueError("No valid features extracted from data")
    
    # Separate features and target
    feature_cols = [col for col in df_features.columns if col not in ['reactant_smiles', 'reaction_type', target_col, 'id']]
    X = df_features[feature_cols].values
    y = df_features[target_col].values
    
    logger.info(f"Feature matrix shape: {X.shape}")
    
    # Apply variance thresholding
    X_vt, vt_selector = apply_variance_threshold(X, threshold=0.0)
    feature_cols_vt = [feature_cols[i] for i in vt_selector.get_support(indices=True)]
    
    # Apply SelectKBest
    k = config.get('modeling', {}).get('feature_selection', {}).get('k', 100)
    scoring_func = config.get('modeling', {}).get('feature_selection', {}).get('scoring_function', 'f_regression')
    
    X_kbest, kbest_selector = apply_select_kbest(X_vt, y, k=k, scoring_func=scoring_func)
    feature_cols_kbest = [feature_cols_vt[i] for i in kbest_selector.get_support(indices=True)]
    
    # Normalize features
    X_normalized, scaler = normalize_features(X_kbest)
    
    # Create final feature dataframe
    final_df = pd.DataFrame(X_normalized, columns=feature_cols_kbest)
    final_df[target_col] = y
    
    # Save to parquet
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Saving feature matrix to {output_path}")
    final_df.to_parquet(output_path, index=False)
    
    # Compute checksum
    with open(output_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    # Register artifact
    register_artifact(
        stage='feature_extraction',
        artifact_name='feature_matrix',
        path=output_path,
        checksum=checksum,
        metadata={
            'input_rows': len(df),
            'output_features': len(feature_cols_kbest),
            'original_features': len(feature_cols),
            'variance_threshold_removed': len(feature_cols) - len(feature_cols_vt),
            'kbest_selected': len(feature_cols_kbest),
            'scoring_function': scoring_func
        }
    )
    
    # Update stage status
    update_stage_status(
        stage='feature_extraction',
        status='completed',
        artifact_path=output_path
    )
    
    logger.info(f"Feature processing complete. Final shape: {final_df.shape}")
    
    return {
        'output_path': output_path,
        'checksum': checksum,
        'final_shape': final_df.shape,
        'features_selected': len(feature_cols_kbest),
        'features_removed': len(feature_cols) - len(feature_cols_kbest)
    }


def main():
    """
    Entry point for feature processing pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Process molecular features for reactivity prediction')
    parser.add_argument('--input', type=str, default='data/processed/filtered_reactions.csv',
                      help='Path to input filtered reactions CSV')
    parser.add_argument('--output', type=str, default='data/processed/feature_matrix.parquet',
                      help='Path to output feature matrix parquet')
    parser.add_argument('--config', type=str, default='src/modeling/config.yaml',
                      help='Path to config file')
    
    args = parser.parse_args()
    
    setup_logger(__name__)
    process_features(args.input, args.output, args.config)
    
    logger.info("Feature processing pipeline completed successfully")


if __name__ == '__main__':
    main()