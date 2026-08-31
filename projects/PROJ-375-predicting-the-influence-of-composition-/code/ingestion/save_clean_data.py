"""
Save cleaned metallic glass dataset to Parquet with checksum manifest.

This module implements T022: Save cleaned dataset to `data/processed/clean_mg_data.parquet`
with checksum manifest using `compute_sha256` from T005a.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.io import compute_sha256, setup_logging
from utils.config import get_env_var
from features.dataset_models import validate_entry_to_model, MetallicGlassEntry

# Configure logging
logger = setup_logging()

def load_intermediate_data(raw_data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load intermediate data from the ingestion pipeline.
    
    T013-T015 should have produced intermediate CSV/Parquet files in data/raw/.
    We look for the most recent intermediate file or the one named 'intermediate_mg_data.csv'.
    
    Returns:
        pd.DataFrame: The loaded data.
    
    Raises:
        FileNotFoundError: If no intermediate data is found.
        ValueError: If the data is empty or invalid.
    """
    if raw_data_dir is None:
        raw_data_dir = project_root / "data" / "raw"
    
    raw_data_dir = Path(raw_data_dir)
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    # Look for intermediate files
    candidates = list(raw_data_dir.glob("intermediate_mg_data.*"))
    if not candidates:
        # Try to find any CSV or Parquet that might be the intermediate result
        candidates = list(raw_data_dir.glob("*.csv")) + list(raw_data_dir.glob("*.parquet"))
    
    if not candidates:
        raise FileNotFoundError(
            f"No intermediate data found in {raw_data_dir}. "
            "Ensure T013-T015 (fetch_data.py) has run successfully."
        )
    
    # Sort by modification time, take the most recent
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_file = candidates[0]
    
    logger.info(f"Loading intermediate data from: {latest_file}")
    
    if latest_file.suffix == ".csv":
        df = pd.read_csv(latest_file)
    elif latest_file.suffix == ".parquet":
        df = pd.read_parquet(latest_file)
    else:
        raise ValueError(f"Unsupported file format: {latest_file.suffix}")
    
    if df.empty:
        raise ValueError("Intermediate data is empty. Check ingestion pipeline.")
    
    logger.info(f"Loaded {len(df)} rows from {latest_file.name}")
    return df

def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the dataset according to the schema.
    
    - Ensure required columns exist
    - Filter out rows with missing critical values
    - Validate against MetallicGlassEntry model
    
    Args:
        df: Input DataFrame from intermediate data.
    
    Returns:
        Cleaned and validated DataFrame.
    
    Raises:
        ValueError: If validation fails.
    """
    required_columns = [
        "composition", "cte", "weighted_mean_atomic_radius",
        "electronegativity_variance", "vec", "atomic_size_mismatch",
        "amorphous_state_flag", "alloy_family", "source"
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for amorphous entries only (per T015)
    if "amorphous_state_flag" in df.columns:
        # Assume 1 or True indicates amorphous
        df = df[df["amorphous_state_flag"].isin([1, True, "amorphous", "Amorphous"])]
        logger.info(f"Filtered to amorphous entries: {len(df)} rows remaining")
    
    # Drop rows with missing critical values (CTE, composition)
    critical_cols = ["composition", "cte", "weighted_mean_atomic_radius"]
    df = df.dropna(subset=critical_cols)
    logger.info(f"After dropping missing values: {len(df)} rows remaining")
    
    if df.empty:
        raise ValueError("No valid entries after cleaning. Check data quality.")
    
    # Validate each row against the model (optional but recommended)
    valid_rows = []
    for idx, row in df.iterrows():
        try:
            # Convert row to dict and validate
            entry_dict = row.to_dict()
            # Ensure types are correct for Pydantic
            if isinstance(entry_dict.get("amorphous_state_flag"), str):
                entry_dict["amorphous_state_flag"] = (
                    entry_dict["amorphous_state_flag"].lower() == "amorphous"
                )
            validate_entry_to_model(entry_dict)
            valid_rows.append(row)
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to validation error: {e}")
    
    if not valid_rows:
        raise ValueError("No valid rows passed model validation.")
    
    cleaned_df = pd.DataFrame(valid_rows)
    logger.info(f"Validation complete: {len(cleaned_df)} valid rows")
    
    return cleaned_df

def save_parquet_and_manifest(df: pd.DataFrame, output_path: Path) -> str:
    """
    Save DataFrame to Parquet and generate a checksum manifest.
    
    Args:
        df: Cleaned DataFrame.
        output_path: Path to save the Parquet file.
    
    Returns:
        str: The SHA256 checksum of the saved file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved cleaned data to: {output_path}")
    
    # Compute checksum
    checksum = compute_sha256(str(output_path))
    logger.info(f"Checksum computed: {checksum}")
    
    # Generate manifest
    manifest = {
        "file": output_path.name,
        "path": str(output_path),
        "sha256": checksum,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "source": "ingestion_pipeline_T013-T015",
        "task_id": "T022"
    }
    
    manifest_path = output_path.with_suffix(".json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to: {manifest_path}")
    return checksum

def write_manifest(manifest: dict, output_path: Path) -> None:
    """
    Write a manifest file for the saved dataset.
    
    Args:
        manifest: Dictionary containing metadata about the dataset.
        output_path: Path to save the manifest JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written to: {output_path}")

def main() -> None:
    """
    Main entry point for T022: Save cleaned dataset.
    
    This function orchestrates the loading, cleaning, and saving of the
    metallic glass dataset, generating a checksum manifest.
    """
    try:
        # Define paths
        output_dir = project_root / "data" / "processed"
        output_file = output_dir / "clean_mg_data.parquet"
        
        logger.info("Starting T022: Save cleaned dataset")
        logger.info(f"Output path: {output_file}")
        
        # Load intermediate data
        df = load_intermediate_data()
        
        # Clean and validate
        cleaned_df = clean_and_validate(df)
        
        # Save to Parquet and generate manifest
        checksum = save_parquet_and_manifest(cleaned_df, output_file)
        
        logger.info(f"T022 completed successfully. Checksum: {checksum}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation/cleaning error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()