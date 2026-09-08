import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from sklearn.model_selection import LeaveOneGroupOut, KFold, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# Import from project modules
from seed import set_seed, get_seed
from hygiene import calculate_md5, save_artifact_hashes
from config.loader import load_schema_map, get_target_columns
from models import ModelPerformance, FeatureImportance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingResult:
    best_model: Any
    best_params: Dict[str, Any]
    metrics: Dict[str, float]
    feature_importance: List[FeatureImportance]
    lomo_results: Optional[Dict[str, Any]] = None
    lomo_warnings: List[str] = field(default_factory=list)
    fallback_mode: str = "none"  # 'kfold' or 'none'

class LeaveOneMaterialClassOut:
    """
    Custom CV splitter that implements Leave-One-Material-Class-Out (LOMO).
    
    Logic:
    1. Groups data by 'material_class'.
    2. Skips classes with fewer than 15 records.
    3. If fewer than 3 valid classes remain, falls back to K-Fold (k=5).
    4. Logs warnings for skipped classes and fallback triggers.
    """
    
    def __init__(self, min_class_size: int = 15, min_valid_classes: int = 3, n_splits_fallback: int = 5):
        self.min_class_size = min_class_size
        self.min_valid_classes = min_valid_classes
        self.n_splits_fallback = n_splits_fallback
        self.warnings: List[str] = []
        self.fallback_mode: str = "none"
        self._valid_classes: List[str] = []

    def _validate_classes(self, groups: pd.Series) -> Tuple[List[str], List[str]]:
        """
        Identify valid classes (>= min_class_size) and log skipped ones.
        Returns (valid_classes, skipped_classes).
        """
        class_counts = groups.value_counts()
        valid_classes = []
        skipped_classes = []
        
        for cls, count in class_counts.items():
            if count >= self.min_class_size:
                valid_classes.append(cls)
            else:
                skipped_classes.append(cls)
                self.warnings.append(
                    f"LOMO: Skipping material class '{cls}' due to insufficient records "
                    f"(count={count}, threshold={self.min_class_size})."
                )
        
        return valid_classes, skipped_classes

    def split(self, X: pd.DataFrame, y: Optional[pd.Series] = None, groups: Optional[pd.Series] = None):
        """
        Generate indices to split data into training and test set.
        
        Args:
            X: Feature DataFrame.
            y: Target Series (unused but required by sklearn interface).
            groups: Material class labels (required for LOMO).
        
        Yields:
            (train_indices, test_indices) tuples.
        """
        if groups is None:
            raise ValueError("LOMO requires 'groups' argument containing material class labels.")
        
        groups = pd.Series(groups)
        valid_classes, skipped_classes = self._validate_classes(groups)
        self._valid_classes = valid_classes
        
        # Filter groups to only valid classes for splitting
        valid_mask = groups.isin(valid_classes)
        valid_groups = groups[valid_mask]
        
        # Check fallback condition
        if len(valid_classes) < self.min_valid_classes:
            self.fallback_mode = "kfold"
            self.warnings.append(
                f"LOMO: Only {len(valid_classes)} valid classes found (threshold={self.min_valid_classes}). "
                f"Falling back to K-Fold ({self.n_splits_fallback}-fold) on valid data."
            )
            # Use K-Fold on valid data
            kf = KFold(n_splits=self.n_splits_fallback, shuffle=True, random_state=get_seed())
            for train_idx, test_idx in kf.split(valid_groups):
                # Map back to original indices
                original_train_idx = valid_groups.index[train_idx]
                original_test_idx = valid_groups.index[test_idx]
                yield original_train_idx, original_test_idx
        else:
            # Standard LOMO on valid classes
            logo = LeaveOneGroupOut()
            # We need to pass only the valid groups and indices
            for train_idx, test_idx in logo.split(valid_groups, groups=valid_groups):
                original_train_idx = valid_groups.index[train_idx]
                original_test_idx = valid_groups.index[test_idx]
                yield original_train_idx, original_test_idx

    def get_n_splits(self, X: Optional[pd.DataFrame] = None, y: Optional[pd.Series] = None, groups: Optional[pd.Series] = None) -> int:
        if groups is None:
            return 0
        groups = pd.Series(groups)
        valid_classes, _ = self._validate_classes(groups)
        
        if len(valid_classes) < self.min_valid_classes:
            return self.n_splits_fallback
        return len(valid_classes)

