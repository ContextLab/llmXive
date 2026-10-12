# NOTE: The original ``code/ingest.py`` file is retained unchanged except for
# a small import adjustment to ensure the logger is configured before any
# module‑level code runs.  Additionally, the CLI argument parser now tolerates
# unexpected trailing arguments (e.g., when the quick‑start chain is passed as a
# single command) by using ``parse_known_args``.  No functional changes are
# required because the robust Zenodo client implemented in ``code/zenodo_client.py``
# now correctly retrieves the dataset.

import os
import sys
import logging
import json
import hashlib
import time
import argparse
from pathlib import Path
from typing import Tuple

import pandas as pd
import yaml
import jsonschema

from zenodo_client import DataUnavailableError, DataInsufficientError, fetch_from_zenodo
from resource_monitor import limit_resources

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """Configure logging for the ingest module."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "ingest.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return Path(__file__).resolve().parent.parent

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_tg_range(df: pd.DataFrame) -> bool:
    """Check if Tg values are within a reasonable range (50 K – 2000 K)."""
    if 'Tg' not in df.columns:
        return False
    valid_tg = df['Tg'].dropna()
    if valid_tg.empty:
        return False
    return valid_tg.min() > 50 and valid_tg.max() < 2000

# ----------------------------------------------------------------------
# Data fetching
# ----------------------------------------------------------------------
def fetch_from_zenodo_wrapper(primary_doi: str, fallback_doi: str) -> Tuple[pd.DataFrame, str]:
    """
    Fetch data from Zenodo. Try primary DOI first, then fallback.
    Returns (DataFrame, used_doi).
    """
    logger = logging.getLogger(__name__)
    data_dir = get_project_root() / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)

    primary_path = data_dir / f"zenodo_{primary_doi.split('.')[-1]}.csv"
    fallback_path = data_dir / f"zenodo_{fallback_doi.split('.')[-1]}.csv"

    # 1️⃣ Check local cache for primary
    if primary_path.exists():
        logger.info(f"Primary file found locally: {primary_path}")
        try:
            df = pd.read_csv(primary_path)
            if validate_tg_range(df) and not df.empty:
                return df, primary_doi
            else:
                logger.warning("Local primary file invalid – will re‑fetch.")
        except Exception as e:
            logger.warning(f"Error reading primary cache: {e} – will re‑fetch.")

    # 2️⃣ Check local cache for fallback
    if fallback_path.exists():
        logger.info(f"Fallback file found locally: {fallback_path}")
        try:
            df = pd.read_csv(fallback_path)
            if validate_tg_range(df) and not df.empty:
                logger.warning("FALLBACK_USED: Using cached fallback data.")
                return df, fallback_doi
            else:
                logger.warning("Local fallback file invalid – will re‑fetch.")
        except Exception as e:
            logger.warning(f"Error reading fallback cache: {e} – will re‑fetch.")

    # 3️⃣ Attempt remote fetch – primary first
    logger.info(f"Attempting to fetch from Zenodo DOI: {primary_doi}")
    try:
        df = fetch_from_zenodo(primary_doi)
        df.to_csv(primary_path, index=False)
        logger.info(f"Primary DOI data saved to {primary_path}")
        return df, primary_doi
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}")

    # 4️⃣ Fallback fetch
    logger.info(f"Attempting fallback DOI: {fallback_doi}")
    try:
        df = fetch_from_zenodo(fallback_doi)
        df.to_csv(fallback_path, index=False)
        logger.warning("FALLBACK_USED: Fallback DOI succeeded.")
        return df, fallback_doi
    except DataUnavailableError as e:
        raise DataUnavailableError("Both primary and fallback DOIs are unavailable.") from e

# ----------------------------------------------------------------------
# Validation & cleaning
# ----------------------------------------------------------------------
def load_and_validate_data(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, float, int, int]:
    """
    Validate and clean the raw dataframe.
    Returns cleaned DataFrame, retention_rate, raw_count, cleaned_count.
    """
    if df.empty:
        raise DataInsufficientError("Dataset is empty.")

    if 'Tg' not in df.columns and 'tg_value' in df.columns:
        df = df.rename(columns={'tg_value': 'Tg'})

    # Ensure a composition column exists; build from ``elements`` if needed.
    if 'composition' not in df.columns and 'elements' in df.columns:
        def elements_to_comp(elem):
            if isinstance(elem, dict):
                parts = []
                for sym, frac in sorted(elem.items()):
                    # Convert fraction (0‑1) to percentage with one decimal.
                    parts.append(f"{sym}{frac * 100:.1f}")
                return "".join(parts)
            return ""
        df['composition'] = df['elements'].apply(elements_to_comp)

    raw_count = len(df)

    # Drop rows missing Tg or composition
    df_clean = df.dropna(subset=['Tg'])
    if 'composition' in df_clean.columns:
        df_clean = df_clean.dropna(subset=['composition'])

    cleaned_count = len(df_clean)
    retention_rate = cleaned_count / raw_count if raw_count else 0.0

    logger.info(
        f"Raw rows: {raw_count}, Cleaned rows: {cleaned_count}, "
        f"Retention rate: {retention_rate:.2%}"
    )

    # -----------------------------------------------------------------
    # Schema validation per row (does not discard rows, only logs)
    # -----------------------------------------------------------------
    schema_path = (
        get_project_root()
        / "specs"
        / "001-predicting-the-influence-of-alloying-on"
        / "contracts"
        / "dataset.schema.yaml"
    )
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load dataset schema at {schema_path}: {e}")
        schema = None

    if schema is not None:
        for idx, row in df_clean.iterrows():
            row_dict = {k: row[k] for k in row.index if pd.notnull(row[k])}
            try:
                jsonschema.validate(instance=row_dict, schema=schema)
            except jsonschema.ValidationError as ve:
                logger.warning(f"Schema validation failed for row {idx}: {ve.message}")
            except jsonschema.SchemaError as se:
                logger.error(f"Invalid schema definition: {se}")
                break

    if cleaned_count == 0:
        raise DataInsufficientError("All rows were dropped during cleaning.")

    return df_clean, retention_rate, raw_count, cleaned_count

def save_cleaned_data(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Write the cleaned dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def write_ingestion_stats(
    source_doi: str,
    retention_rate: float,
    raw_count: int,
    cleaned_count: int,
    project_root: Path
) -> None:
    """Write ingestion statistics JSON."""
    stats = {
        "source_doi": source_doi,
        "retention_rate": retention_rate,
        "raw_count": raw_count,
        "cleaned_count": cleaned_count
    }
    stats_path = project_root / "data" / "ingestion_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    logging.getLogger(__name__).info(f"Ingestion stats written to {stats_path}")

# ----------------------------------------------------------------------
# Compatibility helpers for the test suite
# ----------------------------------------------------------------------
def clean_data(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Thin wrapper used by older tests – returns only the cleaned DataFrame.
    """
    cleaned_df, _, _, _ = load_and_validate_data(df, logger)
    return cleaned_df

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
@limit_resources(cpu_limit=2 * 3600, ram_limit=7 * 1024)
def run_ingestion() -> None:
    """Execute the full ingestion pipeline."""
    logger = setup_logging()
    project_root = get_project_root()

    primary_doi = "10.5281/zenodo.10043838"
    fallback_doi = "10.5281/zenodo.11023456"

    # 1️⃣ Fetch raw data (will raise if both DOIs are unavailable)
    df, used_doi = fetch_from_zenodo_wrapper(primary_doi, fallback_doi)
    logger.info(f"Data fetched from DOI: {used_doi}")

    # 2️⃣ Validate & clean
    df_clean, retention, raw_cnt, clean_cnt = load_and_validate_data(df, logger)

    # 3️⃣ Persist cleaned data
    cleaned_path = project_root / "data" / "processed" / "cleaned_mg.csv"
    save_cleaned_data(df_clean, cleaned_path, logger)

    # 4️⃣ Record statistics
    write_ingestion_stats(used_doi, retention, raw_cnt, clean_cnt, project_root)

    logger.info("Ingestion pipeline completed successfully.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Metallic‑glass data ingestion")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Run the pipeline up to validation without writing output files."
    )
    # Use parse_known_args to tolerate stray arguments (e.g., when commands are chained)
    args, _ = parser.parse_known_args()

    if args.verify_only:
        # Run fetch + validation but skip writing files
        logger = setup_logging()
        primary_doi = "10.5281/zenodo.10043838"
        fallback_doi = "10.5281/zenodo.11023456"
        df, used_doi = fetch_from_zenodo_wrapper(primary_doi, fallback_doi)
        logger.info(f"[VERIFY ONLY] Data fetched from DOI: {used_doi}")
        # Validation (will raise on failure)
        _ = load_and_validate_data(df, logger)
        logger.info("[VERIFY ONLY] Validation passed.")
    else:
        run_ingestion()

if __name__ == "__main__":
    main()