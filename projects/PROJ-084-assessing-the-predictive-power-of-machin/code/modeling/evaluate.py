"""
Evaluation module for assessing model performance on test and training sets.
Implements metrics calculation (R2, RMSE, MAE) and per-class analysis.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# Import existing utilities from the project
from utils.io import load_csv, load_parquet
from utils.validators import validate_output_sample

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
METRICS_KEYS = ['R2', 'RMSE', 'MAE']
DECIMAL_PRECISION = 4

def load_best_models(models_dir: Path) -> Dict[str, Any]:
    """
    Load the best trained models and their metadata from the models directory.
    Expected structure: models_dir contains subdirectories for each model type
    (e.g., 'rf', 'svm') with 'model.pkl' and 'metadata.json'.
    """
    import pickle
    models = {}
    
    # Expected model types based on T024/T025
    model_types = ['rf', 'svm']
    
    for model_type in model_types:
        model_path = models_dir / model_type / 'model.pkl'
        metadata_path = models_dir / model_type / 'metadata.json'
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            continue
        
        with open(model_path, 'rb') as f:
            models[model_type] = {
                'model': pickle.load(f),
                'metadata': json.load(open(metadata_path, 'r')) if metadata_path.exists() else {}
            }
        logger.info(f"Loaded {model_type} model from {model_path}")
    
    return models

def load_test_data(test_indices_path: Path, full_data_path: Path) -> pd.DataFrame:
    """
    Load the held-out test set indices and extract the corresponding data
    from the full processed dataset.
    """
    if not test_indices_path.exists():
        raise FileNotFoundError(f"Test indices file not found: {test_indices_path}")
    
    # Load indices (expected to be a CSV with a column 'index' or similar)
    test_indices_df = load_csv(test_indices_path)
    
    # Determine the index column name
    index_col = 'index' if 'index' in test_indices_df.columns else test_indices_df.columns[0]
    test_indices = test_indices_df[index_col].tolist()
    
    # Load full processed data
    if not full_data_path.exists():
        raise FileNotFoundError(f"Full data file not found: {full_data_path}")
    
    full_data = load_parquet(full_data_path)
    
    # Filter to test set
    test_data = full_data.iloc[test_indices].reset_index(drop=True)
    logger.info(f"Loaded {len(test_data)} samples for testing")
    
    return test_data

def load_train_data(train_indices_path: Path, full_data_path: Path) -> pd.DataFrame:
    """
    Load the training set indices and extract the corresponding data
    from the full processed dataset.
    """
    if not train_indices_path.exists():
        raise FileNotFoundError(f"Train indices file not found: {train_indices_path}")
    
    # Load indices
    train_indices_df = load_csv(train_indices_path)
    
    # Determine the index column name
    index_col = 'index' if 'index' in train_indices_df.columns else train_indices_df.columns[0]
    train_indices = train_indices_df[index_col].tolist()
    
    # Load full processed data
    if not full_data_path.exists():
        raise FileNotFoundError(f"Full data file not found: {full_data_path}")
    
    full_data = load_parquet(full_data_path)
    
    # Filter to train set
    train_data = full_data.iloc[train_indices].reset_index(drop=True)
    logger.info(f"Loaded {len(train_data)} samples for training evaluation")
    
    return train_data

def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a single model on given data and return metrics.
    """
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    
    metrics = {
        'R2': round(r2, DECIMAL_PRECISION),
        'RMSE': round(rmse, DECIMAL_PRECISION),
        'MAE': round(mae, DECIMAL_PRECISION)
    }
    
    logger.info(f"Model Evaluation - R2: {metrics['R2']}, RMSE: {metrics['RMSE']}, MAE: {metrics['MAE']}")
    return metrics

