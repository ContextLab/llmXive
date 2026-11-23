"""
Regime identification using change-point detection and local analysis.
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from analysis.feature_importance import aggregate_importance, get_top_features

logger = logging.getLogger(__name__)

def identify_regimes(df: pd.DataFrame, delta_k_col: str = 'delta_k', 
                     target_col: str = 'da_dN') -> Dict[str, Any]:
    """
    Identify Low/Mid/High Delta K regions using ruptures or fallback.
    
    Args:
        df: DataFrame containing crack propagation data
        delta_k_col: Column name for Delta K values
        target_col: Column name for da/dN values
        
    Returns:
        Dictionary containing regime boundaries and statistics
    """
    logger.info("Starting regime identification...")
    
    # Sort by Delta K
    df_sorted = df.sort_values(by=delta_k_col).reset_index(drop=True)
    X = df_sorted[delta_k_col].values
    y = df_sorted[target_col].values
    
    # Try ruptures first
    try:
        import ruptures as rpt
        
        # Use Pelt algorithm with L2 cost
        model = "l2"
        algo = rpt.Pelt(model=model).fit(X.reshape(-1, 1))
        result = algo.predict(pen=10)
        
        logger.info(f"Regimes identified using ruptures: {len(result)-1} regions")
        return {
            "method": "ruptures",
            "boundaries": result,
            "regime_count": len(result) - 1
        }
        
    except ImportError:
        logger.warning("ruptures not available, using fallback method")
    except Exception as e:
        logger.warning(f"ruptures failed: {e}, using fallback method")
    
    # Fallback: Gaussian Process with varying coefficients
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
        
        kernel = C(1.0) * RBF(1.0)
        gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        gpr.fit(X.reshape(-1, 1), y)
        
        # Simple heuristic: divide into 3 regions based on quantiles
        boundaries = [
            int(len(X) * 0.33),
            int(len(X) * 0.66)
        ]
        
        logger.info("Regimes identified using fallback quantile method")
        return {
            "method": "gp_fallback",
            "boundaries": boundaries,
            "regime_count": 3
        }
        
    except Exception as e:
        logger.error(f"Fallback method also failed: {e}")
        raise

def analyze_regimes(
    df: pd.DataFrame,
    model,
    feature_columns: List[str],
    delta_k_col: str = 'delta_k',
    target_col: str = 'da_dN',
    regime_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate local R^2 and feature importance within identified regimes.
    
    Args:
        df: Full DataFrame with crack propagation data
        model: Trained sklearn-style model with .predict() and .feature_importances_
        feature_columns: List of feature column names used for training
        delta_k_col: Column name for Delta K values
        target_col: Column name for da/dN values
        regime_results: Pre-computed regime boundaries from identify_regimes()
        
    Returns:
        Dictionary containing per-regime R^2 scores and top features
    """
    logger.info("Starting local regime analysis...")
    
    if regime_results is None:
        regime_results = identify_regimes(df, delta_k_col, target_col)
        
    boundaries = regime_results['boundaries']
    method = regime_results['method']
    
    # Sort data by Delta K for consistent slicing
    df_sorted = df.sort_values(by=delta_k_col).reset_index(drop=True)
    X_sorted = df_sorted[feature_columns].values
    y_sorted = df_sorted[target_col].values
    delta_k_sorted = df_sorted[delta_k_col].values
    
    # Create regime slices
    regimes = []
    start_idx = 0
    for i, boundary in enumerate(boundaries[:-1]):
        end_idx = boundary
        if start_idx >= end_idx:
            start_idx = end_idx
            continue
            
        regime_name = f"Regime_{i+1}"
        if i == 0:
            regime_name = "Low_DeltaK"
        elif i == len(boundaries) - 2:
            regime_name = "High_DeltaK"
        else:
            regime_name = f"Mid_DeltaK_{i}"
            
        X_regime = X_sorted[start_idx:end_idx]
        y_regime = y_sorted[start_idx:end_idx]
        delta_k_regime = delta_k_sorted[start_idx:end_idx]
        
        if len(X_regime) < 5:
            logger.warning(f"Regime {regime_name} has too few samples ({len(X_regime)}), skipping")
            start_idx = end_idx
            continue
            
        # Predict and calculate local R^2
        try:
            y_pred = model.predict(X_regime)
            local_r2 = r2_score(y_regime, y_pred)
        except Exception as e:
            logger.error(f"Failed to predict for {regime_name}: {e}")
            local_r2 = np.nan
            
        # Extract local feature importance if model supports it
        local_importance = None
        if hasattr(model, 'feature_importances_'):
            importance_dict = dict(zip(feature_columns, model.feature_importances_))
            # Exclude Delta K from top features list as per task requirements
            top_features = get_top_features(importance_dict, exclude=[delta_k_col], top_n=3)
            local_importance = {
                "raw": importance_dict,
                "top_features": top_features
            }
        elif hasattr(model, 'coef_'):
            # Linear model
            importance_dict = dict(zip(feature_columns, np.abs(model.coef_)))
            top_features = get_top_features(importance_dict, exclude=[delta_k_col], top_n=3)
            local_importance = {
                "raw": importance_dict,
                "top_features": top_features
            }
        
        regimes.append({
            "name": regime_name,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "n_samples": len(X_regime),
            "delta_k_range": (float(delta_k_regime.min()), float(delta_k_regime.max())),
            "r2": float(local_r2),
            "feature_importance": local_importance
        })
        
        start_idx = end_idx
        
    # Handle last regime if boundaries didn't cover all data
    if start_idx < len(X_sorted):
        regime_name = f"Regime_{len(regimes)+1}_Tail"
        X_regime = X_sorted[start_idx:]
        y_regime = y_sorted[start_idx:]
        delta_k_regime = delta_k_sorted[start_idx:]
        
        if len(X_regime) >= 5:
            try:
                y_pred = model.predict(X_regime)
                local_r2 = r2_score(y_regime, y_pred)
            except Exception as e:
                logger.error(f"Failed to predict for tail regime: {e}")
                local_r2 = np.nan
                
            local_importance = None
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(feature_columns, model.feature_importances_))
                top_features = get_top_features(importance_dict, exclude=[delta_k_col], top_n=3)
                local_importance = {
                    "raw": importance_dict,
                    "top_features": top_features
                }
                
            regimes.append({
                "name": regime_name,
                "start_idx": start_idx,
                "end_idx": len(X_sorted),
                "n_samples": len(X_regime),
                "delta_k_range": (float(delta_k_regime.min()), float(delta_k_regime.max())),
                "r2": float(local_r2),
                "feature_importance": local_importance
            })
    
    logger.info(f"Analyzed {len(regimes)} regimes")
    
    return {
        "method": regime_results['method'],
        "regimes": regimes,
        "total_regimes": len(regimes)
    }
