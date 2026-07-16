"""
Preprocessing pipeline for ball milling PSD data.

Input: Merged raw data (DataFrame)
Output: Processed features (DataFrame) with imputation, encoding, scaling,
        and derived columns.
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from src.exceptions import SchemaValidationError, DataFormatError

logger = logging.getLogger(__name__)

# Required predictors for imputation (excluding targets D10/D50/D90)
NUMERIC_PREDICTORS = [
    'ball_milling_speed',
    'ball_to_powder_ratio',
    'milling_time',
    'ball_size',
    'material_density',
    'youngs_modulus',
    'hardness',
    'temperature',
    'process_duration',  # Will be derived if missing
]

CATEGORICAL_PREDICTORS = [
    'material_type',
    'mill_type',
    'atmosphere',
]

TARGETS = ['D10', 'D50', 'D90']

# Regex patterns for extracting milling time from raw text
TIME_PATTERNS = [
    r'milling_time[:\s]+([\d.]+)\s*(h|hr|hours?)',
    r'duration[:\s]+([\d.]+)\s*(h|hr|hours?)',
    r'time[:\s]+([\d.]+)\s*(h|hr|hours?)',
    r'([\d.]+)\s*(h|hr|hours?)\s*milling',
]


def _parse_time_to_hours(time_str: str) -> Optional[float]:
    """
    Parse a time string (e.g., '2.5h', '3 hours', '45 min') to hours.
    Returns None if parsing fails.
    """
    if not isinstance(time_str, str):
        return None
    
    time_str = time_str.strip().lower()
    
    # Handle minutes
    minutes_match = re.search(r'([\d.]+)\s*(min|minutes?)', time_str)
    if minutes_match:
        return float(minutes_match.group(1)) / 60.0
    
    # Handle hours
    hours_match = re.search(r'([\d.]+)\s*(h|hr|hours?)', time_str)
    if hours_match:
        return float(hours_match.group(1))
    
    return None


def _extract_process_duration(row: pd.Series) -> Optional[float]:
    """
    Extract process duration from a row using multiple strategies:
    1. Use existing 'process_duration' column if available and valid
    2. Derive from 'end_time' and 'start_time' if available
    3. Regex extract from 'raw_text_logs'
    """
    # Strategy 1: Use existing column
    if 'process_duration' in row.index and pd.notna(row['process_duration']):
        try:
            return float(row['process_duration'])
        except (ValueError, TypeError):
            pass
    
    # Strategy 2: Derive from timestamps
    if 'end_time' in row.index and 'start_time' in row.index:
        try:
            if pd.notna(row['end_time']) and pd.notna(row['start_time']):
                end = pd.to_datetime(row['end_time'])
                start = pd.to_datetime(row['start_time'])
                diff_seconds = (end - start).total_seconds()
                if diff_seconds > 0:
                    return diff_seconds / 3600.0
        except (ValueError, TypeError):
            pass
    
    # Strategy 3: Regex from raw text logs
    if 'raw_text_logs' in row.index and pd.notna(row['raw_text_logs']):
        raw_text = str(row['raw_text_logs'])
        for pattern in TIME_PATTERNS:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                time_val = match.group(1)
                time_unit = match.group(2) if len(match.groups()) > 1 else 'h'
                parsed = _parse_time_to_hours(f"{time_val}{time_unit}")
                if parsed is not None:
                    return parsed
    
    return None


def calculate_process_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 'process_duration' column if missing or invalid.
    """
    df = df.copy()
    
    # Ensure column exists
    if 'process_duration' not in df.columns:
        df['process_duration'] = np.nan
    
    # Calculate for rows where it's missing or NaN
    mask = df['process_duration'].isna()
    if mask.any():
        durations = df.loc[mask].apply(_extract_process_duration, axis=1)
        df.loc[mask, 'process_duration'] = durations.values
        
        # Log how many were successfully derived
        derived_count = durations.notna().sum()
        logger.info(f"Derived process_duration for {derived_count} rows")
        
        # Log failures
        failed_count = durations.isna().sum()
        if failed_count > 0:
            logger.warning(f"Could not derive process_duration for {failed_count} rows")
    
    return df


def _flag_unstructured_entries(df: pd.DataFrame, output_path: Path) -> None:
    """
    Flag entries with unstructured PSD data (images/curves) to a JSON file.
    """
    flagged_entries = []
    
    # Check for columns that might indicate unstructured data
    unstructured_indicators = [
        'psd_image_path', 'psd_curve_data', 'has_psd_image',
        'psd_data_format', 'unstructured_psd'
    ]
    
    for col in unstructured_indicators:
        if col in df.columns:
            mask = df[col].notna()
            if col == 'has_psd_image':
                mask = df[col] == True
            elif col == 'psd_data_format':
                mask = df[col].str.lower().isin(['image', 'curve', 'graph', 'chart'])
            
            if mask.any():
                for idx in df[mask].index:
                  entry = {
                      'experiment_id': df.loc[idx, 'experiment_id'] if 'experiment_id' in df.columns else f"unknown_{idx}",
                      'source': df.loc[idx, 'source'] if 'source' in df.columns else 'unknown',
                      'issue_type': f'unstructured_{col}',
                      'raw_blob_hash': None  # Would need hashing logic if blob exists
                  }
                  # Add any relevant context
                  if col in df.columns:
                      entry['context_value'] = str(df.loc[idx, col])
                  
                  flagged_entries.append(entry)
    
    if flagged_entries:
        # Load existing or create new
        if output_path.exists():
            try:
                with open(output_path, 'r') as f:
                    existing = json.load(f)
                flagged_entries = existing + flagged_entries
            except (json.JSONDecodeError, IOError):
                logger.warning(f"Could not read existing flagged entries at {output_path}")
        
        # Deduplicate by experiment_id and issue_type
        seen = set()
        unique_entries = []
        for entry in flagged_entries:
            key = (entry['experiment_id'], entry['issue_type'])
            if key not in seen:
                seen.add(key)
                unique_entries.append(entry)
        
        with open(output_path, 'w') as f:
            json.dump(unique_entries, f, indent=2)
        
        logger.info(f"Flagged {len(unique_entries)} unstructured entries to {output_path}")
    else:
        logger.info("No unstructured PSD entries found to flag")


