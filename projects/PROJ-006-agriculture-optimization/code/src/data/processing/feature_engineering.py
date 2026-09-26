"""
Feature Engineering Module for Climate-Smart Agriculture Analysis.

This module implements the calculation of Stability_Score and CSA_Index
from raw NDVI time-series and survey data, as well as village ID derivation
and aggregation logic.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from src.utils.io_helpers import read_parquet_strict, write_parquet_strict, write_json_strict
from src.config.constants import GRID_RESOLUTION_KM, BUFFER_SIZE_KM

# Configure logging
logger = logging.getLogger(__name__)

def load_linkage_validation(log_path: Path) -> Dict[str, Any]:
    """
    Load the linkage validation JSON file.
    
    Args:
        log_path: Path to the linkage_validation.json file.
        
    Returns:
        Dictionary containing linkage validation data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Linkage validation file not found: {log_path}")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def calculate_stability_score(ndvi_values: pd.Series) -> float:
    """
    Calculate the Stability Score from NDVI time-series.
    
    The Stability Score is defined as 1 / CV, where CV is the coefficient of variation.
    CV = std / mean (absolute value to handle potential negative NDVI).
    
    Args:
        ndvi_values: Series of NDVI values for a single household/plot.
        
    Returns:
        Stability Score (float). Returns np.nan if CV is 0 or mean is 0.
    """
    # Remove NaN values
    clean_values = ndvi_values.dropna()
    
    if len(clean_values) < 2:
        logger.warning("Insufficient data points for stability calculation")
        return np.nan
        
    mean_ndvi = clean_values.mean()
    std_ndvi = clean_values.std()
    
    if mean_ndvi == 0:
        logger.warning("Mean NDVI is zero, cannot calculate CV")
        return np.nan
        
    cv = std_ndvi / abs(mean_ndvi)
    
    if cv == 0:
        # Perfectly stable (all values identical)
        return float('inf')
        
    stability_score = 1.0 / cv
    return stability_score

def calculate_csa_index(row: pd.Series) -> int:
    """
    Calculate the CSA Index from binary practice indicators.
    
    The CSA Index is the sum of adopted practices:
    - practice_mixed_farming
    - practice_terracing
    - practice_conservation_tillage
    - practice_agroforestry
    
    Args:
        row: A single row from the survey dataset.
        
    Returns:
        CSA Index (int) ranging from 0 to 4.
    """
    practices = [
        'practice_mixed_farming',
        'practice_terracing',
        'practice_conservation_tillage',
        'practice_agroforestry'
    ]
    
    csa_index = 0
    for practice in practices:
        if practice in row.index:
            val = row[practice]
            if pd.notna(val) and val:
                csa_index += 1
                
    return csa_index

def derive_village_id(lat: float, lon: float) -> str:
    """
    Derive a village ID by rounding coordinates to the nearest grid cell.
    
    Formula: village_id = f'{int(lat / grid_resolution_km) * grid_resolution_km}_{int(lon / grid_resolution_km) * grid_resolution_km}'
    
    Args:
        lat: Latitude coordinate.
        lon: Longitude coordinate.
        
    Returns:
        String formatted village ID.
    """
    grid_res = GRID_RESOLUTION_KM
    
    lat_grid = int(lat / grid_res) * grid_res
    lon_grid = int(lon / grid_res) * grid_res
    
    return f"{lat_grid}_{lon_grid}"

