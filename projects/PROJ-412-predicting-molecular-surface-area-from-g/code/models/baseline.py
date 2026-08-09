import os
import sys
import json
import logging
import argparse
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

# Import project utilities
from code.utils.logging import get_logger
from code.utils.config import get_project_root, get_results_dir, get_data_dir
from code.utils.seed import set_seed

# Ensure logger is configured
logger = get_logger(__name__)

def extract_geometry_features(smiles: str) -> Optional[Dict[str, float]]:
    """
    Extract 3D geometric descriptors from a SMILES string.
    Requires 3D conformer generation. If 3D generation fails, returns None.
    
    Features:
    - SASA (Solvent Accessible Surface Area)
    - Radius of Gyration
    - Principal Moments of Inertia (normalized)
    - Molecular Weight (redundant but useful for linear model)
    - Atom Count
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Generate 3D conformer
        # Using ETKDGv3 parameters as a standard
        params = Chem.ETKDGv3()
        params.randomSeed = 42
        params.maxAttempts = 500
        params.useExpTorsionAnglePrefs = True
        params.useBasicKnowledge = True
        
        # Add hydrogens for accurate 3D geometry
        mol_h = Chem.AddHs(mol)
        
        # Generate conformer
        result = Chem.EmbedMolecule(mol_h, params)
        if result == -1:
            logger.debug(f"ETKDG failed for SMILES: {smiles}")
            return None
        
        # Optimize geometry
        result = Chem.UFFOptimizeMolecule(mol_h, maxIters=500)
        if result != 0:
            # UFF optimization might not converge but we can still use the geometry
            logger.warning(f"UFF optimization did not fully converge for: {smiles}")
        
        # Calculate descriptors
        # 1. SASA (using Shrake-Rupley algorithm)
        try:
            sasa = rdMolDescriptors.CalcSASA(mol_h)
        except Exception as e:
            logger.warning(f"SASA calculation failed for {smiles}: {e}")
            return None
        
        # 2. Radius of Gyration
        try:
            # rdMolDescriptors.CalcRadiusOfGyration requires 3D coordinates
            r_gyr = rdMolDescriptors.CalcRadiusOfGyration(mol_h)
        except Exception as e:
            logger.warning(f"Radius of Gyration calculation failed for {smiles}: {e}")
            return None
        
        # 3. Principal Moments of Inertia
        try:
            # Returns a tuple of 3 floats (moments)
            moments = rdMolDescriptors.CalcPrincipalMomentsOfInertia(mol_h)
            # Normalize by molecular weight to make it size-independent-ish
            mw = Descriptors.MolWt(mol_h)
            if mw > 0:
                moments_norm = tuple(m / mw for m in moments)
            else:
                moments_norm = (0.0, 0.0, 0.0)
        except Exception as e:
            logger.warning(f"Moments of Inertia calculation failed for {smiles}: {e}")
            return None
        
        # 4. Basic 2D features for context (optional but often helpful)
        atom_count = mol.GetNumAtoms()
        mw = Descriptors.MolWt(mol)
        
        return {
            'sasa': float(sasa),
            'radius_of_gyration': float(r_gyr),
            'moments_1': float(moments_norm[0]),
            'moments_2': float(moments_norm[1]),
            'moments_3': float(moments_norm[2]),
            'atom_count': float(atom_count),
            'molecular_weight': float(mw)
        }
    except Exception as e:
        logger.error(f"Unexpected error processing {smiles}: {e}")
        return None

def load_processed_data_for_baseline_3d(split_indices_path: Path, processed_data_path: Path) -> pd.DataFrame:
    """
    Load the processed dataset and filter for the specific split indices.
    """
    logger.info(f"Loading processed data from {processed_data_path}")
    df = pd.read_parquet(processed_data_path)
    
    logger.info(f"Loading split indices from {split_indices_path}")
    # Assuming split_indices.csv has a 'smiles' or 'index' column. 
    # Based on T016, it likely uses indices or SMILES. Let's assume SMILES for robustness 
    # or read the specific file format.
    # T016 output: data/splits/train_indices.csv, test_indices.csv
    # Usually these contain indices or SMILES. Let's try to load as CSV and check columns.
    indices_df = pd.read_csv(split_indices_path)
    
    # Determine key column
    if 'smiles' in indices_df.columns:
        key_col = 'smiles'
    elif 'index' in indices_df.columns:
        key_col = 'index'
    else:
        # Fallback: assume the first column is the key
        key_col = indices_df.columns[0]
    
    if key_col == 'smiles':
        split_smiles = set(indices_df['smiles'].tolist())
        subset = df[df['smiles'].isin(split_smiles)].reset_index(drop=True)
    else:
        # If indices are used, we need to map them back. 
        # For simplicity in this baseline task, we assume SMILES matching or direct index matching if 'smiles' is the index.
        # If the split file contains integer indices, we assume the DataFrame index corresponds.
        split_indices = set(indices_df['index'].tolist())
        subset = df.loc[split_indices].reset_index(drop=True)
    
    logger.info(f"Loaded {len(subset)} samples for the split.")
    return subset

def extract_topological_features_for_geometry(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Extract 3D geometric features from the dataframe.
    Returns X (features), y (target), and list of SMILES.
    """
    smiles_list = []
    features_list = []
    target_list = []
    
    logger.info("Extracting 3D geometric features...")
    
    # We need to regenerate 3D features because the parquet might not have them 
    # or they might be outdated. The task says "derived from 3D conformers".
    # If the parquet already has 'surface_area', we use that as target.
    # If it has pre-calculated 3D features, we could use them, but re-calculating ensures consistency.
    # However, re-calculating 3D for the whole dataset is slow. 
    # Assumption: The task implies using the 3D data generated in T015.
    # T015 produces 'paired_dataset.parquet' with 'surface_area'.
    # We will extract features on-the-fly for the split.
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        sasa_target = row.get('surface_area')
        
        if sasa_target is None or np.isnan(sasa_target):
            continue
        
        features = extract_geometry_features(smiles)
        if features is None:
            logger.warning(f"Skipping {smiles} due to 3D feature extraction failure.")
            continue
        
        smiles_list.append(smiles)
        target_list.append(sasa_target)
        # Flatten features into a list
        feature_vector = [
            features['sasa'],
            features['radius_of_gyration'],
            features['moments_1'],
            features['moments_2'],
            features['moments_3'],
            features['atom_count'],
            features['molecular_weight']
        ]
        features_list.append(feature_vector)
    
    if len(features_list) == 0:
        raise ValueError("No valid samples found for 3D feature extraction.")
    
    X = np.array(features_list)
    y = np.array(target_list)
    
    logger.info(f"Extracted {len(X)} valid samples with 3D features.")
    return X, y, smiles_list

