"""
Merge and Save (T025): Merges features, responses, and labels into a single dataset.

Schema:
  prompt_id, raw_text, features_*, response_text, adherence_label, safety_refusal

Logic:
  - Perform inner join on `prompt_id`.
  - If any required column is missing, abort with clear error (no silent fallback).
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from config import get_config

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_features(config: dict) -> pd.DataFrame:
    """Load features from data/processed/features.csv."""
    features_path = Path(config['paths']['data_processed']) / 'features.csv'
    if not features_path.exists():
        raise FileNotFoundError(f"Required file missing: {features_path}. "
                                "Run T014 (features.py) first.")
    logger.info(f"Loading features from {features_path}")
    df = pd.read_csv(features_path)
    
    required_cols = ['prompt_id', 'raw_text']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Features file missing required columns: {missing}")
    
    return df

def load_responses(config: dict) -> pd.DataFrame:
    """Load model responses from data/interim/model_responses.csv."""
    # Assuming T022/T023/T024 produced a response file. 
    # Based on typical pipeline flow, this is the output of the inference/labeling stage.
    # If the labeling stage (T022-T024) produced a single file with labels, 
    # we might need to split or adjust. 
    # However, T025 implies merging *responses* and *labels*.
    # Let's assume labeling.py (T022-T024) produced 'data/interim/labeling_results.csv' 
    # containing prompt_id, response_text, adherence_label, safety_refusal.
    # If the task description implies separate files, we adjust.
    # Given T022/T023/T024 are in labeling.py, and T025 merges them, 
    # it's likely labeling.py saves an intermediate file or T025 loads from memory?
    # The prompt says "Merge features, responses, and labels".
    # Let's assume the labeling pipeline (T022-T024) saves a file:
    responses_path = Path(config['paths']['data_interim']) / 'labeling_results.csv'
    
    if not responses_path.exists():
        # Fallback: check if main.py or inference.py saved responses separately
        # But T024 (Safety Trigger) and T023 (Label Logic) are part of labeling.py.
        # It is most logical that labeling.py saves the labeled data here.
        raise FileNotFoundError(
            f"Required file missing: {responses_path}. "
            "Run T024 (labeling.py) first to generate labeling_results.csv."
        )
    
    logger.info(f"Loading responses and labels from {responses_path}")
    df = pd.read_csv(responses_path)
    
    required_cols = ['prompt_id', 'response_text', 'adherence_label', 'safety_refusal']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Labeling results missing required columns: {missing}")
    
    return df

def merge_datasets(features_df: pd.DataFrame, responses_df: pd.DataFrame) -> pd.DataFrame:
    """Perform inner join on prompt_id."""
    logger.info("Merging datasets on prompt_id (inner join)")
    merged = pd.merge(
        features_df,
        responses_df,
        on='prompt_id',
        how='inner'
    )
    
    if merged.empty:
        raise ValueError("Merged dataset is empty. Check prompt_id consistency between features and responses.")
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def save_merged_dataset(df: pd.DataFrame, config: dict) -> None:
    """Save the merged dataset to data/interim/labeled_responses.csv."""
    output_path = Path(config['paths']['data_interim']) / 'labeled_responses.csv'
    logger.info(f"Saving merged dataset to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info("Successfully saved labeled_responses.csv")

def run_merge_save_pipeline(config: dict = None) -> None:
    """Main pipeline for T025."""
    if config is None:
        config = get_config()
    
    try:
        # 1. Load Features
        features_df = load_features(config)
        
        # 2. Load Responses/Labels
        responses_df = load_responses(config)
        
        # 3. Merge
        merged_df = merge_datasets(features_df, responses_df)
        
        # 4. Save
        save_merged_dataset(merged_df, config)
        
        logger.info("T025 Merge and Save completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        raise

def main():
    """Entry point for script execution."""
    logger.info("Starting T025: Merge and Save")
    try:
        run_merge_save_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
