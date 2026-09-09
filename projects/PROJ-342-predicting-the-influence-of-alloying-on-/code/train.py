import os
import sys
import logging
import json
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.metrics import r2_score, mean_absolute_error

# Import from local modules based on provided API surface
# Note: resource_monitor is imported inside the function or at top if needed for decorator
# Assuming resource_monitor is available in code/
try:
    from resource_monitor import enforce_resource_limits, ResourceLimitExceeded
except ImportError:
    # Fallback for standalone execution if run from code root
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    current_file = Path(__file__).resolve()
    # Assuming code/train.py is at code/train.py, root is parent of parent?
    # Actually, based on structure: project_root/code/train.py
    # So root is parent of 'code'
    return current_file.parent.parent

def load_prepared_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """Loads the prepared descriptors and target data."""
    if data_path is None:
        project_root = get_project_root()
        data_path = project_root / "data" / "processed" / "descriptors.csv"
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Ensure target column exists
    if 'Tg' not in df.columns:
        raise ValueError("Target column 'Tg' not found in data.")
    
    # Ensure family column exists (assuming 'family' based on context)
    # If the column name is different, adjust here. Usually 'family' or 'alloy_family'
    if 'family' not in df.columns:
        # Try to infer or raise error. Assuming 'family' is present per task context.
        # If not, we might need to check 'alloy_family' or similar.
        # For now, assume 'family' exists as per task description logic.
        raise ValueError("Column 'family' not found in data. Required for LOFO.")
    
    return df

def get_family_groups(df: pd.DataFrame) -> Dict[str, int]:
    """Returns a dictionary of family names and their counts."""
    return df['family'].value_counts().to_dict()

def generate_stratification_limitation_report(family_name: str, count: int, action: str, project_root: Path) -> str:
    """
    Generates a markdown snippet for the stratification limitation.
    Returns the path to the generated file.
    """
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = processed_dir / "stratification_limitation.md"
    
    # If file exists, append or overwrite? Task says "generate", implying creation or update.
    # To be safe and idempotent for a single run, we might append or overwrite.
    # Given the task description: "generate data/processed/stratification_limitation.md with content: ..."
    # We will overwrite if it's the only one, or append if multiple.
    # Let's assume we create/overwrite for simplicity in this single task context, 
    # or append if the file already exists to capture all warnings.
    
    content = f"family_name: {family_name}, count: {count}, action: {action}\n"
    
    if os.path.exists(file_path):
        with open(file_path, 'a') as f:
            f.write(content)
    else:
        with open(file_path, 'w') as f:
            f.write("# Stratification Limitation Report\n")
            f.write("The following families had insufficient samples for robust Leave-One-Family-Out validation:\n\n")
            f.write(content)
    
    logger.info(f"Generated stratification limitation report at {file_path}")
    return str(file_path)

