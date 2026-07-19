"""
Random Forest Baseline model for predicting molecular surface area.

This module implements a Random Forest regressor using 2D topological descriptors
as input features. It explicitly avoids using 3D geometry to prevent circularity
in the evaluation of the GCN model.

Features extracted:
- Atom counts (C, N, O, S, P, Halogens)
- Ring counts (aromatic, aliphatic)
- Topological indices (MolLogP, TPSA, etc.)
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Project imports
from utils.logging import get_logger
from utils.seed import set_seed
from utils.config import get_project_root, get_data_dir, get_results_dir
from models.evaluation_result import EvaluationResult

logger = get_logger(__name__)

def extract_topological_features(smiles_list: List[str]) -> pd.DataFrame:
    """
    Extract 2D topological descriptors from a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings.
        
    Returns:
        DataFrame with extracted features.
        
    Raises:
        ValueError: If SMILES parsing fails for a significant portion.
    """
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, rdchem
    
    features = []
    failed_count = 0
    
    for i, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                failed_count += 1
                continue
            
            # Atom counts
            atom_counts = {
                'num_atoms_C': mol.GetNumAtoms(6),
                'num_atoms_N': mol.GetNumAtoms(7),
                'num_atoms_O': mol.GetNumAtoms(8),
                'num_atoms_S': mol.GetNumAtoms(16),
                'num_atoms_P': mol.GetNumAtoms(15),
                'num_atoms_F': mol.GetNumAtoms(9),
                'num_atoms_Cl': mol.GetNumAtoms(17),
                'num_atoms_Br': mol.GetNumAtoms(35),
                'num_atoms_I': mol.GetNumAtoms(53),
                'total_atoms': mol.GetNumAtoms(),
            }
            
            # Ring counts
            ring_info = mol.GetRingInfo()
            num_rings = ring_info.NumRings()
            aromatic_rings = sum(1 for ring in ring_info.AtomRings() if all(
                mol.GetAtomWithIdx(idx).GetIsAromatic() for idx in ring
            ))
            aliphatic_rings = num_rings - aromatic_rings
            
            ring_features = {
                'num_rings': num_rings,
                'num_aromatic_rings': aromatic_rings,
                'num_aliphatic_rings': aliphatic_rings,
            }
            
            # Topological indices
            topological_features = {
                'mol_logp': Descriptors.MolLogP(mol),
                'tpsa': Descriptors.TPSA(mol),
                'num_h_donors': Descriptors.NumHDonors(mol),
                'num_h_acceptors': Descriptors.NumHAcceptors(mol),
                'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
                'num_heavy_atoms': Descriptors.HeavyAtomCount(mol),
                'molecular_weight': Descriptors.MolWt(mol),
                'formal_charge': Descriptors.FormalCharge(mol),
                'num_radical_electrons': Descriptors.NumRadicalElectrons(mol),
                'qed': Descriptors.QED(mol),
                'sa_score': rdMolDescriptors.CalcSynthAccessibilityScore(mol),
            }
            
            # Connectivity indices
            connectivity = {
                'num_bonds': mol.GetNumBonds(),
                'avg_bond_order': sum(bond.GetBondTypeAsDouble() for bond in mol.GetBonds()) / max(mol.GetNumBonds(), 1),
            }
            
            # Combine all features
            all_features = {
                'smiles': smiles,
                **atom_counts,
                **ring_features,
                **topological_features,
                **connectivity,
            }
            features.append(all_features)
            
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to process SMILES {i}: {e}")
            continue
    
    if failed_count > len(smiles_list) * 0.1:
        raise ValueError(f"Failed to process {failed_count}/{len(smiles_list)} molecules (>10%)")
    
    df = pd.DataFrame(features)
    logger.info(f"Extracted {len(df)} rows with {len(df.columns) - 1} features")
    return df

def train_baseline_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Train a Random Forest regressor.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        n_estimators: Number of trees.
        max_depth: Maximum tree depth.
        random_state: Random seed.
        
    Returns:
        Tuple of (trained model, validation metrics).
    """
    logger.info(f"Training Random Forest with {n_estimators} trees, max_depth={max_depth}")
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate on validation set
    y_pred_val = model.predict(X_val)
    val_metrics = {
        'mae': mean_absolute_error(y_val, y_pred_val),
        'rmse': np.sqrt(mean_squared_error(y_val, y_pred_val)),
        'r2': r2_score(y_val, y_pred_val),
    }
    
    logger.info(f"Validation metrics: MAE={val_metrics['mae']:.4f}, "
                f"RMSE={val_metrics['rmse']:.4f}, R2={val_metrics['r2']:.4f}")
    
    return model, val_metrics

