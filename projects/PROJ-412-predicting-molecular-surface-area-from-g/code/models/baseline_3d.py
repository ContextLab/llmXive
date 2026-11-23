import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir
from data.preprocess import load_conformer_params, generate_conformer_for_molecule

logger = get_logger(__name__)

def calculate_sasa_from_smiles(smiles: str, params: Dict[str, Any]) -> Optional[float]:
    """
    Generate a conformer for a SMILES string and calculate SASA.
    Returns None if generation fails.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    try:
        conf = generate_conformer_for_molecule(mol, params)
        if conf is None:
            return None
        
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
    except Exception as e:
        logger.warning(f"Failed to calculate SASA for {smiles}: {e}")
        return None

def predict_baseline_sasa(model_path: Path, smiles_list: List[str], params: Dict[str, Any]) -> Tuple[List[str], List[float], List[float]]:
    """
    Load the 3D baseline model and predict SASA for a list of SMILES.
    Regenerates conformers on the fly for feature extraction.
    Returns: (smiles, predictions, errors)
    """
    import pickle
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    feature_cols = ['radius_of_gyration', 'principal_moment_1', 'principal_moment_2', 'principal_moment_3', 'sasa_total']
    
    X = []
    valid_smiles = []
    
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        
        try:
            conf = generate_conformer_for_molecule(mol, params)
            if conf is None:
                continue
            
            # Extract features
            coords = conf.GetPositions()
            center_of_mass = np.mean(coords, axis=0)
            distances = np.linalg.norm(coords - center_of_mass, axis=1)
            radius_of_gyration = np.sqrt(np.mean(distances**2))
            
            masses = [atom.GetMass() for atom in mol.GetAtoms()]
            masses = np.array(masses)
            center_mass = np.average(coords, axis=0, weights=masses)
            r_vecs = coords - center_mass
            
            I = np.zeros((3, 3))
            for r, m in zip(r_vecs, masses):
                I[0, 0] += m * (r[1]**2 + r[2]**2)
                I[1, 1] += m * (r[0]**2 + r[2]**2)
                I[2, 2] += m * (r[0]**2 + r[1]**2)
                I[0, 1] -= m * r[0] * r[1]
                I[0, 2] -= m * r[0] * r[2]
                I[1, 2] -= m * r[1] * r[2]
                I[1, 0] = I[0, 1]
                I[2, 0] = I[0, 2]
                I[2, 1] = I[1, 2]
            
            eigenvalues = np.linalg.eigvalsh(I)
            principal_moments = np.sort(eigenvalues)
            sasa = rdMolDescriptors.CalcSASA(mol)
            
            X.append([
                radius_of_gyration,
                principal_moments[0],
                principal_moments[1],
                principal_moments[2],
                sasa
            ])
            valid_smiles.append(smiles)
        except Exception as e:
            logger.warning(f"Feature extraction failed for {smiles}: {e}")
            continue
    
    if len(X) == 0:
        return [], [], []
    
    X = np.array(X)
    preds = model.predict(X)
    
    # We cannot calculate errors here without true labels. 
    # This function is for prediction generation.
    # The error calculation happens in the evaluation step.
    return valid_smiles, preds.tolist(), []

def main():
    """
    Standalone script to run the 3D baseline prediction if needed.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run 3D Baseline Prediction")
    parser.add_argument("--smiles_file", type=str, required=True, help="Path to CSV with smiles")
    parser.add_argument("--output", type=str, required=True, help="Output path")
    args = parser.parse_args()
    
    root = get_project_root()
    data_dir = get_data_dir()
    results_dir = root / "results"
    
    # Load params
    params_path = data_dir / "processed" / "conformer_params.json"
    with open(params_path, 'r') as f:
        params = json.load(f)
    
    # Load model
    model_path = results_dir / "baseline" / "baseline_3d.pkl"
    
    # Load smiles
    df = pd.read_csv(args.smiles_file)
    smiles_list = df['smiles'].tolist()
    
    smiles_out, preds, _ = predict_baseline_sasa(model_path, smiles_list, params)
    
    df_out = pd.DataFrame({
        'smiles': smiles_out,
        'predicted_sasa': preds
    })
    df_out.to_parquet(args.output, index=False)
    logger.info(f"Predictions saved to {args.output}")

if __name__ == "__main__":
    main()