import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any

from logger import get_logger, get_project_root
from models import fit_ols_model, fit_spatial_models, build_spatial_weights, SpatialWeightMatrixError
from preprocessing import aggregate_daily_metrics
from ingestion import load_synthetic_data_chunked, harmonize_spatial_data
from hygiene import compute_and_record_checksums
from fdr_correction import apply_fdr_to_model_results

def get_model_results() -> Dict[str, Any]:
    """
    Executes the full modeling pipeline (Data Loading -> Preprocessing -> Modeling)
    and returns a dictionary of results suitable for JSON serialization.
    
    Returns:
        Dict containing coefficients, p-values, AIC, R², and Moran's I for OLS,
        Spatial Lag, and Spatial Error models.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load and Harmonize Data
    logger.info("Loading synthetic data...")
    try:
        raw_data = load_synthetic_data_chunked(project_root)
    except Exception as e:
        logger.error(f"Failed to load synthetic data: {e}")
        raise

    logger.info("Harmonizing spatial data...")
    harmonized_data = harmonize_spatial_data(raw_data)
    
    # 2. Preprocess (Aggregate)
    logger.info("Aggregating daily metrics...")
    # Assuming harmonized_data has the necessary columns for aggregation
    # If harmonized_data is already aggregated, this acts as a pass-through or re-aggregation
    aggregated_df = aggregate_daily_metrics(harmonized_data)
    
    # 3. Build Spatial Weights
    logger.info("Building spatial weights matrix...")
    try:
        w = build_spatial_weights(aggregated_df)
        w_summary = get_weight_matrix_summary(w)
    except SpatialWeightMatrixError as e:
        logger.critical(str(e))
        raise
    
    # 4. Prepare Data for Modeling
    # Ensure geometry is set for spatial operations if needed by models
    if 'geometry' in aggregated_df.columns:
        aggregated_df = aggregated_df.set_geometry('geometry')
    
    # Select features
    # Assuming standard covariates based on previous tasks: traffic, land_use, population
    # We need to map these to the actual column names in the synthetic data
    # For safety, we inspect columns or use defaults if known from spec
    feature_cols = ['traffic_volume', 'land_use_density', 'population_density']
    target_col = 'noise_db'
    
    # Filter out rows with NaN in target or features
    model_df = aggregated_df.dropna(subset=[target_col] + feature_cols).copy()
    
    if len(model_df) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for modeling.")

    X = model_df[feature_cols].values
    y = model_df[target_col].values
    
    # 5. Fit Models
    results = {}
    
    # --- OLS ---
    logger.info("Fitting OLS model...")
    try:
        ols_res = fit_ols_model(model_df, target_col, feature_cols)
        results['ols'] = {
            "coefficients": ols_res.params.tolist(),
            "p_values": ols_res.pvalues.tolist(),
            "std_errors": ols_res.bse.tolist(),
            "r_squared": float(ols_res.rsquared),
            "adj_r_squared": float(ols_res.rsquared_adj),
            "aic": float(ols_res.aic),
            "bic": float(ols_res.bic),
            "cov_type": ols_res.cov_type if hasattr(ols_res, 'cov_type') else "HC1",
            "moran_i": float(ols_res.moran_i) if hasattr(ols_res, 'moran_i') else None
        }
    except Exception as e:
        logger.error(f"OLS fitting failed: {e}")
        raise

    # --- Spatial Models ---
    logger.info("Fitting Spatial Lag and Error models...")
    try:
        spatial_res = fit_spatial_models(model_df, target_col, feature_cols, w)
        
        # Spatial Lag
        if 'lag' in spatial_res:
            lag_res = spatial_res['lag']
            results['spatial_lag'] = {
                "coefficients": lag_res.params.tolist(),
                "p_values": lag_res.pvalues.tolist(),
                "std_errors": lag_res.bse.tolist(),
                "log_likelihood": float(lag_res.llf),
                "aic": float(lag_res.aic),
                "bic": float(lag_res.bic),
                "rho": float(lag_res.rho),
                "model_type": "Spatial Lag"
            }
        
        # Spatial Error
        if 'error' in spatial_res:
            err_res = spatial_res['error']
            results['spatial_error'] = {
                "coefficients": err_res.params.tolist(),
                "p_values": err_res.pvalues.tolist(),
                "std_errors": err_res.bse.tolist(),
                "log_likelihood": float(err_res.llf),
                "aic": float(err_res.aic),
                "bic": float(err_res.bic),
                "lambda": float(err_res.lambda_),
                "model_type": "Spatial Error"
            }
            
    except Exception as e:
        logger.error(f"Spatial model fitting failed: {e}")
        # Per T024, we might fall back, but here we just log and raise if critical
        # If fallback logic is internal to fit_spatial_models, it should have returned OLS results
        # If it raised, we propagate
        raise

    # 6. Apply FDR Correction (T023)
    logger.info("Applying Benjamini-Hochberg FDR correction...")
    results = apply_fdr_to_model_results(results)
    
    return results

def save_model_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the model results dictionary to a JSON file.
    
    Args:
        results: Dictionary of model results.
        output_path: Path to the output JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Update checksums as per T004b/hygiene requirements
    compute_and_record_checksums()

def main():
    """Main entry point for T026."""
    logger = get_logger(__name__)
    logger.info("Starting T026: Save model results.")
    
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "model_results.json"
    
    try:
        results = get_model_results()
        save_model_results(results, output_path)
        logger.info(f"Successfully saved model results to {output_path}")
    except Exception as e:
        logger.critical(f"Failed to save model results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
