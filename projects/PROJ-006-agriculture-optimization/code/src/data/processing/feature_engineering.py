"""
Feature Engineering Module for Climate-Smart Agriculture Analysis.

Implements village-level aggregation fallback logic as per T021.
Triggers aggregation if linkage validation indicates insufficient data coverage.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import constants from the project config
from src.config.constants import GRID_RESOLUTION_KM

logger = logging.getLogger(__name__)

def load_linkage_validation(log_path: Path) -> Dict[str, Any]:
    """
    Load the linkage validation JSON file.
    
    Args:
        log_path: Path to data/logs/linkage_validation.json
        
    Returns:
        Dictionary containing linkage validation data.
        
    Raises:
        FileNotFoundError: If the validation file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Linkage validation file not found: {log_path}")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def perform_village_aggregation(
    input_df: pd.DataFrame, 
    output_path: Path
) -> pd.DataFrame:
    """
    Perform village-level aggregation fallback.
    
    Logic:
    - Aggregates to village level using 'village_id' as key.
    - Uses 'mean' as the aggregation function for CSA_Index and Stability_Score.
    - Retains 'village_id' and other necessary columns.
    
    Args:
        input_df: DataFrame containing feature engineered data with 'village_id'.
        output_path: Path to write the aggregated CSV.
        
    Returns:
        Aggregated DataFrame.
    """
    logger.info(f"Starting village-level aggregation. Input shape: {input_df.shape}")
    
    if 'village_id' not in input_df.columns:
        raise ValueError("Input DataFrame must contain 'village_id' column for aggregation.")
    
    # Identify columns to aggregate
    numeric_cols = input_df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude village_id from numeric aggregation if present in numeric_cols
    cols_to_aggregate = [col for col in numeric_cols if col != 'village_id']
    
    # Define aggregation dictionary
    agg_dict = {col: 'mean' for col in cols_to_aggregate}
    
    # Group by village_id and aggregate
    # We keep village_id as the index or reset it to be a column
    aggregated_df = input_df.groupby('village_id', as_index=False).agg(agg_dict)
    
    # Ensure unique village_ids (groupby guarantees this, but explicit check is good)
    if aggregated_df['village_id'].duplicated().any():
        logger.warning("Duplicated village_ids found after aggregation. This should not happen.")
        
    logger.info(f"Aggregation complete. Output shape: {aggregated_df.shape}")
    
    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated_df.to_csv(output_path, index=False)
    logger.info(f"Aggregated dataset written to {output_path}")
    
    return aggregated_df

def check_and_aggregate_if_needed(
    feature_engineered_path: Path,
    linkage_log_path: Path,
    output_path: Path
) -> Optional[pd.DataFrame]:
    """
    Main entry point for T021 logic.
    
    Checks linkage validation. If linkage < 95% OR N < 300, performs aggregation.
    
    Args:
        feature_engineered_path: Path to the feature engineered data (T018b output).
        linkage_log_path: Path to linkage validation JSON (T017c output).
        output_path: Path to write the aggregated dataset.
        
    Returns:
        Aggregated DataFrame if triggered, None otherwise.
    """
    logger.info("Checking linkage validation for aggregation trigger...")
    
    try:
        validation_data = load_linkage_validation(linkage_log_path)
    except FileNotFoundError as e:
        logger.error(f"Linkage validation file missing. Cannot determine aggregation trigger. {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Linkage validation file is invalid JSON. {e}")
        return None

    linkage_percentage = validation_data.get('linkage_percentage', 0.0)
    total_valid_households = validation_data.get('total_valid_households', 0)
    triggered_aggregation = validation_data.get('triggered_aggregation', False)
    
    logger.info(f"Linkage: {linkage_percentage:.2f}%, Total Households: {total_valid_households}")
    logger.info(f"Triggered Aggregation Flag in Log: {triggered_aggregation}")

    # Explicit trigger logic as per T021: linkage < 95% OR N < 300
    # Note: The log file might already have this calculated, but we re-verify for robustness
    should_aggregate = (linkage_percentage < 95.0) or (total_valid_households < 300)

    if should_aggregate:
        logger.warning("Aggregation triggered: Linkage < 95% OR N < 300.")
        
        if not feature_engineered_path.exists():
            raise FileNotFoundError(f"Feature engineered data not found at {feature_engineered_path}")
        
        df = pd.read_csv(feature_engineered_path)
        
        # Perform aggregation
        aggregated_df = perform_village_aggregation(df, output_path)
        
        # Verify output constraints
        if aggregated_df['village_id'].isnull().any():
            raise ValueError("Aggregated dataset contains null village_ids.")
        
        if len(aggregated_df) < 300:
            logger.warning(f"Aggregated dataset size ({len(aggregated_df)}) is less than 300. Proceeding with caution.")
        
        logger.info("Aggregation process completed successfully.")
        return aggregated_df
    else:
        logger.info("Aggregation NOT triggered. Linkage >= 95% and N >= 300.")
        return None

def main():
    """
    CLI entry point for T021.
    """
    # Define paths relative to project root
    # Assuming this script is run from the project root or code/
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    if 'code' in project_root.parts:
        project_root = project_root / 'code'
        
    # Ensure paths exist
    feature_engineered_path = project_root / 'data' / 'processed' / 'feature_engineered_data.csv'
    linkage_log_path = project_root / 'data' / 'logs' / 'linkage_validation.json'
    output_path = project_root / 'data' / 'processed' / 'analysis_dataset_village_aggregated.csv'
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result_df = check_and_aggregate_if_needed(
            feature_engineered_path,
            linkage_log_path,
            output_path
        )
        
        if result_df is not None:
            logger.info(f"Aggregation performed. Result saved to {output_path}")
            logger.info(f"Result shape: {result_df.shape}")
            logger.info(f"Unique villages: {result_df['village_id'].nunique()}")
        else:
            logger.info("No aggregation performed.")
            
    except Exception as e:
        logger.error(f"Error during aggregation check: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()