def load_processed_data(data_path: str = "data/processed/aggregated_clean.csv") -> pd.DataFrame:
    """Load the aggregated clean dataset."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}. Run T015 first.")
    return pd.read_csv(path)

def prepare_features_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Separate features, target, and material class groups.
    Excludes 'contact_load' and 'sliding_speed' if target is K (Archard's K) to avoid circularity.
    """
    # Assume target is 'wear_rate' or 'K' (wear coefficient)
    # Based on T013, if target is K, we exclude contact_load and sliding_speed
    target_col = 'wear_rate' # Default, adjust if 'K' is the actual target column name
    if 'K' in df.columns:
        target_col = 'K'
    
    # Define predictor exclusion if target is K
    exclude_cols = []
    if target_col == 'K':
        exclude_cols = ['contact_load', 'sliding_speed']
    
    # Define columns to use
    # Assuming 'material_class' is the grouping column
    group_col = 'material_class'
    
    # Feature columns: all numeric columns except target, group, and excluded
    feature_cols = [col for col in df.columns 
                    if col not in [target_col, group_col] + exclude_cols 
                    and df[col].dtype in ['int64', 'float64', 'object']]
    
    # Filter out non-numeric if needed for specific models, but Pipeline handles encoding
    X = df[feature_cols]
    y = df[target_col]
    groups = df[group_col]
    
    return X, y, groups

def create_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    """
    Create a preprocessor pipeline for numeric and categorical features.
    """
    numeric_features = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    return preprocessor

def train_model(X: pd.DataFrame, y: pd.Series, groups: pd.Series) -> TrainingResult:
    """
    Main training pipeline with LOMO evaluation.
    """
    set_seed()
    
    preprocessor = create_preprocessor(X)
    
    # Define models and parameters
    models = {
        'linear': LinearRegression(),
        'rf': RandomForestRegressor(random_state=get_seed()),
        'gb': GradientBoostingRegressor(random_state=get_seed())
    }
    
    param_grids = {
        'rf': {
            'randomforestregressor__n_estimators': [100, 200],
            'randomforestregressor__max_depth': [None, 5, 10],
            'randomforestregressor__min_samples_split': [2, 5]
        },
        'gb': {
            'gradientboostingregressor__n_estimators': [100, 200],
            'gradientboostingregressor__learning_rate': [0.05, 0.1, 0.2],
            'gradientboostingregressor__max_depth': [3, 5, 7]
        }
        # Linear regression has no hyperparameters for grid search in this context
    }
    
    best_model = None
    best_score = -np.inf
    best_params = {}
    best_model_name = ""
    
    lomo_cv = LeaveOneMaterialClassOut(min_class_size=15, min_valid_classes=3)
    lomo_warnings = []
    fallback_mode = "none"
    
    # Store LOMO results
    lomo_results = {
        'standard_scores': [],
        'lomo_scores': [],
        'ratio': None,
        'drop': None,
        'failure': False
    }
    
    for name, model in models.items():
        logger.info(f"Training {name} model...")
        
        # Create pipeline
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])
        
        # Grid Search if params exist
        if name in param_grids:
            grid_search = GridSearchCV(
                pipeline, 
                param_grids[name], 
                cv=5, 
                scoring='r2',
                n_jobs=-1
            )
            grid_search.fit(X, y)
            model_to_eval = grid_search.best_estimator_
            params = grid_search.best_params_
            score = grid_search.best_score_
        else:
            pipeline.fit(X, y)
            model_to_eval = pipeline
            params = {}
            score = r2_score(y, pipeline.predict(X))
        
        # LOMO Evaluation
        lomo_scores = cross_val_score(
            model_to_eval, X, y, 
            groups=groups, 
            cv=lomo_cv, 
            scoring='r2', 
            n_jobs=-1
        )
        mean_lomo_score = np.mean(lomo_scores)
        
        # Standard CV (for comparison ratio) - using same LOMO object but keeping all data for standard?
        # The task asks for test_R2_loo / test_R2_standard. 
        # Usually 'standard' implies random K-Fold. Let's use 5-Fold K-Fold for standard.
        kfold = KFold(n_splits=5, shuffle=True, random_state=get_seed())
        standard_scores = cross_val_score(
            model_to_eval, X, y, 
            cv=kfold, 
            scoring='r2', 
            n_jobs=-1
        )
        mean_standard_score = np.mean(standard_scores)
        
        logger.info(f"{name} - Standard R²: {mean_standard_score:.4f}, LOMO R²: {mean_lomo_score:.4f}")
        
        # Update LOMO results for the best model later
        if score > best_score:
            best_score = score
            best_model = model_to_eval
            best_params = params
            best_model_name = name
            
            # Calculate transferability metrics
            if mean_standard_score > 0:
                ratio = mean_lomo_score / mean_standard_score
                drop = mean_standard_score - mean_lomo_score
                failure = ratio < 0.8
                
                lomo_results = {
                    'standard_test_R2': float(mean_standard_score),
                    'lomo_test_R2': float(mean_lomo_score),
                    'ratio': float(ratio),
                    'drop': float(drop),
                    'transferability_failure': failure
                }
        
        # Collect warnings from LOMO splitter
        if hasattr(lomo_cv, 'warnings'):
            lomo_warnings.extend(lomo_cv.warnings)
        if hasattr(lomo_cv, 'fallback_mode'):
            if lomo_cv.fallback_mode != "none":
                fallback_mode = lomo_cv.fallback_mode

    # Log warnings
    for warn in lomo_warnings:
        logger.warning(warn)
    
    # Feature Importance (simplified)
    feature_importance = []
    if hasattr(best_model, 'named_steps'):
        regressor = best_model.named_steps['regressor']
        if hasattr(regressor, 'feature_importances_'):
            # Get feature names after preprocessing
            ohe = best_model.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
            cat_features = ohe.get_feature_names_out().tolist()
            num_features = best_model.named_steps['preprocessor'].named_transformers_['num'].get_feature_names_out().tolist()
            all_features = num_features + cat_features
            
            importances = regressor.feature_importances_
            for name, imp in zip(all_features, importances):
                feature_importance.append(FeatureImportance(feature=name, importance=float(imp)))
    
    return TrainingResult(
        best_model=best_model,
        best_params=best_params,
        metrics={'r2': float(best_score)},
        feature_importance=feature_importance,
        lomo_results=lomo_results,
        lomo_warnings=lomo_warnings,
        fallback_mode=fallback_mode
    )

