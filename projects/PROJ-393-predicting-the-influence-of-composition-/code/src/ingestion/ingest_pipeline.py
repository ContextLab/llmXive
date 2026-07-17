"""
Ingestion Pipeline Orchestration for Heusler Alloy Data.

This module orchestrates the fetching, parsing, and saving of raw data
from multiple sources (NIST, Journal Supplements, Manual Curation) into
a unified raw dataset with checksums.

Dependencies:
- T016: nist_fetcher
- T017: journal_supplement_parser
- T018: manual_curator
- T009: checksums
- T008: logging_config
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import from project API surface
from src.ingestion.nist_fetcher import fetch_nist_data
from src.ingestion.journal_supplement_parser import parse_journal_supplements
from src.ingestion.manual_curator import load_manual_curated_data
from src.utils.checksums import generate_raw_data_checksums, save_checksums_to_json
from src.utils.logging_config import setup_logging, log_checksum
from src.utils.schema_validator import validate_csv_file

# Configure logging
logger = setup_logging("ingest_pipeline")


def load_sources(
    nist_url: str,
    journal_dois: List[str],
    manual_csv_path: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Load data from all configured sources.

    Args:
        nist_url: URL for NIST Materials Data Repository.
        journal_dois: List of DOIs for journal supplements.
        manual_csv_path: Path to manual curated CSV file.

    Returns:
        Dictionary mapping source names to DataFrames.
    """
    sources_data = {}

    # 1. Fetch NIST Data
    logger.info(f"Fetching NIST data from {nist_url}...")
    try:
        nist_df = fetch_nist_data(nist_url)
        if nist_df is not None and not nist_df.empty:
            nist_df['source_name'] = 'NIST'
            sources_data['nist'] = nist_df
            logger.info(f"NIST fetch successful: {len(nist_df)} entries.")
        else:
            logger.warning("NIST fetch returned empty or None. Skipping.")
    except Exception as e:
        logger.error(f"Failed to fetch NIST data: {e}")
        # Fail loudly on NIST if it's the primary source, or log and continue if fallback exists
        # Per T016 spec: fallback to manual if API fails. Here we just log.
        # If NIST is critical and fails, the pipeline might produce an empty dataset.
        # We proceed to try other sources.

    # 2. Parse Journal Supplements
    logger.info(f"Parsing {len(journal_dois)} journal supplements...")
    try:
        journal_dfs = parse_journal_supplements(journal_dois)
        if journal_dfs:
            sources_data['journal_supplements'] = pd.concat(journal_dfs, ignore_index=True)
            sources_data['journal_supplements']['source_name'] = 'Journal Supplement'
            logger.info(f"Journal parsing successful: {len(sources_data['journal_supplements'])} entries.")
        else:
            logger.warning("No data found in journal supplements.")
    except Exception as e:
        logger.error(f"Failed to parse journal supplements: {e}")

    # 3. Load Manual Curated Data
    if manual_csv_path and manual_csv_path.exists():
        logger.info(f"Loading manual curated data from {manual_csv_path}...")
        try:
            manual_df = load_manual_curated_data(manual_csv_path)
            if manual_df is not None and not manual_df.empty:
                manual_df['source_name'] = 'Manual Curation'
                sources_data['manual'] = manual_df
                logger.info(f"Manual load successful: {len(manual_df)} entries.")
            else:
                logger.warning("Manual curated file is empty.")
        except Exception as e:
            logger.error(f"Failed to load manual curated data: {e}")
    else:
        logger.warning(f"Manual curated file not found at {manual_csv_path}. Skipping.")

    return sources_data


def merge_and_save(
    sources_data: Dict[str, pd.DataFrame],
    output_path: Path
) -> pd.DataFrame:
    """
    Merge all source DataFrames and save to a single CSV.

    Args:
        sources_data: Dictionary of source DataFrames.
        output_path: Path to save the combined CSV.

    Returns:
        The combined DataFrame.
    """
    if not sources_data:
        raise ValueError("No data sources loaded. Cannot merge.")

    logger.info(f"Merging {len(sources_data)} data sources...")
    combined_df = pd.concat(
        [df.reset_index(drop=True) for df in sources_data.values()],
        ignore_index=True
    )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Combined dataset saved to {output_path} with {len(combined_df)} rows.")

    return combined_df


def run_ingestion_pipeline(
    nist_url: str,
    journal_dois: List[str],
    manual_csv_path: Path,
    output_dir: Path,
    schema_path: Optional[Path] = None
) -> Path:
    """
    Execute the full ingestion pipeline: fetch, merge, save, validate, checksum.

    Args:
        nist_url: NIST data URL.
        journal_dois: List of journal DOIs.
        manual_csv_path: Path to manual CSV.
        output_dir: Directory to save raw data.
        schema_path: Optional path to schema for validation.

    Returns:
        Path to the generated raw CSV file.
    """
    logger.info("Starting Ingestion Pipeline...")
    start_time = datetime.now()

    output_file = output_dir / "alloys_raw_combined.csv"

    # Step 1: Load Data
    sources_data = load_sources(nist_url, journal_dois, manual_csv_path)

    if not sources_data:
        raise RuntimeError("Ingestion Pipeline failed: No data was retrieved from any source.")

    # Step 2: Merge and Save
    combined_df = merge_and_save(sources_data, output_file)

    # Step 3: Validate (if schema provided)
    if schema_path:
        logger.info(f"Validating output against schema {schema_path}...")
        try:
            is_valid = validate_csv_file(output_file, schema_path)
            if not is_valid:
                logger.warning("Data validation against schema failed.")
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
    else:
        logger.info("No schema provided for validation.")

    # Step 4: Generate Checksums
    logger.info("Generating checksums...")
    checksums = generate_raw_data_checksums(output_dir)
    checksum_file = output_dir / "checksums.json"
    save_checksums_to_json(checksums, checksum_file)
    log_checksum(logger, "raw_data", str(checksum_file))

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Ingestion Pipeline completed in {duration:.2f} seconds.")
    logger.info(f"Output: {output_file}")
    logger.info(f"Checksums: {checksum_file}")

    return output_file


def main():
    """
    Entry point for running the ingestion pipeline.
    Expects configuration via environment variables or hardcoded defaults for demo.
    """
    # Configuration
    # Note: These should ideally be loaded from a config.yaml or env vars
    NIST_URL = "https://materials.nist.gov/api/v1/materials?query=Heusler" # Placeholder URL, actual API might differ
    JOURNAL_DOIS = [
        "10.1016/j.actamat.2020.01.001", # Example DOI
        "10.1016/j.jallcom.2019.152000"  # Example DOI
    ]
    MANUAL_CSV = Path("data/raw/manual_curated.csv")
    OUTPUT_DIR = Path("data/raw")

    # Check if manual file exists for the run
    if not MANUAL_CSV.exists():
        logger.warning(f"Manual file {MANUAL_CSV} not found. Pipeline will rely on NIST/Journal.")

    try:
        run_ingestion_pipeline(
            nist_url=NIST_URL,
            journal_dois=JOURNAL_DOIS,
            manual_csv_path=MANUAL_CSV,
            output_dir=OUTPUT_DIR
        )
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        raise


if __name__ == "__main__":
    main()