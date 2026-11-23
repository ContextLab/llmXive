import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.base import BaseEstimator, RegressorMixin
from pathlib import Path
import logging
from typing import List, Dict, Tuple, Optional

class RandomForestBaseline(BaseEstimator, RegressorMixin):
    def __init__(self, n_estimators=100, random_state=42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)
    
    def score(self, X, y):
        return self.model.score(X, y)

class LinearRegressionBaseline(BaseEstimator, RegressorMixin):
    def __init__(self):
        self.model = LinearRegression()

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)
    
    def score(self, X, y):
        return self.model.score(X, y)

class BaselineTrainer:
    """
    Trainer for Random Forest and Linear Regression baselines.
    Handles k-fold cross-validation loops and saves predictions.
    """
    def __init__(self, output_path: str = "data/processed/baseline_predictions.csv"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def train_and_evaluate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        fold_indices: List[Tuple[List[int], List[int]]],
        models: Optional[List[Tuple[str, BaseEstimator]]] = None
    ) -> pd.DataFrame:
        """
        Train baselines on provided folds and collect predictions.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            fold_indices: List of (train_idx, val_idx) tuples for k-fold CV
            models: List of (name, model_instance) tuples. Defaults to RF and LR.

        Returns:
            DataFrame with columns: [fold, model, prediction, target]
        """
        if models is None:
            models = [
                ("RandomForest", RandomForestBaseline()),
                ("LinearRegression", LinearRegressionBaseline())
            ]

        predictions_data = []

        for fold_idx, (train_idx, val_idx) in enumerate(fold_indices):
            self.logger.info(f"Processing fold {fold_idx + 1}/{len(fold_indices)}")
            
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            for model_name, model in models:
                self.logger.info(f"  Training {model_name} on fold {fold_idx + 1}")
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                
                for i, (pred, target) in enumerate(zip(preds, y_val)):
                    predictions_data.append({
                        "fold": fold_idx + 1,
                        "model": model_name,
                        "prediction": float(pred),
                        "target": float(target)
                    })

        df = pd.DataFrame(predictions_data)
        self._save_predictions(df)
        return df

    def _save_predictions(self, df: pd.DataFrame) -> None:
        """Save predictions to the configured CSV path."""
        df.to_csv(self.output_path, index=False)
        self.logger.info(f"Saved baseline predictions to {self.output_path}")

    def run_from_dataset(
        self,
        input_path: str,
        feature_cols: List[str],
        target_col: str,
        n_splits: int = 5,
        shuffle: bool = True,
        random_state: int = 42
    ) -> pd.DataFrame:
        """
        Convenience method to load data, split, train, and save.
        
        Args:
            input_path: Path to the processed CSV dataset
            feature_cols: List of column names to use as features
            target_col: Column name for the target variable
            n_splits: Number of folds for CV
            shuffle: Whether to shuffle data before splitting
            random_state: Random seed for splitting

        Returns:
            DataFrame of predictions
        """
        self.logger.info(f"Loading dataset from {input_path}")
        df = pd.read_csv(input_path)
        
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataset")
        if not all(col in df.columns for col in feature_cols):
            missing = set(feature_cols) - set(df.columns)
            raise ValueError(f"Missing feature columns: {missing}")

        X = df[feature_cols].values
        y = df[target_col].values

        # Simple k-fold split logic without sklearn to avoid extra dependency if not needed,
        # but since we use sklearn models, we can use sklearn.model_selection for consistency
        from sklearn.model_selection import KFold
        
        kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
        fold_indices = list(kf.split(X))

        return self.train_and_evaluate(X, y, fold_indices)

def main():
    """Entry point for running baseline training via CLI."""
    import argparse
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Train baseline models on molecular data.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/merged_dataset.csv",
        help="Path to the input processed dataset"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/baseline_predictions.csv",
        help="Path to save baseline predictions"
    )
    parser.add_argument(
        "--features",
        type=str,
        nargs="+",
        default=["MW", "logP", "PSA", "num_rotatable_bonds"],
        help="Feature columns to use"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="target_mean",
        help="Target column name"
    )
    parser.add_argument(
        "--splits",
        type=int,
        default=5,
        help="Number of CV folds"
    )

    args = parser.parse_args()

    trainer = BaselineTrainer(output_path=args.output)
    
    try:
        df_preds = trainer.run_from_dataset(
            input_path=args.input,
            feature_cols=args.features,
            target_col=args.target,
            n_splits=args.splits
        )
        print(f"Successfully trained baselines. Output saved to {args.output}")
        print(f"Total predictions generated: {len(df_preds)}")
    except Exception as e:
        logging.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
