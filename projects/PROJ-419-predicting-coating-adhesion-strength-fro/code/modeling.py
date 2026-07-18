import logging
import os
import numpy as np
import pandas as pd
import json
import time
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import cross_val_score, KFold, GridSearchCV, cross_val_predict
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import shap
from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr
from utils import check_memory_limit, log_memory_snapshot

logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset."""
    path = 'data/processed/coating_adhesion_dataset.csv'
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed dataset not found at {path}")
    logger.info(f"Loaded processed dataset from {path} with shape {pd.read_csv(path).shape}")
    return pd.read_csv(path)

def train_gradient_boosting(df: pd.DataFrame) -> Tuple[Any, Dict[str, float]]:
    """Train Gradient Boosting Regressor with nested k-fold CV."""
    logger.info("Training Gradient Boosting model with nested CV...")
    
    # Check memory before training
    check_memory_limit()
    
    # Prepare features and target
    # Assume target column is 'adhesion_strength'
    target_col = 'adhesion_strength'
    if target_col not in df.columns:
        # Try to find a similar column
        target_candidates = [c for c in df.columns if 'adhesion' in c.lower() or 'strength' in c.lower()]
        if target_candidates:
            target_col = target_candidates[0]
            logger.warning(f"Using '{target_col}' as target column")
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle any remaining NaN values
    X = X.fillna(X.mean())
    y = y.fillna(y.mean())
    
    # Define parameter grid for inner CV
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1]
    }
    
    # Nested CV: Outer loop for evaluation, Inner loop for hyperparameter tuning
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    base_model = GradientBoostingRegressor(random_state=42)
    
    # Perform nested CV
    outer_scores = []
    best_params_list = []
    
    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Inner CV for hyperparameter tuning
        grid_search = GridSearchCV(
            base_model, 
            param_grid, 
            cv=inner_cv, 
            scoring='r2',
            n_jobs=1  # CPU-only as per requirements
        )
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        best_params_list.append(grid_search.best_params_)
        
        # Evaluate on outer test set
        y_pred = best_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        outer_scores.append(r2)
    
    # Train final model on full data with best average params
    avg_params = {}
    for key in best_params_list[0].keys():
        values = [params[key] for params in best_params_list]
        avg_params[key] = max(set(values), key=values.count)  # Most common value
    
    final_model = GradientBoostingRegressor(**avg_params, random_state=42)
    final_model.fit(X, y)
    
    # Calculate metrics
    y_pred_full = final_model.predict(X)
    metrics = {
        'mean_r2': float(np.mean(outer_scores)),
        'std_r2': float(np.std(outer_scores)),
        'r2_full': float(r2_score(y, y_pred_full)),
        'rmse_full': float(np.sqrt(mean_squared_error(y, y_pred_full))),
        'mae_full': float(mean_absolute_error(y, y_pred_full)),
        'best_params': avg_params
    }
    
    logger.info(f"Gradient Boosting completed. Mean R²: {metrics['mean_r2']:.4f} (+/- {metrics['std_r2']:.4f})")
    log_memory_snapshot()
    
    return final_model, metrics

def train_random_forest(df: pd.DataFrame) -> Tuple[Any, Dict[str, float]]:
    """Train Random Forest Regressor with nested k-fold CV."""
    logger.info("Training Random Forest model with nested CV...")
    
    # Check memory before training
    check_memory_limit()
    
    # Prepare features and target
    target_col = 'adhesion_strength'
    if target_col not in df.columns:
        target_candidates = [c for c in df.columns if 'adhesion' in c.lower() or 'strength' in c.lower()]
        if target_candidates:
            target_col = target_candidates[0]
            logger.warning(f"Using '{target_col}' as target column")
        else:
            raise ValueError(f"Target column '{target_col}' not found in dataset")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Handle any remaining NaN values
    X = X.fillna(X.mean())
    y = y.fillna(y.mean())
    
    # Define parameter grid for inner CV
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10],
        'min_samples_split': [2, 5]
    }
    
    # Nested CV
    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=42)
    
    base_model = RandomForestRegressor(random_state=42, n_jobs=1)
    
    outer_scores = []
    best_params_list = []
    
    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        grid_search = GridSearchCV(
            base_model, 
            param_grid, 
            cv=inner_cv, 
            scoring='r2',
            n_jobs=1
        )
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        best_params_list.append(grid_search.best_params_)
        
        y_pred = best_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        outer_scores.append(r2)
    
    # Train final model
    avg_params = {}
    for key in best_params_list[0].keys():
        values = [params[key] for params in best_params_list]
        avg_params[key] = max(set(values), key=values.count)
    
    final_model = RandomForestRegressor(**avg_params, random_state=42, n_jobs=1)
    final_model.fit(X, y)
    
    # Calculate metrics
    y_pred_full = final_model.predict(X)
    metrics = {
        'mean_r2': float(np.mean(outer_scores)),
        'std_r2': float(np.std(outer_scores)),
        'r2_full': float(r2_score(y, y_pred_full)),
        'rmse_full': float(np.sqrt(mean_squared_error(y, y_pred_full))),
        'mae_full': float(mean_absolute_error(y, y_pred_full)),
        'best_params': avg_params
    }
    
    logger.info(f"Random Forest completed. Mean R²: {metrics['mean_r2']:.4f} (+/- {metrics['std_r2']:.4f})")
    log_memory_snapshot()
    
    return final_model, metrics

def compute_shap_values(model: Any, X: pd.DataFrame) -> Dict[str, Any]:
    """Compute SHAP values for top features."""
    logger.info("Computing SHAP values...")
    
    check_memory_limit()
    
    # Use KernelExplainer for tree-based models if TreeExplainer is too memory intensive
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
    except Exception as e:
        logger.warning(f"TreeExplainer failed ({e}), falling back to KernelExplainer (slower)")
        explainer = shap.KernelExplainer(model.predict, X.sample(min(100, len(X)), random_state=42))
        shap_values = explainer.shap_values(X)
    
    # Get mean absolute SHAP values for ranking
    if isinstance(shap_values, list):
        # For multi-output, take mean across outputs
        mean_shap = np.mean([np.abs(sv) for sv in shap_values], axis=0)
    else:
        mean_shap = np.abs(shap_values)
    
    mean_shap_summary = np.mean(mean_shap, axis=0)
    
    shap_results = {
        'values': shap_values,
        'summary': mean_shap_summary,
        'feature_names': list(X.columns)
    }
    
    logger.info(f"SHAP computation complete for {len(X.columns)} features")
    return shap_results

def compute_permutation_importance(model: Any, X: pd.DataFrame, y: np.ndarray) -> Dict[str, float]:
    """Compute permutation importance for top features."""
    logger.info("Computing permutation importance...")
    
    check_memory_limit()
    
    result = permutation_importance(
        model, X, y, 
        n_repeats=10, 
        random_state=42, 
        n_jobs=1,
        scoring='r2'
    )
    
    importance_dict = {
        feature: float(importance) 
        for feature, importance in zip(X.columns, result.importances_mean)
    }
    
    logger.info(f"Permutation importance computed for {len(importance_dict)} features")
    return importance_dict

def rank_features(shap_vals: Dict, perm_vals: Dict) -> List[str]:
    """Rank features based on SHAP and permutation importance."""
    # Get SHAP summary ranking
    shap_summary = shap_vals.get('summary', np.zeros(len(shap_vals.get('feature_names', []))))
    shap_features = shap_vals.get('feature_names', [])
    
    shap_ranks = np.argsort(np.argsort(-shap_summary))  # Rank from highest to lowest
    shap_ranked_features = [f for _, f in sorted(zip(-shap_summary, shap_features))]
    
    # Get permutation importance ranking
    perm_features = list(perm_vals.keys())
    perm_ranks = np.argsort(np.argsort([-perm_vals[f] for f in perm_features]))
    perm_ranked_features = [f for _, f in sorted(zip([-perm_vals[f] for f in perm_features], perm_features))]
    
    # Combine rankings (simple average of ranks)
    all_features = list(set(shap_ranked_features) | set(perm_ranked_features))
    combined_scores = []
    
    for feat in all_features:
        shap_rank = shap_ranked_features.index(feat) if feat in shap_ranked_features else len(shap_ranked_features)
        perm_rank = perm_ranked_features.index(feat) if feat in perm_ranked_features else len(perm_ranked_features)
        combined_scores.append((shap_rank + perm_rank) / 2, feat)
    
    combined_scores.sort(key=lambda x: x[0])
    ranked_features = [feat for _, feat in combined_scores]
    
    logger.info(f"Features ranked: {len(ranked_features)} features")
    return ranked_features

def calculate_spearman_correlation(rank1: List, rank2: List) -> float:
    """Calculate Spearman correlation between two rankings."""
    if len(rank1) != len(rank2) or len(rank1) == 0:
        return 0.0
    
    # Convert rankings to ranks
    rank1_dict = {feat: i for i, feat in enumerate(rank1)}
    rank2_dict = {feat: i for i, feat in enumerate(rank2)}
    
    common_features = list(set(rank1) & set(rank2))
    if len(common_features) < 2:
        return 0.0
    
    x = [rank1_dict[f] for f in common_features]
    y = [rank2_dict[f] for f in common_features]
    
    corr, _ = spearmanr(x, y)
    return float(corr) if not np.isnan(corr) else 0.0

def distinguish_feature_categories(features: List[str]) -> Dict[str, List[str]]:
    """Distinguish features into compositional and surface categories."""
    compositional_keywords = ['atomic', 'radius', 'density', 'crosslinker', 'carbon', 'oxygen', 'hydrogen', 'element']
    surface_keywords = ['roughness', 'rms', 'skewness', 'kurtosis', 'surface', 'topography']
    
    compositional = []
    surface = []
    other = []
    
    for feat in features:
        feat_lower = feat.lower()
        if any(kw in feat_lower for kw in compositional_keywords):
            compositional.append(feat)
        elif any(kw in feat_lower for kw in surface_keywords):
            surface.append(feat)
        else:
            other.append(feat)
    
    return {
        'compositional': compositional,
        'surface': surface,
        'other': other
    }

def run_modeling_pipeline():
    """Run the full modeling pipeline."""
    logger.info("Starting modeling pipeline...")
    
    try:
        df = load_processed_data()
        
        # Train models
        gb_model, gb_metrics = train_gradient_boosting(df)
        rf_model, rf_metrics = train_random_forest(df)
        
        # Prepare data for SHAP and permutation importance
        target_col = 'adhesion_strength'
        if target_col not in df.columns:
            target_candidates = [c for c in df.columns if 'adhesion' in c.lower() or 'strength' in c.lower()]
            target_col = target_candidates[0] if target_candidates else df.columns[-1]
        
        X = df.drop(columns=[target_col])
        X = X.fillna(X.mean())
        y = df[target_col].values
        
        # Compute SHAP for Gradient Boosting (typically better performance)
        shap_results = compute_shap_values(gb_model, X)
        
        # Compute permutation importance
        perm_importance = compute_permutation_importance(gb_model, X, y)
        
        # Rank features
        ranked_features = rank_features(shap_results, perm_importance)
        
        # Calculate Spearman correlation
        shap_ranking = [f for f in rank_features(shap_results, perm_importance)]
        perm_ranking = [f for f in sorted(perm_importance.keys(), key=lambda x: -perm_importance[x])]
        spearman_corr = calculate_spearman_correlation(shap_ranking, perm_ranking)
        
        # Distinguish categories
        feature_categories = distinguish_feature_categories(ranked_features)
        
        # Compile results
        results = {
            'gradient_boosting': gb_metrics,
            'random_forest': rf_metrics,
            'spearman_correlation': spearman_corr,
            'top_features': ranked_features[:10],
            'feature_categories': feature_categories
        }
        
        # Save results
        os.makedirs('state', exist_ok=True)
        output_path = 'state/modeling_results.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Modeling pipeline completed. Results saved to {output_path}")
        return results
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise

def run_sensitivity_analysis_crosslinker_proxy():
    """Run sensitivity analysis for crosslinker density proxy definitions."""
    logger.info("Running sensitivity analysis for crosslinker proxy...")
    
    try:
        df = load_processed_data()
        target_col = 'adhesion_strength'
        if target_col not in df.columns:
            target_candidates = [c for c in df.columns if 'adhesion' in c.lower() or 'strength' in c.lower()]
            target_col = target_candidates[0] if target_candidates else df.columns[-1]
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        X = X.fillna(X.mean())
        y = y.fillna(y.mean())
        
        # Define proxy definitions to test
        proxy_definitions = [
            ('C/H', lambda d: d.get('carbon_ratio', 0) / (d.get('hydrogen_ratio', 1) + 1e-6)),
            ('O/C', lambda d: d.get('oxygen_ratio', 0) / (d.get('carbon_ratio', 1) + 1e-6)),
            ('(C+O)/H', lambda d: (d.get('carbon_ratio', 0) + d.get('oxygen_ratio', 0)) / (d.get('hydrogen_ratio', 1) + 1e-6))
        ]
        
        results = []
        
        for def_name, proxy_func in proxy_definitions:
            # Create a temporary feature set with this proxy
            X_temp = X.copy()
            
            # Try to calculate proxy if columns exist, else use a placeholder
            if 'carbon_ratio' in X_temp.columns and 'hydrogen_ratio' in X_temp.columns:
                X_temp['crosslinker_proxy'] = X_temp.apply(proxy_func, axis=1)
            else:
                # Fallback: use existing crosslinker density if available
                if 'crosslinker_density' in X_temp.columns:
                    X_temp['crosslinker_proxy'] = X_temp['crosslinker_density']
                else:
                    # Create a synthetic proxy based on available data
                    X_temp['crosslinker_proxy'] = X_temp.mean(axis=1)
            
            # Train model with this proxy
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            scores = cross_val_score(model, X_temp, y, cv=5, scoring='r2')
            
            model.fit(X_temp, y)
            y_pred = model.predict(X_temp)
            rmse = np.sqrt(mean_squared_error(y, y_pred))
            
            results.append({
                'definition': def_name,
                'model_r2': float(np.mean(scores)),
                'model_rmse': float(rmse),
                'variance': float(np.var(scores))
            })
        
        # Save report
        os.makedirs('data/processed', exist_ok=True)
        report_path = 'data/processed/crosslinker_sensitivity_report.csv'
        report_df = pd.DataFrame(results)
        report_df.to_csv(report_path, index=False)
        
        logger.info(f"Sensitivity analysis complete. Report saved to {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

def main():
    """Main entry point for modeling module."""
    logging.info("Modeling module loaded.")

if __name__ == "__main__":
    main()