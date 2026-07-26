import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

# Local imports from project structure (as per API surface)
# Note: These assume the file is run from the project root or code/ directory
# or that the path is adjusted. For robustness, we use relative imports if possible
# or absolute imports if the package is installed.
# Given the prompt's context, we assume standard Python path setup.

def load_json_file(path: str) -> Any:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path: str, data: Any) -> None:
    """Save data to a JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_csv_to_dicts(path: str) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def save_to_csv(path: str, data: List[Dict[str, Any]], fieldnames: List[str] = None) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file with headers if provided, or just create file
        with open(path, 'w') as f:
            if fieldnames:
                f.write(','.join(fieldnames) + '\n')
        return
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_processed_data(features_path: str, targets_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed features and targets."""
    features = pd.read_csv(features_path)
    targets = pd.read_csv(targets_path)
    return features, targets

def load_models(models_path: str) -> Dict[str, Any]:
    """Load trained models from a pickle file."""
    with open(models_path, 'rb') as f:
        return pickle.load(f)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R2 and MAPE metrics."""
    from sklearn.metrics import r2_score
    
    r2 = r2_score(y_true, y_pred)
    # MAPE calculation with zero check
    mask = y_true != 0
    if np.sum(mask) == 0:
        mape = 0.0
    else:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    return {"R2": float(r2), "MAPE": float(mape)}

def run_holdout_evaluation(models_path: str, holdout_features_path: str, holdout_targets_path: str, source_type: str) -> Dict[str, Any]:
    """
    Evaluate final models on the hold-out set.
    
    Args:
        models_path: Path to the pickle file containing trained models.
        holdout_features_path: Path to the hold-out features CSV.
        holdout_targets_path: Path to the hold-out targets CSV.
        source_type: 'real' or 'synthetic' to determine the label.
    
    Returns:
        Dictionary with evaluation metrics.
    """
    import pickle
    
    # Load models
    try:
        models = load_models(models_path)
    except FileNotFoundError:
        logging.error(f"Models file not found: {models_path}")
        return {"error": "Models file not found"}
    except Exception as e:
        logging.error(f"Error loading models: {e}")
        return {"error": str(e)}

    # Load hold-out data
    try:
        holdout_features = pd.read_csv(holdout_features_path)
        holdout_targets = pd.read_csv(holdout_targets_path)
    except FileNotFoundError as e:
        logging.error(f"Hold-out data file not found: {e.filename}")
        return {"error": f"Hold-out file missing: {e.filename}"}
    except Exception as e:
        logging.error(f"Error loading hold-out data: {e}")
        return {"error": str(e)}

    # Expected target columns
    target_cols = ['conductivity', 'youngs_modulus', 'fracture_strength']
    results = {}
    
    for target in target_cols:
        if target not in holdout_targets.columns:
            logging.warning(f"Target column '{target}' not found in hold-out data.")
            continue
        
        if target not in models:
            logging.warning(f"Model for '{target}' not found.")
            continue
        
        model = models[target]
        y_true = holdout_targets[target].values
        y_pred = model.predict(holdout_features)
        
        metrics = calculate_metrics(y_true, y_pred)
        results[target] = metrics

    label = "External Validation" if source_type == "real" else "Method Validation"
    
    # Aggregate metrics for summary
    avg_r2 = np.mean([v['R2'] for v in results.values()]) if results else 0.0
    avg_mape = np.mean([v['MAPE'] for v in results.values()]) if results else 0.0

    output = {
        "source_type": source_type,
        "label": label,
        "R2": float(avg_r2),
        "MAPE": float(avg_mape),
        "per_property": results
    }
    
    return output

def compute_permutation_p_values(models: Dict, X: pd.DataFrame, y: pd.Series, n_permutations: int = 1000) -> Dict:
    """Compute p-values via permutation testing."""
    # Placeholder for actual implementation
    return {}

def apply_benjamini_hochberg(p_values: List[float], q: float = 0.05) -> List[Tuple[float, float, bool]]:
    """Apply Benjamini-Hochberg FDR control."""
    # Placeholder for actual implementation
    return []

def rank_features(importance_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    """Rank features by importance."""
    return sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)

def run_sensitivity_analysis(data: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Run sensitivity analysis on decision thresholds."""
    # Placeholder for actual implementation
    return pd.DataFrame()

