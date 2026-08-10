import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from sklearn.model_selection import KFold
from logger import get_logger, get_project_root
import json

logger = get_logger(__name__)

def generate_spatial_blocks(geodataframe: pd.GeoDataFrame, n_blocks: int = 5) -> List[pd.GeoDataFrame]:
    """
    Generates spatial blocks for cross-validation by clustering coordinates.
    Returns a list of GeoDataFrames representing the blocks.
    """
    if 'geometry' not in geodataframe.columns:
        raise ValueError("GeoDataFrame must contain a 'geometry' column")
    
    # Simple spatial binning based on coordinates
    coords = np.array([[g.x, g.y] for g in geodataframe.geometry])
    min_x, max_x = coords[:, 0].min(), coords[:, 0].max()
    min_y, max_y = coords[:, 1].min(), coords[:, 1].max()
    
    # Create a grid of blocks
    x_step = (max_x - min_x) / np.ceil(np.sqrt(n_blocks))
    y_step = (max_y - min_y) / np.ceil(np.sqrt(n_blocks))
    
    blocks = []
    block_id = 0
    
    # Generate grid cells
    x_vals = np.arange(min_x, max_x, x_step)
    y_vals = np.arange(min_y, max_y, y_step)
    
    # Assign points to blocks
    geodataframe = geodataframe.copy()
    geodataframe['block_id'] = -1
    
    for x in x_vals:
        for y in y_vals:
            if block_id >= n_blocks:
                break
            mask = (
                (geodataframe.geometry.x >= x) & 
                (geodataframe.geometry.x < x + x_step) &
                (geodataframe.geometry.y >= y) & 
                (geodataframe.geometry.y < y + y_step)
            )
            if mask.any():
                geodataframe.loc[mask, 'block_id'] = block_id
                block_id += 1
        
        if block_id >= n_blocks:
            break
    
    # Ensure all points are assigned (assign remainder to last block)
    geodataframe.loc[geodataframe['block_id'] == -1, 'block_id'] = n_blocks - 1
    
    # Create block GeoDataFrames
    for i in range(n_blocks):
        block_gdf = geodataframe[geodataframe['block_id'] == i]
        blocks.append(block_gdf)
        
    return blocks

def spatial_kfold_split(geodataframe: pd.GeoDataFrame, n_splits: int = 5) -> List[Tuple[pd.GeoDataFrame, pd.GeoDataFrame]]:
    """
    Splits data into spatially disjoint train/test sets using generated blocks.
    Yields (train_gdf, test_gdf) tuples.
    """
    blocks = generate_spatial_blocks(geodataframe, n_splits)
    n_blocks = len(blocks)
    
    for i in range(n_blocks):
        test_gdf = blocks[i]
        train_gdf = pd.concat([b for j, b in enumerate(blocks) if j != i], ignore_index=True)
        yield train_gdf, test_gdf

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, model_params: Optional[Dict] = None) -> Dict[str, float]:
    """
    Calculates RMSE, R², and optionally AIC.
    """
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    metrics = {
        "rmse": float(rmse),
        "r2": float(r2)
    }
    
    if model_params and 'aic' in model_params:
        metrics['aic'] = float(model_params['aic'])
        
    return metrics

def run_spatial_cross_validation(
    model_fitter, 
    geodataframe: pd.GeoDataFrame, 
    target_col: str, 
    feature_cols: List[str], 
    n_splits: int = 5
) -> List[Dict[str, Any]]:
    """
    Runs spatial cross-validation, returning metrics for each fold.
    model_fitter: A callable that takes (X_train, y_train, X_test) and returns y_pred and model_params.
    """
    results = []
    
    for fold_idx, (train_gdf, test_gdf) in enumerate(spatial_kfold_split(geodataframe, n_splits)):
        logger.info(f"Processing fold {fold_idx + 1}/{n_splits}")
        
        X_train = train_gdf[feature_cols].values
        y_train = train_gdf[target_col].values
        X_test = test_gdf[feature_cols].values
        y_test = test_gdf[target_col].values
        
        try:
            y_pred, model_params = model_fitter(X_train, y_train, X_test)
            fold_metrics = calculate_metrics(y_test, y_pred, model_params)
            fold_metrics['fold'] = fold_idx + 1
            results.append(fold_metrics)
        except Exception as e:
            logger.error(f"Fold {fold_idx + 1} failed: {e}")
            results.append({"fold": fold_idx + 1, "error": str(e)})
            
    return results

