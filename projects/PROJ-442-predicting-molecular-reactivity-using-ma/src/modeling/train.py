import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_squared_error, r2_score, spearmanr
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.modeling.config import load_config

logger = get_logger(__name__)

def load_target_data(feature_path: str, target_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load feature matrix and target variable.
    If target_path is not provided, assumes target is in the same file as a column 'target'.
    """
    logger.info(f"Loading features from {feature_path}")
    if feature_path.endswith('.parquet'):
        df = pd.read_parquet(feature_path)
    else:
        df = pd.read_csv(feature_path)
    
    if 'target' not in df.columns:
        if target_path is None:
            raise ValueError("Target column 'target' not found in feature file and no target_path provided.")
        target_df = pd.read_csv(target_path)
        if 'target' not in target_df.columns:
            raise ValueError("Target column 'target' not found in target file.")
        df = df.merge(target_df[['id', 'target']], on='id', how='left')
    
    X = df.drop(columns=['target', 'id', 'reaction_smiles', 'reactant_smiles', 'product_smiles'], errors='ignore')
    y = df['target']
    return X, y

def normalize_target(y: pd.Series) -> Tuple[pd.Series, float, float]:
    """
    Normalize target variable using Z-score.
    Returns normalized series, mean, and std.
    """
    mean_val = y.mean()
    std_val = y.std()
    if std_val == 0:
        logger.warning("Target standard deviation is zero. Returning original target.")
        return y, mean_val, 1.0
    y_norm = (y - mean_val) / std_val
    return y_norm, mean_val, std_val

def train_xgboost_model(X_train: pd.DataFrame, y_train: pd.Series, config: Dict[str, Any]) -> xgb.XGBRegressor:
    """
    Train an XGBoost model with parameters from config.
    """
    params = config.get('model', {}).get('xgboost', {})
    model = xgb.XGBRegressor(
        n_estimators=params.get('n_estimators', 100),
        max_depth=params.get('max_depth', 6),
        learning_rate=params.get('learning_rate', 0.1),
        subsample=params.get('subsample', 0.8),
        colsample_bytree=params.get('colsample_bytree', 0.8),
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)
    return model

def get_scaffold(smiles: str) -> Optional[str]:
    """
    Extract the Bemis-Murcko scaffold from a SMILES string.
    Returns None if parsing fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logger.debug(f"Failed to extract scaffold from {smiles}: {e}")
        return None

class LeaveOneScaffoldOut:
    """
    Custom CV splitter that leaves out one scaffold at a time.
    For T026, we implement a 5-fold version of LOSO where we group by scaffold
    and create 5 folds of scaffolds.
    """
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits

    def split(self, X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> Any:
        """
        groups: Series of scaffold strings.
        Yields train_idx, test_idx.
        """
        unique_scaffolds = groups.unique()
        np.random.seed(42)
        np.random.shuffle(unique_scaffolds)
        
        n_scaffolds = len(unique_scaffolds)
        fold_size = n_scaffolds // self.n_splits
        
        for i in range(self.n_splits):
            start_idx = i * fold_size
            if i == self.n_splits - 1:
                end_idx = n_scaffolds
            else:
                end_idx = (i + 1) * fold_size
            
            test_scaffolds = set(unique_scaffolds[start_idx:end_idx])
            train_scaffolds = set(unique_scaffolds) - test_scaffolds
            
            test_mask = groups.isin(test_scaffolds)
            train_mask = groups.isin(train_scaffolds)
            
            yield np.where(train_mask)[0], np.where(test_mask)[0]

def run_training_pipeline(
    feature_path: str,
    output_model_path: str,
    output_metrics_path: str,
    config_path: str = "src/modeling/config.yaml"
) -> Dict[str, Any]:
    """
    Main training pipeline with 5-fold LOSO Cross-Validation.
    """
    config = load_config(config_path)
    logger.info("Starting training pipeline with 5-fold LOSO Cross-Validation")
    
    X, y = load_target_data(feature_path)
    y_norm, mean_val, std_val = normalize_target(y)
    
    # Add scaffold extraction for LOSO
    # Assuming there is a column 'reactant_smiles' or similar to derive scaffold
    # If not present, we might need to infer from the data structure.
    # For this implementation, we assume 'reactant_smiles' exists.
    if 'reactant_smiles' not in X.columns:
        # Fallback: try to find a smiles column
        smiles_cols = [c for c in X.columns if 'smiles' in c.lower()]
        if smiles_cols:
            smiles_col = smiles_cols[0]
        else:
            raise ValueError("No SMILES column found for scaffold extraction. Required for LOSO.")
    else:
        smiles_col = 'reactant_smiles'
    
    logger.info(f"Extracting scaffolds from {smiles_col}")
    X['scaffold'] = X[smiles_col].apply(get_scaffold)
    X = X.dropna(subset=['scaffold'])
    y_norm = y_norm.loc[X.index]
    
    # Initialize LOSO splitter
    loso = LeaveOneScaffoldOut(n_splits=5)
    scaffold_groups = X['scaffold']
    
    y_pred_all = np.zeros(len(y_norm))
    fold_metrics = []
    
    logger.info("Running 5-fold LOSO Cross-Validation")
    start_time = time.time()
    
    for fold_idx, (train_idx, test_idx) in enumerate(loso.split(X, y_norm, scaffold_groups)):
        logger.info(f"Fold {fold_idx + 1}/5: Train size={len(train_idx)}, Test size={len(test_idx)}")
        
        X_train, X_test = X.iloc[train_idx].drop(columns=['scaffold']), X.iloc[test_idx].drop(columns=['scaffold'])
        y_train, y_test = y_norm.iloc[train_idx], y_norm.iloc[test_idx]
        
        model = train_xgboost_model(X_train, y_train, config)
        
        # Predict on test set
        y_pred_test = model.predict(X_test)
        y_pred_all[test_idx] = y_pred_test
        
        # Metrics
        mse = mean_squared_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)
        spearman_rho, p_val = spearmanr(y_test, y_pred_test)
        
        fold_metrics.append({
            "fold": fold_idx + 1,
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "mse": float(mse),
            "r2": float(r2),
            "spearman_rho": float(spearman_rho),
            "p_value": float(p_val)
        })
        logger.info(f"Fold {fold_idx + 1} Metrics: MSE={mse:.4f}, R2={r2:.4f}, Spearman={spearman_rho:.4f}")
    
    total_time = time.time() - start_time
    logger.info(f"Cross-validation completed in {total_time:.2f} seconds")
    
    # Overall metrics
    overall_mse = mean_squared_error(y_norm, y_pred_all)
    overall_r2 = r2_score(y_norm, y_pred_all)
    overall_spearman, overall_p = spearmanr(y_norm, y_pred_all)
    
    # Re-train on full data for final model artifact
    logger.info("Training final model on full dataset")
    X_final = X.drop(columns=['scaffold'])
    model_final = train_xgboost_model(X_final, y_norm, config)
    
    # Save model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    model_final.save_model(output_model_path)
    logger.info(f"Model saved to {output_model_path}")
    
    # Save metrics
    metrics = {
        "overall": {
            "mse": float(overall_mse),
            "r2": float(overall_r2),
            "spearman_rho": float(overall_spearman),
            "p_value": float(overall_p),
            "runtime_seconds": float(total_time)
        },
        "folds": fold_metrics,
        "config_used": config
    }
    
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_metrics_path}")
    
    # Register artifacts
    register_artifact("model", output_model_path)
    register_artifact("metrics", output_metrics_path)
    
    return metrics

def main():
    """
    Entry point for training script.
    """
    logger = setup_logger("train")
    config_path = "src/modeling/config.yaml"
    config = load_config(config_path)
    
    feature_path = config.get('data', {}).get('feature_matrix_path', 'data/processed/feature_matrix.parquet')
    model_output = config.get('model', {}).get('output_path', 'data/models/xgboost_model.json')
    metrics_output = config.get('model', {}).get('metrics_path', 'data/processed/training_log.json')
    
    try:
        metrics = run_training_pipeline(feature_path, model_output, metrics_output, config_path)
        logger.info("Training pipeline completed successfully.")
        print(json.dumps(metrics['overall'], indent=2))
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()