def evaluate_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> EvaluationResult:
    """
    Evaluate the trained model on the test set.
    
    Args:
        model: Trained Random Forest model.
        X_test: Test features.
        y_test: Test targets.
        
    Returns:
        EvaluationResult object.
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    result = EvaluationResult(
        model_type="RandomForest",
        metrics={
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
        },
        predictions=y_pred.tolist(),
        actuals=y_test.tolist(),
        hyperparameters={
            'n_estimators': model.n_estimators,
            'max_depth': model.max_depth,
            'random_state': model.random_state,
        }
    )
    
    logger.info(f"Test metrics: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
    return result

def load_processed_data_for_baseline() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load processed data with 2D features and SASA targets.
    
    Returns:
        Tuple of (feature DataFrame, target Series).
    """
    data_dir = get_data_dir()
    processed_path = data_dir / "processed" / "graphs_with_features.parquet"
    
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}. "
                                "Run data preprocessing first.")
    
    df = pd.read_parquet(processed_path)
    
    # Extract features from node_features (2D features)
    # The node_features column contains a list of feature vectors for each atom
    # We need to aggregate these to molecule-level features
    
    # For baseline, we'll use the pre-extracted topological features if available
    # Otherwise, we'll extract them from SMILES
    
    required_cols = ['smiles', 'surface_area']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Required columns {required_cols} not found in {processed_path}")
    
    # Check if topological features are already present
    feature_cols = [col for col in df.columns if col not in ['smiles', 'surface_area', 'node_features', 'edge_features']]
    
    if len(feature_cols) < 5:
        # Need to extract features from SMILES
        logger.info("Extracting topological features from SMILES...")
        feature_df = extract_topological_features(df['smiles'].tolist())
        df = df.merge(feature_df, on='smiles', how='left')
    
    # Get feature columns (exclude metadata)
    feature_cols = [col for col in df.columns if col not in ['smiles', 'surface_area']]
    
    logger.info(f"Using {len(feature_cols)} features for baseline model")
    logger.info(f"Features: {feature_cols}")
    
    return df[feature_cols], df['surface_area']

def main(args: Optional[argparse.Namespace] = None):
    """
    Main entry point for training and evaluating the Random Forest baseline.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Train Random Forest Baseline")
        parser.add_argument("--n_estimators", type=int, default=100, help="Number of trees")
        parser.add_argument("--max_depth", type=int, default=None, help="Max tree depth")
        parser.add_argument("--test_size", type=float, default=0.2, help="Test split size")
        parser.add_argument("--val_size", type=float, default=0.1, help="Validation split size")
        parser.add_argument("--seed", type=int, default=42, help="Random seed")
        parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
        args = parser.parse_args()
    
    set_seed(args.seed)
    
    results_dir = get_results_dir() if args.output_dir is None else Path(args.output_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading processed data...")
    X, y = load_processed_data_for_baseline()
    
    # Split data: train -> val -> test
    # First split off test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, shuffle=True
    )
    
    # Then split validation from remaining
    val_size_adjusted = args.val_size / (1 - args.test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size_adjusted, random_state=args.seed, shuffle=True
    )
    
    logger.info(f"Data split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
    
    # Train model
    model, val_metrics = train_baseline_model(
        X_train.values, y_train.values,
        X_val.values, y_val.values,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.seed
    )
    
    # Evaluate on test set
    test_result = evaluate_model(model, X_test.values, y_test.values)
    
    # Save model
    model_path = results_dir / "baseline_random_forest.pkl"
    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Save results
    results = {
        "model_type": "RandomForest",
        "validation_metrics": val_metrics,
        "test_metrics": test_result.metrics,
        "hyperparameters": {
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "test_size": args.test_size,
            "val_size": args.val_size,
            "seed": args.seed,
        },
        "feature_columns": X.columns.tolist(),
        "feature_count": len(X.columns),
    }
    
    results_path = results_dir / "baseline_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {results_path}")
    
    return test_result

if __name__ == "__main__":
    main()