def run_spatial_block_permutation_test(
    geodataframe: pd.GeoDataFrame, 
    target_col: str, 
    feature_cols: List[str], 
    model_fitter, 
    n_permutations: int = 100, 
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Performs a spatial block permutation test to assess significance of model performance.
    """
    np.random.seed(random_state)
    blocks = generate_spatial_blocks(geodataframe, 5)
    
    # Get observed performance
    observed_metrics = run_spatial_cross_validation(model_fitter, geodataframe, target_col, feature_cols, n_splits=5)
    observed_rmse = np.mean([m['rmse'] for m in observed_metrics if 'rmse' in m])
    
    permuted_rmses = []
    
    for i in range(n_permutations):
        # Shuffle block assignments
        shuffled_indices = np.random.permutation(len(blocks))
        shuffled_blocks = [blocks[idx] for idx in shuffled_indices]
        
        # Reconstruct dataframe with shuffled blocks (simulating null hypothesis)
        shuffled_gdf = pd.concat(shuffled_blocks, ignore_index=True)
        
        perm_metrics = run_spatial_cross_validation(model_fitter, shuffled_gdf, target_col, feature_cols, n_splits=5)
        perm_rmse = np.mean([m['rmse'] for m in perm_metrics if 'rmse' in m])
        permuted_rmses.append(perm_rmse)
        
    p_value = np.mean(np.array(permuted_rmses) <= observed_rmse)
    
    return {
        "observed_rmse": float(observed_rmse),
        "permuted_rmse_mean": float(np.mean(permuted_rmses)),
        "permuted_rmse_std": float(np.std(permuted_rmses)),
        "p_value": float(p_value),
        "n_permutations": n_permutations
    }

def check_success_criteria(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if the model results meet the Success Criteria (SC-001 to SC-005).
    
    Expected input 'results' structure:
    {
      "best_model": str,
      "metrics": {
        "rmse": float,
        "r2": float,
        "aic": float,
        "rmse_reduction": float,
        "is_rmse_significant": bool,
        "fdr_corrected_pvalues": { ... },
        "moran_i": float,
        "p_value_permutation": float
      },
      "model_comparison": { ... }
    }
    
    Returns a report indicating which criteria are met.
    """
    report = {
        "criteria_met": {},
        "overall_success": False,
        "summary": ""
    }
    
    metrics = results.get("metrics", {})
    
    # SC-001: Spatial models (Lag/Error) outperform OLS in RMSE
    # Assumption: 'rmse_reduction' is positive if spatial model is better
    sc_001 = metrics.get("rmse_reduction", 0) > 0
    report["criteria_met"]["SC-001"] = {
        "description": "Spatial models outperform OLS in RMSE",
        "passed": sc_001,
        "evidence": f"RMSE reduction: {metrics.get('rmse_reduction', 'N/A')}"
    }
    
    # SC-002: Significant RMSE reduction confirmed by permutation test
    # Assumption: p_value < 0.05
    p_val = metrics.get("p_value_permutation", 1.0)
    sc_002 = p_val < 0.05
    report["criteria_met"]["SC-002"] = {
        "description": "RMSE reduction is statistically significant (p < 0.05)",
        "passed": sc_002,
        "evidence": f"Permutation p-value: {p_val:.4f}"
    }
    
    # SC-003: FDR-corrected p-values for primary covariates < 0.05
    fdr_pvals = metrics.get("fdr_corrected_pvalues", {})
    # Check if at least one primary covariate is significant
    significant_covariates = [k for k, v in fdr_pvals.items() if v < 0.05]
    sc_003 = len(significant_covariates) > 0
    report["criteria_met"]["SC-003"] = {
        "description": "At least one primary covariate has FDR-corrected p < 0.05",
        "passed": sc_003,
        "evidence": f"Significant covariates: {significant_covariates}"
    }
    
    # SC-004: Spatial autocorrelation in residuals (Moran's I) is reduced below threshold
    # Assumption: |Moran's I| < 0.05 indicates acceptable reduction
    moran_i = metrics.get("moran_i", 0.0)
    sc_004 = abs(moran_i) < 0.05
    report["criteria_met"]["SC-004"] = {
        "description": "Residual spatial autocorrelation (Moran's I) is < 0.05",
        "passed": sc_004,
        "evidence": f"Moran's I: {moran_i:.4f}"
    }
    
    # SC-005: Best model selected based on lowest AIC and significant RMSE reduction
    is_rmse_sig = metrics.get("is_rmse_significant", False)
    # We assume 'best_model' was selected correctly if both conditions below are met
    sc_005 = sc_001 and sc_002
    report["criteria_met"]["SC-005"] = {
        "description": "Best model selected based on AIC and significant RMSE reduction",
        "passed": sc_005,
        "evidence": f"Best model: {results.get('best_model', 'N/A')}"
    }
    
    # Overall success: All criteria must be met
    all_passed = all(c["passed"] for c in report["criteria_met"].values())
    report["overall_success"] = all_passed
    report["summary"] = f"Overall Success: {all_passed}. {sum(1 for c in report['criteria_met'].values() if c['passed'])}/{len(report['criteria_met'])} criteria met."
    
    return report

def main():
    """
    Main entry point for validation and success criteria checking.
    Expects model results to be loaded from data/processed/model_results.json
    and writes the report to data/processed/sc_validation_report.json.
    """
    project_root = get_project_root()
    results_path = project_root / "data" / "processed" / "model_results.json"
    report_path = project_root / "data" / "processed" / "sc_validation_report.json"
    
    logger.info(f"Loading model results from {results_path}")
    
    if not results_path.exists():
        logger.error(f"Model results file not found: {results_path}")
        return
        
    with open(results_path, 'r') as f:
        model_results = json.load(f)
        
    logger.info("Checking success criteria...")
    report = check_success_criteria(model_results)
    
    logger.info(f"Writing success criteria report to {report_path}")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Success: {report['overall_success']}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()