def train_baseline_model(X: np.ndarray, y: np.ndarray) -> LinearRegression:
    """
    Train a Linear Regression model on the 3D geometric features.
    """
    logger.info("Training Geometry-Based Linear Regression model...")
    model = LinearRegression()
    model.fit(X, y)
    logger.info(f"Model training complete. R2 on training set: {model.score(X, y):.4f}")
    return model

def evaluate_model(model: LinearRegression, X: np.ndarray, y: np.ndarray, smiles_list: List[str]) -> Dict[str, Any]:
    """
    Evaluate the model and return metrics and predictions.
    """
    y_pred = model.predict(X)
    
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    
    logger.info(f"Evaluation Metrics: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
        'predictions': y_pred,
        'smiles': smiles_list
    }

def save_predictions(smiles_list: List[str], predictions: np.ndarray, target: np.ndarray, output_path: Path):
    """
    Save predictions to a parquet file.
    """
    errors = predictions - target
    df = pd.DataFrame({
        'smiles': smiles_list,
        'predicted_sasa': predictions,
        'error': errors
    })
    df.to_parquet(output_path, index=False)
    logger.info(f"Predictions saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train Geometry-Based Baseline (3D)")
    parser.add_argument("--split", type=str, default="test", help="Split to use (train or test)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    project_root = get_project_root()
    data_dir = get_data_dir(project_root)
    results_dir = get_results_dir(project_root)
    
    # Paths
    processed_data_path = data_dir / "processed" / "paired_dataset.parquet"
    split_indices_path = data_dir / "splits" / f"{args.split}_indices.csv"
    
    baseline_model_path = results_dir / "baseline" / "baseline_model_geometry.pkl"
    predictions_path = results_dir / "predictions" / "baseline_geometry_predictions.parquet"
    
    # Ensure directories exist
    baseline_model_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_data_path}. Run T015 first.")
    
    if not split_indices_path.exists():
        raise FileNotFoundError(f"Split indices not found at {split_indices_path}. Run T016 first.")
    
    # Load Data
    df = load_processed_data_for_baseline_3d(split_indices_path, processed_data_path)
    
    # Extract Features
    X, y, smiles_list = extract_topological_features_for_geometry(df)
    
    # Train
    model = train_baseline_model(X, y)
    
    # Evaluate
    metrics = evaluate_model(model, X, y, smiles_list)
    
    # Save Model
    with open(baseline_model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {baseline_model_path}")
    
    # Save Predictions
    save_predictions(metrics['smiles'], metrics['predictions'], y, predictions_path)
    
    # Log Summary
    summary = {
        "model_type": "LinearRegression_3D_Geometry",
        "split": args.split,
        "mae": metrics['mae'],
        "rmse": metrics['rmse'],
        "r2": metrics['r2'],
        "sample_size": len(X)
    }
    logger.info(f"Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    main()