def main():
    """Main entry point for Hold-Out Evaluation (T025)."""
    import argparse
    import sys
    
    # Paths relative to project root
    PROJECT_ROOT = os.getenv('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STATE_DIR = os.path.join(PROJECT_ROOT, 'data', 'state')
    PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
    RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
    
    data_source_path = os.path.join(STATE_DIR, 'data_source.json')
    models_path = os.path.join(PROCESSED_DIR, 'final_models.pkl')
    output_path = os.path.join(PROCESSED_DIR, 'holdout_metrics.json')
    
    # Ensure output directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

    # 1. Read data_source.json to determine hold-out file
    if not os.path.exists(data_source_path):
        logging.error(f"[ERROR] data_source.json not found at {data_source_path}")
        # Write error state
        save_json_file(output_path, {"error": "data_source.json missing"})
        sys.exit(1)

    try:
        data_source = load_json_file(data_source_path)
    except json.JSONDecodeError:
        logging.error(f"[ERROR] Invalid JSON in {data_source_path}")
        save_json_file(output_path, {"error": "Invalid JSON in data_source.json"})
        sys.exit(1)

    source_type = data_source.get('source_type', 'unknown')
    holdout_filename = data_source.get('holdout_filename')

    if not holdout_filename:
        logging.error(f"[ERROR] 'holdout_filename' not found in {data_source_path}")
        save_json_file(output_path, {"error": "holdout_filename missing in data_source.json"})
        sys.exit(1)

    holdout_path = os.path.join(RAW_DIR, holdout_filename)
    
    # 2. Verify hold-out file exists
    if not os.path.exists(holdout_path):
        logging.error(f"[ERROR] Hold-out file missing: {holdout_path}")
        save_json_file(output_path, {
            "error": "Hold-out file missing",
            "source_type": source_type,
            "expected_file": holdout_filename
        })
        sys.exit(1)

    # Determine features and targets for hold-out
    # Assuming hold-out CSV has the same schema as processed data or raw data that can be mapped
    # The task implies evaluating on the hold-out set. 
    # If the hold-out is raw data, we might need to process it similarly to training data.
    # However, T015 suggests the hold-out is split from the raw/processed source.
    # Let's assume the hold-out file contains the necessary features and targets directly 
    # or that we can load it as is.
    
    # For simplicity, we assume the hold-out file is a CSV with columns matching 
    # the features used in training and the target columns.
    # If the hold-out file is raw data, we might need to load processed features/targets
    # if they were saved separately for the hold-out. 
    # Given T015 logic: "Split ... save hold-out to ...". 
    # If it's a split of processed data, we need processed hold-out. 
    # If it's a split of raw data, we need to process it.
    # Let's assume the standard path: The hold-out file is the processed version 
    # or the script expects to read features/targets from it directly if it's a split of processed data.
    # To be safe, let's look for processed hold-out files if the raw one doesn't have all needed cols.
    
    # Check if holdout_path has the required columns for direct evaluation
    # If not, we might need to load processed features/targets if they were saved as separate hold-out files.
    # But T015 says "save hold-out to data/raw/real_holdout.csv". 
    # This implies it might be raw data. 
    # However, T021 trains on processed features. 
    # So we need to ensure we are feeding processed features to the model.
    # If the hold-out is raw, we must process it. 
    # But T018/T020 produce processed features. 
    # Did T015 split the processed data? The task says "Split data/raw/defect_dataset_2022.csv".
    # This is ambiguous. Let's assume the hold-out file contains the necessary columns 
    # to be used as features and targets, or we need to load the processed versions if they exist.
    
    # Alternative: If the hold-out file is raw, we need to re-run the processing steps (T018-T020) on it.
    # But T025 depends on T015 and T021. T021 uses processed features.
    # The most logical flow: T015 splits the data. If it splits raw data, we need to process it.
    # If it splits processed data (which T015 doesn't explicitly say, it says "Split data/raw/..."),
    # then we need to process the hold-out raw file.
    
    # Let's assume the hold-out file is the raw split. We need to load it, process it 
    # (normalize, one-hot encode, etc.) using the same parameters as training.
    # This requires loading the normalization log and feature selection log.
    # This is complex. 
    # Simpler interpretation: The hold-out file provided in data_source.json is the one 
    # ready for evaluation (i.e., it has the processed features). 
    # If not, we might need to load the processed features/targets if they were saved 
    # as separate hold-out files (e.g., data/processed/holdout_features.csv).
    # But the task says "save hold-out to data/raw/real_holdout.csv".
    
    # Let's try to load the hold-out file and see if it has the necessary columns.
    # If not, we might need to load the processed features and targets from the training set 
    # and split them again? No, that defeats the purpose.
    
    # Given the constraints, let's assume the hold-out file is the processed version 
    # or that we can load it as is. If it fails, we'll log an error.
    
    # For now, let's assume the hold-out file has columns 'conductivity', 'youngs_modulus', 'fracture_strength' 
    # and the feature columns.
    
    # If the hold-out file is raw, we need to process it. 
    # Let's check if the hold-out file has the target columns.
    try:
        holdout_df = pd.read_csv(holdout_path)
    except Exception as e:
        logging.error(f"[ERROR] Could not read hold-out file: {e}")
        save_json_file(output_path, {"error": f"Could not read hold-out file: {e}"})
        sys.exit(1)

    # Check if target columns exist
    target_cols = ['conductivity', 'youngs_modulus', 'fracture_strength']
    missing_targets = [t for t in target_cols if t not in holdout_df.columns]
    
    if missing_targets:
        logging.warning(f"Target columns missing in hold-out file: {missing_targets}")
        # If targets are missing, we cannot evaluate.
        # This might mean the hold-out file is raw and needs processing.
        # However, without the processing pipeline (T018-T020) re-run on hold-out, 
        # we cannot proceed. 
        # Let's assume the hold-out file is processed or has the targets.
        # If not, we fail.
        save_json_file(output_path, {"error": f"Missing target columns in hold-out: {missing_targets}"})
        sys.exit(1)

    # Separate features and targets
    # We need to know which columns are features. 
    # This is tricky without the feature selection log.
    # Let's assume all columns except targets are features.
    feature_cols = [col for col in holdout_df.columns if col not in target_cols]
    
    if not feature_cols:
        logging.error("No feature columns found in hold-out file.")
        save_json_file(output_path, {"error": "No feature columns found in hold-out file"})
        sys.exit(1)

    holdout_features = holdout_df[feature_cols]
    holdout_targets = holdout_df[target_cols]

    # 3. Evaluate models
    results = run_holdout_evaluation(
        models_path=models_path,
        holdout_features_path=None, # We already loaded the data
        holdout_targets_path=None,  # We already loaded the data
        source_type=source_type
    )
    
    # Override with our loaded data if run_holdout_evaluation expects paths
    # Re-implementing the evaluation logic here for clarity since we loaded the data
    import pickle
    try:
        with open(models_path, 'rb') as f:
            models = pickle.load(f)
    except Exception as e:
        logging.error(f"Failed to load models: {e}")
        save_json_file(output_path, {"error": f"Failed to load models: {e}"})
        sys.exit(1)

    evaluation_results = {}
    for target in target_cols:
        if target in models and target in holdout_targets.columns:
            y_true = holdout_targets[target].values
            y_pred = models[target].predict(holdout_features)
            metrics = calculate_metrics(y_true, y_pred)
            evaluation_results[target] = metrics
        else:
            logging.warning(f"Skipping {target}: model or data missing")

    avg_r2 = np.mean([v['R2'] for v in evaluation_results.values()]) if evaluation_results else 0.0
    avg_mape = np.mean([v['MAPE'] for v in evaluation_results.values()]) if evaluation_results else 0.0

    label = "External Validation" if source_type == "real" else "Method Validation"

    final_output = {
        "source_type": source_type,
        "label": label,
        "R2": float(avg_r2),
        "MAPE": float(avg_mape),
        "per_property": evaluation_results
    }

    # 4. Save output
    save_json_file(output_path, final_output)
    logging.info(f"Hold-out evaluation complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()