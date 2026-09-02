import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATA_RESULTS_DIR = Path("data/results")
DATA_PROCESSED_DIR = Path("data/processed")

def load_best_models(models_dir: Path = None) -> Dict[str, Any]:
    """
    Load the best trained models from the saved artifacts.
    Expected to find model files in data/results/best_models/
    """
    if models_dir is None:
        models_dir = DATA_RESULTS_DIR / "best_models"
    
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    models = {}
    for model_file in models_dir.glob("*.pkl"):
        model_name = model_file.stem
        logger.info(f"Loading model: {model_name} from {model_file}")
        with open(model_file, 'rb') as f:
            models[model_name] = joblib.load(f)
    
    if not models:
        raise FileNotFoundError(f"No model files found in {models_dir}")
    
    return models

def load_test_data(test_indices_path: Path = None, data_path: Path = None) -> pd.DataFrame:
    """
    Load the test set data using the held-out indices.
    """
    if test_indices_path is None:
        test_indices_path = DATA_PROCESSED_DIR / "test_indices.csv"
    if data_path is None:
        data_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    if test_indices_path.exists():
        test_indices = pd.read_csv(test_indices_path, index_col=0).index.tolist()
        logger.info(f"Loading {len(test_indices)} test samples from indices file")
        df = df.iloc[test_indices].reset_index(drop=True)
    else:
        # Fallback: assume last 20% are test if no indices file (should not happen in valid pipeline)
        logger.warning("Test indices file not found, using last 20% as test set")
        split_idx = int(len(df) * 0.8)
        df = df.iloc[split_idx:].reset_index(drop=True)
    
    return df

def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray, model_name: str = "model") -> Dict[str, float]:
    """
    Evaluate a single model and return metrics.
    """
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    
    return {
        "model_name": model_name,
        "R2": round(r2, 4),
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4)
    }

def compute_per_class_metrics(
    df: pd.DataFrame, 
    model: Any, 
    feature_cols: List[str], 
    target_col: str = "yield"
) -> List[Dict[str, Any]]:
    """
    Compute R2, RMSE, and MAE for each reaction class.
    
    Args:
        df: DataFrame containing features, target, and reaction_class
        model: Trained sklearn model
        feature_cols: List of column names to use as features
        target_col: Name of the target column
    
    Returns:
        List of dictionaries with reaction_class, R2, RMSE, MAE
    """
    if "reaction_class" not in df.columns:
        raise ValueError("DataFrame must contain 'reaction_class' column")
    
    classes = df["reaction_class"].unique()
    metrics_list = []
    
    logger.info(f"Computing per-class metrics for {len(classes)} classes")
    
    for cls in classes:
        class_mask = df["reaction_class"] == cls
        class_df = df[class_mask]
        
        if len(class_df) < 5:
            logger.warning(f"Skipping class '{cls}' with only {len(class_df)} samples")
            continue
        
        X_class = class_df[feature_cols].values
        y_class = class_df[target_col].values
        
        y_pred = model.predict(X_class)
        
        r2 = r2_score(y_class, y_pred)
        rmse = np.sqrt(mean_squared_error(y_class, y_pred))
        mae = mean_absolute_error(y_class, y_pred)
        
        metrics_list.append({
            "reaction_class": cls,
            "R2": round(r2, 4),
            "RMSE": round(rmse, 4),
            "MAE": round(mae, 4),
            "sample_count": len(class_df)
        })
        
        logger.info(f"Class '{cls}': R2={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f} (n={len(class_df)})")
    
    return metrics_list

def run_evaluation(
    models: Dict[str, Any],
    test_df: pd.DataFrame,
    feature_cols: List[str],
    output_path: Path = None
) -> Dict[str, Any]:
    """
    Run full evaluation: global metrics + per-class metrics.
    
    Args:
        models: Dict of model_name -> model
        test_df: Test set DataFrame
        feature_cols: List of feature column names
        output_path: Path to save per_class_metrics.json
    
    Returns:
        Full evaluation results dictionary
    """
    if output_path is None:
        output_path = DATA_RESULTS_DIR / "per_class_metrics.json"
    
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {
        "global_metrics": {},
        "per_class_metrics": {}
    }
    
    X_test = test_df[feature_cols].values
    y_test = test_df["yield"].values
    
    for model_name, model in models.items():
        # Global metrics
        global_metrics = evaluate_model(model, X_test, y_test, model_name)
        results["global_metrics"][model_name] = global_metrics
        
        # Per-class metrics
        per_class = compute_per_class_metrics(test_df, model, feature_cols)
        results["per_class_metrics"][model_name] = per_class
        
        # Save per-class metrics to file (as per T031a requirement)
        if model_name == "random_forest":  # Save for the primary model
            with open(output_path, 'w') as f:
                json.dump(per_class, f, indent=2)
            logger.info(f"Saved per-class metrics to {output_path}")
    
    return results

def main():
    """
    Main entry point for running evaluation and generating per-class metrics.
    """
    logger.info("Starting evaluation pipeline (T031a)")
    
    # Paths
    models_dir = DATA_RESULTS_DIR / "best_models"
    data_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    output_path = DATA_RESULTS_DIR / "per_class_metrics.json"
    
    # Load models
    try:
        models = load_best_models(models_dir)
        logger.info(f"Loaded {len(models)} models: {list(models.keys())}")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        sys.exit(1)
    
    # Load test data
    try:
        test_df = load_test_data(data_path=data_path)
        logger.info(f"Loaded test data with {len(test_df)} samples")
    except Exception as e:
        logger.error(f"Failed to load test data: {e}")
        sys.exit(1)
    
    # Identify feature columns (exclude target and metadata)
    exclude_cols = ["smiles", "yield", "reaction_class"]
    feature_cols = [col for col in test_df.columns if col not in exclude_cols]
    
    if not feature_cols:
        logger.error("No feature columns found in dataset")
        sys.exit(1)
    
    logger.info(f"Using {len(feature_cols)} feature columns")
    
    # Run evaluation
    try:
        results = run_evaluation(models, test_df, feature_cols, output_path)
        logger.info("Evaluation completed successfully")
        
        # Print summary
        if "random_forest" in results["per_class_metrics"]:
            per_class = results["per_class_metrics"]["random_forest"]
            logger.info(f"Per-class metrics saved to {output_path}")
            logger.info(f"Number of reaction classes evaluated: {len(per_class)}")
            
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("T031a task completed")

if __name__ == "__main__":
    main()