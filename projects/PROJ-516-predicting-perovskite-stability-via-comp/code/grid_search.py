"""
Grid Search Implementation for Perovskite Stability Modeling.

Implements a hard cap of ≤10 hyperparameter combinations per model
as required by T022. Supports Random Forest, Gradient Boosting, and
Elastic Net models with uncertainty-weighted training where applicable.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import ParameterGrid, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler

# Import existing training functions from model_training
from model_training import (
    train_random_forest,
    train_gradient_boosting,
    train_elastic_net,
    load_data
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Hard cap on hyperparameter combinations
MAX_COMBINATIONS = 10

def load_preprocessed_data(data_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.Series]]:
    """
    Load preprocessed descriptors and target variable.

    Args:
        data_path: Path to the processed descriptors CSV

    Returns:
        Tuple of (features_df, target_series, uncertainty_series)
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    # Identify target and feature columns
    target_col = 'T_d'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {data_path}")

    # Check for uncertainty column for weighting
    uncertainty_col = 'T_d_uncertainty'
    uncertainty_series = None
    if uncertainty_col in df.columns:
        uncertainty_series = df[uncertainty_col]
        logger.info(f"Found uncertainty column '{uncertainty_col}', will use for weighting")
    else:
        logger.warning(f"Uncertainty column '{uncertainty_col}' not found. Training without weights.")

    # Separate features and target
    feature_cols = [col for col in df.columns if col not in [target_col, uncertainty_col]]
    X = df[feature_cols]
    y = df[target_col]

    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    return X, y, uncertainty_series

def create_parameter_grid(model_type: str) -> List[Dict[str, Any]]:
    """
    Create a parameter grid with at most MAX_COMBINATIONS combinations.

    Args:
        model_type: One of 'random_forest', 'gradient_boosting', 'elastic_net'

    Returns:
        List of parameter dictionaries (at most MAX_COMBINATIONS)
    """
    if model_type == 'random_forest':
        # RF parameters: limit combinations to ≤10
        param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [5, 10, None],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        }
    elif model_type == 'gradient_boosting':
        # GB parameters: limit combinations to ≤10
        param_grid = {
            'n_estimators': [50, 100],
            'learning_rate': [0.05, 0.1],
            'max_depth': [3, 5],
            'min_samples_split': [2, 5]
        }
    elif model_type == 'elastic_net':
        # Elastic Net parameters: limit combinations to ≤10
        param_grid = {
            'alpha': [0.001, 0.01, 0.1, 1.0],
            'l1_ratio': [0.2, 0.5, 0.8],
            'max_iter': [1000, 2000]
        }
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Generate all combinations and cap at MAX_COMBINATIONS
    all_combinations = list(ParameterGrid(param_grid))
    if len(all_combinations) > MAX_COMBINATIONS:
        logger.warning(
            f"Parameter grid has {len(all_combinations)} combinations, "
            f"capping at {MAX_COMBINATIONS}"
        )
        # Take first MAX_COMBINATIONS combinations deterministically
        selected_combinations = all_combinations[:MAX_COMBINATIONS]
    else:
        selected_combinations = all_combinations
        logger.info(f"Parameter grid has {len(selected_combinations)} combinations (within limit)")

    return selected_combinations