def extract_features_and_target(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract feature vectors (fingerprints) and target (yield) from dataframe.
    Expected columns: 'fingerprint_ecfp', 'fingerprint_maccs', 'yield'
    """
    # Combine fingerprints if both exist, otherwise use ECFP4
    if 'fingerprint_ecfp' in df.columns:
        # ECFP4 is typically the primary feature set
        X = np.array([np.array(f) for f in df['fingerprint_ecfp'].values], dtype=np.float32)
    elif 'fingerprint_maccs' in df.columns:
        X = np.array([np.array(f) for f in df['fingerprint_maccs'].values], dtype=np.float32)
    else:
        raise ValueError("No fingerprint columns found in dataframe")
    
    y = df['yield'].values.astype(np.float32)
    return X, y

def run_evaluation(
    models_dir: Path,
    full_data_path: Path,
    test_indices_path: Path,
    train_indices_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Main evaluation routine:
    1. Load best models
    2. Load test and train data
    3. Evaluate on both sets
    4. Save metrics to JSON files
    """
    logger.info("Starting evaluation pipeline...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load models
    models = load_best_models(models_dir)
    if not models:
        raise RuntimeError("No models found to evaluate. Ensure T024/T025 completed successfully.")
    
    # Load data
    test_data = load_test_data(test_indices_path, full_data_path)
    train_data = load_train_data(train_indices_path, full_data_path)
    
    results = {}
    
    # Evaluate on Test Set
    logger.info("Evaluating on Test Set...")
    test_metrics = {}
    for model_type, model_info in models.items():
        X_test, y_test = extract_features_and_target(test_data)
        metrics = evaluate_model(model_info['model'], X_test, y_test)
        test_metrics[model_type] = metrics
    
    # Save test metrics
    test_metrics_path = output_dir / 'test_metrics.json'
    with open(test_metrics_path, 'w') as f:
        json.dump(test_metrics, f, indent=2)
    logger.info(f"Saved test metrics to {test_metrics_path}")
    
    # Evaluate on Training Set
    logger.info("Evaluating on Training Set...")
    train_metrics = {}
    for model_type, model_info in models.items():
        X_train, y_train = extract_features_and_target(train_data)
        metrics = evaluate_model(model_info['model'], X_train, y_train)
        train_metrics[model_type] = metrics
    
    # Save train metrics
    train_metrics_path = output_dir / 'train_metrics.json'
    with open(train_metrics_path, 'w') as f:
        json.dump(train_metrics, f, indent=2)
    logger.info(f"Saved train metrics to {train_metrics_path}")
    
    results['test_metrics'] = test_metrics
    results['train_metrics'] = train_metrics
    
    logger.info("Evaluation pipeline completed successfully.")
    return results

def compute_per_class_metrics(
    df: pd.DataFrame,
    model: Any,
    class_column: str = 'reaction_class'
) -> Dict[str, Dict[str, float]]:
    """
    Compute metrics per reaction class.
    Filters classes with sample count > 20.
    """
    per_class = {}
    
    for cls in df[class_column].unique():
        cls_df = df[df[class_column] == cls]
        if len(cls_df) <= 20:
            logger.debug(f"Skipping class '{cls}' with only {len(cls_df)} samples (threshold > 20)")
            continue
        
        X, y = extract_features_and_target(cls_df)
        metrics = evaluate_model(model, X, y)
        per_class[cls] = metrics
    
    return per_class

def compute_permutation_importance(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 5,
    random_state: int = 42,
    n_jobs: int = -1
) -> List[Dict[str, Any]]:
    """
    Compute permutation importance for a model.
    Returns list of dicts with feature_index and importance_score.
    """
    from sklearn.inspection import permutation_importance
    
    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=n_jobs
    )
    
    importance_list = []
    for i, score in enumerate(result.importances_mean):
        importance_list.append({
            'feature_index': i,
            'importance_score': float(score)
        })
    
    return importance_list

def get_substructure_for_atom(bit_index: int, mol: Any) -> Optional[str]:
    """
    Map a fingerprint bit to a substructure SMILES.
    Note: This is a placeholder for RDKit bit-to-atom mapping logic.
    """
    # Implementation depends on specific RDKit fingerprinting method used
    # For ECFP4, we would use GetMorganFingerprintAsBitVect with bitInfo
    return None

def map_bits_to_substructures(
    df: pd.DataFrame,
    importance_scores: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Map important bits to substructures and aggregate scores.
    """
    # Placeholder for complex bit-to-atom mapping logic
    return {
        'top_3_substructures': [],
        'collision_details': []
    }

def main():
    """
    Entry point for the evaluation script.
    Assumes paths are configured or passed as arguments.
    """
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent.parent
    models_dir = project_root / 'data' / 'results' / 'best_models'
    full_data_path = project_root / 'data' / 'processed' / 'cleaned_reactions.parquet'
    test_indices_path = project_root / 'data' / 'processed' / 'held_out_test_indices.csv'
    train_indices_path = project_root / 'data' / 'processed' / 'train_indices.csv'
    output_dir = project_root / 'data' / 'results'
    
    try:
        results = run_evaluation(
            models_dir=models_dir,
            full_data_path=full_data_path,
            test_indices_path=test_indices_path,
            train_indices_path=train_indices_path,
            output_dir=output_dir
        )
        logger.info("Evaluation completed successfully.")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()