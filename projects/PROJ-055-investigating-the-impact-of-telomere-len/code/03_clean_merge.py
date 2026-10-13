import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# --------------------------------------------------------------
# Configuration handling
# --------------------------------------------------------------
from config import get_config, set_random_seed

_config = get_config()

# Apply random seed for any stochastic operations in cleaning/merging
if "random_seed" in _config:
    try:
        set_random_seed(int(_config["random_seed"]))
    except Exception as e:
        logging.warning(f"Could not set random seed from config: {e}")

# Configuration values that may affect cleaning logic
ALPHA_THRESHOLD = _config.get("alpha", 0.05)

# --------------------------------------------------------------
# Public API (unchanged signatures)
# --------------------------------------------------------------
def load_ingested_data(telomere_path: Path, anage_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw telomere and AnAge ecological data from disk.
    """
    tel_df = pd.read_csv(telomere_path)
    anage_df = pd.read_csv(anage_path)
    return tel_df, anage_df

def filter_wild_caught_early_life(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataframe for wild‑caught and early‑life individuals.
    Records not matching the criteria are logged to `logs/unconvertible_units.csv`.
    """
    # Expected column names; be tolerant if they differ
    origin_col = "origin" if "origin" in df.columns else "source_type"
    life_stage_col = "life_stage" if "life_stage" in df.columns else "stage"

    mask = (df[origin_col] == "wild") & (df[life_stage_col] == "juvenile")
    filtered = df[mask].copy()
    excluded = df[~mask]
    if not excluded.empty:
        log_path = Path("logs") / "wild_caught_filter_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        excluded.to_csv(log_path, index=False)
    return filtered

def convert_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all telomere units to kilobases (kb).
    Unconvertible rows are logged to `logs/unconvertible_units.csv`.
    """
    from clean import clean_telomere_units, convert_to_kb

    df_clean = clean_telomere_units(df, unit_col="unit", value_col="telomere_length")
    # Apply conversion
    def _convert(row):
        try:
            return convert_to_kb(row["telomere_length"], row["unit"])
        except Exception:
            return None

    df_clean["telomere_length_kb"] = df_clean.apply(_convert, axis=1)
    # Separate rows where conversion failed
    unconvertible = df_clean[df_clean["telomere_length_kb"].isna()]
    if not unconvertible.empty:
        log_path = Path("logs") / "unconvertible_units.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        unconvertible.to_csv(log_path, index=False)
    # Keep only successfully converted rows
    return df_clean.dropna(subset=["telomere_length_kb"])

def merge_data(telomere_df: pd.DataFrame, anage_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join telomere data with AnAge ecological data on species name.
    Unmatched records are logged to `logs/missing_data_log.csv`.
    """
    merged = pd.merge(
        telomere_df,
        anage_df,
        left_on="species_name",
        right_on="species_name",
        how="inner",
    )
    # Identify species present in one dataframe but not the other
    tel_species = set(telomere_df["species_name"].unique())
    anage_species = set(anage_df["species_name"].unique())
    missing = (tel_species ^ anage_species)
    if missing:
        log_path = Path("logs") / "missing_data_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"species_name": list(missing)}).to_csv(log_path, index=False)
    return merged

def validate_output_schema(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Validate that the output dataframe meets the schema requirements.
    """
    # Load the schema
    from jsonschema import validate, ValidationError
    schema_path = Path("contracts") / "dataset.schema.yaml"
    import yaml

    with schema_path.open() as f:
        schema = yaml.safe_load(f)

    # Convert DataFrame to records for validation
    records = df.to_dict(orient="records")
    try:
        for rec in records:
            validate(instance=rec, schema=schema)
        return True
    except ValidationError as e:
        logging.error(f"Schema validation error: {e}")
        return False

def main() -> None:
    """
    Main entry point for the cleaning and merging pipeline.
    """
    raw_dir = Path("data") / "raw"
    # Load all CSV files that are not the AnAge file
    tel_files = [p for p in raw_dir.glob("*.csv") if p.name != "anage_birds.csv"]
    if not tel_files:
        print("No raw telomere CSV files found. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Concatenate all telomere datasets
    tel_dfs = [pd.read_csv(p) for p in tel_files]
    tel_df = pd.concat(tel_dfs, ignore_index=True)

    anage_path = raw_dir / "anage_birds.csv"
    if not anage_path.is_file():
        print("AnAge data not found. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Load AnAge data
    anage_df = pd.read_csv(anage_path)

    # --------------------------------------------------------------
    # Cleaning steps
    # --------------------------------------------------------------
    tel_df = filter_wild_caught_early_life(tel_df)
    tel_df = convert_units(tel_df)

    # Write the unit‑standardised intermediate file
    standardized_path = Path("data") / "processed" / "telomere_standardized.csv"
    standardized_path.parent.mkdir(parents=True, exist_ok=True)
    tel_df.to_csv(standardized_path, index=False)

    # --------------------------------------------------------------
    # Merge with ecological covariates
    # --------------------------------------------------------------
    merged_df = merge_data(tel_df, anage_df)

    # Collapse to one row per species (mean telomere length)
    merged_df = (
        merged_df.groupby("species_name")
        .agg(
            {
                "telomere_length_kb": "mean",
                "max_lifespan_years": "first",
                "migration_status": "first",
                "body_mass_g": "first",
            }
        )
        .reset_index()
    )
    merged_df = merged_df.rename(
        columns={
            "species_name": "species",
            "max_lifespan_years": "lifespan",
        }
    )

    # Write final analysis dataset
    output_path = Path("data") / "processed" / "merged_analysis.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)

    # Validate against schema
    if not validate_output_schema(merged_df, output_path):
        sys.exit(1)

    # The pipeline orchestrator will handle state hash updates.

if __name__ == "__main__":
    main()