def run_grid_search(
    model_type: str,
    X: pd.DataFrame,
    y: pd.Series,
    uncertainty: Optional[pd.Series] = None,
    cv_folds: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run grid search with hard cap on combinations.

    Args:
        model_type: Type of model to search
        X: Feature DataFrame
        y: Target Series
        uncertainty: Optional uncertainty series for weighting
        cv_folds: Number of CV folds
        random_state: Random seed for reproducibility

    Returns:
        Dictionary with best parameters, metrics, and search history
    """
    logger.info(f"Starting grid search for {model_type} with max {MAX_COMBINATIONS} combinations")

    param_grid = create_parameter_grid(model_type)
    logger.info(f"Testing {len(param_grid)} parameter combinations")

    results = []
    best_score = -np.inf
    best_params = None
    best_model = None

    # Scale features for Elastic Net (and potentially others)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    for i, params in enumerate(param_grid):
        logger.info(f"Evaluating combination {i+1}/{len(param_grid)}: {params}")

        # Create model instance with current parameters
        if model_type == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=params.get('n_estimators', 100),
                max_depth=params.get('max_depth', None),
                min_samples_split=params.get('min_samples_split', 2),
                min_samples_leaf=params.get('min_samples_leaf', 1),
                random_state=random_state,
                n_jobs=1  # CPU-only constraint
            )
            # RF doesn't natively support sample weights in sklearn,
            # but we can use a custom approach or skip weighting for RF
            sample_weights = None
        elif model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=params.get('n_estimators', 100),
                learning_rate=params.get('learning_rate', 0.1),
                max_depth=params.get('max_depth', 3),
                min_samples_split=params.get('min_samples_split', 2),
                random_state=random_state
            )
            sample_weights = None
        elif model_type == 'elastic_net':
            model = ElasticNet(
                alpha=params.get('alpha', 0.1),
                l1_ratio=params.get('l1_ratio', 0.5),
                max_iter=params.get('max_iter', 1000),
                random_state=random_state
            )
            # Use uncertainty for weighting: weight = 1/uncertainty
            if uncertainty is not None:
                sample_weights = 1.0 / uncertainty.replace(0, np.nan).fillna(1.0)
            else:
                sample_weights = None

        # Cross-validation
        try:
            if sample_weights is not None:
                # For models that support sample_weight in fit
                # We'll use a custom CV loop for weighted scoring
                scores = []
                from sklearn.model_selection import KFold
                kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
                for train_idx, val_idx in kf.split(X_scaled):
                    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    w_train = sample_weights.iloc[train_idx] if sample_weights is not None else None

                    model.fit(X_train, y_train, sample_weight=w_train)
                    y_pred = model.predict(X_val)
                    score = r2_score(y_val, y_pred)
                    scores.append(score)
                mean_score = np.mean(scores)
            else:
                # Standard CV without weights
                scores = cross_val_score(model, X_scaled, y, cv=cv_folds, scoring='r2')
                mean_score = np.mean(scores)

            logger.info(f"  CV R² score: {mean_score:.4f} ± {np.std(scores):.4f}")

            results.append({
                'params': params,
                'mean_r2': mean_score,
                'std_r2': np.std(scores),
                'cv_scores': scores.tolist()
            })

            if mean_score > best_score:
                best_score = mean_score
                best_params = params
                # Train final model with best params
                if sample_weights is not None:
                    model.fit(X_scaled, y, sample_weight=sample_weights)
                else:
                    model.fit(X_scaled, y)
                best_model = model

        except Exception as e:
            logger.error(f"  Error with params {params}: {e}")
            results.append({
                'params': params,
                'mean_r2': -np.inf,
                'std_r2': 0.0,
                'cv_scores': [],
                'error': str(e)
            })

    # Prepare results summary
    summary = {
        'model_type': model_type,
        'best_params': best_params,
        'best_cv_r2': best_score,
        'total_combinations_tested': len(param_grid),
        'max_combinations_allowed': MAX_COMBINATIONS,
        'results': results
    }

    logger.info(f"Grid search complete. Best R²: {best_score:.4f} with params: {best_params}")
    return summary, best_model

def save_grid_search_results(
    results: Dict[str, Any],
    model: Any,
    output_path: Path
):
    """
    Save grid search results and trained model.

    Args:
        results: Grid search results dictionary
        model: Best trained model
        output_path: Path to save results JSON
    """
    # Prepare model state for serialization (sklearn models can be pickled)
    # For JSON, we'll save parameters and metrics, not the full model object
    serializable_results = {
        'model_type': results['model_type'],
        'best_params': results['best_params'],
        'best_cv_r2': results['best_cv_r2'],
        'total_combinations_tested': results['total_combinations_tested'],
        'max_combinations_allowed': results['max_combinations_allowed'],
        'results': results['results']
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2, default=str)

    logger.info(f"Grid search results saved to {output_path}")

def main():
    """Main entry point for grid search execution."""
    logging.basicConfig(level=logging.INFO)

    # Paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / 'data' / 'processed' / 'descriptors.csv'
    output_path = project_root / 'data' / 'processed' / 'grid_search_results.json'

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please run feature_engineering.py and finalize_descriptors.py first")
        return

    # Load data
    X, y, uncertainty = load_preprocessed_data(data_path)

    # Run grid search for each model type
    model_types = ['random_forest', 'gradient_boosting', 'elastic_net']
    all_results = {}
    best_models = {}

    for model_type in model_types:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running grid search for {model_type}")
        logger.info(f"{'='*60}")

        try:
            results, best_model = run_grid_search(
                model_type=model_type,
                X=X,
                y=y,
                uncertainty=uncertainty,
                cv_folds=5,
                random_state=42
            )
            all_results[model_type] = results
            best_models[model_type] = best_model

        except Exception as e:
            logger.error(f"Grid search failed for {model_type}: {e}")
            all_results[model_type] = {'error': str(e)}

    # Save results
    save_grid_search_results(
        all_results,
        best_models,
        output_path
    )

    logger.info(f"\n{'='*60}")
    logger.info("Grid search complete for all models")
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"{'='*60}")

    # Print summary
    print("\nGrid Search Summary:")
    print("-" * 60)
    for model_type, results in all_results.items():
        if 'error' not in results:
            print(f"{model_type}:")
            print(f"  Best CV R²: {results['best_cv_r2']:.4f}")
            print(f"  Best params: {results['best_params']}")
            print(f"  Combinations tested: {results['total_combinations_tested']}")
        else:
            print(f"{model_type}: ERROR - {results['error']}")
        print()

if __name__ == '__main__':
    main()
