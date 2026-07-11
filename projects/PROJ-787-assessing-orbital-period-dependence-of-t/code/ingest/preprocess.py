import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure we can import from the project root if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging_config import get_logger, log_ingestion_summary
from utils.config import get_config

logger = get_logger("ingest.preprocess")

def load_merged_catalogs(merged_path: Path) -> pd.DataFrame:
    """
    Load the merged catalog from disk.
    """
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged catalog not found at {merged_path}")
    logger.info("Loading merged catalog from %s", merged_path)
    return pd.read_csv(merged_path)

def filter_planets(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Filter planets based on uncertainty criteria and missing stellar parameters.
    
    Criteria:
    - radius uncertainty < 20%
    - period uncertainty < 1%
    - stellar effective temperature (teff) must not be missing
    
    Returns:
      Tuple of (filtered_df, exclusion_reasons)
    """
    logger.info("Starting planet filtering...")
    total = len(df)
    exclusion_reasons = {
        "missing_radius_uncert": 0,
        "missing_period_uncert": 0,
        "missing_teff": 0,
        "radius_uncert_too_high": 0,
        "period_uncert_too_high": 0,
    }

    # Calculate relative uncertainties if not present, assuming raw columns exist
    # Expected columns: radius, radius_uncert, period, period_uncert, teff
    
    # Check for missing critical columns first
    if "radius_uncert" not in df.columns or "radius" not in df.columns:
        raise ValueError("DataFrame missing radius columns")
    if "period_uncert" not in df.columns or "period" not in df.columns:
        raise ValueError("DataFrame missing period columns")
    if "teff" not in df.columns:
        raise ValueError("DataFrame missing teff column")

    # Identify rows with missing critical data
    mask_missing_radius_uncert = df["radius_uncert"].isna() | (df["radius"] == 0)
    mask_missing_period_uncert = df["period_uncert"].isna() | (df["period"] == 0)
    mask_missing_teff = df["teff"].isna()

    exclusion_reasons["missing_radius_uncert"] = int(mask_missing_radius_uncert.sum())
    exclusion_reasons["missing_period_uncert"] = int(mask_missing_period_uncert.sum())
    exclusion_reasons["missing_teff"] = int(mask_missing_teff.sum())

    # Calculate relative uncertainties
    df = df.copy()
    df["rel_radius_uncert"] = np.where(
        df["radius"] != 0, df["radius_uncert"] / df["radius"], np.nan
    )
    df["rel_period_uncert"] = np.where(
        df["period"] != 0, df["period_uncert"] / df["period"], np.nan
    )

    # Apply filters
    mask_good_radius_uncert = df["rel_radius_uncert"] < 0.20
    mask_good_period_uncert = df["rel_period_uncert"] < 0.01

    exclusion_reasons["radius_uncert_too_high"] = int(
        (~mask_good_radius_uncert & ~mask_missing_radius_uncert).sum()
    )
    exclusion_reasons["period_uncert_too_high"] = int(
        (~mask_good_period_uncert & ~mask_missing_period_uncert).sum()
    )

    # Combined mask for valid rows
    valid_mask = (
        ~mask_missing_radius_uncert
        & ~mask_missing_period_uncert
        & ~mask_missing_teff
        & mask_good_radius_uncert
        & mask_good_period_uncert
    )

    filtered_df = df[valid_mask].copy()
    
    # Clean up temporary columns
    filtered_df.drop(columns=["rel_radius_uncert", "rel_period_uncert"], inplace=True, errors="ignore")

    log_ingestion_summary(
        logger,
        stage="Filtering",
        total_input=total,
        excluded_count=total - len(filtered_df),
        reasons=exclusion_reasons,
    )

    return filtered_df, exclusion_reasons

def resolve_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Resolve duplicates by keeping the entry with the lowest radius uncertainty.
    
    Assumes 'kepler_id' or 'kic_id' is the unique identifier.
    We use 'kic_id' as the primary key for duplication check based on typical Kepler data.
    """
    logger.info("Resolving duplicates...")
    total = len(df)
    
    # Identify the ID column
    id_col = "kic_id" if "kic_id" in df.columns else "kepler_id"
    if id_col not in df.columns:
        raise ValueError("No KIC or Kepler ID column found for duplicate resolution")

    # Sort by radius uncertainty to keep the best one first
    # Handle NaNs by pushing them to the end
    df_sorted = df.sort_values(by="radius_uncert", na_position="last")
    
    # Drop duplicates, keeping the first (lowest uncertainty)
    before_count = len(df_sorted)
    deduped_df = df_sorted.drop_duplicates(subset=[id_col], keep="first")
    after_count = len(deduped_df)
    
    removed_count = before_count - after_count
    
    logger.info("Found %d duplicate %s entries.", removed_count, id_col)
    logger.info("Kept %d unique entries.", after_count)
    
    return deduped_df, removed_count

def save_filtered_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the filtered DataFrame to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Saving filtered data to %s", output_path)
    df.to_csv(output_path, index=False)
    logger.info("Saved %d rows to %s", len(df), output_path)

def main() -> None:
    """
    Main entry point for the preprocessing pipeline.
    Orchestrates loading, filtering, deduplication, and saving.
    """
    config = get_config()
    base_dir = Path(config.get("paths", {}).get("base_dir", "."))
    
    # Paths
    merged_path = base_dir / "data" / "raw" / "merged_catalog.csv" # Assumed output from T013
    filtered_path = base_dir / "data" / "processed" / "filtered_planets.csv"
    deduped_path = base_dir / "data" / "processed" / "deduped_planets.csv"

    # Ensure directories exist
    filtered_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load
        df = load_merged_catalogs(merged_path)
        
        # 2. Filter
        df_filtered, _ = filter_planets(df)
        save_filtered_data(df_filtered, filtered_path)
        
        # 3. Deduplicate
        df_deduped, _ = resolve_duplicates(df_filtered)
        save_filtered_data(df_deduped, deduped_path)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.exception("Preprocessing pipeline failed: %s", e)
        raise

if __name__ == "__main__":
    main()