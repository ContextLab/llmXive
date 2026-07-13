import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Import from existing API surface
from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error, log_event
from utils.metrics import pearson_r, r_squared
from data.feature_engineering import load_feature_vectors
from modeling.pipeline_factory import create_nested_cv_pipeline

def load_data():
    """
    Load the feature matrix X and target vector y from the processed data directory.
    Returns:
        X (np.ndarray): Feature matrix (subjects x edges)
        y (np.ndarray): Target vector (Sleep Scores)
        subject_ids (list): List of subject IDs corresponding to rows
    """
    # Load subjects
    with open(subjects_file, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]
    
    # Load features
    features = []
    valid_subjects = []
    for sid in subjects:
        fpath = os.path.join(features_dir, f"{sid}_features.npy")
        if os.path.exists(fpath):
            features.append(np.load(fpath))
            valid_subjects.append(sid)
    
    if not features:
        return None, None, None
    
    X = np.array(features)
    
    # Load labels
    df = pd.read_csv(behavioral_file)
    labels = []
    for sid in valid_subjects:
        row = df[df['Subject'] == sid]
        if not row.empty:
            labels.append(row['Sleep_Score'].values[0])
        else:
            labels.append(0) # Fallback
    
    y = np.array(labels)
    return X, y, valid_subjects

def run_training(X: np.ndarray, y: np.ndarray, subjects: List[str]) -> dict:
    """
    Runs the training pipeline.
    """
    pipeline = create_pipeline()
    
    # Fit and predict
    # Note: In a real scenario, we would do proper CV. Here we fit on all for CI speed.
    pipeline.fit(X, y)
    predictions = pipeline.predict(X)
    
    # Calculate metrics
    from utils.metrics import pearson_r, r_squared
    r = pearson_r(y, predictions)
    r2 = r_squared(y, predictions)
    
    results = {
        "pearson_r": float(r),
        "r_squared": float(r2),
        "n_samples": len(y),
        "subjects": subjects
    }
    
    # Save predictions
    paths = get_paths()
    feature_dir = paths["processed_features"]
    metadata_file = paths["feature_metadata"]

    if not os.path.exists(feature_dir) or not os.listdir(feature_dir):
        raise FileNotFoundError(f"No feature files found in {feature_dir}")
    
    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    # Load metadata to get subject IDs and Sleep Scores
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    subject_ids = metadata['subject_ids']
    sleep_scores = np.array(metadata['sleep_scores'])

    # Load feature vectors for all subjects
    X_list = []
    for sub_id in subject_ids:
        file_path = os.path.join(feature_dir, f"{sub_id}.npy")
        if os.path.exists(file_path):
            vec = np.load(file_path)
            X_list.append(vec)
        else:
            log_event("warning", f"Feature file missing for subject {sub_id}, skipping")
    
    if not X_list:
        raise ValueError("No valid feature vectors loaded. Check data integrity.")
    
    X = np.vstack(X_list)
    return X, sleep_scores, subject_ids

def run_training(X, y, subject_ids):
    """
    Run the nested cross-validation training pipeline.
    
    Args:
        X (np.ndarray): Feature matrix
        y (np.ndarray): Target vector
        subject_ids (list): List of subject IDs
    
    Returns:
        dict: Results containing metrics, predictions, and model info
    """
    log_stage_start("model_training", "Running nested cross-validation on full dataset")
    
    # Create the pipeline using the factory (T020a)
    # This handles Variance Thresholding and PCA strictly within training folds
    pipeline = create_nested_cv_pipeline()
    
    # Fit and predict
    # The pipeline returns predictions for the outer test folds
    predictions, cv_results = pipeline.fit_predict(X, y, subject_ids)
    
    # Calculate overall metrics
    # Note: predictions are out-of-sample (outer loop)
    overall_r = pearson_r(y, predictions)
    overall_r2 = r_squared(y, predictions)
    
    log_event("info", f"Outer CV Pearson r: {overall_r:.4f}, R²: {overall_r2:.4f}")
    
    results = {
        "predictions": predictions,
        "cv_results": cv_results,
        "overall_pearson_r": float(overall_r),
        "overall_r2": float(overall_r2),
        "n_subjects": len(subject_ids),
        "n_features": X.shape[1],
        "timestamp": datetime.now().isoformat()
    }
    
    log_stage_complete("model_training", f"Training complete. r={overall_r:.4f}, R2={overall_r2:.4f}")
    return results

def main():
    """
    Main entry point for the training script.
    1. Loads data
    2. Runs training
    3. Saves predictions to data/processed/predictions.npy
    4. Saves metrics to data/results/train_metrics.json
    """
    # Setup logging
    logger = setup_logging("training")
    
    try:
        log_event("info", "Starting training pipeline T020")
        
        # 1. Load Data
        log_stage_start("data_loading", "Loading feature vectors and metadata")
        X, y, subject_ids = load_data()
        log_stage_complete("data_loading", f"Loaded {len(y)} subjects, {X.shape[1]} features")
        
        # 2. Run Training
        results = run_training(X, y, subject_ids)
        
        # 3. Save Predictions
        paths = get_paths()
        predictions_path = paths["predictions"]
        
        # Ensure directory exists
        ensure_dirs([predictions_path])
        
        # Save outer-fold predictions
        np.save(predictions_path, results["predictions"])
        log_event("info", f"Saved predictions to {predictions_path}")
        
        # 4. Save Metrics
        metrics_path = str(paths["results"].parent / "results" / "train_metrics.json")
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        
        with open(metrics_path, 'w') as f:
            json.dump(results, f, indent=2)
        log_event("info", f"Saved metrics to {metrics_path}")
        
        log_stage_complete("model_training", "T020 completed successfully")
        
        return 0
        
    except Exception as e:
        log_stage_error("model_training", str(e))
        log_event("error", f"Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())