import logging
import sys
import json
import time
import traceback
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, log_result_artifact

def load_graph_features_only(csv_path: str) -> tuple:
    """
    Loads the flattened graph topology features from the specified CSV.
    Returns X (features) and y (target).
    
    Strict Constraint: Explicitly excludes standard molecular descriptors 
    (MW, logP, TPSA) from the feature set.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading graph features only from {csv_path}")
    
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Graph features file not found: {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    # Identify feature columns (exclude 'target' and standard descriptors)
    standard_descriptors = ['MW', 'logP', 'TPSA', 'Molecular_Weight', 'LogP', 'Topological_Polar_Surface_Area']
    
    # Filter out standard descriptors and target column
    feature_cols = [col for col in df.columns 
                   if col not in standard_descriptors and col != 'target' and col != 'SMILES']
    
    if not feature_cols:
        raise ValueError("No graph topology features found after excluding standard descriptors.")
        
    logger.info(f"Loaded {len(feature_cols)} graph topology features: {feature_cols[:5]}...")
    
    X = df[feature_cols].values
    y = df['target'].values
    
    return X, y

def train_ablation_model(X_train: np.ndarray, y_train: np.ndarray, 
                        output_path: str, random_state: int = 42) -> dict:
    """
    Trains a Random Forest model using ONLY graph topology features.
    Saves the model and returns training metadata.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Training ablation Random Forest model on {X_train.shape[0]} samples")
    
    start_time = time.time()
    
    # Configure Random Forest for CPU execution
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        n_jobs=-1,  # Use all CPU cores
        random_state=random_state,
        verbose=0
    )
    
    model.fit(X_train, y_train)
    
    training_time = time.time() - start_time
    
    # Save model
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    
    logger.info(f"Model saved to {output_path}")
    logger.info(f"Training completed in {training_time:.2f} seconds")
    
    metadata = {
        "model_type": "RandomForest_Ablation",
        "feature_source": "graph_topology_only",
        "training_samples": len(y_train),
        "training_time_seconds": round(training_time, 2),
        "random_state": random_state,
        "model_path": str(output_path)
    }
    
    return metadata

def evaluate_ablation_model(model_path: str, X_test: np.ndarray, y_test: np.ndarray, 
                           metrics_output_path: str) -> dict:
    """
    Evaluates the ablation model on test data and saves metrics.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Evaluating ablation model from {model_path}")
    
    # Load model
    model = joblib.load(model_path)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"Ablation Model Metrics - RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
    
    metrics = {
        "model_name": "RF_Ablation",
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "feature_set": "graph_topology_only",
        "test_samples": len(y_test)
    }
    
    # Save metrics
    metrics_path = Path(metrics_output_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if present
    existing_metrics = {}
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                existing_metrics = json.load(f)
        except:
            existing_metrics = {}
    
    # Update with ablation metrics
    existing_metrics["RF_Ablation"] = metrics
    
    with open(metrics_path, 'w') as f:
        json.dump(existing_metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {metrics_output_path}")
    
    return metrics

def main():
    """
    Main entry point for the ablation study training.
    Orchestrates loading graph features, training the model, and evaluating.
    """
    logger = setup_logging("ablation_study")
    logger.info("Starting Ablation Study (FR-012)")
    
    try:
        # Paths
        project_root = Path(__file__).parent.parent.parent
        graph_features_path = project_root / "data" / "processed" / "graph_features.csv"
        train_split_path = project_root / "data" / "processed" / "train.csv"
        test_split_path = project_root / "data" / "processed" / "test.csv"
        ablation_model_path = project_root / "data" / "interim" / "rf_ablation_checkpoint.pkl"
        metrics_path = project_root / "results" / "metrics.json"
        
        # Load graph features only
        logger.info("Loading graph topology features...")
        X, y = load_graph_features_only(str(graph_features_path))
        
        # Load train/test splits to get indices
        train_df = pd.read_csv(train_split_path)
        test_df = pd.read_csv(test_split_path)
        
        # Extract indices for proper splitting
        train_indices = train_df.index.tolist()
        test_indices = test_df.index.tolist()
        
        # Split features and target based on indices
        X_train = X[train_indices]
        y_train = y[train_indices]
        X_test = X[test_indices]
        y_test = y[test_indices]
        
        logger.info(f"Train set: {len(y_train)} samples, Test set: {len(y_test)} samples")
        
        # Train ablation model
        logger.info("Training ablation model...")
        train_metadata = train_ablation_model(
            X_train, y_train, 
            str(ablation_model_path)
        )
        
        # Evaluate ablation model
        logger.info("Evaluating ablation model...")
        eval_metrics = evaluate_ablation_model(
            str(ablation_model_path),
            X_test, y_test,
            str(metrics_path)
        )
        
        logger.info("Ablation study completed successfully")
        
        # Log result artifact
        log_result_artifact(
            artifact_type="ablation_study",
            status="completed",
            details={
                "model_path": str(ablation_model_path),
                "metrics": eval_metrics,
                "training_metadata": train_metadata
            }
        )
        
    except Exception as e:
        logger.error(f"Ablation study failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()