def perform_village_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to the village level.
    
    Excludes rows with null Stability_Score or CSA_Index before aggregation.
    Aggregates CSA_Index and Stability_Score using mean.
    
    Args:
        df: DataFrame with village_id column.
        
    Returns:
        Aggregated DataFrame with one row per village_id.
    """
    logger.info(f"Performing village-level aggregation on {len(df)} rows")
    
    # Exclude rows with null key metrics
    initial_count = len(df)
    df_clean = df.dropna(subset=['Stability_Score', 'CSA_Index', 'village_id'])
    excluded_count = initial_count - len(df_clean)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows with null key metrics before aggregation")
    
    if len(df_clean) == 0:
        logger.error("No valid rows remaining for aggregation")
        return pd.DataFrame()
    
    # Aggregate
    agg_dict = {
        'CSA_Index': 'mean',
        'Stability_Score': 'mean'
    }
    
    # Add other numeric columns to aggregation if they exist
    for col in df_clean.columns:
        if df_clean[col].dtype in ['float64', 'int64', 'float32', 'int32'] and col not in ['CSA_Index', 'Stability_Score', 'village_id']:
            agg_dict[col] = 'mean'
    
    aggregated = df_clean.groupby('village_id').agg(agg_dict).reset_index()
    
    logger.info(f"Aggregation complete: {initial_count} rows -> {len(aggregated)} villages")
    return aggregated

def check_and_aggregate_if_needed(
    df: pd.DataFrame,
    linkage_validation_path: Path,
    output_path: Path
) -> Tuple[pd.DataFrame, bool]:
    """
    Check linkage validation and perform aggregation if triggered.
    
    Args:
        df: The feature engineered dataset.
        linkage_validation_path: Path to linkage_validation.json.
        output_path: Path to write the aggregated dataset.
        
    Returns:
        Tuple of (resulting DataFrame, was_aggregation_triggered).
    """
    try:
        validation_data = load_linkage_validation(linkage_validation_path)
    except FileNotFoundError:
        logger.warning("Linkage validation file not found, skipping aggregation check")
        return df, False
    
    triggered = validation_data.get('triggered_aggregation', False)
    
    if triggered:
        logger.info("Aggregation triggered by linkage validation, performing village-level aggregation")
        result = perform_village_aggregation(df)
        write_parquet_strict(result, output_path)
        logger.info(f"Aggregated dataset written to {output_path}")
        return result, True
    else:
        logger.info("Aggregation not triggered, using full dataset")
        return df, False

def main():
    """
    Main entry point for feature engineering.
    
    Reads raw NDVI time-series and survey data, calculates metrics,
    and writes the feature engineered dataset.
    """
    project_root = Path(____).parent.parent.parent.parent
    data_dir = project_root / 'data'
    
    # Define paths
    ndvi_timeseries_path = data_dir / 'processed' / 'raw_ndvi_timeseries.parquet'
    survey_data_path = data_dir / 'raw' / 'filtered_survey.csv'
    linkage_validation_path = data_dir / 'logs' / 'linkage_validation.json'
    output_path = data_dir / 'processed' / 'feature_engineered_data.csv'
    aggregated_output_path = data_dir / 'processed' / 'analysis_dataset_village_aggregated.csv'
    
    logger.info(f"Starting feature engineering pipeline")
    logger.info(f"NDVI timeseries path: {ndvi_timeseries_path}")
    logger.info(f"Survey data path: {survey_data_path}")
    
    # Load raw NDVI time-series
    if not ndvi_timeseries_path.exists():
        raise FileNotFoundError(f"Raw NDVI timeseries file not found: {ndvi_timeseries_path}")
    
    ndvi_df = read_parquet_strict(ndvi_timeseries_path)
    logger.info(f"Loaded NDVI timeseries with {len(ndvi_df)} records")
    
    # Load survey data
    if not survey_data_path.exists():
        raise FileNotFoundError(f"Survey data file not found: {survey_data_path}")
    
    survey_df = pd.read_csv(survey_data_path)
    logger.info(f"Loaded survey data with {len(survey_df)} records")
    
    # Merge datasets
    if 'household_id' not in ndvi_df.columns or 'household_id' not in survey_df.columns:
        raise ValueError("Both datasets must contain 'household_id' for merging")
    
    merged_df = pd.merge(ndvi_df, survey_df, on='household_id', how='inner')
    logger.info(f"Merged dataset has {len(merged_df)} records")
    
    if len(merged_df) == 0:
        raise ValueError("No matching records between NDVI and survey data")
    
    # Calculate Stability_Score
    logger.info("Calculating Stability_Score from NDVI time-series")
    # Assuming 'ndvi_values' is stored as a list/array in the parquet file
    # If it's a long format (household_id, timestamp, ndvi), we need to pivot first
    if 'timestamp' in merged_df.columns and 'ndvi_values' not in merged_df.columns:
        # Long format: pivot to wide format
        pivot_df = merged_df.pivot_table(
            index='household_id',
            columns='timestamp',
            values='ndvi_values',
            aggfunc='mean'
        )
        pivot_df.columns = [f'ndvi_{i}' for i in range(len(pivot_df.columns))]
        ndvi_wide = pivot_df.reset_index()
        
        # Calculate stability for each household
        stability_scores = []
        for idx, row in ndvi_wide.iterrows():
            household_id = row['household_id']
            ndvi_series = row[[col for col in row.index if col.startswith('ndvi_')]]
            score = calculate_stability_score(ndvi_series)
            stability_scores.append({'household_id': household_id, 'Stability_Score': score})
        
        stability_df = pd.DataFrame(stability_scores)
    else:
        # Assume 'ndvi_values' is already a list/array or we have a single value per row
        # For this implementation, we assume the data is in long format and we need to group
        if 'ndvi_values' in merged_df.columns:
            # If it's a string representation of a list, convert it
            if merged_df['ndvi_values'].dtype == 'object':
                try:
                    merged_df['ndvi_list'] = merged_df['ndvi_values'].apply(
                        lambda x: eval(x) if isinstance(x, str) else x
                    )
                except:
                    raise ValueError("Could not parse 'ndvi_values' column")
            else:
                merged_df['ndvi_list'] = merged_df['ndvi_values']
            
            # Group by household_id and calculate stability
            stability_df = merged_df.groupby('household_id').apply(
                lambda x: calculate_stability_score(x['ndvi_list'].iloc[0])
            ).reset_index()
            stability_df.columns = ['household_id', 'Stability_Score']
        else:
            raise ValueError("Expected 'ndvi_values' column in merged dataset")
    
    # Merge stability scores back to main dataframe
    final_df = pd.merge(merged_df, stability_df, on='household_id', how='left')
    
    # Calculate CSA_Index
    logger.info("Calculating CSA_Index from practice indicators")
    final_df['CSA_Index'] = final_df.apply(calculate_csa_index, axis=1)
    
    # Derive village_id
    logger.info("Deriving village_id from coordinates")
    if 'latitude' in final_df.columns and 'longitude' in final_df.columns:
        final_df['village_id'] = final_df.apply(
            lambda row: derive_village_id(row['latitude'], row['longitude']),
            axis=1
        )
    else:
        logger.warning("Latitude/longitude columns not found, skipping village_id derivation")
    
    # Ensure required columns exist
    required_columns = [
        'household_id', 'latitude', 'longitude', 'land_size', 'education_level',
        'finance_access', 'practice_mixed_farming', 'practice_terracing',
        'practice_conservation_tillage', 'practice_agroforestry', 'extension_visits',
        'hlias', 'CSA_Index', 'Stability_Score', 'HFIAS', 'village_id'
    ]
    
    missing_cols = [col for col in required_columns if col not in final_df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in output: {missing_cols}")
        # Add missing columns with NaN
        for col in missing_cols:
            final_df[col] = np.nan
    
    # Select and order columns
    output_columns = [col for col in required_columns if col in final_df.columns]
    final_df = final_df[output_columns]
    
    # Write intermediate output
    logger.info(f"Writing feature engineered data to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    # Check linkage validation and aggregate if needed
    if linkage_validation_path.exists():
        result_df, was_triggered = check_and_aggregate_if_needed(
            final_df, linkage_validation_path, aggregated_output_path
        )
        if was_triggered:
            logger.info("Aggregation was triggered and performed")
    else:
        logger.info("Linkage validation file not found, skipping aggregation check")
    
    logger.info("Feature engineering pipeline completed successfully")
    
    return final_df

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
