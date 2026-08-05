import os
import sys
import logging
import yaml
import pandas as pd
from pathlib import Path

# Import utilities from sibling module
from utils import log_setup, checksum_file, causal_language_scanner

# Import config constants
from config import DATA_ROOT, RESULTS_ROOT, RANDOM_SEED

def load_schema_contract(schema_path: str) -> dict:
    """Load and return the dataset schema contract."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(data: pd.DataFrame, schema: dict) -> bool:
    """Validate that the dataframe matches the expected schema columns."""
    required_cols = schema.get('required_columns', [])
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        logging.error(f"Missing required columns: {missing}")
        return False
    return True

def parse_raw_file(input_path: str) -> pd.DataFrame:
    """Parse raw CSV file into a dataframe."""
    logging.info(f"Parsing raw file: {input_path}")
    try:
        df = pd.read_csv(input_path)
        logging.info(f"Raw file parsed: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logging.error(f"Failed to parse raw file: {e}")
        raise

def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """Compute switching_index = num_platforms * self_reported_switching_frequency."""
    logging.info("Engineering switching_index variable")
    required_cols = ['num_platforms', 'self_reported_switching_frequency']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        logging.error(f"Missing required columns for engineering: {missing}")
        # Attempt to handle missing columns if they exist in alternative names
        # For now, strictly enforce schema
        raise ValueError(f"Cannot engineer switching_index. Missing: {missing}")
    
    df['switching_index'] = df['num_platforms'] * df['self_reported_switching_frequency']
    logging.info(f"switching_index computed. Range: [{df['switching_index'].min()}, {df['switching_index'].max()}]")
    return df

def handle_missing_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing outcomes by excluding rows and logging exclusion count."""
    outcome_col = 'cognitive_flexibility_score'
    if outcome_col not in df.columns:
        logging.warning(f"Outcome column '{outcome_col}' not found. Skipping missing value handling.")
        return df
    
    initial_count = len(df)
    df_clean = df.dropna(subset=[outcome_col])
    excluded_count = initial_count - len(df_clean)
    
    if excluded_count > 0:
        logging.info(f"Excluded {excluded_count} rows due to missing {outcome_col} data.")
    else:
        logging.info("No rows excluded due to missing outcome data.")
        
    return df_clean

def validate_and_save(df: pd.DataFrame, schema: dict, output_path: str):
    """Validate dataframe against schema and save to disk."""
    logging.info(f"Validating engineered dataframe against schema...")
    if not validate_schema_structure(df, schema):
        raise ValueError("Schema validation failed after engineering")
    
    logging.info(f"Saving engineered data to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Engineered data saved successfully. Total rows: {len(df)}")

def main():
    """Main entry point for variable engineering."""
    # Setup logging as per T020 requirement
    logger = log_setup(level=logging.INFO, destination='stdout')
    
    logging.info("Starting variable engineering pipeline")
    
    # Define paths
    schema_path = "contracts/dataset.schema.yaml"
    processed_dir = Path(DATA_ROOT) / "processed"
    output_dir = Path(DATA_ROOT) / "processed"
    
    input_file = processed_dir / "participants_cleaned.csv"
    if not input_file.exists():
        logging.error(f"Input file {input_file} not found. Run ingestion first.")
        sys.exit(1)
    
    # Load schema
    try:
        schema = load_schema_contract(schema_path)
        logging.info("Schema contract loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Parse raw data
    df = parse_raw_file(str(input_file))
    
    # Engineer variables
    df = engineer_switching_index(df)
    
    # Handle missing outcomes
    df = handle_missing_outcomes(df)
    
    # Validate and save
    output_file = output_dir / "participants_cleaned.csv"
    validate_and_save(df, schema, str(output_file))
    
    logging.info("Variable engineering pipeline completed successfully")

if __name__ == "__main__":
    main()
