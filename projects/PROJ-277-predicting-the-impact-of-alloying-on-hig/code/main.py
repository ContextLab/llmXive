"""
CLI entry point for the Alloy Oxidation Resistance Prediction Pipeline.

This script orchestrates the full workflow:
1. Parse arguments and configure environment (CI vs Local).
2. Ensure required directory structures exist.
3. Fetch and validate data (with fallback logic if real data is unavailable).
4. Process data (calculate descriptors, validate, downsample).
5. Train models (Random Forest, Gradient Boosting, Gaussian Process).
6. Select best model and generate predictions.
7. (Optional) Perform gap analysis if microstructural data is present.
8. Generate outputs (predictions.csv, gap_analysis_report.json, SHAP plots).
9. Log final summary and warnings.
"""

import sys
import os
import logging

# Add the project root to the path to allow imports from sibling modules
# This is necessary when running as a script from the code directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import parse_args, get_config, ensure_directories, get_config_from_args
from utils.logger import configure_logging, get_logger, log_startup_info, log_final_summary
from data.fetcher import fetch_data, log_data_gap_report
from data.processor import process_data, downsample_dataset, validate_data
from models.trainer import train_models, select_best_model
from models.evaluator import perform_gap_analysis
from viz.shap_plots import generate_shap_plots, generate_feature_table

def main():
    """Main entry point for the CLI."""
    # Parse arguments
    args = parse_args()
    config = get_config(args)
    
    # Configure logging
    configure_logging(config.log_level, config.log_file)
    logger = get_logger(__name__)
    
    # Log startup information
    log_startup_info(logger, config)
    
    # Ensure directories exist
    ensure_directories(config)
    
    try:
        # Step 1: Fetch Data
        logger.info("Step 1: Fetching and validating data...")
        data_path, used_synthetic = fetch_data(config)
        
        if data_path is None:
            logger.error("Data fetching failed and no synthetic fallback was triggered or available.")
            # Log the gap report if real data failed
            log_data_gap_report(logger, "Data fetching failed: No real data source available.")
            sys.exit(1)
        
        if used_synthetic:
            logger.warning("Using synthetic data as fallback. Scientific validity warning will be applied.")
            config.using_synthetic_data = True
        
        # Step 2: Process Data
        logger.info("Step 2: Processing data (descriptors, validation, downsampling)...")
        
        # Load and validate raw data
        df_processed = process_data(data_path, config)
        
        if df_processed is None or df_processed.empty:
            logger.error("Data processing failed: No valid data returned.")
            sys.exit(1)
        
        # Downsample if necessary (T017 logic)
        if config.mode == 'ci' and len(df_processed) > 500:
            logger.info("CI mode detected with >500 rows. Downsampling to 500.")
            df_processed = downsample_dataset(df_processed, 500, config)
        elif config.mode == 'local' and len(df_processed) > 1000:
            logger.info("Local mode detected with >1000 rows. Downsampling to 1000.")
            df_processed = downsample_dataset(df_processed, 1000, config)
        
        logger.info(f"Processed dataset shape: {df_processed.shape}")
        
        # Step 3: Train Models
        logger.info("Step 3: Training models (RF, GB, GP)...")
        
        # Prepare features and target
        # Assuming 'observed_weight_gain' is the target
        target_col = 'observed_weight_gain'
        feature_cols = [col for col in df_processed.columns if col != target_col]
        
        X = df_processed[feature_cols].values
        y = df_processed[target_col].values
        
        # Train models
        trained_models, cv_results = train_models(X, y, config, feature_names=feature_cols)
        
        if not trained_models:
            logger.error("Model training failed: No models were trained successfully.")
            sys.exit(1)
        
        # Step 4: Select Best Model
        logger.info("Step 4: Selecting best model based on RMSE...")
        best_model_name, best_model, best_rmse = select_best_model(trained_models, cv_results)
        
        if best_model is None:
            logger.error("Model selection failed: Could not determine best model.")
            sys.exit(1)
        
        logger.info(f"Best model selected: {best_model_name} (RMSE: {best_rmse:.4f})")
        
        # Step 5: Generate Predictions
        logger.info("Step 5: Generating predictions and uncertainty estimates...")
        
        # Generate predictions on the full processed dataset (or a hold-out set if configured)
        # For this MVP, we predict on the processed data to demonstrate the pipeline
        predictions, uncertainties = best_model.predict_with_uncertainty(X)
        
        # Create output DataFrame
        output_df = df_processed.copy()
        output_df['predicted_weight_gain'] = predictions
        output_df['prediction_uncertainty'] = uncertainties
        output_df['model_used'] = best_model_name
        
        # Add scientific validity warning if synthetic data was used
        if config.using_synthetic_data:
            output_df['scientific_validity_warning'] = "WARNING: Predictions based on synthetic data. Results may not reflect physical reality."
        
        # Save predictions to CSV
        output_path = os.path.join(config.data_processed_dir, 'predictions.csv')
        output_df.to_csv(output_path, index=False)
        logger.info(f"Predictions saved to: {output_path}")
        
        # Step 6: Gap Analysis (if microstructural data present)
        # Check if microstructural features are present
        microstructural_cols = [col for col in feature_cols if any(m in col.lower() for m in ['grain', 'precipitate', 'microstructure'])]
        
        if microstructural_cols and len(microstructural_cols) > 0:
            logger.info("Step 6: Performing gap analysis (microstructural effect)...")
            gap_report = perform_gap_analysis(X, y, trained_models, config, feature_cols, microstructural_cols)
            
            if gap_report:
                # Save gap analysis report
                gap_report_path = os.path.join(config.data_processed_dir, 'gap_analysis_report.json')
                # Convert to dict if it's a custom object
                if hasattr(gap_report, '__dict__'):
                    gap_report_dict = gap_report.__dict__
                else:
                    gap_report_dict = gap_report
                import json
                with open(gap_report_path, 'w') as f:
                    json.dump(gap_report_dict, f, indent=2)
                logger.info(f"Gap analysis report saved to: {gap_report_path}")
        else:
            logger.info("Step 6: Skipping gap analysis - no microstructural features detected.")
        
        # Step 7: Visualization (SHAP)
        logger.info("Step 7: Generating SHAP plots and feature importance...")
        
        # Generate SHAP summary plot
        shap_plot_path = os.path.join(config.data_processed_dir, 'shap_summary_plot.png')
        generate_shap_plots(best_model, X, feature_cols, output_path=shap_plot_path)
        logger.info(f"SHAP summary plot saved to: {shap_plot_path}")
        
        # Generate feature importance table
        feature_table_path = os.path.join(config.data_processed_dir, 'feature_importance.csv')
        generate_feature_table(best_model, feature_cols, output_path=feature_table_path)
        logger.info(f"Feature importance table saved to: {feature_table_path}")
        
        # Step 8: Final Summary
        log_final_summary(logger, config, {
            'best_model': best_model_name,
            'rmse': best_rmse,
            'predictions_file': output_path,
            'shap_plot': shap_plot_path,
            'using_synthetic_data': config.using_synthetic_data
        })
        
        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Pipeline execution failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())