def run_lomo_evaluation(result: TrainingResult, X: pd.DataFrame, y: pd.Series, groups: pd.Series):
    """
    Re-run or finalize LOMO evaluation if needed.
    In this implementation, LOMO is integrated into train_model.
    This function serves as a placeholder for any post-processing.
    """
    logger.info("LOMO evaluation integrated into training pipeline.")
    return result

def run_training_pipeline(data_path: str = "data/processed/aggregated_clean.csv", output_path: str = "models/best_model.joblib"):
    """
    Full pipeline: load data, train, evaluate, save.
    """
    df = load_processed_data(data_path)
    X, y, groups = prepare_features_targets(df)
    
    result = train_model(X, y, groups)
    
    # Save model
    joblib.dump(result.best_model, output_path)
    logger.info(f"Best model saved to {output_path}")
    
    # Save performance report
    performance_report = {
        'best_model_name': 'unknown', # Determine from result if needed
        'best_params': result.best_params,
        'metrics': result.metrics,
        'lomo_results': result.lomo_results,
        'fallback_mode': result.fallback_mode,
        'warnings': result.lomo_warnings
    }
    
    report_path = "reports/model_performance.json"
    with open(report_path, 'w') as f:
        json.dump(performance_report, f, indent=2)
    logger.info(f"Performance report saved to {report_path}")
    
    # Update artifact hashes
    save_artifact_hashes([output_path, report_path])
    
    return result

def save_results(result: TrainingResult, path: str = "reports/training_result.json"):
    """Save training result to JSON (serializing non-serializable parts)."""
    serializable = {
        'metrics': result.metrics,
        'best_params': result.best_params,
        'lomo_results': result.lomo_results,
        'fallback_mode': result.fallback_mode,
        'warnings': result.lomo_warnings
    }
    with open(path, 'w') as f:
        json.dump(serializable, f, indent=2)

def main():
    """Entry point for training."""
    logger.info("Starting training pipeline (T021: LOMO Logic Implementation)...")
    try:
        result = run_training_pipeline()
        logger.info("Training pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()