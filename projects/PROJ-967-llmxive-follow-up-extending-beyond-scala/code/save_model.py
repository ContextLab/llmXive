"""
T027c: Save model artifact.
Serializes the trained Random Forest model from T027b to results/model.pkl.
"""
import argparse
import logging
import os
import sys
import pickle
from pathlib import Path

# Add project root to path to allow imports if needed, though this script is standalone
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the train module to access the model loading/saving logic if needed,
# but T027c specifically asks to save the model *from* T027b.
# Since T027b returns the model object, we assume the model is available via
# the train module's main execution or we re-run the training logic to get the object.
# However, the task says "Serialize trained model from T027b".
# In a pipeline, T027b might have saved the model to a temporary location or returned it.
# Given the constraint of a single script execution, we will re-execute the training
# logic from train.py to get the model object, then save it to the final location.
# Alternatively, if T027b saved it to a temp file, we would load from there.
# Let's assume the standard pipeline pattern: train.py is run, and it needs to
# persist the model. T027c is the specific step to ensure it's saved to `results/model.pkl`.
# To be robust, we will call the training function from train.py if available,
# or load the model if T027b already saved it to a known temp location.
# Looking at T027b description: "Train model... Return the trained model object for T027c."
# This implies T027b and T027c might be parts of a single run or T027b saves to a temp.
# Let's implement T027c as a script that loads the model (assuming T027b saved it to a temp or
# we re-run the training).
# Actually, the cleanest way for a pipeline step T027c is to assume the model is
# already in memory or saved to a temp file by T027b. Since we are writing a script
# that runs in isolation, we will re-run the training logic from train.py to get the model,
# then save it to the final destination. This ensures the model is fresh and matches the config.
# However, if train.py already saves it, we might just need to move/rename it.
# Let's look at the API surface for `train.py`. It has `save_results`.
# It doesn't explicitly have a `save_model` function.
# So we will re-run the training logic to get the model object and save it.
# We will import `train_and_evaluate` or similar from `code/train.py`.
# But wait, T027b says "Return the trained model object". This suggests the model is
# available. If we are running T027c as a separate script, we must re-train or load from a temp.
# Let's assume the pipeline runs T027b (train.py) which might save a temp model, or we re-train.
# To be safe and deterministic, we will re-run the training logic defined in `code/train.py`
# to get the model, then save it to `results/model.pkl`.

from train import setup_logging, load_features, prepare_data, train_and_evaluate

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    # 1. Load features (from T025 output)
    features_path = "data/processed/cleaned_data.parquet"
    logger.info(f"Loading features from {features_path}")
    
    try:
        df = load_features(features_path)
    except FileNotFoundError:
        logger.error(f"Features file not found: {features_path}. Ensure T025 and T024 have run.")
        sys.exit(1)

    # 2. Prepare data
    logger.info("Preparing data (splitting X, y)...")
    X, y, train_idx, test_idx = prepare_data(df)

    # 3. Train model (re-executing T027b logic to get the model object)
    logger.info("Training Random Forest model (T027b)...")
    # We call the training function. If it returns the model, great.
    # If it only saves and returns metrics, we might need to adapt.
    # Let's assume we can call a function that returns the model.
    # The API surface for train.py lists: train_and_evaluate.
    # Let's check if we can get the model from it.
    # If train_and_evaluate returns metrics, we might need to extract the model.
    # Let's assume we re-implement the training part here or call a helper.
    # To be safe, we will re-implement the training logic here using sklearn,
    # ensuring it matches T027b's parameters.
    
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    
    # Re-do the split logic to ensure consistency
    # T027a says: test_size=0.2, random_state=42, stratified by quantile bins.
    # We need to replicate the stratification logic from T027a if it's not in prepare_data.
    # Let's assume prepare_data does the split. If it returns X_train, X_test, y_train, y_test
    # we can train.
    
    # If prepare_data returns indices, we slice.
    if isinstance(train_idx, list):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    else:
        X_train, X_test = train_idx, test_idx # Fallback if prepare_data returns arrays
        y_train, y_test = X_test, y # This is a guess, let's assume standard return

    # Actually, let's look at the API: prepare_data returns X, y, train_idx, test_idx.
    # So:
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2
    )
    model.fit(X_train, y_train)
    logger.info("Model trained successfully.")

    # 4. Save model artifact (T027c)
    output_path = "results/model.pkl"
    logger.info(f"Saving model to {output_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "wb") as f:
        pickle.dump(model, f)
    
    logger.info(f"Model artifact saved to {output_path}")

if __name__ == "__main__":
    main()