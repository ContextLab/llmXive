import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
import xgboost as xgb

# Assuming config is available in the project root or code directory
# If not, we assume it's imported or paths are constructed relative to the script
try:
    import config
except ImportError:
    # Fallback if run as script without package structure
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import config

def compute_roc_auc(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Compute ROC-AUC score."""
    if len(np.unique(y_true)) < 2:
        warnings.warn("Only one class present in y_true. ROC-AUC is undefined.")
        return float('nan')
    return roc_auc_score(y_true, y_proba)

def run_permutation_importance(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_permutations: int = 1000,
    random_state: int = 42
) -> pd.DataFrame:
    """Run permutation importance and return results as DataFrame."""
    result = permutation_importance(
        model, X, y,
        n_repeats=n_permutations,
        random_state=random_state,
        scoring='roc_auc',
        n_jobs=-1
    )
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'mean_importance': result.importances_mean,
        'std_importance': result.importances_std,
        'raw_scores': list(result.importances)
    })
    importance_df = importance_df.sort_values('mean_importance', ascending=False)
    return importance_df

def apply_fdr_correction(
    importance_df: pd.DataFrame,
    p_value_col: str = 'p_value',
    alpha: float = 0.05
) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    if p_value_col not in importance_df.columns:
        # If p-values aren't provided, we can't correct them.
        # In a full pipeline, p-values might be derived from permutation distribution.
        # For this task, we assume p-values are passed or calculated elsewhere.
        # If missing, we return the dataframe as is with a warning.
        warnings.warn("No p-value column found. Skipping FDR correction.")
        importance_df['fdr_corrected_p'] = importance_df.get('p_value', np.nan)
        return importance_df

    p_values = importance_df[p_value_col].values
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # BH procedure
    rank = np.arange(1, n + 1)
    corrected_p = (sorted_p_values * n) / rank
    corrected_p = np.minimum.accumulate(corrected_p[::-1])[::-1]
    corrected_p = np.minimum(corrected_p, 1.0)
    
    importance_df['fdr_corrected_p'] = 0.0
    importance_df.loc[sorted_indices, 'fdr_corrected_p'] = corrected_p
    
    return importance_df

def bootstrap_stability(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_resamples: int = 100,
    top_k: int = 3,
    random_state: int = 42,
    scoring_metric: str = 'roc_auc'
) -> Dict[str, Any]:
    """
    Perform Bootstrap Stability analysis to measure ranking stability of top-k predictors.
    
    Args:
        model: Trained model (e.g., XGBoost).
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names corresponding to X columns.
        n_resamples: Number of bootstrap resamples.
        top_k: Number of top features to analyze for stability.
        random_state: Random seed for reproducibility.
        scoring_metric: Metric used for permutation importance (default 'roc_auc').
        
    Returns:
        Dictionary containing stability metrics and detailed results.
    """
    rng = np.random.default_rng(random_state)
    n_samples = X.shape[0]
    
    top_feature_rankings = {f: [] for f in feature_names}
    top_feature_scores = {f: [] for f in feature_names}
    
    for i in range(n_resamples):
        # Bootstrap sample
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        X_boot = X[indices]
        y_boot = y[indices]
        
        # Retrain model on bootstrap sample to capture model variance
        # Assuming the model has a .fit() method. 
        # For XGBoost, we need to clone the model or reinitialize with same params.
        # Since we don't have the original params here, we assume the passed model 
        # is a template or we retrain a new one. 
        # To be safe and accurate to the "stability of predictors" concept, 
        # we retrain a fresh model with the same hyperparameters as the original.
        # However, without access to original params, we might just refit the passed model 
        # if it's a class instance that can be reset, or we assume the caller 
        # passes a factory. 
        # Given the constraints, we will assume the model passed is the best estimator 
        # and we retrain a new instance with the same type. 
        # Since we don't have the type, we'll assume the model passed is the one to retrain 
        # but that's not possible if it's already fitted. 
        # Strategy: We will assume the input model is a "template" or we just refit 
        # a new XGBClassifier with default params if not specified? 
        # No, that changes the model. 
        # Correct approach for this task: The task asks for stability of *predictors*.
        # This usually means: "If we resample data, do the same features remain important?"
        # We should use the *same* model architecture. 
        # Since we can't easily clone without params, we will assume the model passed 
        # is the one we are evaluating, and we are just evaluating feature importance 
        # on resampled data *using the same model*? 
        # No, standard bootstrap stability for feature importance involves retraining 
        # on the bootstrap sample. 
        # Let's assume we can retrain a new model of the same type. 
        # Since we don't have the type, we will use the passed model's class 
        # but we need to know it. 
        # To avoid complex cloning, we will assume the model is an XGBClassifier 
        # and retrain it. If it's not, this might fail, but it's the most likely case.
        
        # Better approach: The prompt implies we have a trained model. 
        # We will assume we are testing the stability of the feature ranking 
        # derived from the model trained on the full data, but evaluated on resampled data?
        # No, that's not bootstrap stability of the ranking. 
        # Bootstrap stability of ranking: Train on Bootstrap -> Get Rank -> Repeat.
        # We need to retrain. 
        # Let's assume the model is an XGBClassifier and we can retrain it.
        # We need to get the parameters. 
        # Since we can't get them from a fitted object easily without get_params,
        # and we don't know if it's fitted, we will try to get params.
        
        try:
            # Try to get params
            params = model.get_params()
            # Remove 'n_estimators' if it was set to a specific value for the full model?
            # No, keep it.
            # Create new instance
            new_model = model.__class__(**params)
            new_model.fit(X_boot, y_boot)
        except Exception as e:
            # Fallback: if we can't clone, we might just use the original model 
            # but that defeats the purpose of bootstrap stability for model variance.
            # However, for the sake of this task, we will assume the model is cloneable.
            # If not, we skip this resample or use the original model (less accurate).
            # Let's raise a clear error if we can't retrain.
            warnings.warn(f"Could not retrain model for bootstrap resample {i}: {e}. Skipping.")
            continue
        
        # Compute permutation importance on the bootstrap sample
        # We need to evaluate on the bootstrap sample itself or a holdout?
        # Usually, importance is computed on the data used for training or a validation set.
        # Here we compute on the bootstrap sample to see if the model 
        # identifies the same features as important.
        try:
            perm_result = permutation_importance(
                new_model, X_boot, y_boot,
                n_repeats=10, # Fewer repeats for speed in bootstrap
                random_state=random_state + i,
                scoring=scoring_metric,
                n_jobs=1
            )
            
            # Extract mean importance
            importances = perm_result.importances_mean
            feature_importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            })
            feature_importance_df = feature_importance_df.sort_values('importance', ascending=False)
            
            # Record top-k ranks
            top_features = feature_importance_df.head(top_k)['feature'].tolist()
            for feat in feature_names:
                if feat in top_features:
                    rank = top_features.index(feat) + 1
                    top_feature_rankings[feat].append(rank)
                else:
                    top_feature_rankings[feat].append(None) # Not in top k
                    
        except Exception as e:
            warnings.warn(f"Permutation importance failed for resample {i}: {e}. Skipping.")
            continue
    
    # Calculate stability metrics
    stability_results = {}
    for feat in feature_names:
        ranks = [r for r in top_feature_rankings[feat] if r is not None]
        if not ranks:
            stability_results[feat] = {
                'mean_rank': None,
                'std_rank': None,
                'frequency_in_top_k': 0.0,
                'stability_score': 0.0
            }
        else:
            mean_rank = np.mean(ranks)
            std_rank = np.std(ranks)
            freq_in_top_k = len(ranks) / n_resamples
            # Stability score: 1 / (1 + std_rank) -> lower std = higher stability
            stability_score = 1.0 / (1.0 + std_rank) if std_rank is not None else 0.0
            
            stability_results[feat] = {
                'mean_rank': float(mean_rank),
                'std_rank': float(std_rank),
                'frequency_in_top_k': float(freq_in_top_k),
                'stability_score': float(stability_score)
            }
    
    # Sort by stability score descending
    sorted_stability = sorted(stability_results.items(), key=lambda x: x[1]['stability_score'], reverse=True)
    
    return {
        'n_resamples': n_resamples,
        'top_k': top_k,
        'stability_metrics': stability_results,
        'top_stable_features': [f for f, _ in sorted_stability[:top_k]]
    }

def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: List[str],
    output_dir: Path
) -> Dict[str, Any]:
    """
    Comprehensive evaluation: ROC-AUC, Permutation Importance, FDR, Bootstrap Stability.
    """
    results = {}
    
    # Predictions
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # ROC-AUC
    roc_auc = compute_roc_auc(y_test, y_proba)
    results['roc_auc'] = roc_auc
    print(f"ROC-AUC: {roc_auc:.4f}")
    
    # Permutation Importance
    perm_imp = run_permutation_importance(model, X_test, y_test, feature_names, n_permutations=1000)
    results['permutation_importance'] = perm_imp.to_dict(orient='records')
    
    # Calculate p-values for permutation importance (simple z-score approach)
    # H0: importance is 0. Z = (mean - 0) / std
    perm_imp['z_score'] = perm_imp['mean_importance'] / (perm_imp['std_importance'] + 1e-9)
    # Two-tailed p-value from normal distribution (approximation)
    from scipy.stats import norm
    perm_imp['p_value'] = 2 * (1 - norm.cdf(np.abs(perm_imp['z_score'])))
    
    # FDR Correction
    perm_imp_corrected = apply_fdr_correction(perm_imp, p_value_col='p_value')
    results['fdr_corrected_importance'] = perm_imp_corrected.to_dict(orient='records')
    
    # Bootstrap Stability
    stability = bootstrap_stability(model, X_test, y_test, feature_names, n_resamples=100, top_k=3)
    results['bootstrap_stability'] = stability
    
    # Save results to JSON
    output_path = output_dir / 'evaluation_results.json'
    # Convert numpy types to python types for JSON serialization
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj
    
    with open(output_path, 'w') as f:
        json.dump(convert(results), f, indent=2)
    
    print(f"Evaluation results saved to {output_path}")
    return results

def main():
    """Main entry point for evaluation script."""
    # Load data (assuming processed data exists from previous steps)
    # This is a placeholder for the actual data loading logic
    # In a real scenario, we would load from data/processed/filtered_features.csv
    # and load the trained model from data/models/
    
    try:
        # Load data
        data_path = config.DATA_PROCESSED / 'filtered_features.csv'
        if not data_path.exists():
            print(f"Error: Data file not found at {data_path}. Please run the ingestion and feature engineering pipeline first.")
            sys.exit(1)
        
        df = pd.read_csv(data_path)
        
        # Assume target column is 'bleaching_label' and features are everything else except 'id', 'lat', 'lon', etc.
        # This is a simplification. The actual column names should be defined in the config or spec.
        target_col = 'bleaching_label'
        if target_col not in df.columns:
            print(f"Error: Target column '{target_col}' not found in data.")
            sys.exit(1)
        
        feature_cols = [col for col in df.columns if col not in [target_col, 'id', 'lat', 'lon', 'reef_id', 'species_id']]
        
        X = df[feature_cols].values
        y = df[target_col].values
        feature_names = feature_cols
        
        # Split data spatially (Western vs Eastern Pacific)
        # This logic should ideally be in train.py, but for evaluation we need a test set
        # We assume the model was trained on Western and we evaluate on Eastern
        # For this script, we will simulate a split or load a pre-split test set
        # If we don't have a pre-split, we do a random split as a fallback (not ideal)
        # But the task says "held-out geographic test set". 
        # Let's assume we have a 'region' column or we split by coordinates.
        if 'region' in df.columns:
            train_mask = df['region'] == 'Western'
            test_mask = df['region'] == 'Eastern'
        else:
            # Fallback to longitude split
            # Western Pacific: ~100E to 180, Eastern: ~180 to 70W (or negative)
            # This is a rough approximation
            if 'lon' in df.columns:
                train_mask = df['lon'] > 100
                test_mask = df['lon'] <= 100
            else:
                # Random split if no spatial info
                warnings.warn("No spatial info found. Using random split for evaluation.")
                train_mask, test_mask = train_test_split(
                    np.arange(len(df)), test_size=0.2, random_state=42
                )
                train_mask = np.isin(np.arange(len(df)), train_mask)
                test_mask = np.isin(np.arange(len(df)), test_mask)
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]
        
        # Train a model for evaluation (if not provided)
        # In a real pipeline, we would load the trained model from disk
        model_path = config.DATA_MODELS / 'best_model.json'
        if model_path.exists():
            model = xgb.XGBClassifier()
            model.load_model(str(model_path))
        else:
            # Train a new model for demonstration
            warnings.warn("No trained model found. Training a new one for evaluation.")
            model = xgb.XGBClassifier(
                max_depth=5,
                learning_rate=0.1,
                n_estimators=100,
                random_state=42
            )
            model.fit(X_train, y_train)
        
        # Run evaluation
        results = evaluate_model(model, X_test, y_test, feature_names, config.DATA_MODELS)
        
        # Print stability summary
        stability = results['bootstrap_stability']
        print("\nBootstrap Stability Analysis (Top 3 Predictors):")
        for feat, metrics in stability['stability_metrics'].items():
            if metrics['frequency_in_top_k'] > 0:
                print(f"  {feat}: Mean Rank: {metrics['mean_rank']:.2f}, "
                      f"Freq in Top 3: {metrics['frequency_in_top_k']:.2f}, "
                      f"Stability Score: {metrics['stability_score']:.4f}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()