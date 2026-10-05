"""
Main entry point for the llmXive research pipeline.
Orchestrates: Load -> Preprocess -> Train -> Predict -> Save.

Implements FR-001, FR-004, FR-005, FR-007.
"""
import sys
import os
from pathlib import Path
import pandas as pd
import json
import time
import traceback

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import ensure_dirs, get_config
from code.utils.logging import get_logger, log_warning_structured
from code.data.loader import load_and_validate_dataset
from code.data.processor import process_dataset
from code.models.trainer import run_training_pipeline
from code.models.predictor import run_prediction_pipeline
from code.models.saver import save_predictions, save_new_predictions, save_pipeline_log
from code.models.evaluator import run_evaluation

logger = get_logger(__name__)

def validate_alloy_family_counts(processed_df: pd.DataFrame, min_samples: int = 50) -> bool:
    """
    Validate that every alloy family has at least min_samples.
    Returns True if valid, False otherwise.
    """
    if 'alloy_family' not in processed_df.columns:
        logger.error("Column 'alloy_family' not found in processed data.")
        return False
    
    counts = processed_df['alloy_family'].value_counts()
    logger.info(f"Sample counts per alloy family:\n{counts}")
    
    if (counts < min_samples).any():
        families_below = counts[counts < min_samples].index.tolist()
        logger.error(f"Validation Failed: The following alloy families have < {min_samples} samples: {families_below}")
        return False
    
    return True

def main():
    """
    Main execution flow.
    """
    start_time = time.time()
    config = get_config()
    warnings_list = []
    status = "completed"

    try:
        # 1. Setup Directories
        ensure_dirs(config['data']['processed_path'])
        ensure_dirs(config['data']['output_path'])
        ensure_dirs(config['data']['figures_path'])

        # 2. Load and Validate Data
        logger.info("Step 1: Loading and validating dataset...")
        df_raw, metadata = load_and_validate_dataset(
            real_data_path=config['data']['real_data_path'],
            synthetic_config=config['data']['synthetic_config'],
            min_samples_per_family=config['data']['min_samples_per_family']
        )
        
        if df_raw is None:
            raise RuntimeError("Data loading failed. Aborting.")

        # 3. Preprocess Data
        logger.info("Step 2: Preprocessing data...")
        df_processed = process_dataset(df_raw, config['data']['feature_derivation'])
        
        if df_processed.empty:
            raise RuntimeError("Preprocessing resulted in empty dataset. Aborting.")

        # 4. Validate Alloy Family Counts (FR-008 / T016)
        logger.info("Step 3: Validating alloy family sample counts...")
        if not validate_alloy_family_counts(df_processed, min_samples=config['data']['min_samples_per_family']):
            raise RuntimeError("Insufficient samples per alloy family. Aborting.")

        # 5. Train Model
        logger.info("Step 4: Training model...")
        model, scaler, feature_names, cv_results = run_training_pipeline(
            df_processed,
            target_cols=config['model']['target_columns'],
            feature_cols=config['model']['feature_columns'],
            cv_folds=config['model']['cv_folds'],
            timeout_seconds=config['model']['timeout_seconds']
        )

        # 6. Predictions (Test Set)
        logger.info("Step 5: Generating predictions on test set...")
        # Note: run_prediction_pipeline handles the split internally if not provided,
        # or we assume the trainer returns the test split used for CV.
        # For this pipeline, we assume the predictor takes the processed data and model.
        # We need to extract test data. Let's assume run_training_pipeline returns the test split used.
        # If not, we might need to re-split. For simplicity, we assume the predictor 
        # can handle the full processed data and we rely on the model's internal state 
        # or we pass the specific test set from the trainer if available.
        
        # Correction: The predictor usually needs a separate input. 
        # Let's assume the trainer returns the test set used for validation.
        # If run_training_pipeline doesn't return it, we must split here.
        # Given the constraints, we'll assume the predictor function handles the split 
        # or we pass the processed dataframe and let it split internally for prediction 
        # (which is less ideal but fits the "orchestrator" pattern if trainer doesn't expose test set).
        
        # Better approach: The trainer should return the test set used for evaluation.
        # If not, we split again.
        from sklearn.model_selection import train_test_split
        X = df_processed[feature_names]
        y = df_processed[config['model']['target_columns']]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=config['random_seed'])
        
        predictions_df = run_prediction_pipeline(
            model, scaler, X_test, y_test, feature_names, config['model']['target_columns']
        )

        # 7. Save Predictions (FR-005 / T017)
        logger.info("Step 6: Saving predictions...")
        predictions_path = config['data']['output_path'] + "/predictions.csv"
        save_predictions(predictions_df, predictions_path, metadata={"source": "test_set"})

        # 8. New Predictions (Simulated New Samples)
        logger.info("Step 7: Generating and saving new predictions...")
        # Create a small sample of "new" data for demonstration
        new_samples = X_test.sample(n=min(5, len(X_test)), random_state=42)
        new_predictions_df = run_prediction_pipeline(
            model, scaler, new_samples, None, feature_names, config['model']['target_columns'], is_new_data=True
        )
        
        new_predictions_path = config['data']['output_path'] + "/new_predictions.csv"
        save_new_predictions(new_predictions_df, new_predictions_path, metadata={"source": "new_samples"})

        # 9. Evaluation (US2)
        logger.info("Step 8: Running evaluation...")
        eval_report = run_evaluation(
            predictions_df, 
            df_processed, 
            config['model']['target_columns']
        )
        
        eval_report_path = config['data']['output_path'] + "/evaluation_report.json"
        with open(eval_report_path, 'w') as f:
            json.dump(eval_report, f, indent=2)

        logger.info(f"Pipeline completed successfully in {time.time() - start_time:.2f}s")

    except Exception as e:
        status = "failed"
        logger.error(f"Pipeline failed with error: {str(e)}")
        warnings_list.append(f"Critical Error: {str(e)}")
        traceback.print_exc()

    finally:
        # 10. Save Pipeline Log (FR-007 / T018)
        logger.info("Step 9: Saving pipeline log...")
        log_path = config['data']['output_path'] + "/pipeline.log"
        save_pipeline_log(
            log_path,
            hyperparams=config['model'],
            warnings=warnings_list,
            status=status
        )
        
        if status == "failed":
            sys.exit(1)

if __name__ == "__main__":
    main()
