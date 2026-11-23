import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_preprocessed_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load the preprocessed descriptors and split into features, target, and strata."""
    logger.info(f"Loading preprocessed data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Target variable
    target_col = 'T_d'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Available columns: {df.columns.tolist()}")
    
    # Stratification column
    strata_col = 'perovskite_family'
    if strata_col not in df.columns:
        raise ValueError(f"Stratification column '{strata_col}' not found in data.")
    
    # Uncertainty weights column
    weight_col = 'T_d_uncertainty'
    if weight_col not in df.columns:
        raise ValueError(f"Weight column '{weight_col}' not found in data.")
    
    # Feature columns (exclude metadata and target)
    exclude_cols = [target_col, strata_col, weight_col, 'formula']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    strata = df.loc[X.index, strata_col]
    weights = df.loc[X.index, weight_col]
    
    # Drop rows with NaN in features or target
    valid_mask = ~(y.isna() | strata.isna() | weights.isna())
    X = X[valid_mask]
    y = y[valid_mask]
    strata = strata[valid_mask]
    weights = weights[valid_mask]
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    return X, y, strata, weights

def create_parameter_grid() -> Dict[str, List[Dict[str, Any]]]:
    """
    Create parameter grids with a hard cap of <= 10 combinations per model.
    This ensures grid search completes within resource constraints.
    """
    # Random Forest: 2 params * 2 values * 2 values = 4 combinations
    rf_params = [
        {
            'n_estimators': [50, 100],
            'max_depth': [3, None]
        }
    ]
    
    # Gradient Boosting: 2 params * 2 values * 2 values = 4 combinations
    gb_params = [
        {
            'n_estimators': [50, 100],
            'learning_rate': [0.05, 0.1]
        }
    ]
    
    # Elastic Net: 2 params * 2 values * 2 values = 4 combinations
    en_params = [
        {
            'alpha': [0.01, 0.1],
            'l1_ratio': [0.2, 0.8]
        }
    ]
    
    return {
        'RandomForest': rf_params,
        'GradientBoosting': gb_params,
        'ElasticNet': en_params
    }

def run_grid_search(
    X: pd.DataFrame,
    y: pd.Series,
    strata: pd.Series,
    weights: pd.Series,
    model_type: str,
    param_grid: List[Dict[str, Any]],
    cv_folds: int = 5
) -> Tuple[Any, Dict[str, Any]]:
    """
    Run grid search with stratified K-fold and optional sample weighting.
    Returns the best model and search results summary.
    """
    logger.info(f"Running grid search for {model_type} with {len(param_grid)} parameter combinations")
    
    # Initialize model
    if model_type == 'RandomForest':
        model = RandomForestRegressor(random_state=42, n_jobs=-1)
    elif model_type == 'GradientBoosting':
        model = GradientBoostingRegressor(random_state=42)
    elif model_type == 'ElasticNet':
        model = ElasticNet(random_state=42, max_iter=1000)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Create stratified KFold
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    # Handle sample weights - some models support sample_weight directly in fit
    # For GridSearchCV, we need to pass sample_weight via fit_params
    # We'll use a wrapper approach for weighted fitting
    
    # For models that support sample_weight in fit (RF, GB, EN)
    fit_params = {'sample_weight': weights.values}
    
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=skf,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y, **fit_params)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_score = grid_search.best_score_
    
    # Get all results
    results = {
        'best_params': best_params,
        'best_score': best_score,
        'cv_results': grid_search.cv_results_
    }
    
    logger.info(f"Best {model_type} params: {best_params}, CV R²: {best_score:.4f}")
    
    return best_model, results

def save_grid_search_results(
    results: Dict[str, Any],
    output_path: str,
    model_type: str
):
    """Save grid search results to JSON file."""
    # Convert cv_results to serializable format
    serializable_results = {}
    for key, value in results.items():
        if key == 'cv_results':
            serializable_results[key] = {}
            for k, v in value.items():
                # Convert numpy arrays to lists
                if isinstance(v, np.ndarray):
                    serializable_results[key][k] = v.tolist()
                else:
                    serializable_results[key][k] = v
        elif isinstance(value, np.ndarray):
            serializable_results[key] = value.tolist()
        elif isinstance(value, (np.float64, np.float32)):
            serializable_results[key] = float(value)
        else:
            serializable_results[key] = value
    
    output_data = {
        'model_type': model_type,
        'timestamp': pd.Timestamp.now().isoformat(),
        'results': serializable_results
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved grid search results for {model_type} to {output_path}")

def main():
    """Main entry point for grid search execution."""
    # Configuration
    data_path = 'data/processed/descriptors.csv'
    output_dir = 'data/processed'
    output_file = Path(output_dir) / 'grid_search_results.json'
    
    logger.info("Starting grid search for perovskite stability prediction")
    
    # Load data
    try:
        X, y, strata, weights = load_preprocessed_data(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    # Create parameter grids (capped at <= 10 combinations each)
    param_grids = create_parameter_grid()
    
    # Run grid search for each model
    all_results = {}
    
    for model_type, param_grid in param_grids.items():
        logger.info(f"\n--- Processing {model_type} ---")
        
        # Verify parameter count
        total_combinations = 1
        for param_set in param_grid:
            param_count = 1
            for values in param_set.values():
                param_count *= len(values)
            total_combinations *= param_count
        
        if total_combinations > 10:
            raise ValueError(f"{model_type} has {total_combinations} combinations, exceeding limit of 10")
        
        logger.info(f"Testing {total_combinations} parameter combinations for {model_type}")
        
        try:
            best_model, search_results = run_grid_search(
                X, y, strata, weights, model_type, param_grid
            )
            
            # Save results for this model
            model_output_path = str(output_file.with_name(f'grid_search_{model_type.lower()}.json'))
            save_grid_search_results(search_results, model_output_path, model_type)
            
            # Store in all_results
            all_results[model_type] = {
                'best_params': search_results['best_params'],
                'best_cv_score': search_results['best_score'],
                'output_file': model_output_path
            }
            
        except Exception as e:
            logger.error(f"Grid search failed for {model_type}: {e}")
            all_results[model_type] = {
                'error': str(e),
                'best_params': None,
                'best_cv_score': None
            }
    
    # Save summary of all results
    summary_path = str(output_file)
    summary_data = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'parameter_limit': 10,
        'models': all_results
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    logger.info(f"Grid search completed. Summary saved to {summary_path}")
    logger.info("Summary:")
    for model_type, result in all_results.items():
        if result.get('best_params'):
            logger.info(f"  {model_type}: R²={result['best_cv_score']:.4f}, params={result['best_params']}")
        else:
            logger.info(f"  {model_type}: FAILED - {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    main()