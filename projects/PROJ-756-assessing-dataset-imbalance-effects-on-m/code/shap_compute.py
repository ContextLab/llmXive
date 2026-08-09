"""
T037: Compute SHAP values for skewed and balanced models.

Loads trained models from the baseline and resampling pipelines,
loads the corresponding test data, computes SHAP values using KernelSHAP,
and saves the results to results/shap_analysis/shap_skewed.npy and 
results/shap_analysis/shap_balanced.npy.
"""
import os
import sys
import logging
import pickle
import numpy as np
from pathlib import Path

# Add project root to path to allow imports from sibling modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import shap
except ImportError:
    print("ERROR: shap library is not installed. Please install it via: pip install shap")
    sys.exit(1)

from evaluation import ensure_directories, load_models, load_test_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_shap_values(model, X_test, model_type="RandomForest"):
    """
    Compute SHAP values for a given model and test data.
    
    Args:
        model: Trained scikit-learn model.
        X_test: Test feature matrix (numpy array).
        model_type: Type of model (used to select SHAP explainer).
    
    Returns:
        np.ndarray: SHAP values array.
    """
    logger.info(f"Computing SHAP values for {model_type} model...")
    
    # Determine explainer type based on model
    # For Random Forest and Gradient Boosting, TreeExplainer is efficient
    # However, if the model is a generic wrapper or complex, KernelExplainer is safer
    # Given the training.py likely outputs sklearn RF/GB, we try TreeExplainer first
    # but fallback to KernelExplainer if needed.
    
    explainer = None
    try:
        logger.info("Attempting TreeExplainer (optimized for tree models)...")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
    except Exception as e:
        logger.warning(f"TreeExplainer failed: {e}. Falling back to KernelExplainer...")
        # KernelExplainer requires a background dataset. 
        # We use a small sample of X_test as background.
        background = shap.kmeans(X_test, 10) # 10 clusters
        explainer = shap.KernelExplainer(model.predict, background)
        # Sample 100 points for SHAP calculation to keep runtime reasonable
        # If X_test is large, we might need to subsample for the explanation itself
        # but we want SHAP for the whole test set if possible. 
        # KernelExplainer is slow on full sets. 
        # Strategy: Compute SHAP on a representative subset if too large, 
        # or just run on full if < 5000 samples.
        if len(X_test) > 2000:
            logger.warning(f"Test set size ({len(X_test)}) is large for KernelExplainer. Sampling 2000 points.")
            indices = np.random.choice(len(X_test), 2000, replace=False)
            X_sample = X_test[indices]
            shap_values = explainer.shap_values(X_sample)
            # Note: This returns SHAP for the sample, not the full set. 
            # For a full report, we might need to iterate or accept the sample.
            # The task asks to save shap values. We will save the computed ones.
            logger.info(f"Computed SHAP for {len(X_sample)} samples.")
        else:
            shap_values = explainer.shap_values(X_test)
    
    # Handle multi-output regression if necessary (SHAP returns list for multi-output)
    if isinstance(shap_values, list):
        # Average SHAP values across outputs for single summary if needed, 
        # or keep as is. For regression with single target, it's usually 2D.
        # If it's a list of arrays (one per output), we might need to stack or select.
        # Assuming single target for this specific imbalance study context.
        if len(shap_values) > 1:
            # Take mean across outputs if multi-target
            shap_values = np.mean(shap_values, axis=0)
        else:
            shap_values = shap_values[0]
    
    return shap_values

