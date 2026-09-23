import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from scipy.stats import ttest_ind
import warnings

# Import local utilities
from seed import set_seed
from logging_config import get_logger, raise_on_missing_data
from hygiene import update_artifact_hash

warnings.filterwarnings('ignore')

logger = get_logger(__name__)

@dataclass
class TrainingResult:
    model_name: str
    r2: float
    mae: float
    rmse: float
    params: Dict[str, Any]
    feature_importance: Optional[Dict[str, float]] = None

class LeaveOneMaterialClassOutCV:
    """Custom CV splitter for Leave-One-Material-Class-Out validation."""
    def __init__(self, material_col: str = 'material_class'):
        self.material_col = material_col

    def split(self, X: pd.DataFrame, y: Optional[np.ndarray] = None, groups: Optional[np.ndarray] = None):
        if groups is not None:
            unique_groups = np.unique(groups)
        else:
            unique_groups = X[self.material_col].unique()

        if len(unique_groups) < 3:
            logger.warning(f"Less than 3 material classes found ({len(unique_groups)}). Falling back to K-Fold (K=5).")
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            for train_idx, test_idx in kf.split(X):
                yield train_idx, test_idx
        else:
            for i, group in enumerate(unique_groups):
                test_mask = X[self.material_col] == group
                train_mask = ~test_mask
                yield np.where(train_mask)[0], np.where(test_mask)[0]

def load_processed_data(filepath: str) -> pd.DataFrame:
    """Load the preprocessed dataset."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded data from {filepath}: {len(df)} records")
    return df

def prepare_features_targets(df: pd.DataFrame, target_col: str = 'wear_coefficient', 
                             exclude_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Prepare X and y, handling categorical features."""
    exclude = exclude_cols or []
    feature_cols = [c for c in df.columns if c not in exclude + [target_col]]
    
    # Identify categorical columns
    categorical_cols = df[feature_cols].select_dtypes(include=['object', 'category']).columns.tolist()
    numeric_cols = df[feature_cols].select_dtypes(include=['number']).columns.tolist()
    
    X = df[feature_cols]
    y = df[target_col]
    
    return X, y, categorical_cols, numeric_cols

