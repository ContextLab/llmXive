import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

# FR-008 Disclaimer constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str) -> None:
    """Print a formatted header with the FR-008 disclaimer."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"  {FR008_DISCLAIMER}")
    print(f"{'='*60}\n")

def log_disclaimer() -> None:
    """Log the FR-008 disclaimer to stdout."""
    print(f"[DISCLAIMER] {FR008_DISCLAIMER}")

def get_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_datasets(processed_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all processed datasets."""
    log_disclaimer()
    datasets = {}
    for file_path in processed_dir.glob("*_processed.csv"):
        df = pd.read_csv(file_path)
        datasets[file_path.stem] = df
        print(f"Loaded {file_path.stem} with shape {df.shape}")
    return datasets

def train_model(df: pd.DataFrame, model_type: str, dataset_id: str, random_state: int = 42):
    """
    Train a model on the dataset.
    Returns a dictionary with model metadata and predictions (simplified).
    """
    log_disclaimer()
    
    # Identify columns
    # Assuming 'protected_attribute' and 'outcome' are present after preprocessing
    # This is a simplified logic
    target_col = 'outcome'
    feature_cols = [c for c in df.columns if c not in ['protected_attribute', 'outcome']]
    
    if 'protected_attribute' in df.columns:
        # Include protected attribute as a feature for some models, or exclude for fairness analysis
        # For this task, we include it to see its effect
        pass
        
    if target_col not in df.columns:
        print(f"Error: Target column {target_col} not found in {dataset_id}")
        return None
        
    X = df[feature_cols]
    y = df[target_col]
    
    # Train/Test Split
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    
    # Train model
    if model_type == "Logistic Regression":
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=random_state, max_iter=1000)
    elif model_type == "Random Forest":
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(random_state=random_state)
    elif model_type == "Gradient Boosting":
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(random_state=random_state)
    else:
        print(f"Unknown model type: {model_type}")
        return None
        
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    # Save model (simplified - in real impl, use joblib)
    model_id = f"{dataset_id}_{model_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    model_dir = Path("data/processed/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    metadata = {
        "model_id": model_id,
        "model_type": model_type,
        "dataset_id": dataset_id,
        "random_state": random_state,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "features": feature_cols
    }
    
    meta_path = model_dir / f"{model_id}.json"
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Saved model metadata to {meta_path}")
    
    # Return predictions and metadata for metrics calculation
    return {
        "model_id": model_id,
        "predictions": predictions,
        "true_labels": y_test.values,
        "protected_attr": X_test.get('protected_attribute', pd.Series([0]*len(X_test))).values if 'protected_attribute' in X_test else None,
        "metadata": metadata
    }

def main():
    """Main entry point for model training."""
    log_header("US2 Model Training Pipeline")
    log_disclaimer()
    
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        print(f"Error: Processed data directory {processed_dir} does not exist.")
        return
        
    datasets = load_processed_datasets(processed_dir)
    
    model_types = ["Logistic Regression", "Random Forest", "Gradient Boosting"]
    
    all_results = []
    
    for dataset_id, df in datasets.items():
        print(f"\nTraining models for {dataset_id}")
        for model_type in model_types:
            result = train_model(df, model_type, dataset_id)
            if result:
                all_results.append(result)
                print(f"Trained {model_type} on {dataset_id}")
                
    print(f"\n{'='*60}")
    print(f"Model Training Summary")
    print(f"{'='*60}")
    print(f"Total models trained: {len(all_results)}")
    print(f"{FR008_DISCLAIMER}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
