import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from config import get_config, get_data_path
from logging_config import get_logger, initialize_modeling_log, append_log_entry, update_log_section

# Custom exception for data errors
class CustomDataError(Exception):
    """Custom exception for data ingestion and cleaning failures."""
    pass

def load_raw_data(raw_file_path: str) -> pd.DataFrame:
    """
    Load raw data from a CSV file.
    
    Args:
        raw_file_path: Path to the raw CSV file.
        
    Returns:
        pd.DataFrame: The loaded dataframe.
        
    Raises:
        CustomDataError: If the file cannot be loaded or is empty.
    """
    logger = get_logger()
    try:
        if not os.path.exists(raw_file_path):
            msg = f"Raw data file not found: {raw_file_path}"
            logger.error(msg)
            raise CustomDataError(msg)
        
        df = pd.read_csv(raw_file_path)
        if df.empty:
            msg = f"Raw data file is empty: {raw_file_path}"
            logger.error(msg)
            raise CustomDataError(msg)
        
        logger.info(f"Successfully loaded {len(df)} rows from {raw_file_path}")
        return df
    except pd.errors.EmptyDataError:
        msg = f"Raw data file is empty or malformed: {raw_file_path}"
        logger.error(msg)
        raise CustomDataError(msg)
    except Exception as e:
        msg = f"Failed to load raw data from {raw_file_path}: {str(e)}"
        logger.error(msg)
        raise CustomDataError(msg)

