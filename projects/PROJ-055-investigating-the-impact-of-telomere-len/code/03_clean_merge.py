"""
03_clean_merge.py

Loads the raw telomere CSVs and the AnAge ecological CSV, applies
filtering, unit conversion and merges the datasets into the final
analysis file ``data/processed/merged_analysis.csv``.
"""

import sys
import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
import yaml

from clean import clean_telomere_units, convert_to_kb

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
CONFIG_PATH = Path("code") / "config.yaml"

def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_cfg = load_config()
RANDOM_SEED = int(_cfg.get("random_seed", 42))
ALPHA_THRESHOLD = float(_cfg.get("alpha", 0.05))

# Set seed for reproducibility (used by any stochastic steps)
import random
random.seed(RANDOM_SEED)
try:
    import numpy as np
    np.random.seed(RANDOM_SEED)
except ImportError:
    pass

# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def load_ingested_data(telomere_path: Path, anage_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    tel_df = pd.read_csv(telomere_path)
    anage_df = pd.read_csv(anage_path)
    return tel_df, anage_df

def filter_wild_caught_early_life(df: pd.DataFrame) -> pd.DataFrame:
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
    df_clean = clean_telomere_units(df, unit_col="unit", value_col="telomere_length")
    def _convert(row):
        try:
            return convert_to_kb(row["telomere_length"], row["unit"])
        except Exception:
            return None
    df_clean["telomere_length_kb"] = df_clean.apply(_convert, axis=1)
    unconvertible = df_clean[df_clean["telomere_length_kb"].isna()]
    if not unconvertible.empty:
        log_path = Path("logs") / "unconvertible_units.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        unconvertible.to_csv(log_path, index=False)
    return df_clean.dropna(subset=["telomere_length_kb"])

def merge_data(telomere_df: pd.DataFrame, anage_df: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        telomere_df,
        anage_df,
        left_on="species_name",
        right_on="species_name",
        how="inner",
    )
    tel_species = set(telomere_df["species_name"].unique())
    anage_species = set(anage_df["species_name"].unique())
    missing = tel_species.symmetric_difference(anage_species)
    if missing:
        log_path = Path("logs") / "missing_data_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"species_name": list(missing)}).to_csv(log_path, index=False)
    return merged

def validate_output_schema(df: pd.DataFrame, output_path: Path) -> bool:
    from jsonschema import validate, ValidationError
    import yaml
    schema_path = Path("contracts") / "dataset.schema.yaml"
    with schema_path.open() as f:
        schema = yaml.safe_load(f)
    records = df.to_dict(orient="records")
    try:
        for rec in records:
            validate(instance=rec, schema=schema)
        return True
    except ValidationError as e:
        logging.error(f"Schema validation error: {e}")
        return False

def main() -> None:
    raw_dir = Path("data") / "raw"
    tel_files = [p for p in raw_dir.glob("*.csv") if p.name != "anage_birds.csv"]
    if not tel_files:
        print("No raw telomere CSV files found. Exiting.", file=sys.stderr)
        sys.exit(1)

    tel_dfs = [pd.read_csv(p) for p in tel_files]
    tel_df = pd.concat(tel_dfs, ignore_index=True)

    anage_path = raw_dir / "anage_birds.csv"
    if not anage_path.is_file():
        print("AnAge data not found. Exiting.", file=sys.stderr)
        sys.exit(1)

    anage_df = pd.read_csv(anage_path)

    # Cleaning
    tel_df = filter_wild_caught_early_life(tel_df)
    tel_df = convert_units(tel_df)

    # Save intermediate standardized file
    std_path = Path("data") / "processed" / "telomere_standardized.csv"
    std_path.parent.mkdir(parents=True, exist_ok=True)
    tel_df.to_csv(std_path, index=False)

    # Merge
    merged_df = merge_data(tel_df, anage_df)

    # Collapse to one row per species (mean values)
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

    output_path = Path("data") / "processed" / "merged_analysis.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)

    if not validate_output_schema(merged_df, output_path):
        sys.exit(1)

if __name__ == "__main__":
    main()
