"""
Ingestion pipeline for environmental and fungal community data.
Handles downloading, validation, metadata harmonization, and ontology mapping.
"""

import os
import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import pandas as pd
import requests
from tqdm import tqdm

# Local imports
from ..utils.logging import get_logger
from ..utils.checksums import verify_checksum, compute_checksum
from ..models.schemas import EnvironmentalMatrix, ASVTable

logger = get_logger(__name__)

# Constants for ontology mapping
ONTOLOGY_MAP = {
    # Forest Biomes
    'temperate forest': 'Forest',
    'tropical forest': 'Forest',
    'boreal forest': 'Forest',
    'taiga': 'Forest',
    'deciduous forest': 'Forest',
    'coniferous forest': 'Forest',
    'rainforest': 'Forest',
    'cloud forest': 'Forest',
    
    # Grassland Biomes
    'temperate grassland': 'Grassland',
    'savanna': 'Grassland',
    'prairie': 'Grassland',
    'steppe': 'Grassland',
    'meadow': 'Grassland',
    
    # Agricultural
    'cropland': 'Agricultural',
    'farmland': 'Agricultural',
    'orchard': 'Agricultural',
    'vineyard': 'Agricultural',
    
    # Desert
    'desert': 'Desert',
    'arid land': 'Desert',
    'semi-arid': 'Desert',
    
    # Wetland
    'wetland': 'Wetland',
    'marsh': 'Wetland',
    'swamp': 'Wetland',
    'bog': 'Wetland',
    'fen': 'Wetland',
    
    # Tundra
    'tundra': 'Tundra',
    'alpine tundra': 'Tundra',
    
    # Urban
    'urban': 'Urban',
    'urban soil': 'Urban',
    'garden': 'Urban',
    
    # Other
    'rangeland': 'Rangeland',
    'shrubland': 'Shrubland',
    'scrubland': 'Shrubland',
}

