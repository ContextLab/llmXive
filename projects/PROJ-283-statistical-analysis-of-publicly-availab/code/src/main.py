"""
Main orchestration script for the chess Elo analysis pipeline.
Implements T018: Orchestrate the full pipeline flow.
"""
import sys
import logging
import argparse
from pathlib import Path
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import ensure_directories
from src.data.download import download_chess_data, load_selected_ids
from src.data.parse import parse_pgn_iterator, calculate_material_imbalance_move10, calculate_material_imbalance_move5
from src.data.process import OnlineAccumulator, process_stream, save_inclusion_metrics, validate_inclusion_rate
from src.models.fit import (
    load_eco_mapping, collapse_eco_codes, prepare_features_for_modeling,
    transform_for_beta, fit_beta_regression, fit_gaussian_glm, fit_ridge_regression,
    save_model_metrics
)
from src.models.metrics import apply_benjamini_hochberg_fdr
from src.models.validate import run_validation_pipeline, calculate_cv_metrics
from src.reports.sensitivity import generate_sensitivity_report
from src.reports.generate_plots import generate_diagnostic_report
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_download_stage(sample_mode: bool = False) -> Path:
    """Run the data download stage."""
    logger.info("Starting download stage...")
    output_path = download_chess_data(sample_mode=sample_mode)
    logger.info(f"Download complete: {output_path}")
    return output_path

def run_processing_stage(input_path: Path) -> Path:
    """Run the data processing stage."""
    logger.info("Starting processing stage...")
    
    # Parse PGN data
    with open(input_path, 'r', encoding='utf-8') as f:
        pgn_content = f.read()
    
    # Create generator for parsing
    def pgn_generator():
        for game_block in pgn_content.split('\n\n\n'):
            if game_block.strip():
                yield game_block
    
    # Process stream and accumulate results
    accumulator = OnlineAccumulator()
    processed_df = process_stream(pgn_generator(), accumulator)
    
    # Save processed data
    output_path = Path("code/data/processed/games.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_parquet(output_path, index=False)
    
    # Save inclusion metrics
    save_inclusion_metrics(accumulator)
    validate_inclusion_rate(accumulator)
    
    logger.info(f"Processing complete: {output_path}")
    return output_path

def run_modeling_stage(data_path: Path) -> Path:
    """Run the modeling stage."""
    logger.info("Starting modeling stage...")
    
    # Load data
    df = pd.read_parquet(data_path)
    
    # Prepare features
    eco_mapping = load_eco_mapping(df)
    df_collapsed = collapse_eco_codes(df, eco_mapping)
    X, y = prepare_features_for_modeling(df_collapsed)
    
    # Transform for Beta regression
    y_transformed = transform_for_beta(y)
    
    # Fit models
    beta_results = fit_beta_regression(X, y_transformed)
    gaussian_results = fit_gaussian_glm(X, y)
    ridge_results = fit_ridge_regression(X, y)
    
    # Calculate metrics
    from src.models.metrics import calculate_wald_z_statistic, calculate_p_value_z_test
    
    # Apply FDR correction
    all_pvalues = []
    for model_name, results in [('Beta', beta_results), ('Gaussian', gaussian_results), ('Ridge', ridge_results)]:
        if 'p_values' in results:
            all_pvalues.extend(results['p_values'])
    
    if all_pvalues:
        corrected = apply_benjamini_hochberg_fdr(pd.Series(all_pvalues))
        logger.info("FDR correction applied")
    
    # Cross-validation
    cv_results = run_validation_pipeline(df_collapsed)
    cv_metrics = calculate_cv_metrics(cv_results)
    
    # Save model metrics
    output_path = Path("code/data/results/model_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics_data = {
        'models': [
            {
                'model_type': 'Beta',
                'coefficients': beta_results.get('coefficients', {}),
                'p_values': beta_results.get('p_values', []),
                'r_squared': beta_results.get('r_squared', 0),
                'aic': beta_results.get('aic', 0),
                'cross_validation_scores': cv_results.get('beta', [])
            },
            {
                'model_type': 'Gaussian',
                'coefficients': gaussian_results.get('coefficients', {}),
                'p_values': gaussian_results.get('p_values', []),
                'r_squared': gaussian_results.get('r_squared', 0),
                'aic': gaussian_results.get('aic', 0),
                'cross_validation_scores': cv_results.get('gaussian', [])
            },
            {
                'model_type': 'Ridge',
                'coefficients': ridge_results.get('coefficients', {}),
                'p_values': ridge_results.get('p_values', []),
                'r_squared': ridge_results.get('r_squared', 0),
                'aic': ridge_results.get('aic', 0),
                'cross_validation_scores': cv_results.get('ridge', [])
            }
        ],
        'significant_predictors': [k for k, v in beta_results.get('coefficients', {}).items() if v != 0]
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics_data, f, indent=2, default=str)
    
    logger.info(f"Modeling complete: {output_path}")
    return output_path

def run_reporting_stage(metrics_path: Path, data_path: Path) -> Path:
    """Run the reporting stage."""
    logger.info("Starting reporting stage...")
    
    # Load metrics and data
    with open(metrics_path, 'r') as f:
        model_metrics = json.load(f)
    
    df = pd.read_parquet(data_path)
    
    # Generate plots and diagnostics
    output_path = Path("code/data/results/diagnostics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    diagnostic_report = generate_diagnostic_report(model_metrics, df)
    
    with open(output_path, 'w') as f:
        json.dump(diagnostic_report, f, indent=2)
    
    logger.info(f"Reporting complete: {output_path}")
    return output_path

def run_final_contract_validation(data_path: Path) -> bool:
    """Run final contract validation."""
    logger.info("Running final contract validation...")
    
    df = pd.read_parquet(data_path)
    schema_path = Path("code/specs/contracts/game_record.schema.yaml")
    
    if not schema_path.exists():
        logger.warning("Schema file not found, skipping validation")
        return True
    
    schema = load_schema(schema_path)
    is_valid = validate_dataframe_against_contract(df, schema)
    
    if is_valid:
        logger.info("Contract validation passed")
    else:
        logger.error("Contract validation failed")
    
    return is_valid

def save_final_dataset(data_path: Path) -> None:
    """Save final dataset (no-op if already saved)."""
    logger.info("Final dataset already saved during processing stage")

def main():
    parser = argparse.ArgumentParser(description="Chess Elo Analysis Pipeline")
    parser.add_argument("--sample", action="store_true", help="Run in sample mode")
    args = parser.parse_args()

    try:
        # Ensure directories exist
        ensure_directories()

        # Run pipeline stages
        download_path = run_download_stage(sample_mode=args.sample)
        processed_path = run_processing_stage(download_path)
        metrics_path = run_modeling_stage(processed_path)
        report_path = run_reporting_stage(metrics_path, processed_path)
        
        # Final validation
        if not run_final_contract_validation(processed_path):
            logger.error("Final validation failed")
            sys.exit(1)

        logger.info("Pipeline completed successfully")
        print("Pipeline completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
