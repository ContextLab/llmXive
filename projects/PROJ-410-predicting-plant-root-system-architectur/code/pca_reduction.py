"""
PCA and L1 regularization for high-dimensional linear models.

Implements Feature Reduction Requirement FR-010:
- Applies PCA or L1 regularization strictly for Linear Models if features > 5000.
- Saves transformed features to data/processed/pca_features.parquet.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

# Import existing project utilities
from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessed_data(processed_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load the unified dataset splits created by preprocess.py.
    Returns X_train, X_val, X_test, and y_train/y_val/y_test if available.
    """
    train_path = processed_dir / "train.parquet"
    val_path = processed_dir / "val.parquet"
    test_path = processed_dir / "test.parquet"

    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found at {train_path}. Run preprocessing first.")

    logger.info(f"Loading training data from {train_path}")
    df_train = pd.read_parquet(train_path)
    
    # Identify feature and target columns
    # Assuming the preprocessing step created a 'target' column and numeric features
    # If the schema is different, this might need adjustment based on data-model.md
    # Common convention: last column is target, or specific column name
    if 'target' in df_train.columns:
        target_col = 'target'
    elif 'phenotype' in df_train.columns:
        target_col = 'phenotype'
    else:
        # Fallback: assume last column is target if not explicitly named
        target_col = df_train.columns[-1]
        logger.warning(f"Target column not explicitly named, assuming '{target_col}'")

    feature_cols = [c for c in df_train.columns if c != target_col]
    
    X_train = df_train[feature_cols].select_dtypes(include=[np.number])
    y_train = df_train[target_col]

    X_val = None
    y_val = None
    if val_path.exists():
        logger.info(f"Loading validation data from {val_path}")
        df_val = pd.read_parquet(val_path)
        X_val = df_val[feature_cols].select_dtypes(include=[np.number])
        y_val = df_val[target_col]

    X_test = None
    y_test = None
    if test_path.exists():
        logger.info(f"Loading test data from {test_path}")
        df_test = pd.read_parquet(test_path)
        X_test = df_test[feature_cols].select_dtypes(include=[np.number])
        y_test = df_test[target_col]

    return X_train, X_val, X_test, y_train, y_val, y_test, feature_cols

def apply_pca(X: pd.DataFrame, n_components: int = 0.95, random_state: int = 42) -> Tuple[pd.DataFrame, PCA, StandardScaler]:
    """
    Apply PCA to reduce dimensionality while retaining variance.
    
    Args:
        X: Input feature DataFrame.
        n_components: Number of components or variance ratio to retain.
        random_state: Random seed for reproducibility.
        
    Returns:
        Transformed DataFrame, fitted PCA object, fitted Scaler.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components, random_state=random_state)
    X_pca = pca.fit_transform(X_scaled)
    
    # Create DataFrame with component names
    component_names = [f'PC{i+1}' for i in range(X_pca.shape[1])]
    X_pca_df = pd.DataFrame(X_pca, columns=component_names, index=X.index)
    
    logger.info(f"PCA reduced features from {X.shape[1]} to {X_pca_df.shape[1]} (variance retained: {sum(pca.explained_variance_ratio_):.4f})")
    
    return X_pca_df, pca, scaler

def apply_l1_regularization(X: pd.DataFrame, y: pd.Series, alpha: float = 0.01, random_state: int = 42) -> Tuple[pd.DataFrame, np.ndarray, Lasso]:
    """
    Apply L1 (Lasso) regularization to select features.
    Returns the subset of features with non-zero coefficients.
    
    Args:
        X: Input feature DataFrame.
        y: Target Series.
        alpha: Regularization strength.
        random_state: Random seed.
        
    Returns:
        Reduced DataFrame, non-zero coefficients, fitted Lasso model.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    lasso = Lasso(alpha=alpha, random_state=random_state, max_iter=10000)
    lasso.fit(X_scaled, y)
    
    # Identify features with non-zero coefficients
    mask = lasso.coef_ != 0
    selected_features = X.columns[mask]
    X_reduced = X[selected_features]
    
    logger.info(f"L1 regularization selected {len(selected_features)} features out of {X.shape[1]} (alpha={alpha})")
    
    return X_reduced, lasso.coef_, lasso, scaler

