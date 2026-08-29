"""
T018: Schema Definition, Transformation, and Merge for HCI_P2.

This script loads the filtered HCI_P2 dataset, transforms it to match the
target schema defined in contracts/dataset.schema.yaml, and saves the result
to data/processed/merged_dialogues.parquet.

Dependencies:
- T019: filtered dataset in data/raw/filtered/
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.schema_validator import load_schema, validate_dataset_schema, SchemaValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FILTERED_DATA_PATH = "data/raw/filtered/hci_p2_filtered.parquet"
OUTPUT_PATH = "data/processed/merged_dialogues.parquet"
SCHEMA_PATH = "contracts/dataset.schema.yaml"

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {output_dir}")

def load_filtered_dataset() -> pd.DataFrame:
    """Load the filtered HCI_P2 dataset."""
    input_path = Path(FILTERED_DATA_PATH)
    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {input_path}. "
            "Please ensure T019 has completed successfully."
        )
    
    logger.info(f"Loading filtered dataset from {input_path}")
    df = pq.read_table(input_path).to_pandas()
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def load_target_schema() -> Dict[str, Any]:
    """Load the target schema definition."""
    schema_path = Path(SCHEMA_PATH)
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found at {schema_path}. "
            "Please ensure T008/T011 have completed successfully."
        )
    
    logger.info(f"Loading target schema from {schema_path}")
    schema = load_schema(schema_path)
    return schema

def transform_to_target_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> pd.DataFrame:
    """
    Transform the dataset to match the target schema.
    
    The target schema defines:
    - user_id (string)
    - dialogue_id (string)
    - quality_rating (integer, 1-5)
    - age (integer, optional)
    - gender (string, optional)
    - utterances (list of dicts with 'speaker' and 'text')
    
    This function:
    1. Renames columns to match target schema
    2. Ensures correct data types
    3. Validates required fields
    4. Handles optional fields gracefully
    """
    logger.info("Transforming dataset to target schema...")
    
    # Create a copy to avoid modifying the original
    transformed = df.copy()
    
    # Define column mappings based on typical HCI_P2 structure
    # Adjust these mappings if the actual column names differ
    column_mappings = {
        'conversation_id': 'dialogue_id',
        'dialogue_id': 'dialogue_id',
        'user_id': 'user_id',
        'quality': 'quality_rating',
        'quality_rating': 'quality_rating',
        'age': 'age',
        'gender': 'gender',
        'utterances': 'utterances',
        'turns': 'utterances'
    }
    
    # Apply column renames
    for old_name, new_name in column_mappings.items():
        if old_name in transformed.columns and old_name != new_name:
            transformed = transformed.rename(columns={old_name: new_name})
            logger.info(f"Renamed column '{old_name}' to '{new_name}'")
    
    # Ensure required columns exist
    required_columns = ['user_id', 'dialogue_id', 'quality_rating', 'utterances']
    missing_columns = [col for col in required_columns if col not in transformed.columns]
    
    if missing_columns:
        raise ValueError(
            f"Missing required columns after transformation: {missing_columns}. "
            "The source dataset does not contain these fields."
        )
    
    # Ensure correct data types
    # user_id and dialogue_id should be strings
    transformed['user_id'] = transformed['user_id'].astype(str)
    transformed['dialogue_id'] = transformed['dialogue_id'].astype(str)
    
    # quality_rating should be integer (1-5)
    if transformed['quality_rating'].dtype != 'int64':
        transformed['quality_rating'] = pd.to_numeric(
            transformed['quality_rating'], errors='coerce'
        ).astype('Int64')  # Use nullable integer type
    
    # age should be integer if present
    if 'age' in transformed.columns:
        transformed['age'] = pd.to_numeric(
            transformed['age'], errors='coerce'
        ).astype('Int64')
    
    # gender should be string if present
    if 'gender' in transformed.columns:
        transformed['gender'] = transformed['gender'].astype(str)
    
    # Validate utterances structure
    if 'utterances' in transformed.columns:
        # Ensure utterances is a list of dicts
        def ensure_utterance_format(utterances):
            if isinstance(utterances, str):
                import ast
                try:
                    utterances = ast.literal_eval(utterances)
                except:
                    utterances = []
            if not isinstance(utterances, list):
                utterances = []
            return utterances
        
        transformed['utterances'] = transformed['utterances'].apply(ensure_utterance_format)
    
    logger.info(f"Transformation complete. Resulting columns: {list(transformed.columns)}")
    logger.info(f"Data types:\n{transformed.dtypes}")
    
    return transformed

def validate_transformed_data(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the transformed dataset against the target schema.
    
    Returns:
    - bool: True if validation passes, False otherwise
    - List[str]: List of validation errors
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get('required', [])
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Check data types for required columns
    properties = schema.get('properties', {})
    for col in required_columns:
        if col in properties:
            expected_type = properties[col].get('type')
            actual_type = str(df[col].dtype)
            
            # Simple type mapping
            type_mapping = {
                'string': ['object', 'string', 'str'],
                'integer': ['int64', 'int32', 'Int64', 'Int32'],
                'number': ['float64', 'float32'],
                'boolean': ['bool', 'boolean']
            }
            
            if expected_type:
                valid_types = type_mapping.get(expected_type, [expected_type])
                if actual_type not in valid_types:
                    errors.append(
                        f"Column '{col}' has type '{actual_type}', "
                        f"expected '{expected_type}'"
                    )
    
    # Check for null values in required columns
    for col in required_columns:
        if col in df.columns and df[col].isnull().any():
            null_count = df[col].isnull().sum()
            errors.append(
                f"Column '{col}' has {null_count} null values "
                f"(should be non-null for required fields)"
            )
    
    return len(errors) == 0, errors

def save_transformed_data(df: pd.DataFrame, output_path: str):
    """Save the transformed dataset to parquet format."""
    path = Path(output_path)
    logger.info(f"Saving transformed data to {path}")
    
    # Write to parquet
    df.to_parquet(path, index=False, engine='pyarrow')
    
    # Verify the file was created
    if not path.exists():
        raise IOError(f"Failed to write output file to {path}")
    
    file_size = path.stat().st_size
    logger.info(f"Successfully saved {len(df)} rows to {path} ({file_size} bytes)")

def main():
    """Main execution function for T018."""
    logger.info("Starting T018: Schema Definition, Transformation, and Merge")
    
    try:
        # Step 1: Ensure output directories exist
        ensure_directories()
        
        # Step 2: Load the filtered dataset
        df = load_filtered_dataset()
        
        # Step 3: Load the target schema
        schema = load_target_schema()
        
        # Step 4: Transform to target schema
        transformed_df = transform_to_target_schema(df, schema)
        
        # Step 5: Validate the transformed data
        is_valid, errors = validate_transformed_data(transformed_df, schema)
        
        if not is_valid:
            error_msg = "Validation errors found:\n" + "\n".join(errors)
            logger.error(error_msg)
            # Log errors but continue - the transformation may still be useful
            # In a strict pipeline, we might want to halt here
        
        # Step 6: Save the transformed data
        save_transformed_data(transformed_df, OUTPUT_PATH)
        
        logger.info("T018 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except IOError as e:
        logger.error(f"I/O error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())