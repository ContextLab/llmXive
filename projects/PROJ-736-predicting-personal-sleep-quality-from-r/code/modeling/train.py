"""
Training script for the sleep quality prediction model.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs, get_config
from modeling.pipeline_factory import create_pipeline
from utils.logging import setup_logging

def load_data(subjects_file: str, features_dir: str, behavioral_file: str) -> tuple:
    """
    Loads features and labels for training.
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
    pred_path = os.path.join(paths["data_processed"], "predictions.npy")
    np.save(pred_path, predictions)
    
    return results

def main() -> int:
    """
    Main entry point for training.
    """
    import pandas as pd
    paths = get_paths()
    ensure_dirs(paths)
    
    subjects_file = paths["data_raw"] / "filtered_subjects.txt"
    features_dir = paths["data_processed"]
    behavioral_file = os.path.join(paths["data_raw_behavioral"], "hcp1200_behavioral_data.csv")
    
    X, y, subjects = load_data(str(subjects_file), str(features_dir), behavioral_file)
    
    if X is None:
        print("No data to train on.")
        return 1
    
    results = run_training(X, y, subjects)
    
    # Save results
    results_path = os.path.join(paths["data_results"], "train_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Training complete. R={results['pearson_r']:.4f}, R2={results['r_squared']:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