def run_preprocessing_pipeline(
    input_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    flagged_output_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Run the full preprocessing pipeline:
    1. Calculate process_duration
    2. Impute missing numeric values
    3. One-hot encode categorical variables
    4. Standard scale numeric features
    5. Flag unstructured entries
    
    Args:
        input_df: Raw merged DataFrame
        output_path: Optional path to save processed DataFrame
        flagged_output_path: Path to save flagged unstructured entries JSON
    
    Returns:
        Tuple of (processed DataFrame, metadata dict)
    """
    if input_df.empty:
        raise DataFormatError("Input DataFrame is empty")
    
    logger.info(f"Starting preprocessing pipeline with {len(input_df)} rows")
    
    # Step 1: Calculate process_duration
    df = calculate_process_duration(input_df)
    
    # Step 2: Flag unstructured entries
    if flagged_output_path:
        _flag_unstructured_entries(df, Path(flagged_output_path))
    
    # Identify columns to use
    # Filter to only existing columns
    available_numeric = [col for col in NUMERIC_PREDICTORS if col in df.columns]
    available_categorical = [col for col in CATEGORICAL_PREDICTORS if col in df.columns]
    available_targets = [col for col in TARGETS if col in df.columns]
    
    if not available_numeric and not available_categorical:
        raise SchemaValidationError("No predictor columns found in input data")
    
    # Step 3: Build preprocessing pipeline
    transformers = []
    
    # Numeric pipeline: impute + scale
    if available_numeric:
        numeric_pipeline = Pipeline([
            ('imputer', IterativeImputer(
                max_iter=10,
                random_state=42,
                initial_strategy='mean',
                random_state_for_sampling=42
            )),
            ('scaler', StandardScaler())
        ])
        transformers.append(('num', numeric_pipeline, available_numeric))
    
    # Categorical pipeline: one-hot encode
    if available_categorical:
        categorical_pipeline = Pipeline([
            ('onehot', OneHotEncoder(
                handle_unknown='ignore',
                sparse_output=False
            ))
        ])
        transformers.append(('cat', categorical_pipeline, available_categorical))
    
    # Create column transformer
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder='drop'  # Drop columns not in the pipeline
    )
    
    # Step 4: Apply preprocessing
    logger.info(f"Applying preprocessor to {len(available_numeric)} numeric and {len(available_categorical)} categorical columns")
    
    try:
        processed_array = preprocessor.fit_transform(df[available_numeric + available_categorical])
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise DataFormatError(f"Preprocessing pipeline failed: {str(e)}")
    
    # Get feature names after transformation
    feature_names = []
    if available_numeric:
        # Scaler doesn't change names
        feature_names.extend(available_numeric)
    
    if available_categorical:
        ohe = preprocessor.named_transformers_['cat'].named_steps['onehot']
        cat_feature_names = ohe.get_feature_names_out(available_categorical)
        feature_names.extend(cat_feature_names)
    
    # Create processed DataFrame
    processed_df = pd.DataFrame(processed_array, columns=feature_names, index=df.index)
    
    # Add back targets if they exist
    if available_targets:
        processed_df[available_targets] = df[available_targets]
    
    # Add experiment_id if it exists
    if 'experiment_id' in df.columns:
        processed_df['experiment_id'] = df['experiment_id']
    
    # Add source if it exists
    if 'source' in df.columns:
        processed_df['source'] = df['source']
    
    # Step 5: Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        processed_df.to_parquet(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
    
    # Metadata
    metadata = {
        'input_rows': len(input_df),
        'output_rows': len(processed_df),
        'numeric_features_processed': available_numeric,
        'categorical_features_processed': available_categorical,
        'final_feature_names': feature_names,
        'targets_preserved': available_targets,
        'imputation_method': 'IterativeImputer',
        'scaling_method': 'StandardScaler',
        'encoding_method': 'OneHotEncoder'
    }
    
    logger.info(f"Preprocessing complete: {len(processed_df)} rows, {len(feature_names)} features")
    
    return processed_df, metadata


def main():
    """
    CLI entry point for preprocessing pipeline.
    Expected to be called with input and output paths.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess ball milling PSD data')
    parser.add_argument('--input', type=str, required=True, help='Input parquet/CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output parquet file')
    parser.add_argument('--flagged', type=str, default='data/flagged_psd.json', 
                      help='Output path for flagged unstructured entries')
    parser.add_argument('--log-level', type=str, default='INFO', 
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Run preprocessing
    output_path = Path(args.output)
    flagged_path = Path(args.flagged)
    
    processed_df, metadata = run_preprocessing_pipeline(
        input_df=df,
        output_path=output_path,
        flagged_output_path=flagged_path
    )
    
    # Save metadata
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Pipeline complete. Metadata saved to {metadata_path}")


if __name__ == '__main__':
    main()