def load_ontology_map(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load or return the default ontology mapping for biome labels.
    
    Args:
        config_path: Optional path to a custom ontology YAML file.
        
    Returns:
        Dictionary mapping raw biome labels to standardized categories.
    """
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                custom_map = yaml.safe_load(f)
                if custom_map:
                    return {k.lower(): v for k, v in custom_map.items()}
        except Exception as e:
            logger.warning(f"Failed to load custom ontology map from {config_path}: {e}")
    
    return ONTOLOGY_MAP.copy()

def map_biome_label(label: str, ontology_map: Dict[str, str]) -> str:
    """
    Map a raw biome label to a standardized category.
    
    Args:
        label: The raw biome label from the dataset.
        ontology_map: The mapping dictionary.
        
    Returns:
        Standardized biome category, or the original label if no mapping exists.
    """
    if pd.isna(label) or not isinstance(label, str):
        return 'Unknown'
    
    normalized = label.strip().lower()
    return ontology_map.get(normalized, label.strip())

def harmonize_biome_ontology(
    df: pd.DataFrame,
    biome_column: str = 'biome',
    output_column: str = 'standardized_biome',
    ontology_map: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Standardize biome labels in the environmental metadata DataFrame.
    
    This function applies ontology mapping to convert various biome names
    into standardized categories (e.g., 'Temperate Forest' -> 'Forest').
    
    Args:
        df: Input DataFrame containing environmental metadata.
        biome_column: Name of the column containing raw biome labels.
        output_column: Name of the new column for standardized labels.
        ontology_map: Optional custom mapping dictionary.
        
    Returns:
        DataFrame with new standardized_biome column added.
        
    Raises:
        ValueError: If the specified biome column does not exist.
    """
    if biome_column not in df.columns:
        raise ValueError(f"Biome column '{biome_column}' not found in DataFrame. "
                       f"Available columns: {list(df.columns)}")
    
    if ontology_map is None:
        ontology_map = load_ontology_map()
    
    # Apply mapping
    df[output_column] = df[biome_column].apply(
        lambda x: map_biome_label(x, ontology_map)
    )
    
    # Log transformation summary
    original_counts = df[biome_column].value_counts()
    standardized_counts = df[output_column].value_counts()
    
    logger.info(f"Biome ontology mapping complete:")
    logger.info(f"  Original unique labels: {len(original_counts)}")
    logger.info(f"  Standardized unique categories: {len(standardized_counts)}")
    
    # Log specific transformations for audit trail
    transformed = df[df[biome_column] != df[output_column]]
    if len(transformed) > 0:
        logger.info(f"  Transformed {len(transformed)} rows:")
        for orig, std in zip(transformed[biome_column], transformed[output_column]):
            logger.debug(f"    '{orig}' -> '{std}'")
    
    return df

def validate_and_clean_metadata(
    metadata_path: str,
    required_columns: List[str] = None,
    biome_column: str = 'biome'
) -> pd.DataFrame:
    """
    Load, validate, and clean environmental metadata with ontology mapping.
    
    Args:
        metadata_path: Path to the metadata CSV file.
        required_columns: List of required columns (default: standard environmental columns).
        biome_column: Column name containing biome information.
        
    Returns:
        Cleaned DataFrame with standardized biome labels.
    """
    if required_columns is None:
        required_columns = ['sample_id', 'biome', 'pH', 'temperature', 
                          'moisture', 'organic_carbon', 'nitrogen', 'phosphorus']
    
    # Load metadata
    logger.info(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    
    # Validate required columns
    missing = set(required_columns) - set(df.columns)
    if missing:
        logger.warning(f"Missing required columns: {missing}. "
                     f"Proceeding with available columns: {list(df.columns)}")
    
    # Apply ontology mapping to biome labels
    df = harmonize_biome_ontology(df, biome_column=biome_column)
    
    # Basic cleaning
    df = df.dropna(subset=['sample_id'])
    df['sample_id'] = df['sample_id'].astype(str).str.strip()
    
    # Convert numeric columns where possible
    numeric_cols = ['pH', 'temperature', 'moisture', 'organic_carbon', 'nitrogen', 'phosphorus']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Metadata validation complete: {len(df)} samples processed")
    return df

def process_harmonized_metadata(
    input_path: str,
    output_path: str,
    biome_column: str = 'biome'
) -> Dict[str, Any]:
    """
    Main entry point for processing environmental metadata with ontology mapping.
    
    This function:
    1. Loads raw metadata
    2. Validates structure
    3. Applies biome ontology mapping
    4. Saves cleaned output
    
    Args:
        input_path: Path to input metadata CSV.
        output_path: Path to save cleaned metadata CSV.
        biome_column: Column containing raw biome labels.
        
    Returns:
        Dictionary with processing statistics.
    """
    logger.info(f"Starting metadata harmonization pipeline")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Process metadata
    df = validate_and_clean_metadata(input_path, biome_column=biome_column)
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized metadata to {output_path}")
    
    # Generate summary statistics
    stats = {
        'total_samples': len(df),
        'unique_biomes': df['standardized_biome'].nunique(),
        'biome_distribution': df['standardized_biome'].value_counts().to_dict(),
        'missing_values': df.isnull().sum().to_dict()
    }
    
    logger.info(f"Processing complete. Statistics: {stats}")
    return stats

# Example usage for testing
if __name__ == "__main__":
    # Test the ontology mapping functionality
    test_data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'biome': ['Temperate Forest', 'Tropical Rainforest', 'Savanna', 'Desert', 'Unknown Biome'],
        'pH': [6.5, 5.8, 7.2, 8.1, 6.0]
    }
    df_test = pd.DataFrame(test_data)
    
    print("Original data:")
    print(df_test)
    print("\nAfter ontology mapping:")
    
    result = harmonize_biome_ontology(df_test, biome_column='biome')
    print(result[['biome', 'standardized_biome']])
    
    print("\nBiome distribution:")
    print(result['standardized_biome'].value_counts())