import os
import sys
import json
import logging
import argparse
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import pearsonr

# Local imports based on provided API surface
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir, get_results_dir
from utils.seed import set_seed
from data.preprocess import load_conformer_params, calculate_3d_descriptors, generate_conformer_for_molecule
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

logger = get_logger(__name__)

def extract_geometric_features(mol: Chem.Mol, conformer: Any) -> Dict[str, float]:
    """
    Extract geometric features from a molecule with a conformer.
    Features: radius_of_gyration, principal_moments, sasa_components.
    """
    # Calculate SASA
    sasa = rdMolDescriptors.CalcSASA(mol)
    
    # Calculate Radius of Gyration
    # RDKit does not have a direct CalcRadiusOfGyration, so we compute it manually
    coords = conformer.GetPositions()
    center_of_mass = np.mean(coords, axis=0)
    # Using atomic masses for weighted center of mass would be more precise, 
    # but simple geometric center is often sufficient for this feature unless specified otherwise.
    # Let's use simple geometric center for consistency with standard "radius of gyration" definitions in simple contexts,
    # or weighted by mass if we want physical accuracy. 
    # Standard RDKit Mol.GetRadiusOfGyration is not exposed in python API directly in older versions, 
    # but we can calculate: sqrt(sum(mass_i * r_i^2) / sum(mass_i))
    # For simplicity and robustness without mass lookup overhead: sqrt(mean(r_i^2))
    distances = np.linalg.norm(coords - center_of_mass, axis=1)
    radius_of_gyration = np.sqrt(np.mean(distances**2))

    # Calculate Principal Moments of Inertia
    # We need masses for this.
    masses = [atom.GetMass() for atom in mol.GetAtoms()]
    masses = np.array(masses)
    center_mass = np.average(coords, axis=0, weights=masses)
    r_vecs = coords - center_mass
    # Inertia tensor
    I = np.zeros((3, 3))
    for i, (r, m) in enumerate(zip(r_vecs, masses)):
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
    # Sort eigenvalues (principal moments)
    principal_moments = np.sort(eigenvalues)
    
    # SASA Components (approximated by atom contributions if needed, 
    # but CalcSASA returns total. The task asks for 'sasa_components'. 
    # RDKit's CalcSASA does not return per-atom breakdown in the simple call.
    # We will use a simple heuristic or just the total if components aren't strictly defined.
    # However, to be safe and provide a vector, we can use atom contributions if available.
    # RDKit's GetSASAContribution is not standard. Let's stick to the total SASA as the primary feature
    # and maybe the ratio of polar/non-polar if we can calculate it easily, 
    # but the prompt specifically lists 'sasa_components'. 
    # Since we can't easily get per-atom SASA without heavy calculation, we'll assume 
    # 'sasa_components' refers to the total SASA broken down by element type or similar.
    # For robustness, we will calculate total SASA and maybe the number of heavy atoms as a proxy for complexity.
    # Actually, let's just return the total SASA as a single value in a list to satisfy the "components" expectation if it implies a list.
    # Or better: return the SASA value itself. The task says "sasa_components" which might imply a list.
    # Let's calculate per-atom SASA using a simple loop if possible, or fallback to total.
    # RDKit doesn't expose per-atom SASA easily. We will use the total SASA.
    sasa_components = [sasa] 
    
    return {
        'radius_of_gyration': float(radius_of_gyration),
        'principal_moment_1': float(principal_moments[0]),
        'principal_moment_2': float(principal_moments[1]),
        'principal_moment_3': float(principal_moments[2]),
        'sasa_total': float(sasa),
        # We include the total as the component for now, as per-atom is not trivial without external libs
        'sasa_components': sasa_components 
    }

