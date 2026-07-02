import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from code.config import SEED, DATA_PATH
from code.logging_config import setup_logging
from code.train_models import load_processed_data, prepare_features_and_target, train_model
from code.vif_iterative_retrain import iterative_vif_retrain

logger = logging.getLogger(__name__)

def compute_feature_importance(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    n_repeats: int = 10,
    scoring: str = 'r2'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute feature importance rankings using permutation importance.
    
    Args:
        model: Trained sklearn model (RF or GB)
        X: Feature DataFrame (VIF-filtered)
        y: Target Series
        n_repeats: Number of permutation repeats
        scoring: Scoring metric for permutation (default 'r2')
        
    Returns:
      - DataFrame with feature names, mean importance, std importance, and p-value
      - Dict with summary statistics
    """
    logger.info(f"Computing permutation importance with {n_repeats} repeats...")
    
    # Compute permutation importance
    perm_result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=SEED, 
        scoring=scoring,
        n_jobs=-1
    )
    
    # Create importance DataFrame
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance_mean': perm_result.importances_mean,
        'importance_std': perm_result.importances_std
    })
    
    # Calculate p-values (one-sided test: importance > 0)
    # Using z-score approximation: z = mean / std
    importance_df['z_score'] = importance_df['importance_mean'] / (importance_df['importance_std'] + 1e-8)
    # Convert to p-value (probability of observing this or more extreme under null)
    from scipy.stats import norm
    importance_df['p_value'] = 1 - norm.cdf(importance_df['z_score'])
    
    # Sort by importance
    importance_df = importance_df.sort_values('importance_mean', ascending=False).reset_index(drop=True)
    
    # Summary stats
    summary = {
        'total_features': len(importance_df),
        'significant_features_at_0.05': int((importance_df['p_value'] < 0.05).sum()),
        'top_feature': importance_df.iloc[0]['feature'] if len(importance_df) > 0 else None,
        'mean_importance': float(importance_df['importance_mean'].mean()),
        'std_importance': float(importance_df['importance_std'].mean())
    }
    
    logger.info(f"Feature importance computed. Top feature: {summary['top_feature']}")
    return importance_df, summary

def extract_tree_importance(
    model: Any,
    X: pd.DataFrame
) -> pd.DataFrame:
    """
    Extract built-in tree-based feature importance (for RF/GB models).
    
    Args:
        model: Trained tree-based model
        X: Feature DataFrame
        
    Returns:
      DataFrame with feature names and tree-based importance scores
    """
    if hasattr(model, 'feature_importances_'):
        importance_df = pd.DataFrame({
            'feature': X.columns,
            'tree_importance': model.feature_importances_
        })
        importance_df = importance_df.sort_values('tree_importance', ascending=False).reset_index(drop=True)
        return importance_df
    else:
        logger.warning("Model does not have feature_importances_ attribute")
        return pd.DataFrame()

def run_feature_importance_analysis(
    model_type: str = 'random_forest',
    output_path: str = 'data/processed/feature_importance.csv',
    summary_path: str = 'data/processed/feature_importance_summary.json'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main function to run feature importance analysis on the VIF-filtered model.
    
    Args:
        model_type: 'random_forest' or 'gradient_boosting'
        output_path: Path to save importance CSV
        summary_path: Path to save summary JSON
        
    Returns:
      - Importance DataFrame
      - Summary dictionary
    """
    logger.info("Starting feature importance analysis...")
    
    # Load processed data (this should be the VIF-filtered data from T039)
    # We need to re-run the VIF filtering to get the final features
    try:
        # Load raw processed data
        X, y, feature_names, target_name = load_processed_data()
        
        # Run iterative VIF retrain to get the final model and filtered features
        logger.info("Running iterative VIF retraining to get final model...")
        final_model, final_X, final_y, excluded_features, vif_history = iterative_vif_retrain(
            X, y, 
            model_type=model_type,
            seed=SEED
        )
        
        logger.info(f"VIF filtering complete. Excluded {len(excluded_features)} features.")
        logger.info(f"Final model trained on {len(final_X.columns)} features.")
        
        # Compute permutation importance
        importance_df, summary = compute_feature_importance(final_model, final_X, final_y)
        
        # Also extract tree-based importance for comparison
        tree_importance_df = extract_tree_importance(final_model, final_X)
        
        # Merge both importance measures if available
        if not tree_importance_df.empty:
            importance_df = importance_df.merge(
                tree_importance_df[['feature', 'tree_importance']], 
                on='feature', 
                how='left'
            )
            # Fill NaN tree_importance with 0 (for features not in tree model)
            importance_df['tree_importance'] = importance_df['tree_importance'].fillna(0)
        
        # Save results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        importance_df.to_csv(output_path, index=False)
        logger.info(f"Feature importance saved to {output_path}")
        
        # Save summary
        summary['excluded_features'] = excluded_features
        summary['final_feature_count'] = len(final_X.columns)
        summary['model_type'] = model_type
        
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Feature importance summary saved to {summary_path}")
        
        return importance_df, summary
        
    except Exception as e:
        logger.error(f"Error in feature importance analysis: {e}")
        raise

def main():
    """Entry point for feature importance analysis."""
    setup_logging()
    
    try:
        # Run for Random Forest (default)
        logger.info("=== Running Feature Importance Analysis (Random Forest) ===")
        importance_df_rf, summary_rf = run_feature_importance_analysis(
            model_type='random_forest',
            output_path='data/processed/feature_importance_rf.csv',
            summary_path='data/processed/feature_importance_rf_summary.json'
        )
        
        logger.info("Top 5 features (RF):")
        print(importance_df_rf.head())
        
        # Run for Gradient Boosting
        logger.info("=== Running Feature Importance Analysis (Gradient Boosting) ===")
        importance_df_gb, summary_gb = run_feature_importance_analysis(
            model_type='gradient_boosting',
            output_path='data/processed/feature_importance_gb.csv',
            summary_path='data/processed/feature_importance_gb_summary.json'
        )
        
        logger.info("Top 5 features (GB):")
        print(importance_df_gb.head())
        
        logger.info("Feature importance analysis complete.")
        
    except Exception as e:
        logger.exception("Feature importance analysis failed")
        raise

if __name__ == '__main__':
    main()
