import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import sys
import json
import logging
import os

# Import from local utils
from utils.logging import get_logger
from config import load_paths

# Initialize logger
logger = get_logger(__name__)

# Constants
CHUNK_SIZE = 10000  # Rows per chunk for memory efficiency
DESCRIPTOR_COLS = ['mean_electronegativity', 'variance_electronegativity',
                   'mean_radius', 'variance_radius',
                   'mean_valence', 'variance_valence',
                   'mean_melting_point', 'variance_melting_point',
                   'mean_ionization_energy', 'variance_ionization_energy']
FORMATION_ENERGY_COL = 'formation_energy_per_atom'

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the dataset schema from a YAML/JSON file."""
    with open(schema_path, 'r') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            import yaml
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate dataframe against schema. Returns (is_valid, errors)."""
    errors = []
    required_cols = schema.get('required_columns', [])
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Check for nulls in descriptor columns
    if 'descriptor_columns' in schema:
        for col in schema['descriptor_columns']:
            if col in df.columns and df[col].isnull().any():
                errors.append(f"Null values found in descriptor column: {col}")
    
    return len(errors) == 0, errors

def get_elemental_properties_df() -> pd.DataFrame:
    """Load elemental properties from pymatgen."""
    try:
        from pymatgen.core import Element
        from pymatgen.util.num import PeriodicTable
        
        # Get all elements
        elements = [Element(e) for e in Element.periodic_table]
        
        # Build dataframe
        data = []
        for el in elements:
            try:
                row = {
                    'element': el.symbol,
                    'electronegativity': el.electronegativity,
                    'radius': el.atomic_radius,
                    'valence': el.oxidation_states[0] if el.oxidation_states else 0,
                    'melting_point': el.melting_point,
                    'ionization_energy': el.ionization_energy
                }
                data.append(row)
            except Exception as e:
                logger.warning(f"Could not get properties for {el.symbol}: {e}")
                continue
        
        return pd.DataFrame(data)
    except ImportError:
        logger.error("pymatgen not installed. Please install it via pip install pymatgen")
        raise

def calculate_weighted_mean_variance(composition: Dict[str, float], 
                                     properties: pd.DataFrame, 
                                     prop_name: str) -> Tuple[float, float]:
    """
    Calculate weighted mean and variance for a given property based on composition.
    
    Args:
        composition: Dict mapping element symbol to fraction
        properties: DataFrame with element properties
        prop_name: Name of the property column
        
    Returns:
        Tuple of (weighted_mean, weighted_variance)
    """
    weighted_sum = 0.0
    weighted_sq_sum = 0.0
    total_fraction = 0.0
    
    for elem, frac in composition.items():
        if elem not in properties['element'].values:
            continue
        
        prop_val = properties[properties['element'] == elem][prop_name].values[0]
        weighted_sum += frac * prop_val
        weighted_sq_sum += frac * (prop_val ** 2)
        total_fraction += frac
    
    if total_fraction == 0:
        return np.nan, np.nan
    
    mean = weighted_sum / total_fraction
    variance = (weighted_sq_sum / total_fraction) - (mean ** 2)
    
    return mean, max(0, variance)  # Ensure non-negative variance

def compute_descriptors_row(row: pd.Series, properties_df: pd.DataFrame) -> pd.Series:
    """Compute descriptors for a single row."""
    try:
        # Parse composition string like "Li1.0Fe1.0O2.0" into dict
        composition_str = row['composition']
        composition = {}
        current_elem = ""
        current_num = ""
        
        for char in composition_str:
            if char.isupper():
                if current_elem:
                    if current_num:
                        composition[current_elem] = float(current_num)
                    current_elem = char
                    current_num = ""
                else:
                    current_elem = char
            elif char.islower():
                current_elem += char
            elif char.isdigit() or char == '.':
                current_num += char
            elif char == ' ':
                continue
            else:
                # Handle end of number
                if current_elem:
                    if current_num:
                        composition[current_elem] = float(current_num)
                    current_elem = ""
                    current_num = ""
        
        # Handle last element
        if current_elem:
            if current_num:
                composition[current_elem] = float(current_num)
        
        # Normalize fractions
        total = sum(composition.values())
        if total > 0:
            composition = {k: v/total for k, v in composition.items()}
        
        descriptors = {}
        for prop in ['electronegativity', 'radius', 'valence', 'melting_point', 'ionization_energy']:
            mean_val, var_val = calculate_weighted_mean_variance(composition, properties_df, prop)
            descriptors[f'mean_{prop}'] = mean_val
            descriptors[f'variance_{prop}'] = var_val
        
        # Create new row with descriptors
        new_row = row.copy()
        for key, val in descriptors.items():
            new_row[key] = val
        
        return new_row
    except Exception as e:
        logger.warning(f"Error computing descriptors for row: {e}")
        return None