def calculate_missingness(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the percentage of missing values for each column.
    
    Args:
        df: The dataframe to analyze.
        
    Returns:
        Dict[str, float]: A dictionary mapping column names to missing percentages.
    """
    missing_pct = df.isna().mean() * 100
    return missing_pct.to_dict()

def handle_missing_values(df: pd.DataFrame, threshold: float = 30.0) -> pd.DataFrame:
    """
    Handle missing values by imputing or dropping rows.
    
    Args:
        df: The dataframe to clean.
        threshold: The percentage of missing values above which a row is dropped.
        
    Returns:
        pd.DataFrame: The cleaned dataframe.
        
    Raises:
        CustomDataError: If the dataframe becomes empty after cleaning.
    """
    logger = get_logger()
    initial_rows = len(df)
    
    # Calculate row-wise missing percentage
    row_missing_pct = df.isna().sum(axis=1) / len(df.columns) * 100
    
    # Drop rows exceeding the threshold
    mask = row_missing_pct <= threshold
    df_clean = df[mask].copy()
    
    dropped_rows = initial_rows - len(df_clean)
    if dropped_rows > 0:
        logger.info(f"Dropped {dropped_rows} rows ({dropped_rows/initial_rows*100:.2f}%) due to excessive missing values.")
    
    # Impute remaining missing values with column mean (numeric) or mode (categorical)
    for col in df_clean.columns:
        if df_clean[col].isna().any():
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                fill_val = df_clean[col].mean()
                df_clean[col].fillna(fill_val, inplace=True)
                logger.debug(f"Imputed {col} with mean: {fill_val:.2f}")
            else:
                fill_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else "Unknown"
                df_clean[col].fillna(fill_val, inplace=True)
                logger.debug(f"Imputed {col} with mode: {fill_val}")
    
    if df_clean.empty:
        msg = "Dataframe became empty after cleaning."
        logger.error(msg)
        raise CustomDataError(msg)
        
    return df_clean

def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize categorical codes to standard values.
    
    Args:
        df: The dataframe to normalize.
        
    Returns:
        pd.DataFrame: The normalized dataframe.
    """
    logger = get_logger()
    # Example normalization logic (expand based on specific requirements)
    # Assuming 'education' and 'engagement' items might have varying codes
    categorical_cols = ['education', 'engagement_level'] # Example columns
    for col in categorical_cols:
        if col in df.columns:
            # Ensure consistent string representation or specific mapping
            # This is a placeholder for specific mapping logic
            df[col] = df[col].astype(str).str.strip().str.lower()
    return df

def validate_clean_data(df: pd.DataFrame) -> bool:
    """
    Validate the cleaned dataframe against expected schema.
    
    Args:
        df: The cleaned dataframe.
        
    Returns:
        bool: True if valid, False otherwise.
        
    Raises:
        CustomDataError: If validation fails.
    """
    logger = get_logger()
    required_columns = ['age', 'education', 'farm_size', 'credit', 'adoption', 'engagement_items']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        msg = f"Cleaned data missing required columns: {missing_cols}"
        logger.error(msg)
        raise CustomDataError(msg)
        
    if df.isna().any().any():
        msg = "Cleaned data still contains missing values."
        logger.error(msg)
        raise CustomDataError(msg)
        
    logger.info("Cleaned data validation passed.")
    return True

def update_modeling_log(log_entry: Dict[str, Any]) -> None:
    """
    Update the modeling_log.yaml with a new entry.
    
    Args:
        log_entry: The dictionary to append/update in the log.
    """
    config = get_config()
    log_path = Path(config['log_file'])
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if log_path.exists():
            with open(log_path, 'r') as f:
                log_data = yaml.safe_load(f) or {}
        else:
            log_data = {}
        
        # Append or update specific section
        # For T016, we log errors or specific validation steps
        if 'data_cleaning_errors' not in log_data:
            log_data['data_cleaning_errors'] = []
        
        log_data['data_cleaning_errors'].append(log_entry)
        
        with open(log_path, 'w') as f:
            yaml.dump(log_data, f, default_flow_style=False)
            
    except Exception as e:
        # If logging fails, we still want the main process to fail or warn
        logging.error(f"Failed to update modeling_log.yaml: {e}")

def calculate_power_analysis(df: pd.DataFrame, num_predictors: int = 1) -> Dict[str, Any]:
    """
    Calculate power analysis metrics.
    
    Args:
        df: The cleaned dataframe.
        num_predictors: Number of predictors in the model.
        
    Returns:
        Dict[str, Any]: Power analysis results.
    """
    # Placeholder for actual power analysis logic
    # Assuming 'adoption_binary' exists or is derived
    if 'adoption_binary' in df.columns:
        effective_N_events = df['adoption_binary'].sum()
    else:
        # Fallback estimation
        effective_N_events = int(len(df) * 0.5)
        
    ratio = effective_N_events / num_predictors if num_predictors > 0 else 0
    shortfall = ratio < 10
    
    return {
        'effective_N_events': effective_N_events,
        'num_predictors': num_predictors,
        'ratio': ratio,
        'shortfall': shortfall
    }

def main():
    """Main function to run the data cleaning pipeline."""
    logger = get_logger()
    config = get_config()
    
    raw_file = get_data_path(config['raw_data_file'])
    clean_file = get_data_path(config['cleaned_data_file'])
    
    # Ensure output directory exists
    Path(clean_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = load_raw_data(raw_file)
        
        # Calculate missingness
        missingness = calculate_missingness(df)
        logger.info(f"Missingness: {missingness}")
        
        # Handle missing values
        df_clean = handle_missing_values(df)
        
        # Normalize categorical codes
        df_clean = normalize_categorical_codes(df_clean)
        
        # Validate cleaned data
        validate_clean_data(df_clean)
        
        # Power analysis
        power_stats = calculate_power_analysis(df_clean)
        
        # Log power analysis
        update_modeling_log({
            'step': 'power_analysis',
            'timestamp': str(pd.Timestamp.now()),
            'metrics': power_stats
        })
        
        # Export cleaned data
        df_clean.to_csv(clean_file, index=False)
        logger.info(f"Cleaned data saved to {clean_file}")
        
    except CustomDataError as e:
        # Log the specific error to modeling_log.yaml
        update_modeling_log({
            'step': 'error_handling',
            'timestamp': str(pd.Timestamp.now()),
            'error_type': 'CustomDataError',
            'message': str(e)
        })
        logger.error(f"Data cleaning failed: {e}")
        sys.exit(1)
    except Exception as e:
        # Catch-all for unexpected errors
        update_modeling_log({
            'step': 'error_handling',
            'timestamp': str(pd.Timestamp.now()),
            'error_type': type(e).__name__,
            'message': str(e)
        })
        logger.error(f"Unexpected error during data cleaning: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
