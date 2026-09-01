import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

# Import from local project structure
from utils.logging import get_logger
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, CONTRACTS_DIR

logger = get_logger(__name__)

def load_halo_data(source_path: str) -> pd.DataFrame:
    """
    Load halo data from a Parquet or HDF5 file.
    
    Args:
        source_path: Path to the source data file.
        
    Returns:
        pandas DataFrame containing halo data.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source data file not found: {source_path}")
    
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix in ['.h5', '.hdf5']:
        return pd.read_hdf(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def filter_halos_by_particles(df: pd.DataFrame, min_particles: int = 300) -> pd.DataFrame:
    """
    Filter halos to retain only those with >= min_particles.
    
    Args:
        df: Input DataFrame.
        min_particles: Minimum number of particles required.
        
    Returns:
        Filtered DataFrame.
    """
    total_count = len(df)
    # Handle potential column name variations
    particle_col = 'particle_count' if 'particle_count' in df.columns else 'num_particles'
    
    if particle_col not in df.columns:
        logger.warning(f"Column '{particle_col}' not found in DataFrame. Using 'num_particles' as fallback if available.")
        particle_col = 'num_particles'
        
    if particle_col not in df.columns:
        raise ValueError("Neither 'particle_count' nor 'num_particles' column found in DataFrame.")
        
    filtered_df = df[df[particle_col] >= min_particles].reset_index(drop=True)
    filtered_count = len(filtered_df)
    
    logger.info(f"Filtered halos: {total_count} -> {filtered_count} (min_particles={min_particles})")
    
    if filtered_count == 0:
        logger.warning("No halos passed the particle count filter.")
        
    return filtered_df

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a YAML file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary representing the schema.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
        
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate a DataFrame against a JSON schema.
    
    This function converts the DataFrame to a list of dictionaries and validates
    each row against the provided schema using the jsonschema library.
    
    Args:
        df: DataFrame to validate.
        schema: JSON schema dictionary.
        
    Returns:
        True if validation passes.
        
    Raises:
        jsonschema.ValidationError: If validation fails.
        jsonschema.SchemaError: If the schema itself is invalid.
    """
    try:
        import jsonschema
    except ImportError:
        raise ImportError("jsonschema library is required for schema validation. Install with: pip install jsonschema")

    # Convert DataFrame to list of dicts
    # We validate row by row to get specific error messages
    records = df.to_dict('records')
    
    # Ensure required fields exist in schema
    required_fields = schema.get('required', [])
    schema_properties = schema.get('properties', {})
    
    # Quick check: ensure all required fields are present in the DataFrame columns
    df_columns = set(df.columns)
    missing_required = [f for f in required_fields if f not in df_columns]
    if missing_required:
        raise ValueError(f"DataFrame missing required fields: {missing_required}")

    logger.info(f"Validating {len(records)} records against schema...")
    
    errors_found = False
    error_count = 0
    
    for i, record in enumerate(records):
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            if not errors_found:
                logger.error(f"Schema validation failed at row {i}: {e.message}")
                logger.error(f"Path: {list(e.path)}")
                logger.error(f"Schema path: {list(e.schema_path)}")
            errors_found = True
            error_count += 1
            # Only log the first few errors to avoid spam
            if error_count >= 5:
                logger.warning(f"Stopping detailed error logging after {error_count} errors.")
                break
    
    if errors_found:
        raise jsonschema.ValidationError(f"Schema validation failed for {error_count} rows.")
        
    logger.info(f"Schema validation successful for all {len(records)} records.")
    return True

def stream_write_parquet(df: pd.DataFrame, output_path: str, chunk_size: int = 10000) -> None:
    """
    Write DataFrame to Parquet file in chunks.
    
    Args:
        df: DataFrame to write.
        output_path: Path to the output Parquet file.
        chunk_size: Number of rows per chunk.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    total_rows = len(df)
    logger.info(f"Writing {total_rows} rows to {output_path} in chunks of {chunk_size}")
    
    # Write in chunks using pyarrow
    table = pa.Table.from_pandas(df)
    
    # Write the entire table at once if it fits, otherwise use chunked writer
    # pyarrow.parquet.ParquetWriter handles chunking internally for large datasets
    # but for explicit control we can use the writer directly
    with pq.ParquetWriter(path, table.schema) as writer:
        # If the table is small, just write it
        if total_rows <= chunk_size:
            writer.write_table(table)
        else:
            # Write in chunks
            for i in range(0, total_rows, chunk_size):
                chunk = table.slice(i, chunk_size)
                writer.write_table(chunk)
                
    logger.info(f"Successfully wrote {total_rows} rows to {output_path}")

def run_preprocessing_pipeline(
    input_path: str,
    output_dir: Optional[str] = None,
    min_particles: int = 300,
    schema_path: Optional[str] = None
) -> str:
    """
    Run the full preprocessing pipeline: load, filter, validate, and write.
    
    Args:
        input_path: Path to input data file.
        output_dir: Directory for output files. Defaults to DATA_PROCESSED_DIR.
        min_particles: Minimum particles for filtering.
        schema_path: Path to schema file. If None, validation is skipped.
        
    Returns:
        Path to the output Parquet file.
    """
    start_time = time.time()
    output_dir = output_dir or str(DATA_PROCESSED_DIR)
    
    logger.info(f"Starting preprocessing pipeline for {input_path}")
    
    # 1. Load data
    logger.info("Loading data...")
    df = load_halo_data(input_path)
    logger.info(f"Loaded {len(df)} halos")
    
    # 2. Filter data
    logger.info(f"Filtering halos with >= {min_particles} particles...")
    df_filtered = filter_halos_by_particles(df, min_particles)
    
    # 3. Validate against schema if provided
    if schema_path:
        logger.info(f"Validating against schema: {schema_path}")
        schema = load_schema(schema_path)
        validate_schema(df_filtered, schema)
    else:
        logger.warning("No schema provided. Skipping validation.")
        
    # 4. Write output
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_halos_{timestamp}.parquet"
    output_path = os.path.join(output_dir, output_filename)
    
    logger.info(f"Writing filtered data to {output_path}")
    stream_write_parquet(df_filtered, output_path)
    
    elapsed = time.time() - start_time
    logger.info(f"Preprocessing pipeline completed in {elapsed:.2f} seconds")
    logger.info(f"Output: {output_path}")
    
    return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run halo data preprocessing pipeline")
    parser.add_argument("--input", type=str, required=True, help="Input data file path")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--min-particles", type=int, default=300, help="Minimum particles per halo")
    parser.add_argument("--schema", type=str, default=None, help="Schema file path for validation")
    
    args = parser.parse_args()
    
    run_preprocessing_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        min_particles=args.min_particles,
        schema_path=args.schema
    )
