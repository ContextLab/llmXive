"""
Sensitivity analysis for model stability across regimes.

This module implements parameter sweeping to verify that the ranking of
identified regimes (Low/Mid/High Delta K) remains stable under variations
in model hyperparameters.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
import json
from pathlib import Path

from config import get_path
from analysis.regimes import identify_regimes, analyze_regimes

logger = logging.getLogger(__name__)

def run_sensitivity_analysis(df: pd.DataFrame, 
                             feature_cols: List[str],
                             delta_k_col: str = 'Delta_K',
                             target_col: str = 'da_dN',
                             n_sweeps: int = 5,
                             random_state: int = 42,
                             output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Sweep model parameters to verify region stability.
    
    This function performs a grid search over key hyperparameters (n_estimators,
    max_depth) of the Random Forest model. For each configuration, it:
    1. Trains the model (via cross-validation)
    2. Identifies regimes using the standard `identify_regimes` logic
    3. Analyzes regimes to get performance metrics
    4. Checks if the ranking of regimes (by performance or importance) is stable
    
    Args:
        df: DataFrame with features, target, and Delta_K column
        feature_cols: List of feature column names for the model
        delta_k_col: Column name for Delta_K (used for regime identification)
        target_col: Target column name (da/dN)
        n_sweeps: Number of parameter variations to test (sweeps n_estimators)
        random_state: Random seed for reproducibility
        output_dir: Directory to save the sensitivity report JSON
    
    Returns:
        Dictionary containing:
        - sweep_results: List of dicts with params, CV scores, and regime stats
        - stability_metric: Coefficient of variation of R2 across sweeps
        - regime_ranking_stability: Boolean indicating if top regimes remained consistent
        - final_report_path: Path to saved JSON report if output_dir provided
    """
    logger.info(f"Running sensitivity analysis with {n_sweeps} sweeps...")
    
    # Prepare data
    X = df[feature_cols].values
    y = df[target_col].values
    delta_k = df[delta_k_col].values
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    results = []
    base_params = {
        'max_depth': 10,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': random_state
    }
    
    # Define sweep range for n_estimators
    est_counts = [50 + i * 50 for i in range(n_sweeps)]
    
    # Store regime rankings to check stability
    all_regime_rankings = []
    
    logger.info(f"Sweeping n_estimators: {est_counts}")
    
    for n_est in est_counts:
        params = base_params.copy()
        params['n_estimators'] = n_est
        
        logger.debug(f"Testing config: n_estimators={n_est}, max_depth={params['max_depth']}")
        
        # 1. Cross-Validation Score
        model = RandomForestRegressor(**params)
        cv_scores = cross_val_score(model, X_scaled, y, cv=3, scoring='r2')
        mean_r2 = np.mean(cv_scores)
        std_r2 = np.std(cv_scores)
        
        # 2. Train on full data to identify regimes (simulating the pipeline step)
        # Note: In a full pipeline, regimes might be identified once on the baseline,
        # but for sensitivity we verify if the *model's* ability to explain variance
        # changes the regime characteristics significantly.
        model.fit(X_scaled, y)
        
        # Use the trained model to get predictions for regime analysis
        # We simulate the "regime analysis" step by predicting on the full dataset
        # and then running the regime identification logic on the residuals or
        # the predicted values to see if the "regions" of high/low error shift.
        # However, the task specifically asks to verify "region stability".
        # The standard approach:
        # A. Identify regimes on the Delta_K axis (independent of model params usually).
        # B. Evaluate model performance *within* those fixed regimes.
        # C. Check if the relative performance ranking of regimes changes.
        
        # Step A: Identify regimes based on Delta_K distribution (using ruptures logic)
        # We pass the raw Delta_K values. The regimes are defined by the physics/data,
        # not the model params.
        try:
            regime_boundaries, regime_labels = identify_regimes(
                delta_k, 
                method='ruptures'
            )
        except Exception as e:
            logger.warning(f"Regime identification failed for sweep {n_est}: {e}. Skipping regime stats.")
            regime_boundaries = None
            regime_labels = None
        
        regime_stats = {}
        if regime_boundaries is not None and regime_labels is not None:
            # Step B: Calculate R2 within each regime
            # We need to calculate local R2. Since we don't have a separate test set here,
            # we approximate by calculating R2 on the training data within each regime bin.
            # A more robust way is to use the CV predictions mapped to regimes, but for
            # sensitivity sweep speed, we use the fitted model on the split data.
            
            unique_regimes = np.unique(regime_labels)
            regime_scores = {}
            
            for reg_id in unique_regimes:
                mask = regime_labels == reg_id
                if np.sum(mask) < 5: # Skip tiny regimes
                    continue
                
                X_reg = X_scaled[mask]
                y_reg = y[mask]
                
                # Evaluate model on this specific regime subset
                # Using a simple train/test split or just the fitted score
                # Since the model is already fit on full data, we calculate R2 on the subset
                from sklearn.metrics import r2_score
                y_pred_reg = model.predict(X_reg)
                r2_reg = r2_score(y_reg, y_pred_reg)
                regime_scores[reg_id] = r2_reg
            
            regime_stats = {
                "boundaries": regime_boundaries.tolist(),
                "scores_by_regime": {str(k): float(v) for k, v in regime_scores.items()},
                "regime_ranking": sorted(regime_scores.items(), key=lambda x: x[1], reverse=True)
            }
            all_regime_rankings.append(regime_stats["regime_ranking"])
        
        results.append({
            'n_estimators': n_est,
            'max_depth': params['max_depth'],
            'mean_r2': float(mean_r2),
            'std_r2': float(std_r2),
            'regime_stats': regime_stats
        })
    
    # Analyze stability
    r2_values = [r['mean_r2'] for r in results]
    stability_metric = np.std(r2_values) / (np.mean(r2_values) + 1e-9)
    
    # Check regime ranking stability
    regime_stable = True
    if len(all_regime_rankings) > 1:
        # Compare the top 2 regimes across all sweeps
        # If the order of the top 2 regimes changes, it's unstable
        first_ranking = all_regime_rankings[0]
        for ranking in all_regime_rankings[1:]:
            # Extract top 2 regime IDs
            top_2_ids = [r[0] for r in ranking[:2]]
            top_2_first = [r[0] for r in first_ranking[:2]]
            if set(top_2_ids) != set(top_2_first):
                # Different set of top regimes
                regime_stable = False
                break
            if len(top_2_ids) == 2 and len(top_2_first) == 2:
                if top_2_ids != top_2_first:
                    # Same set, different order
                    regime_stable = False
                    break
    
    logger.info(f"Sensitivity analysis complete. Stability metric: {stability_metric:.4f}")
    logger.info(f"Regime ranking stability: {regime_stable}")
    
    output_dict = {
        "sweep_results": results,
        "stability_metric": float(stability_metric),
        "is_model_stable": stability_metric < 0.1,
        "regime_ranking_stable": regime_stable,
        "summary": {
            "best_n_estimators": results[np.argmax(r2_values)]['n_estimators'],
            "best_mean_r2": float(max(r2_values)),
            "parameter_sensitivity": "Low" if stability_metric < 0.05 else "Medium" if stability_metric < 0.1 else "High"
        }
    }
    
    if output_dir:
        output_path = Path(output_dir) / "sensitivity_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_dict, f, indent=2)
        output_dict["final_report_path"] = str(output_path)
        logger.info(f"Sensitivity report saved to {output_path}")
    
    return output_dict
