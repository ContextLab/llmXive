import os
import sys
import logging
import json
import argparse
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import yaml
import jsonschema

from zenodo_client import DataUnavailableError, DataInsufficientError, download_csv_from_zenodo
from resource_monitor import limit_resources

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

def parse_composition_string(comp_str: Any) -> Optional[Dict[str, float]]:
    """
    Parses composition strings (e.g., 'Zr50Cu40Al10') or JSON strings 
    into a dictionary of atomic fractions.
    """
    if not comp_str or pd.isna(comp_str):
        return None
    
    if isinstance(comp_str, dict):
        return comp_str

    # Try JSON first
    if isinstance(comp_str, str) and (comp_str.startswith('{') and comp_str.endswith('}')):
        try:
            return json.loads(comp_str.replace("'", '"'))
        except json.JSONDecodeError:
            pass

    # Try regex for 'Zr50Cu40Al10' format
    if isinstance(comp_str, str):
        pattern = re.compile(r'([A-Z][a-z]?)(\d+(?:\.\d+)?)')
        matches = pattern.findall(comp_str)
        if matches:
            total = sum(float(count) for _, count in matches)
            if total > 0:
                return {symbol: float(count)/total for symbol, count in matches}
    
    return None

def validate_and_clean_chunk(chunk: pd.DataFrame, schema: Dict, source_doi: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Validates a chunk of data against the schema and cleans it.
    """
    processed_rows = []
    
    for idx, row in chunk.iterrows():
        row_dict = row.to_dict()
        
        # 1. Tg value check (FR-001)
        tg = row_dict.get('tg_value')
        if pd.isna(tg) or tg is None:
            continue
        
        # 2. Composition check (FR-001)
        elements_raw = row_dict.get('elements')
        elements_parsed = parse_composition_string(elements_raw)
        if not elements_parsed:
            continue
        
        row_dict['elements'] = elements_parsed

        # 3. Metadata enrichment
        row_dict['source'] = source_doi
        row_dict['status'] = 'valid'
        if 'record_id' not in row_dict or pd.isna(row_dict['record_id']):
            row_dict['record_id'] = str(idx)
        
        # Infer family from primary element if missing
        if 'family' not in row_dict or pd.isna(row_dict['family']):
            primary_el = max(elements_parsed, key=elements_parsed.get)
            row_dict['family'] = f"{primary_el}-based"

        # 4. Schema validation
        try:
            jsonschema.validate(instance=row_dict, schema=schema)
            processed_rows.append(row_dict)
        except jsonschema.ValidationError as ve:
            logger.debug(f"Row {idx} failed schema validation: {ve.message}")
            continue

    return pd.DataFrame(processed_rows)

@limit_resources(cpu_limit=2 * 3600, ram_limit=7 * 1024)
def run_ingestion() -> None:
    """Execute the full ingestion pipeline."""
    logger = setup_logging()
    project_root = get_project_root()

    primary_doi = "10.5281/zenodo.10043838"
    fallback_doi = "10.5281/zenodo.11023456"

    # 1. Fetch raw data
    data_dir = project_root / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    used_doi = primary_doi
    raw_path = data_dir / "metallic_glass_raw.csv"
    
    try:
        download_csv_from_zenodo(primary_doi, raw_path)
        logger.info(f"Successfully fetched primary DOI: {primary_doi}")
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}. Attempting fallback...")
        used_doi = fallback_doi
        try:
            download_csv_from_zenodo(fallback_doi, raw_path)
            logger.info(f"Successfully fetched fallback DOI: {fallback_doi}")
        except DataUnavailableError as fe:
            logger.error("Both primary and fallback DOIs are unavailable.")
            raise DataUnavailableError("Both primary and fallback DOIs are unavailable.") from fe

    # 2. Load Schema
    schema_path = project_root / "specs" / "001-predicting-the-influence-of-alloying-on" / "contracts" / "dataset.schema.yaml"
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Could not load schema at {schema_path}: {e}")
        raise

    # 3. Stream, Validate and Clean
    cleaned_path = project_root / "data" / "processed" / "cleaned_data.csv"
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    
    raw_count = 0
    cleaned_count = 0
    first_chunk = True
    
    try:
        # Use chunksize=1000 to stay within RAM budget
        reader = pd.read_csv(raw_path, chunksize=1000)
        for chunk in reader:
            raw_count += len(chunk)
            
            # Normalize column names to match schema (Tg -> tg_value)
            if 'Tg' in chunk.columns and 'tg_value' not in chunk.columns:
                chunk = chunk.rename(columns={'Tg': 'tg_value'})
            
            cleaned_chunk = validate_and_clean_chunk(chunk, schema, used_doi, logger)
            cleaned_count += len(cleaned_chunk)
            
            mode = 'w' if first_chunk else 'a'
            header = True if first_chunk else False
            cleaned_chunk.to_csv(cleaned_path, index=False, mode=mode, header=header)
            first_chunk = False
    except Exception as e:
        logger.error(f"Error during streaming processing: {e}")
        raise

    if cleaned_count == 0:
        raise DataInsufficientError("No valid records remained after cleaning.")

    # 4. Emit Statistics
    retention_rate = cleaned_count / raw_count if raw_count > 0 else 0.0
    stats = {
        "source_doi": used_doi,
        "raw_count": raw_count,
        "cleaned_count": cleaned_count,
        "retention_rate": retention_rate
    }
    stats_path = project_root / "data" / "ingestion_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Ingestion complete. Source: {used_doi}, Raw: {raw_count}, Cleaned: {cleaned_count}, Rate: {retention_rate:.2%}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Metallic-glass data ingestion")
    parser.add_argument("--verify-only", action="store_true", help="Verify data availability without writing processed files.")
    args, _ = parser.parse_known_args()

    if args.verify_only:
        logger = setup_logging()
        project_root = get_project_root()
        primary_doi = "10.5281/zenodo.10043838"
        fallback_doi = "10.5281/zenodo.11023456"
        data_dir = project_root / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        raw_path = data_dir / "metallic_glass_raw.csv"
        try:
            download_csv_from_zenodo(primary_doi, raw_path)
            logger.info("Primary DOI verification successful.")
        except DataUnavailableError:
            raw_path = data_dir / "metallic_glass_raw.csv"
            try:
                download_csv_from_zenodo(fallback_doi, raw_path)
                logger.info("Fallback DOI verification successful.")
            except DataUnavailableError as e:
                logger.error(f"Verification failed: {e}")
                sys.exit(1)
    else:
        run_ingestion()

if __name__ == "__main__":
    main()
