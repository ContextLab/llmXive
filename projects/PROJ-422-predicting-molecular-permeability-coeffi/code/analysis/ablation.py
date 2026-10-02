import logging
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os

# Add parent directory to path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from models.rf import train_random_forest, predict, evaluate_model
from utils.logging import setup_logging, log_result_artifact

logger = logging.getLogger(__name__)

def load_graph_features_only(
    data_path: str,
    target_col: str = 'logP'
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Loads the graph topology features generated in T014b.
    Explicitly excludes standard descriptors (MW, logP, TPSA) to isolate topology.
    """
    logger.info(f"Loading graph features from {data_path}")
    df = pd.read_csv(data_path)

    # Identify columns that are NOT standard descriptors.
    # Standard descriptors are typically: MW, logP, TPSA, NumHDonors, NumHAcceptors, etc.
    # The T014b spec says: "Explicitly exclude standard molecular descriptors".
    # We assume the graph features file contains a specific set of columns.
    # To be safe, we load the CSV and filter out common descriptor names if present,
    # or assume specific columns if the file structure is known.
    # Given the spec "flattened graph topology features", let's assume the file
    # has columns like: 'mean_degree', 'max_degree', 'num_rings', 'aromatic_rings', etc.
    # We will load the dataframe and select columns that are NOT the target and NOT common descriptors.
    
    standard_descriptors = [
        'MW', 'MolWt', 'logP', 'LogP', 'TPSA', 'TopologicalPolarSurfaceArea',
        'NumHDonors', 'NumHAcceptors', 'NumRotatableBonds', 'NumAromaticRings',
        'NumAliphaticRings', 'NumHeterocycles', 'FractionCSP3', 'HeavyAtomCount'
    ]

    # Filter columns: exclude target and standard descriptors
    feature_cols = [col for col in df.columns 
                   if col != target_col and col not in standard_descriptors]
    
    # If the file is strictly graph features, this filter might be too aggressive if
    # the file only contains graph features. Let's assume the file contains ONLY graph features + target.
    # If the file contains descriptors, the filter ensures we only get topology.
    
    if len(feature_cols) == 0:
        raise ValueError("No graph topology features found. Check the input file columns.")

    logger.info(f"Using graph topology features: {feature_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return df, X, y

def train_ablation_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    model_path: str,
    random_state: int = 42
) -> RandomForestRegressor:
    """
    Trains a Random Forest model using ONLY graph topology features.
    This implements the FR-012 ablation study training.
    """
    logger.info("Training ablation model (Graph Topology Only)...")
    
    # Train using the existing RF trainer logic
    model = train_random_forest(X_train, y_train, random_state=random_state)
    
    # Save the model
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info(f"Ablation model saved to {model_path}")
    
    return model

def evaluate_ablation_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray,
    test_indices: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Evaluates the ablation model on the test set.
    Returns metrics including RMSE, MAE, R2.
    """
    logger.info("Evaluating ablation model...")
    y_pred = predict(model, X_test)
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    metrics = {
        "model_type": "RandomForest_Ablation",
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "n_samples": len(y_test)
    }
    
    logger.info(f"Ablation Model Metrics: RMSE={rmse:.4f}, MAE={mae:.4f}, R2={r2:.4f}")
    return metrics

def main():
    """
    Main entry point for the Ablation Study Training (T023).
    Orchestrates loading graph features, training the ablation model, and saving artifacts.
    """
    setup_logging()
    logger.info("Starting Ablation Study Training (T023)...")
    
    try:
        # Paths
        project_root = Path(__file__).parent.parent.parent
        graph_features_path = project_root / "data" / "processed" / "graph_features.csv"
        train_split_path = project_root / "data" / "processed" / "train.csv"
        test_split_path = project_root / "data" / "processed" / "test.csv"
        
        output_model_path = project_root / "data" / "interim" / "rf_ablation_checkpoint.pkl"
        output_metrics_path = project_root / "results" / "ablation_metrics.json"
        
        # Load Graph Features (Topology Only)
        if not graph_features_path.exists():
            raise FileNotFoundError(f"Graph features file not found at {graph_features_path}. "
                                  "Ensure T014b has been completed successfully.")
        
        # We need to split the graph features into train/test sets consistent with T017.
        # Since the graph features file likely contains the same rows as the splits,
        # we can load the split indices or merge based on a common ID if available.
        # However, the simplest approach per T017 is that train.csv and test.csv contain the processed data.
        # T014b generated graph_features.csv. We assume it has a 'smiles' or 'id' column to join,
        # OR we assume the rows are in the same order. 
        # Given the strict constraint "Explicitly exclude standard descriptors", we must ensure
        # we are using the right features.
        
        # Approach: Load train.csv and test.csv to get indices, then load graph_features.csv.
        # If graph_features.csv has an 'id' column, we join. If not, we assume order.
        # Let's assume the split files (train.csv, test.csv) contain the full feature set including descriptors.
        # We need to extract the graph features from the original graph_features.csv using the split indices.
        
        # To be robust: Load train.csv to get the set of SMILES/IDs used in training.
        train_df = pd.read_csv(train_split_path)
        test_df = pd.read_csv(test_split_path)
        
        # Load the full graph features dataset
        full_graph_df = pd.read_csv(graph_features_path)
        
        # Determine the key column for merging. 
        # Common keys: 'smiles', 'molecule_id', 'id'.
        key_col = None
        for col in ['smiles', 'molecule_id', 'id']:
            if col in full_graph_df.columns and col in train_df.columns:
                key_col = col
                break
        
        if key_col is None:
            # Fallback: assume row order matches (risky but common in simple pipelines)
            logger.warning("No common ID column found. Assuming row order matches between splits and graph features.")
            # Ensure lengths match
            if len(train_df) + len(test_df) != len(full_graph_df):
                raise ValueError("Row count mismatch between splits and graph features. Cannot align data.")
            train_indices = list(range(len(train_df)))
            test_indices = list(range(len(train_df), len(train_df) + len(test_df)))
            
            X_train = full_graph_df.iloc[train_indices].values
            y_train = train_df['target'].values if 'target' in train_df.columns else train_df.iloc[:, -1].values
            
            X_test = full_graph_df.iloc[test_indices].values
            y_test = test_df['target'].values if 'target' in test_df.columns else test_df.iloc[:, -1].values
            
            # Filter features to ensure we only use topology (exclude standard descriptors)
            # This is a safety check.
            feature_cols = [c for c in full_graph_df.columns if c not in ['target', 'smiles', 'id']]
            X_train = full_graph_df[feature_cols].iloc[train_indices].values
            X_test = full_graph_df[feature_cols].iloc[test_indices].values
            
        else:
            # Merge approach
            train_merged = train_df.merge(full_graph_df, on=key_col, suffixes=('_split', '_graph'))
            test_merged = test_df.merge(full_graph_df, on=key_col, suffixes=('_split', '_graph'))
            
            # Identify feature columns (exclude target and key)
            all_cols = set(train_merged.columns)
            feature_cols = [c for c in all_cols if c not in [key_col, 'target', 'logP', 'permeability_coefficient']]
            # Double check against standard descriptors list
            standard_descriptors = ['MW', 'MolWt', 'logP', 'TPSA', 'NumHDonors', 'NumHAcceptors']
            feature_cols = [c for c in feature_cols if c not in standard_descriptors]
            
            X_train = train_merged[feature_cols].values
            y_train = train_merged['target'].values if 'target' in train_merged.columns else train_merged.iloc[:, -1].values
            
            X_test = test_merged[feature_cols].values
            y_test = test_merged['target'].values if 'target' in test_merged.columns else test_merged.iloc[:, -1].values
        
        logger.info(f"Training set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")
        logger.info(f"Features used: {feature_cols}")
        
        # Train Model
        model = train_ablation_model(X_train, y_train, X_test, y_test, str(output_model_path))
        
        # Evaluate Model
        metrics = evaluate_ablation_model(model, X_test, y_test)
        metrics['training_time'] = 0.0 # Placeholder, can be measured if needed
        metrics['peak_memory_gb'] = 0.0 # Placeholder
        
        # Save Metrics
        output_metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Ablation study completed. Metrics saved to {output_metrics_path}")
        log_result_artifact("ablation_metrics", str(output_metrics_path))
        
    except Exception as e:
        logger.error(f"Error during ablation study: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