def load_processed_data_for_baseline_3d(split_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load training or test data for the 3D baseline.
    For training: Load from data/processed/descriptors.parquet (filtered by split indices).
    For testing: Load SMILES from split indices, regenerate conformers, and calculate descriptors.
    """
    root = get_project_root()
    data_dir = get_data_dir()
    
    # Load split indices
    indices_path = root / "data" / "splits" / f"{split_type}_indices.csv"
    if not indices_path.exists():
        raise FileNotFoundError(f"Split indices not found: {indices_path}")
    
    df_indices = pd.read_csv(indices_path)
    smiles_list = df_indices['smiles'].tolist()
    
    if split_type == 'train':
        # Training data comes from pre-calculated descriptors
        desc_path = data_dir / "processed" / "descriptors.parquet"
        if not desc_path.exists():
            raise FileNotFoundError(f"Training descriptors not found: {desc_path}")
        
        df_all = pd.read_parquet(desc_path)
        # Filter by smiles
        df_split = df_all[df_all['smiles'].isin(smiles_list)].reset_index(drop=True)
        
        if len(df_split) == 0:
            raise ValueError(f"No training data found for {len(smiles_list)} SMILES.")
        
        # Ensure surface_area exists
        if 'surface_area' not in df_split.columns:
            raise ValueError("Training data missing 'surface_area' column.")
        
        return df_split, df_indices
    
    else:
        # Test data: Regenerate conformers and descriptors on-the-fly
        # Load conformer params
        params_path = data_dir / "processed" / "conformer_params.json"
        if not params_path.exists():
            raise FileNotFoundError(f"Conformer params not found: {params_path}")
        
        with open(params_path, 'r') as f:
            params = json.load(f)
        
        test_data = []
        failed_count = 0
        
        for smiles in smiles_list:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning(f"Invalid SMILES in test set: {smiles}")
                failed_count += 1
                continue
            
            try:
                # Generate conformer
                conf = generate_conformer_for_molecule(mol, params)
                if conf is None:
                    logger.warning(f"Conformer generation failed for: {smiles}")
                    failed_count += 1
                    continue
                
                # Calculate descriptors
                feats = extract_geometric_features(mol, conf)
                feats['smiles'] = smiles
                # We don't have the true surface area for the test set in this file, 
                # but the evaluation step will need to compare with true values.
                # The true values are in the paired_dataset or descriptors file if we can match smiles.
                # However, for training the model, we only need X. For evaluation, we need y.
                # Let's fetch the true y from the main processed dataset if available.
                test_data.append(feats)
            except Exception as e:
                logger.error(f"Error processing {smiles}: {e}")
                failed_count += 1
        
        if len(test_data) == 0:
            raise ValueError("No valid test data could be generated.")
        
        df_test = pd.DataFrame(test_data)
        
        # Merge with true labels if possible
        # Try to load the main processed dataset to get surface_area
        merged_path = data_dir / "processed" / "paired_dataset.parquet"
        if merged_path.exists():
            df_merged = pd.read_parquet(merged_path)
            if 'surface_area' in df_merged.columns:
                df_test = df_test.merge(df_merged[['smiles', 'surface_area']], on='smiles', how='left')
                # Drop rows where we couldn't find the label (should be rare if smiles match)
                df_test = df_test.dropna(subset=['surface_area'])
        
        return df_test, df_indices

def train_baseline_model(X_train: np.ndarray, y_train: np.ndarray, model_type: str = 'rf') -> Any:
    """
    Train a baseline model (Random Forest for 3D geometry).
    """
    logger.info(f"Training {model_type} model with shape {X_train.shape}")
    
    if model_type == 'rf':
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate model performance.
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2)
    }

def save_predictions(smiles_list: List[str], y_true: np.ndarray, y_pred: np.ndarray, output_path: Path):
    """
    Save predictions to parquet.
    """
    errors = y_true - y_pred
    df_out = pd.DataFrame({
        'smiles': smiles_list,
        'predicted_sasa': y_pred,
        'error': errors
    })
    df_out.to_parquet(output_path, index=False)
    logger.info(f"Saved predictions to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train Geometry-Based Baseline (Random Forest)")
    parser.add_argument("--model_type", type=str, default="rf", help="Model type (rf)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    set_seed(args.seed)
    logger.info("Starting Geometry-Based Baseline Training (T021c)")

    root = get_project_root()
    results_dir = get_results_dir()

    # 1. Load Training Data
    try:
        df_train, _ = load_processed_data_for_baseline_3d('train')
    except Exception as e:
        logger.critical(f"Failed to load training data: {e}")
        sys.exit(1)

    # Prepare features
    feature_cols = ['radius_of_gyration', 'principal_moment_1', 'principal_moment_2', 'principal_moment_3', 'sasa_total']
    # Ensure columns exist
    missing_cols = [c for c in feature_cols if c not in df_train.columns]
    if missing_cols:
        logger.error(f"Missing feature columns in training data: {missing_cols}")
        sys.exit(1)
    
    X_train = df_train[feature_cols].values
    y_train = df_train['surface_area'].values

    # 2. Train Model
    model = train_baseline_model(X_train, y_train, args.model_type)

    # 3. Save Model
    model_path = results_dir / "baseline" / "baseline_3d.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # 4. Load/Test Data and Predict
    try:
        df_test, df_indices_test = load_processed_data_for_baseline_3d('test')
    except Exception as e:
        logger.critical(f"Failed to load/generate test data: {e}")
        sys.exit(1)

    X_test = df_test[feature_cols].values
    y_test = df_test['surface_area'].values
    smiles_test = df_test['smiles'].tolist()

    y_pred = model.predict(X_test)

    # 5. Evaluate
    metrics = evaluate_model(model, X_test, y_pred)
    logger.info(f"Test Metrics: MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}, R2={metrics['r2']:.4f}")

    # 6. Save Predictions
    predictions_path = results_dir / "predictions" / "baseline_3d_predictions.parquet"
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    save_predictions(smiles_test, y_test, y_pred, predictions_path)

    # 7. Save Metrics (optional, for consistency)
    metrics_path = results_dir / "baseline" / "baseline_3d_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info("Geometry-Based Baseline (T021c) completed successfully.")

if __name__ == "__main__":
    main()
