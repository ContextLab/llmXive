"""
Output Writer Module for HEA Pipeline.

Handles writing processed features to CSV and source metadata to YAML.
Implements FR-009: Dynamic generation of source_metadata.yaml.
"""
import os
import sys
import logging
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.utils.logging_config import get_logger
from src.utils.seeds import get_seed

# Ensure the code directory is in the path for imports if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(code_root))

logger = get_logger(__name__)

def write_processed_features(df: pd.DataFrame, output_path: str) -> None:
    """
    Writes the processed features DataFrame to a CSV file.
    
    Args:
        df: The processed DataFrame containing features and targets.
        output_path: The relative path from project root where the CSV will be saved.
    
    Raises:
        FileNotFoundError: If the directory for output_path does not exist.
        IOError: If writing the file fails.
    """
    full_path = Path(output_path)
    
    # Ensure directory exists
    if not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {full_path.parent}")
    
    # Check for NaN values before writing (critical for T011/T012)
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        logger.warning(f"DataFrame contains NaN values before writing to {output_path}:")
        for col, count in null_counts[null_counts > 0].items():
            logger.warning(f"  Column '{col}': {count} NaNs")
        # Depending on strictness, one might raise here, but the task implies
        # we are writing the result of the pipeline which should ideally be clean.
        # We log the warning and proceed, as the pipeline logic (T017/T018) 
        # should have handled this.
    
    try:
        df.to_csv(full_path, index=False)
        logger.info(f"Successfully wrote processed features to {output_path} "
                    f"({len(df)} rows, {len(df.columns)} columns)")
    except Exception as e:
        logger.error(f"Failed to write CSV to {output_path}: {e}")
        raise

def write_source_metadata(
    output_path: str,
    sources: List[Dict[str, Any]],
    pipeline_params: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None
) -> None:
    """
    Writes the source metadata to a YAML file (FR-009).
    
    This function dynamically generates the metadata file recording:
    - API versions
    - Query parameters
    - Timestamps
    - Sample counts
    - Random seed used
    
    Args:
        output_path: The relative path from project root for the YAML file.
        sources: List of dictionaries containing metadata for each data source 
               (e.g., OQMD, Materials Project). Each dict should have keys like 
               'source_name', 'query_params', 'api_version', 'timestamp', 'record_count'.
        pipeline_params: Optional dictionary of global pipeline parameters (e.g., seeds, filters).
        run_id: Optional unique identifier for this run.
    
    Raises:
        IOError: If writing the file fails.
    """
    full_path = Path(output_path)
    
    if not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created metadata output directory: {full_path.parent}")
    
    current_time = datetime.utcnow().isoformat()
    seed_val = get_seed()
    
    metadata = {
        "generated_at": current_time,
        "run_id": run_id or f"run_{int(time.time())}",
        "random_seed": seed_val,
        "pipeline_version": "1.0.0", # Should be read from config if available
        "data_sources": sources,
        "pipeline_parameters": pipeline_params or {
            "composition_filter": ">=5_elements",
            "target_type": "residual_bulk_modulus"
        }
    }
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Successfully wrote source metadata to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write YAML metadata to {output_path}: {e}")
        raise

def main():
    """
    Command-line interface for testing the output writer module.
    Expected usage: python -m src.pipeline.output_writer
    """
    # Setup basic logging for CLI usage
    init_default_logging()
    
    logger.info("Running output_writer module in test mode.")
    
    # Create a dummy DataFrame to simulate pipeline output
    dummy_data = {
        "composition": ["FeCoNiCrMn", "FeCoNiCrAl"],
        "bulk_modulus_observed": [150.0, 145.0],
        "bulk_modulus_miedema": [140.0, 135.0],
        "bulk_modulus_residual": [10.0, 10.0],
        "ilr_element_1": [0.1, 0.2],
        "ilr_element_2": [0.3, 0.4],
        "mixing_enthalpy_miedema": [-5.0, -4.0],
        "atomic_radius_variance_miedema": [0.02, 0.03],
        "electronegativity_variance_miedema": [0.1, 0.15]
    }
    df = pd.DataFrame(dummy_data)
    
    # Define output paths relative to project root
    csv_path = "data/processed/hea_features.csv"
    yaml_path = "data/source_metadata.yaml"
    
    # Mock source metadata
    mock_sources = [
        {
            "source_name": "OQMD",
            "query_params": {"elements": ">=5", "modulus": "bulk"},
            "api_version": "2023.10",
            "timestamp": datetime.utcnow().isoformat(),
            "record_count": 120
        },
        {
            "source_name": "Materials Project",
            "query_params": {"elements": ">=5", "modulus": "bulk"},
            "api_version": "v2023.09",
            "timestamp": datetime.utcnow().isoformat(),
            "record_count": 85
        }
    ]
    
    try:
        write_processed_features(df, csv_path)
        write_source_metadata(yaml_path, mock_sources)
        logger.info("Test mode completed successfully.")
    except Exception as e:
        logger.error(f"Test mode failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()