def process_high_dimensional_features(
    X_train: pd.DataFrame, 
    X_val: Optional[pd.DataFrame], 
    X_test: Optional[pd.DataFrame],
    y_train: Optional[pd.Series] = None,
    feature_type: str = "pca", 
    variance_threshold: float = 0.95,
    l1_alpha: float = 0.01,
    output_dir: Path = Path("data/processed")
) -> Dict[str, Any]:
    """
    Main logic for FR-010: Apply PCA or L1 if features > 5000.
    
    Args:
        X_train: Training features.
        X_val: Validation features.
        X_test: Test features.
        y_train: Training targets (needed for L1).
        feature_type: "pca" or "l1".
        variance_threshold: Variance to retain for PCA.
        l1_alpha: Alpha for Lasso.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing transformed data and metadata.
    """
    original_n_features = X_train.shape[1]
    
    if original_n_features <= 5000:
        logger.info(f"Feature count ({original_n_features}) <= 5000. Skipping dimensionality reduction.")
        return {
            "X_train": X_train,
            "X_val": X_val,
            "X_test": X_test,
            "metadata": {
                "method": "none",
                "original_features": original_n_features,
                "reduced_features": original_n_features
            }
        }

    logger.info(f"Feature count ({original_n_features}) > 5000. Applying {feature_type.upper()} reduction.")
    
    results = {}
    
    if feature_type == "pca":
        if y_train is not None:
            logger.warning("PCA is unsupervised; y_train will not be used for fitting, but passed for consistency.")
        
        X_train_red, pca_model, scaler = apply_pca(X_train, n_components=variance_threshold)
        
        # Transform validation and test sets
        X_val_red = None
        if X_val is not None:
            X_val_scaled = scaler.transform(X_val)
            X_val_red = pd.DataFrame(
                pca_model.transform(X_val_scaled),
                columns=X_train_red.columns,
                index=X_val.index
            )
        
        X_test_red = None
        if X_test is not None:
            X_test_scaled = scaler.transform(X_test)
            X_test_red = pd.DataFrame(
                pca_model.transform(X_test_scaled),
                columns=X_train_red.columns,
                index=X_test.index
            )
        
        results["X_train"] = X_train_red
        results["X_val"] = X_val_red
        results["X_test"] = X_test_red
        
        # Save models
        model_path = output_dir / "pca_model.joblib"
        scaler_path = output_dir / "pca_scaler.joblib"
        joblib.dump(pca_model, model_path)
        joblib.dump(scaler, scaler_path)
        logger.info(f"Saved PCA model to {model_path} and scaler to {scaler_path}")
        
        results["metadata"] = {
            "method": "pca",
            "original_features": original_n_features,
            "reduced_features": X_train_red.shape[1],
            "variance_retained": variance_threshold,
            "model_path": str(model_path),
            "scaler_path": str(scaler_path)
        }
        
    elif feature_type == "l1":
        if y_train is None:
            raise ValueError("y_train is required for L1 regularization.")
        
        X_train_red, coef, lasso_model, scaler = apply_l1_regularization(X_train, y_train, alpha=l1_alpha)
        
        X_val_red = None
        if X_val is not None:
            X_val_red = X_val[X_train_red.columns]
        
        X_test_red = None
        if X_test is not None:
            X_test_red = X_test[X_train_red.columns]
        
        results["X_train"] = X_train_red
        results["X_val"] = X_val_red
        results["X_test"] = X_test_red
        
        # Save models
        model_path = output_dir / "l1_model.joblib"
        scaler_path = output_dir / "l1_scaler.joblib"
        joblib.dump(lasso_model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Save coefficients
        coef_path = output_dir / "l1_coefficients.csv"
        coef_df = pd.DataFrame({
            "feature": X_train.columns,
            "coefficient": lasso_model.coef_
        })
        coef_df.to_csv(coef_path, index=False)
        
        logger.info(f"Saved L1 model to {model_path}, scaler to {scaler_path}, and coefficients to {coef_path}")
        
        results["metadata"] = {
            "method": "l1",
            "original_features": original_n_features,
            "reduced_features": X_train_red.shape[1],
            "alpha": l1_alpha,
            "model_path": str(model_path),
            "scaler_path": str(scaler_path),
            "coefficients_path": str(coef_path)
        }
    else:
        raise ValueError(f"Unknown feature_type: {feature_type}. Use 'pca' or 'l1'.")

    return results

def save_transformed_features(results: Dict[str, Any], output_dir: Path):
    """
    Save the transformed features to parquet files as required by FR-010.
    """
    ensure_directories()
    
    train_path = output_dir / "pca_features.parquet"
    results["X_train"].to_parquet(train_path)
    logger.info(f"Saved transformed training features to {train_path}")
    
    if results["X_val"] is not None:
        val_path = output_dir / "pca_features_val.parquet"
        results["X_val"].to_parquet(val_path)
        logger.info(f"Saved transformed validation features to {val_path}")
        
    if results["X_test"] is not None:
        test_path = output_dir / "pca_features_test.parquet"
        results["X_test"].to_parquet(test_path)
        logger.info(f"Saved transformed test features to {test_path}")
    
    # Save metadata
    meta_path = output_dir / "pca_metadata.json"
    import json
    with open(meta_path, 'w') as f:
        json.dump(results["metadata"], f, indent=2)
    logger.info(f"Saved metadata to {meta_path}")

def main():
    parser = argparse.ArgumentParser(description="Apply PCA/L1 reduction for high-dimensional linear models (FR-010)")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Directory containing preprocessed data")
    parser.add_argument("--method", type=str, default="pca", choices=["pca", "l1"], help="Reduction method: PCA or L1")
    parser.add_argument("--variance", type=float, default=0.95, help="Variance threshold for PCA")
    parser.add_argument("--alpha", type=float, default=0.01, help="Alpha for L1 regularization")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = data_dir
    
    try:
        X_train, X_val, X_test, y_train, y_val, y_test, feature_cols = load_preprocessed_data(data_dir)
        
        results = process_high_dimensional_features(
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            feature_type=args.method,
            variance_threshold=args.variance,
            l1_alpha=args.alpha,
            output_dir=output_dir
        )
        
        save_transformed_features(results, output_dir)
        
        logger.info("PCA/L1 reduction completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during reduction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