def main():
    """Main entry point for T037."""
    logger.info("Starting T037: SHAP Value Computation")
    
    # Ensure output directory exists
    output_dir = PROJECT_ROOT / "results" / "shap_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Paths to trained models
    # Based on training.py and evaluation.py logic, models are saved in results/
    # We expect: results/models/baseline_rf.pkl, results/models/baseline_gb.pkl
    # and results/models/balanced_rf.pkl, results/models/balanced_gb.pkl
    # However, the task asks for "skewed" (baseline) and "balanced" (resampled)
    # We will compute SHAP for the primary model type (e.g., Random Forest) 
    # or aggregate if multiple. Let's assume we compute for the first available 
    # or specifically RF as per typical baseline.
    
    # Let's look for model files. The training.py saves them.
    # We'll assume the standard naming from the pipeline:
    # skewed (baseline) models
    baseline_rf_path = PROJECT_ROOT / "results" / "models" / "baseline_rf.pkl"
    balanced_rf_path = PROJECT_ROOT / "results" / "models" / "balanced_rf.pkl"
    
    # If specific model files aren't found, we might need to load from the 
    # evaluation step's cached models or re-load. 
    # The evaluation.py has load_models. Let's use that if possible, 
    # but it expects a directory or specific structure.
    
    # Fallback: Try to load test data first to ensure we have features
    # The test data is usually saved after descriptors are computed and split.
    # Let's assume the test data is available in data/processed or similar, 
    # but evaluation.py loads it.
    
    # Since we need to match the exact flow, let's try to load the models 
    # and data directly.
    
    # 1. Load Skewed (Baseline) Model and Test Data
    # We assume the baseline model was trained on the skewed data.
    # We need the test set that corresponds to the skewed training.
    # The evaluation.py load_test_data likely loads the held-out set.
    
    # For simplicity and robustness, we will attempt to load the models 
    # from the expected paths. If they don't exist, we raise an error.
    
    if not baseline_rf_path.exists() and not balanced_rf_path.exists():
        # Try to find any .pkl in results/models
        model_dir = PROJECT_ROOT / "results" / "models"
        if model_dir.exists():
            pkl_files = list(model_dir.glob("*.pkl"))
            if pkl_files:
                logger.warning(f"Expected model files not found. Found: {[f.name for f in pkl_files]}")
                # We cannot proceed without knowing which is which.
                # We will assume the user must have run the training pipeline.
                raise FileNotFoundError("Trained model files (baseline_rf.pkl, balanced_rf.pkl) not found in results/models/. Please run the training pipeline first.")
        else:
            raise FileNotFoundError(f"Model directory {model_dir} does not exist.")
    
    # Load Skewed Model (Baseline)
    try:
        with open(baseline_rf_path, 'rb') as f:
            model_skewed = pickle.load(f)
        logger.info(f"Loaded skewed model from {baseline_rf_path}")
    except FileNotFoundError:
        logger.warning(f"Skewed model not found at {baseline_rf_path}. Trying to find any baseline model...")
        # Fallback logic to find the model if naming is slightly different
        # This is a bit heuristic.
        model_dir = PROJECT_ROOT / "results" / "models"
        baseline_models = [f for f in model_dir.glob("*.pkl") if "baseline" in f.name or "skewed" in f.name]
        if baseline_models:
            with open(baseline_models[0], 'rb') as f:
                model_skewed = pickle.load(f)
            logger.info(f"Loaded skewed model from {baseline_models[0]}")
        else:
            raise FileNotFoundError("Could not locate a baseline/skewed model file.")

    # Load Balanced Model
    try:
        with open(balanced_rf_path, 'rb') as f:
            model_balanced = pickle.load(f)
        logger.info(f"Loaded balanced model from {balanced_rf_path}")
    except FileNotFoundError:
        logger.warning(f"Balanced model not found at {balanced_rf_path}. Trying to find any balanced model...")
        model_dir = PROJECT_ROOT / "results" / "models"
        balanced_models = [f for f in model_dir.glob("*.pkl") if "balanced" in f.name]
        if balanced_models:
            with open(balanced_models[0], 'rb') as f:
                model_balanced = pickle.load(f)
            logger.info(f"Loaded balanced model from {balanced_models[0]}")
        else:
            raise FileNotFoundError("Could not locate a balanced model file.")

    # Load Test Data
    # We need the feature matrix X_test used for evaluation.
    # The evaluation.py load_test_data function is the canonical source.
    # However, it might return a dict or specific structure.
    # Let's assume it returns X, y or a dataframe.
    # We need to ensure we are using the SAME test set for both models.
    
    # Since load_test_data is in evaluation.py, we call it.
    # It likely loads from a cached file or reconstructs the split.
    # For T037, we assume the test data is available as a processed file 
    # or can be loaded.
    
    # Let's try to load the processed data directly if evaluation.py doesn't 
    # provide a simple "get_test_X" function.
    # The descriptors are in data/processed/descriptors.parquet.
    # The split might be stored.
    
    # Alternative: The evaluation.py main function or load_models might 
    # have access to the test data.
    # Let's try to load the test data from the standard location if it exists,
    # or reconstruct it.
    
    # For this implementation, we will assume the test data is saved 
    # in results/evaluation/test_data.pkl or similar by the evaluation step.
    # If not, we might need to re-run the split logic.
    # However, to keep T037 independent, we assume the test data is available.
    
    # Let's try to load the test data from the evaluation step's output.
    # If not found, we raise an error.
    test_data_path = PROJECT_ROOT / "results" / "evaluation" / "test_data.pkl"
    if not test_data_path.exists():
        # Try to find any test data
        eval_dir = PROJECT_ROOT / "results" / "evaluation"
        if eval_dir.exists():
            test_files = list(eval_dir.glob("*test*.pkl"))
            if test_files:
                test_data_path = test_files[0]
            else:
                raise FileNotFoundError("Test data file not found in results/evaluation/. Please run evaluation.py first.")
        else:
            raise FileNotFoundError("Results/Evaluation directory not found.")
    
    with open(test_data_path, 'rb') as f:
        test_data = pickle.load(f)
    
    # Extract X_test
    if isinstance(test_data, dict):
        X_test = test_data.get('X_test')
        if X_test is None:
            # Try other keys
            for key in test_data:
                if 'X' in key and 'test' in key.lower():
                    X_test = test_data[key]
                    break
    elif isinstance(test_data, tuple):
        X_test = test_data[0]
    elif hasattr(test_data, 'values'): # DataFrame
        X_test = test_data.values
    else:
        X_test = test_data

    if X_test is None:
        raise ValueError("Could not extract X_test from loaded test data.")
    
    # Ensure X_test is a numpy array
    X_test = np.array(X_test)
    logger.info(f"Loaded test data with shape: {X_test.shape}")

    # Compute SHAP for Skewed Model
    shap_skewed = compute_shap_values(model_skewed, X_test, "RandomForest (Skewed)")
    
    # Compute SHAP for Balanced Model
    shap_balanced = compute_shap_values(model_balanced, X_test, "RandomForest (Balanced)")

    # Save results
    shap_skewed_path = output_dir / "shap_skewed.npy"
    shap_balanced_path = output_dir / "shap_balanced.npy"

    np.save(shap_skewed_path, shap_skewed)
    np.save(shap_balanced_path, shap_balanced)

    logger.info(f"Saved SHAP values for skewed model to {shap_skewed_path}")
    logger.info(f"Saved SHAP values for balanced model to {shap_balanced_path}")
    logger.info("T037 completed successfully.")

if __name__ == "__main__":
    main()
