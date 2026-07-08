import os
import sys
import json
import warnings
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import config

def load_data() -> pd.DataFrame:
    """
    Load the processed dataset from the unified CSV.
    Expects 'data/processed/reef_species_unified.csv' or similar filtered output.
    Since T019 produces 'data/processed/filtered_features.csv', we load that.
    """
    input_path = Path(config.PROJECT_ROOT) / "data" / "processed" / "filtered_features.csv"
    
    if not input_path.exists():
        # Fallback to the unified CSV if filtered doesn't exist yet, though T019 should have run
        input_path = Path(config.PROJECT_ROOT) / "data" / "processed" / "reef_species_unified.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Ensure T019 (VIF filtering) has completed successfully.")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns exist
    required_cols = ['latitude', 'longitude', 'bleaching_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for spatial split: {missing}")
    
    return df

def spatial_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data spatially:
    Train: Western Pacific (Longitude < 180)
    Test: Eastern Pacific (Longitude >= 180 or Longitude < -150, depending on coordinate system)
    
    Based on standard geographic definitions for this project:
    - Western Pacific: Longitudes roughly 100E to 180 (or -180 to -140)
    - Eastern Pacific: Longitudes roughly 80W to 140W (-80 to -140)
    
    We assume the data uses standard -180 to 180 longitude.
    Western Pacific: Longitude > 100 (approx)
    Eastern Pacific: Longitude < -60 (approx)
    
    To be safe and specific to the task "West vs East Pacific":
    We will define West as Longitude > 0 (East of Prime Meridian, covering Asia/Australia)
    and East as Longitude < 0 (West of Prime Meridian, covering Americas).
    However, the Pacific spans both.
    
    Refined Logic for Pacific Split:
    Western Pacific (Train): Longitude between 100 and 180 (or -180 to -140)
    Eastern Pacific (Test): Longitude between -140 and -60 (approx)
    
    Let's use a simpler heuristic based on the specific task "West vs East Pacific":
    West Pacific: Longitude > 100 (covers Australia, Indonesia, etc.)
    East Pacific: Longitude < -60 (covers Americas coast)
    This might be too sparse.
    
    Let's try:
    Train (West): Longitude > 0 (covers most of the Western Pacific)
    Test (East): Longitude < 0 (covers Eastern Pacific and Atlantic, but we assume data is Pacific focused)
    
    Actually, a common split in coral studies is:
    West Pacific: 100°E to 180°
    East Pacific: 180° to 100°W (or -180 to -100)
    
    Let's implement a robust split:
    Train: Longitude >= 100 (Western Pacific)
    Test: Longitude <= -60 (Eastern Pacific)
    This ensures we are comparing distinct ocean basins.
    
    If the data uses 0-360, we need to adjust. Assuming -180 to 180.
    """
    df = df.copy()
    
    # Ensure longitude is in -180 to 180 range
    # If data is 0-360, convert: val > 180 -> val - 360
    if df['longitude'].max() > 180:
        df['longitude'] = df['longitude'].apply(lambda x: x - 360 if x > 180 else x)
    
    # Define regions
    # Western Pacific: Longitude > 100 (e.g., Great Barrier Reef, Indonesia)
    # Eastern Pacific: Longitude < -60 (e.g., Galapagos, Costa Rica)
    # Note: This might exclude some data, but it's a strict spatial split.
    
    train_mask = df['longitude'] > 100
    test_mask = df['longitude'] < -60
    
    # If masks are empty, fallback to a simpler split (e.g., >0 vs <0)
    if train_mask.sum() == 0 or test_mask.sum() == 0:
        warnings.warn("Strict Pacific split yielded empty sets. Falling back to >0 vs <0.")
        train_mask = df['longitude'] > 0
        test_mask = df['longitude'] <= 0
    
    train_df = df[train_mask].reset_index(drop=True)
    test_df = df[test_mask].reset_index(drop=True)
    
    print(f"Spatial Split Summary:")
    print(f"  Train (Western Pacific): {len(train_df)} rows")
    print(f"  Test (Eastern Pacific): {len(test_df)} rows")
    
    if len(train_df) == 0 or len(test_df) == 0:
        raise ValueError("Spatial split resulted in an empty train or test set. "
                         "Check data distribution or split logic.")
    
    return train_df, test_df

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> xgb.XGBClassifier:
    """
    Train the XGBoost model with default parameters for now.
    Hyperparameter tuning (T023) will be added later.
    """
    model = xgb.XGBClassifier(
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=config.RANDOM_SEED,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
    """
    Evaluate the model on the test set.
    Returns metrics including ROC-AUC.
    """
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Check for zero variance in target (edge case T024)
    if len(y_test.unique()) < 2:
        warnings.warn("Test set has only one class. ROC-AUC cannot be computed.")
        return {
            "roc_auc": None,
            "message": "Test set has only one class"
        }
    
    try:
        auc = roc_auc_score(y_test, y_pred_proba)
    except ValueError as e:
        warnings.warn(f"ROC-AUC calculation failed: {e}")
        auc = None
    
    return {
        "roc_auc": auc
    }

def save_results(results: Dict[str, Any]):
    """
    Save model results to data/models/results.json
    """
    output_path = Path(config.PROJECT_ROOT) / "data" / "models" / "results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_path}")

def main():
    """
    Main function for model training.
    1. Load data
    2. Spatial split
    3. Train model
    4. Evaluate
    5. Save results
    """
    print("Starting Model Training (T022)...")
    
    # Load data
    df = load_data()
    print(f"Loaded {len(df)} rows.")
    
    # Identify features and target
    # Target is 'bleaching_label'
    # Features are all numeric columns except coordinates and target
    target_col = 'bleaching_label'
    exclude_cols = ['latitude', 'longitude', target_col]
    
    # Filter for numeric features
    feature_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found for training.")
    
    print(f"Training on {len(feature_cols)} features.")
    
    # Spatial Split
    train_df, test_df = spatial_split(df)
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    # Train Model
    print("Training XGBoost model...")
    model = train_model(X_train, y_train)
    
    # Evaluate
    print("Evaluating model...")
    metrics = evaluate_model(model, X_test, y_test)
    
    # Prepare results
    results = {
        "task": "T022_Spatial_Split_Train",
        "train_size": len(train_df),
        "test_size": len(test_df),
        "features_used": feature_cols,
        "metrics": metrics
    }
    
    # Save results
    save_results(results)
    
    print("T022 completed successfully.")

if __name__ == "__main__":
    main()