def compute_descriptors_chunked(input_path: str, output_path: str, schema_path: str) -> bool:
    """
    Compute descriptors using chunked reading to handle large datasets.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        schema_path: Path to schema file
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting chunked descriptor computation for {input_path}")
    
    # Load properties once
    properties_df = get_elemental_properties_df()
    logger.info(f"Loaded {len(properties_df)} elemental properties")
    
    # Load schema for validation
    schema = load_schema(schema_path)
    
    # Create output directory if needed
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Process in chunks
    chunks = []
    total_rows = 0
    processed_rows = 0
    skipped_rows = 0
    
    for chunk in pd.read_csv(input_path, chunksize=CHUNK_SIZE):
        total_rows += len(chunk)
        logger.debug(f"Processing chunk of {len(chunk)} rows")
        
        valid_chunks = []
        for _, row in chunk.iterrows():
            try:
                new_row = compute_descriptors_row(row, properties_df)
                if new_row is not None:
                    # Check for NaN in descriptor columns
                    has_nan = False
                    for col in DESCRIPTOR_COLS:
                        if pd.isna(new_row.get(col, np.nan)):
                            has_nan = True
                            break
                    
                    if not has_nan:
                        valid_chunks.append(new_row)
                        processed_rows += 1
                    else:
                        skipped_rows += 1
                        logger.debug(f"Skipped row with missing descriptors: {row.get('composition', 'N/A')}")
            except Exception as e:
                skipped_rows += 1
                logger.warning(f"Error processing row: {e}")
        
        if valid_chunks:
            chunks.append(pd.DataFrame(valid_chunks))
    
    if not chunks:
        logger.error("No valid rows processed!")
        return False
    
    # Concatenate all chunks
    final_df = pd.concat(chunks, ignore_index=True)
    logger.info(f"Combined {len(final_df)} rows from {len(chunks)} chunks")
    
    # Validate against schema
    is_valid, errors = validate_schema(final_df, schema)
    if not is_valid:
        logger.warning(f"Schema validation failed: {errors}")
    
    # Save to output
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
    logger.info(f"Total rows: {total_rows}, Processed: {processed_rows}, Skipped: {skipped_rows}")
    
    return True

def detect_and_cap_outliers(df: pd.DataFrame, 
                            feature: str = FORMATION_ENERGY_COL, 
                            lower_percentile: float = 1.0, 
                            upper_percentile: float = 99.0) -> Tuple[pd.DataFrame, int]:
    """
    Detect and cap outliers in a specified feature column.
    
    Args:
        df: Input dataframe
        feature: Column name to process
        lower_percentile: Lower percentile bound
        upper_percentile: Upper percentile bound
        
    Returns:
        Tuple of (processed dataframe, count of capped rows)
    """
    logger.info(f"Detecting outliers in {feature} using {lower_percentile}-{upper_percentile} percentiles")
    
    if feature not in df.columns:
        logger.warning(f"Feature {feature} not found in dataframe")
        return df, 0
    
    lower_bound = df[feature].quantile(lower_percentile / 100.0)
    upper_bound = df[feature].quantile(upper_percentile / 100.0)
    
    logger.info(f"Lower bound: {lower_bound}, Upper bound: {upper_bound}")
    
    # Count outliers
    outliers = ((df[feature] < lower_bound) | (df[feature] > upper_bound)).sum()
    logger.info(f"Found {outliers} outliers")
    
    if outliers > 0:
        # Cap values
        df[feature] = df[feature].clip(lower=lower_bound, upper=upper_bound)
        logger.info(f"Capped {outliers} outlier values")
    
    return df, int(outliers)

def validate_final_dataset(df: pd.DataFrame, schema_path: str) -> bool:
    """Validate the final dataset against the schema."""
    schema = load_schema(schema_path)
    is_valid, errors = validate_schema(df, schema)
    
    if not is_valid:
        logger.error(f"Final dataset validation failed: {errors}")
        return False
    
    # Check for nulls in descriptor columns
    for col in DESCRIPTOR_COLS:
        if col in df.columns and df[col].isnull().any():
            logger.error(f"Null values found in {col}")
            return False
    
    logger.info("Final dataset validation passed")
    return True

def main():
    """Main entry point for descriptor computation."""
    paths = load_paths()
    input_path = paths['data_processed_sampled_raw']
    output_path = paths['data_processed_computed_descriptors']
    schema_path = paths['schema_dataset']
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    success = compute_descriptors_chunked(input_path, output_path, schema_path)
    
    if not success:
        logger.error("Descriptor computation failed")
        sys.exit(1)
    
    # Load and validate
    final_df = pd.read_csv(output_path)
    if not validate_final_dataset(final_df, schema_path):
        logger.error("Final validation failed")
        sys.exit(1)
    
    logger.info("Descriptor computation completed successfully")

if __name__ == "__main__":
    main()