def train_model(model: Any, X_train: pd.DataFrame, y_train: pd.Series, 
                categorical_cols: List[str], numeric_cols: List[str]) -> Pipeline:
    """Train a model within a pipeline to prevent leakage."""
    preprocessor = ColumnTransformer(transformers=[
        ('num', StandardScaler(), numeric_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
    ])
    
    pipe = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    
    pipe.fit(X_train, y_train)
    return pipe

def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Evaluate model performance."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    return {'r2': r2, 'mae': mae, 'rmse': rmse}

def evaluate_models(results: List[TrainingResult]) -> TrainingResult:
    """Select the best model based on R2."""
    if not results:
        raise ValueError("No models to evaluate.")
    best = max(results, key=lambda x: x.r2)
    logger.info(f"Best model: {best.model_name} with R2={best.r2:.4f}")
    return best

def run_lomo_cv(model: Pipeline, X: pd.DataFrame, y: pd.Series, 
                categorical_cols: List[str], numeric_cols: List[str],
                material_col: str = 'material_class') -> Dict[str, float]:
    """Run Leave-One-Material-Class-Out cross-validation."""
    splitter = LeaveOneMaterialClassOutCV(material_col=material_col)
    r2_scores = []
    mae_scores = []
    
    for train_idx, test_idx in splitter.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Retrain model for this fold
        fold_model = train_model(model, X_train, y_train, categorical_cols, numeric_cols)
        metrics = evaluate_model(fold_model, X_test, y_test)
        r2_scores.append(metrics['r2'])
        mae_scores.append(metrics['mae'])
    
    return {
        'mean_r2': np.mean(r2_scores),
        'std_r2': np.std(r2_scores),
        'mean_mae': np.mean(mae_scores),
        'std_mae': np.std(mae_scores)
    }

def analyze_transferability(standard_metrics: Dict[str, float], lomo_metrics: Dict[str, float]) -> Dict[str, Any]:
    """Analyze transferability by comparing standard and LOMO performance."""
    ratio = lomo_metrics['mean_r2'] / standard_metrics['r2'] if standard_metrics['r2'] > 0 else 0
    drop = standard_metrics['r2'] - lomo_metrics['mean_r2']
    failure = ratio < 0.8
    
    return {
        'ratio': ratio,
        'r2_drop': drop,
        'transferability_failure': failure,
        'lomo_mean_r2': lomo_metrics['mean_r2'],
        'standard_r2': standard_metrics['r2']
    }

def save_best_model(best_result: TrainingResult, model: Pipeline, 
                    performance_metrics: Dict[str, Any], output_model_path: str, 
                    output_report_path: str) -> None:
    """
    Save the best trained model and its performance report.
    
    Args:
        best_result: The TrainingResult object containing model metadata and metrics.
        model: The trained sklearn Pipeline.
        performance_metrics: Dictionary containing detailed performance metrics (R2, MAE, etc.).
        output_model_path: Path to save the model (.joblib).
        output_report_path: Path to save the performance report (.json).
    """
    logger.info(f"Saving best model ({best_result.model_name}) to {output_model_path}")
    
    # Ensure directories exist
    Path(output_model_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_report_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save the model
    joblib.dump(model, output_model_path)
    logger.info(f"Model saved successfully.")
    
    # Prepare report data
    report_data = {
        'best_model_name': best_result.model_name,
        'metrics': {
            'r2': best_result.r2,
            'mae': best_result.mae,
            'rmse': best_result.rmse
        },
        'hyperparameters': best_result.params,
        'feature_importance': best_result.feature_importance,
        'performance_details': performance_metrics
    }
    
    # Save the report
    with open(output_report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Performance report saved to {output_report_path}")
    
    # Update artifact hash for the model
    update_artifact_hash(output_model_path)
    update_artifact_hash(output_report_path)

def main():
    """Main entry point for training and saving the best model."""
    set_seed(42)
    
    # Configuration
    data_path = "data/processed/normalized_only.csv"
    model_output_path = "models/best_model.joblib"
    report_output_path = "reports/model_performance.json"
    
    # Load data
    try:
        df = load_processed_data(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if df.empty:
        logger.error("Dataset is empty after loading.")
        sys.exit(1)
    
    # Prepare features
    target_col = 'wear_coefficient'
    exclude_cols = ['contact_load', 'sliding_speed', 'normalization_method', 'material_class']
    
    try:
        X, y, categorical_cols, numeric_cols = prepare_features_targets(
            df, target_col=target_col, exclude_cols=exclude_cols
        )
    except Exception as e:
        logger.error(f"Failed to prepare features: {e}")
        sys.exit(1)
    
    # Define models
    models = {
        'LinearRegression': LinearRegression(),
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    
    # Grid search parameters
    param_grids = {
        'LinearRegression': {},
        'RandomForest': {'model__n_estimators': [50, 100], 'model__max_depth': [None, 10]},
        'GradientBoosting': {'model__n_estimators': [50, 100], 'model__learning_rate': [0.05, 0.1]}
    }
    
    results = []
    best_model_pipe = None
    best_score = -np.inf
    
    # Train and evaluate
    for name, model in models.items():
        logger.info(f"Training {name}...")
        
        # Setup pipeline for GridSearchCV
        preprocessor = ColumnTransformer(transformers=[
            ('num', StandardScaler(), numeric_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ])
        
        pipe = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        grid = GridSearchCV(
            pipe, 
            param_grids[name], 
            cv=5, 
            scoring='r2', 
            n_jobs=-1,
            refit=True
        )
        
        try:
            grid.fit(X, y)
            best_params = grid.best_params_
            best_estimator = grid.best_estimator_
            metrics = evaluate_model(best_estimator, X, y) # Using full data for final score estimation as per simplified flow
            
            # Extract feature importance if available
            feat_imp = None
            if hasattr(best_estimator.named_steps['model'], 'feature_importances_'):
                # This is a simplification; proper extraction requires inverse transform of one-hot
                feat_imp = {} 
            
            results.append(TrainingResult(
                model_name=name,
                r2=metrics['r2'],
                mae=metrics['mae'],
                rmse=metrics['rmse'],
                params=best_params,
                feature_importance=feat_imp
            ))
            
            if metrics['r2'] > best_score:
                best_score = metrics['r2']
                best_model_pipe = best_estimator
                
        except Exception as e:
            logger.error(f"Error training {name}: {e}")
            continue
    
    if not results:
        logger.error("No models were trained successfully.")
        sys.exit(1)
    
    # Select best model
    best_result = evaluate_models(results)
    logger.info(f"Best model selected: {best_result.model_name}")
    
    # Run LOMO CV for the best model
    lomo_metrics = run_lomo_cv(best_model_pipe, X, y, categorical_cols, numeric_cols)
    
    # Analyze transferability
    transfer_analysis = analyze_transferability(
        {'r2': best_result.r2}, 
        lomo_metrics
    )
    
    # Compile performance metrics
    performance_metrics = {
        'best_model': best_result.model_name,
        'metrics': {
            'r2': best_result.r2,
            'mae': best_result.mae,
            'rmse': best_result.rmse
        },
        'lomo_validation': lomo_metrics,
        'transferability_analysis': transfer_analysis
    }
    
    # Save best model and report
    save_best_model(
        best_result, 
        best_model_pipe, 
        performance_metrics, 
        model_output_path, 
        report_output_path
    )
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
