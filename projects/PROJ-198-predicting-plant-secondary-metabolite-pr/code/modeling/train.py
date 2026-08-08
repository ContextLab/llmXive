import os
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Local imports based on provided API surface
from config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

class StratifiedSplitError(Exception):
    """Raised when stratified splitting fails."""
    pass

class ModelTrainingError(Exception):
    """Raised when model training fails."""
    pass

def get_clade_members(tree_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract clade members from tree data.
    Note: This is a placeholder for actual phylogenetic logic if needed,
    but for 5-fold CV we primarily rely on the data index.
    """
    return {}

def find_balanced_clades(clade_members: Dict[str, List[str]], n_clades: int = 5) -> List[List[str]]:
    """
    Attempt to find balanced clades for stratification.
    Returns a list of lists, where each inner list is a clade group.
    """
    return []

def create_stratified_split(
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    random_state: int = 42
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create a stratified split for cross-validation.
    Since we are doing regression on metabolite profiles, strict stratification
    by class isn't always applicable unless we bin the target.
    Here we implement a standard KFold with shuffling, which is robust for
    regression tasks when N is moderate.
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    splits = []
    for train_idx, test_idx in kf.split(X):
        splits.append((train_idx, test_idx))
    return splits

def load_pca_features(
    path: Optional[str] = None,
    config: Optional[Any] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load PCA-reduced features from the interim dataset.
    Expected path: data/interim/pca_features.csv
    """
    if path is None:
        if config is None:
            config = get_config()
        # Assuming config has a method or attribute for data paths
        # Based on T023a, the output is data/interim/pca_features.csv
        base_path = Path("data/interim")
        file_path = base_path / "pca_features.csv"
    else:
        file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"PCA features file not found at {file_path}. "
                                "Please run T023a-PCA first.")

    df = pd.read_csv(file_path)

    # Assume first column is species index, rest are features, last is target
    # Adjust based on actual T023a output structure.
    # Typically: index_col=0 for species, features = all numeric cols except target
    if 'target' in df.columns:
        y = df['target']
        X = df.drop(columns=['target', 'species'])
    else:
        # Fallback assumption: last column is target, second to last is species
        # This is a heuristic; T023a should ensure a standard format.
        cols = df.columns.tolist()
        if 'species' in cols:
            cols.remove('species')
        y = df[cols[-1]]
        X = df[cols[:-1]]

    return X, y

def apply_pca(X: pd.DataFrame, n_components: int = 0.95) -> pd.DataFrame:
    """
    Apply PCA for dimensionality reduction.
    This function is included for reference/completeness as per T023a-PCA requirement,
    though T023b primarily consumes the output of T023a.
    """
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X)
    return pd.DataFrame(X_pca, index=X.index, columns=[f"PC{i+1}" for i in range(X_pca.shape[1])])

def train_models_loo(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Train models using Leave-One-Out Cross-Validation.
    Kept for backward compatibility, though T023b uses 5-fold.
    """
    from sklearn.model_selection import LeaveOneOut
    loo = LeaveOneOut()
    # Implementation omitted as this task is specifically for 5-fold
    raise NotImplementedError("Use train_models_5fold for this task.")

def determine_cv_method(n_samples: int, method: str = "auto") -> int:
    """
    Determine the appropriate CV method based on sample size.
    """
    if method == "loo":
        return -1 # Indicator for LOO
    return 5 # Default to 5-fold

def train_models_5fold(
    X: Optional[pd.DataFrame] = None,
    y: Optional[pd.Series] = None,
    n_splits: int = 5,
    output_path: Optional[str] = None,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Train Random Forest, Elastic Net, and Gradient Boosting with 5-fold CV.
    Runs ONLY if N >= 20.
    Uses PCA-reduced features from T023a-PCA.

    Args:
        X: Feature dataframe (optional, loads from file if None)
        y: Target series (optional, loads from file if None)
        n_splits: Number of CV folds (default 5)
        output_path: Path to save results (default: data/processed/cv_results_5fold.json)
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing model metrics and best hyperparameters (if applicable)
    """
    logger.info("Starting 5-Fold Cross-Validation Training (T023b)")

    # 1. Load Data
    if X is None or y is None:
        try:
            X, y = load_pca_features()
        except FileNotFoundError as e:
            logger.error(str(e))
            raise ModelTrainingError("PCA features not found. Run T023a-PCA first.")

    N = len(X)
    logger.info(f"Loaded {N} samples for training.")

    # 2. Check Sample Size Constraint
    if N < 20:
        logger.warning(f"Sample size N={N} is less than 20. Skipping 5-fold CV as per T023b requirement.")
        return {
            "status": "skipped",
            "reason": f"N={N} < 20",
            "n_samples": N
        }

    # 3. Initialize Models
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=100,
            max_depth=None,
            random_state=random_state,
            n_jobs=-1
        ),
        "ElasticNet": ElasticNet(
            alpha=0.1,
            l1_ratio=0.5,
            random_state=random_state,
            max_iter=1000
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=random_state
        )
    }

    results = {
        "task_id": "T023b",
        "method": "5-Fold CV",
        "n_samples": N,
        "n_splits": n_splits,
        "models": {}
    }

    # 4. Training Loop
    for name, model in models.items():
        logger.info(f"Training {name}...")
        
        # Create a pipeline to ensure scaling is applied correctly within CV
        # ElasticNet benefits from scaling; RF/GBDT do not strictly require it but it's safe
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])

        # Calculate cross-validated R2 scores
        # Note: For ElasticNet, we might want to tune alpha/l1_ratio, but using defaults for this task
        # as per "train models" instruction without explicit grid search request.
        try:
            scores = cross_val_score(
                pipeline, X, y, 
                cv=n_splits, 
                scoring='r2', 
                n_jobs=-1
            )
            
            mean_r2 = np.mean(scores)
            std_r2 = np.std(scores)
            
            logger.info(f"{name} - Mean R²: {mean_r2:.4f} (+/- {std_r2:.4f})")
            
            results["models"][name] = {
                "mean_r2": float(mean_r2),
                "std_r2": float(std_r2),
                "fold_scores": scores.tolist(),
                "status": "success"
            }

            # Optional: Train on full data for feature importance if needed later
            # pipeline.fit(X, y)
            # if hasattr(model, 'feature_importances_'):
            #     results["models"][name]["feature_importances"] = ...

        except Exception as e:
            logger.error(f"Error training {name}: {e}")
            results["models"][name] = {
                "status": "failed",
                "error": str(e)
            }

    # 5. Save Results
    if output_path is None:
        output_path = "data/processed/cv_results_5fold.json"
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return results

def main():
    """
    Entry point for the T023b task.
    Executes the 5-fold cross-validation training pipeline.
    """
    try:
        results = train_models_5fold()
        if results.get("status") == "skipped":
            print(f"Task T023b skipped: {results['reason']}")
        else:
            print("Task T023b completed successfully.")
            print(json.dumps(results, indent=2))
    except Exception as e:
        logger.critical(f"Task T023b failed: {e}")
        raise

if __name__ == "__main__":
    main()