def check_family_stratification(df: pd.DataFrame, min_samples: int = 50, drop_threshold: int = 2) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Checks family sizes and drops/warns as per T072.
    
    Args:
        df: Input dataframe with 'family' column.
        min_samples: Threshold for warning (N < 50).
        drop_threshold: Threshold for dropping (N < 2).
        
    Returns:
        Tuple of (cleaned_df, list_of_limitation_records)
    """
    family_counts = df['family'].value_counts()
    records = []
    families_to_drop = []
    
    for family, count in family_counts.items():
        if count < drop_threshold:
            families_to_drop.append(family)
            records.append({
                "family_name": family,
                "count": count,
                "action": "dropped"
            })
            logger.warning(f"FAMILY_DROPPED: Family '{family}' has {count} samples (< {drop_threshold}). Dropping.")
        elif count < min_samples:
            records.append({
                "family_name": family,
                "count": count,
                "action": "warning"
            })
            logger.warning(f"STRATIFICATION_WARNING: Family '{family}' has {count} samples (< {min_samples}). Proceeding with caution.")
    
    if families_to_drop:
        df_cleaned = df[~df['family'].isin(families_to_drop)].reset_index(drop=True)
        logger.info(f"Dropped {len(families_to_drop)} families. New shape: {df_cleaned.shape}")
    else:
        df_cleaned = df
    
    return df_cleaned, records

def lofo_cv_score(df: pd.DataFrame, max_depth: int = 5) -> Dict[str, float]:
    """
    Performs Leave-One-Family-Out Cross-Validation.
    """
    X = df.drop(columns=['Tg', 'family'])
    y = df['Tg']
    groups = df['family']
    
    gkf = GroupKFold(n_splits=len(groups.unique()))
    
    # Check if we have enough groups
    if gkf.n_splits < 2:
        logger.warning("Not enough unique families for LOFO CV. Returning dummy score.")
        return {"r2": 0.0, "mae": 0.0}
    
    model = GradientBoostingRegressor(max_depth=max_depth, random_state=42)
    
    scores = cross_validate(
        model, X, y, 
        groups=groups, 
        cv=gkf, 
        scoring=['r2', 'neg_mean_absolute_error'],
        return_train_score=False
    )
    
    r2_scores = scores['test_r2']
    mae_scores = -scores['test_neg_mean_absolute_error']
    
    return {
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores))
    }

def train_and_evaluate(df: pd.DataFrame, max_depth: int = 5) -> Tuple[GradientBoostingRegressor, Dict[str, float]]:
    """
    Trains the final model on the full dataset.
    """
    X = df.drop(columns=['Tg', 'family'])
    y = df['Tg']
    
    model = GradientBoostingRegressor(max_depth=max_depth, random_state=42)
    model.fit(X, y)
    
    # Calculate metrics on training set (or holdout if specified, but task implies full training for artifact)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    metrics = {
        "r2": float(r2),
        "mae": float(mae),
        "max_depth": max_depth
    }
    
    return model, metrics

def save_artifacts(model: GradientBoostingRegressor, metrics: Dict[str, float], project_root: Path):
    """Saves model and metrics to artifacts directory."""
    models_dir = project_root / "artifacts" / "models"
    metrics_dir = project_root / "artifacts" / "metrics"
    
    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = models_dir / "best_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    # Save metrics
    metrics_path = metrics_dir / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

@enforce_resource_limits
def main():
    """
    Main execution flow for T072: Stratification check and LOFO training.
    """
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    # 1. Load Data
    df = load_prepared_data()
    
    # 2. Check Stratification (T072 Core Logic)
    df_cleaned, limitation_records = check_family_stratification(df)
    
    # Generate limitation report if any issues found
    if limitation_records:
        generate_stratification_limitation_report(
            limitation_records[0]['family_name'], 
            limitation_records[0]['count'], 
            limitation_records[0]['action'],
            project_root
        )
        # Note: The function appends, so calling it once for the first record 
        # is sufficient if we assume it's the only one or we handle appending inside.
        # The function implementation handles appending for subsequent calls.
        # To be thorough, we could loop, but the function already handles file existence.
        # Let's ensure all records are written if multiple exist.
        for rec in limitation_records[1:]:
             generate_stratification_limitation_report(
                rec['family_name'], 
                rec['count'], 
                rec['action'],
                project_root
            )

    # 3. Perform LOFO CV (Optional but good for validation)
    # We skip full LOFO in main if just training, but task implies LOFO context.
    # Let's run a quick LOFO to ensure split works without crash.
    try:
        lofo_results = lofo_cv_score(df_cleaned)
        logger.info(f"LOFO CV Results: {lofo_results}")
    except Exception as e:
        logger.error(f"LOFO CV failed: {e}")
        # Continue to training even if LOFO fails due to group issues

    # 4. Train Final Model
    model, metrics = train_and_evaluate(df_cleaned)
    
    # 5. Save Artifacts
    save_artifacts(model, metrics, project_root)
    
    logger.info("T072 Execution Complete.")

if __name__ == "__main__":
    main()