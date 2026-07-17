import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Ensure logging is configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    output_dir = Path("data/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_test_data():
    """
    Load the preprocessed test data used for evaluation.
    This assumes the preprocessing pipeline has run and saved data to data/processed/processed_data.csv
    """
    data_path = Path("data/processed/processed_data.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found at {data_path}. Run preprocessing first.")
    
    df = pd.read_csv(data_path)
    
    # Identify target columns based on common conventions or schema
    # Assuming the schema defines specific target columns for isotherm parameters
    # Common targets from context: langmuir_capacity, henry_constant
    target_cols = [col for col in df.columns if col in ['langmuir_capacity', 'henry_constant']]
    
    if not target_cols:
        raise ValueError("No target columns found in dataset. Expected 'langmuir_capacity' or 'henry_constant'.")
    
    # For this task, we focus on one target at a time or aggregate if needed.
    # Let's assume we evaluate against the first available target for simplicity, 
    # or we can return metrics for all.
    return df, target_cols

def load_models():
    """
    Load the trained models from disk.
    Expected path: data/models/
    We need to load the models that were trained in T020/T021.
    Since we are implementing T024, we assume T020/T021/T023 have run.
    We expect joblib files or similar.
    """
    model_dir = Path("data/models")
    if not model_dir.exists():
        raise FileNotFoundError(f"Models directory not found at {model_dir}. Run training first.")
    
    # We need to know which model is the "best" or simply compare against the set of trained models.
    # For T024, we compare the BEST model against the null model.
    # Let's assume the best model was saved as 'best_model.pkl' or similar by the training pipeline.
    # If not, we might need to load all and pick based on a metadata file.
    
    # Attempt to load a metadata file that records the best model
    metadata_path = model_dir / "evaluation_results.json"
    best_model_name = None
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            # Assuming the evaluation results saved the best model name
            best_model_name = metadata.get('best_model_name')
    
    if not best_model_name:
        # Fallback: try to find any .pkl or .joblib file and assume it's the one we want to compare
        # This is risky but necessary if metadata is missing.
        # Better: raise error if we can't identify the best model.
        import glob
        model_files = list(model_dir.glob("*.pkl")) + list(model_dir.glob("*.joblib"))
        if not model_files:
            raise FileNotFoundError("No model files found.")
        # Pick the first one found (should be the best if the pipeline is correct)
        best_model_path = model_files[0]
        best_model_name = best_model_path.stem
        logger.warning(f"Could not determine best model from metadata. Using {best_model_name}.")
    
    # Load the model using joblib
    import joblib
    model_path = model_dir / f"{best_model_name}.pkl"
    if not model_path.exists():
        model_path = model_dir / f"{best_model_name}.joblib"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Best model file {model_path} not found.")
    
    model = joblib.load(model_path)
    return model, best_model_name

def predict_mean_null_model(X_train: pd.DataFrame, y_train: pd.Series) -> float:
    """
    The null model simply predicts the mean of the training targets for all test instances.
    Returns the mean value.
    """
    return y_train.mean()

def calculate_null_model_metrics(y_true: pd.Series, y_pred_mean: float) -> Dict[str, float]:
    """
    Calculate metrics for the null model (predicting mean).
    """
    y_pred = np.full_like(y_true, y_pred_mean)
    
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "model_type": "null_mean"
    }

def compare_models(null_metrics: Dict[str, float], model_metrics: Dict[str, float], model_name: str):
    """
    Compare the null model metrics with the trained model metrics.
    Verify significant RMSE improvement.
    Returns a dictionary with the comparison results.
    """
    null_rmse = null_metrics['rmse']
    model_rmse = model_metrics['rmse']
    
    improvement = null_rmse - model_rmse
    improvement_pct = (improvement / null_rmse) * 100 if null_rmse > 0 else 0.0
    
    # Significant improvement threshold (arbitrary but strict, e.g., > 10% reduction)
    significant = improvement_pct > 10.0
    
    comparison = {
        "model_name": model_name,
        "null_model_rmse": null_rmse,
        "trained_model_rmse": model_rmse,
        "rmse_improvement": improvement,
        "improvement_percentage": improvement_pct,
        "significant_improvement": significant,
        "null_model_r2": null_metrics['r2'],
        "trained_model_r2": model_metrics['r2']
    }
    
    logger.info(f"Null Model RMSE: {null_rmse:.4f}")
    logger.info(f"Trained Model ({model_name}) RMSE: {model_rmse:.4f}")
    logger.info(f"RMSE Improvement: {improvement_pct:.2f}%")
    logger.info(f"Significant Improvement: {significant}")
    
    return comparison

def main():
    """
    Main entry point for the null model comparison task.
    1. Load test data.
    2. Load the best trained model.
    3. Calculate null model predictions (mean of training targets).
       *Note*: We need the training targets. Since we are in T024 and the pipeline 
       usually splits data, we need to access the training set used for the model.
       However, standard practice is to store the training mean in the model or metadata.
       Alternatively, we re-run the split or load the training data if available.
       
       Assumption: The training pipeline (T020/T021) saved the training mean in the model's metadata
       or we can load the training data from data/processed/train_data.csv if the preprocessing step saved it.
       Let's assume the preprocessing step saved train/test splits: data/processed/train_data.csv, data/processed/test_data.csv
    """
    try:
        # Ensure directories
        output_dir = ensure_dirs()
        
        # Load test data
        test_df, target_cols = load_test_data()
        logger.info(f"Loaded test data with shape {test_df.shape}")
        
        # Load training data to calculate the mean
        train_path = Path("data/processed/train_data.csv")
        if not train_path.exists():
            raise FileNotFoundError("Training data not found. Preprocessing must save train_data.csv.")
        
        train_df = pd.read_csv(train_path)
        
        # Load the trained model
        model, model_name = load_models()
        
        results = []
        
        for target in target_cols:
            logger.info(f"Evaluating against target: {target}")
            
            # Get training and test targets
            y_train = train_df[target]
            y_test = test_df[target]
            X_test = test_df.drop(columns=[target])
            
            # 1. Calculate Null Model Metrics
            mean_pred = predict_mean_null_model(X_test, y_train) # X_test not used, just for signature
            null_metrics = calculate_null_model_metrics(y_test, mean_pred)
            
            # 2. Calculate Trained Model Metrics
            # We need to predict on X_test
            y_pred_trained = model.predict(X_test)
            
            # Calculate metrics for the trained model
            trained_metrics = {
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_trained))),
                "mae": float(mean_absolute_error(y_test, y_pred_trained)),
                "r2": float(r2_score(y_test, y_pred_trained)),
                "model_type": model_name
            }
            
            # 3. Compare
            comparison = compare_models(null_metrics, trained_metrics, model_name)
            comparison["target"] = target
            results.append(comparison)
        
        # Save results
        output_path = output_dir / "null_model_comparison.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Null model comparison results saved to {output_path}")
        
        # Verify significant improvement
        all_significant = all(r['significant_improvement'] for r in results)
        if not all_significant:
            logger.warning("Not all targets showed significant RMSE improvement (>10%).")
        else:
            logger.info("All targets showed significant RMSE improvement.")
            
        return results

    except Exception as e:
        logger.error(f"Error in null model comparison: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()