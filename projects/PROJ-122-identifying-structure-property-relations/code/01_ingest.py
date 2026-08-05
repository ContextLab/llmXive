import os
import json
import logging
import sys
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import local utilities
from utils.logger import get_logger
from utils.schema_validator import load_schema, validate_output_file
from utils.checksum import compute_file_checksum
from utils.ingest_utils import is_valid_smiles, celsius_to_kelvin, pascal_to_gpa
from config import ensure_directories

# Initialize logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-122-identifying-structure-property-relations.yaml"

def fetch_with_backoff(url: str, max_retries: int = 5, initial_delay: float = 1.0, multiplier: float = 2.0) -> Optional[Dict]:
    """
    Fetches data from a URL with exponential backoff.
    Returns the parsed JSON data or None if all retries fail.
    """
    import requests
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay + random.uniform(0, 0.1))
                delay *= multiplier
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
    return None

def load_dataset_schema(schema_path: Optional[Path] = None) -> Dict:
    """
    Loads the dataset schema from a YAML file.
    Defaults to specs/001-structure-property-relationships/contracts/dataset.schema.yaml
    """
    if schema_path is None:
        schema_path = PROJECT_ROOT / "specs" / "001-structure-property-relationships" / "contracts" / "dataset.schema.yaml"
    return load_schema(schema_path)

def validate_ingested_data(record: Dict, schema: Dict) -> bool:
    """
    Validates a single record against the provided schema.
    """
    # Basic validation logic based on schema requirements
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in record:
            logger.debug(f"Record missing required field: {field}")
            return False
    return True

def detect_temperature_unit(value: float, source_context: str = "") -> str:
    """
    Heuristically detects if a temperature value is in Celsius or Kelvin.
    Assumes values < 200 are likely Celsius, >= 200 are Kelvin.
    """
    if value < 200:
        return "C"
    return "K"

def detect_pressure_unit(value: float, source_context: str = "") -> str:
    """
    Heuristically detects if a pressure/modulus value is in Pa, kPa, MPa, or GPa.
    Assumes values > 1e9 are GPa, > 1e6 are MPa, etc.
    """
    if value > 1e9:
        return "GPa"
    if value > 1e6:
        return "MPa"
    if value > 1e3:
        return "kPa"
    return "Pa"

def harmonize_temperature(value: float, detected_unit: str) -> float:
    """
    Converts temperature to Kelvin.
    """
    if detected_unit == "C":
        return celsius_to_kelvin(value)
    return value

def harmonize_modulus(value: float, detected_unit: str) -> float:
    """
    Converts modulus to GPa.
    """
    if detected_unit == "Pa":
        return value / 1e9
    if detected_unit == "kPa":
        return value / 1e6
    if detected_unit == "MPa":
        return value / 1e3
    return value

def harmonize_record(record: Dict) -> Dict:
    """
    Harmonizes a single record: converts units and validates SMILES.
    """
    # Temperature Harmonization
    if "tg_k" in record:
        unit = detect_temperature_unit(record["tg_k"])
        record["tg_k"] = harmonize_temperature(record["tg_k"], unit)
    
    # Modulus Harmonization
    if "modulus_gpa" in record:
        unit = detect_pressure_unit(record["modulus_gpa"])
        record["modulus_gpa"] = harmonize_modulus(record["modulus_gpa"], unit)

    # SMILES Validation
    if "smiles" in record and not is_valid_smiles(record["smiles"]):
        logger.warning(f"Invalid SMILES detected: {record['smiles']}")
        record["smiles_valid"] = False
    else:
        record["smiles_valid"] = True
    
    return record

def validate_and_exclude_invalid_records(records: List[Dict], schema: Dict) -> List[Dict]:
    """
    Validates records against schema and excludes invalid ones.
    """
    valid_records = []
    for record in records:
        if validate_ingested_data(record, schema):
            valid_records.append(record)
        else:
            logger.debug(f"Excluding invalid record: {record.get('id', 'unknown')}")
    return valid_records

def run_unit_harmonization_and_validation(raw_data_path: Path, output_path: Path) -> List[Dict]:
    """
    Main pipeline for harmonization and validation.
    """
    ensure_directories([output_path.parent])
    
    # Load raw data (assuming JSON for this example)
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    with open(raw_data_path, 'r') as f:
        raw_records = json.load(f)
    
    schema = load_dataset_schema()
    harmonized = [harmonize_record(r) for r in raw_records]
    valid_records = validate_and_exclude_invalid_records(harmonized, schema)
    
    with open(output_path, 'w') as f:
        json.dump(valid_records, f, indent=2)
    
    logger.info(f"Harmonization complete. {len(valid_records)} valid records saved to {output_path}")
    return valid_records

def generate_data_quality_report(data: List[Dict], report_path: Path) -> Dict:
    """
    Generates a data quality report based on the provided dataset.
    Calculates statistics on missing values, unit distributions, and validity flags.
    
    Args:
        data: List of processed records (harmonized and validated).
        report_path: Path to save the JSON report.
    
    Returns:
        Dictionary containing the report metrics.
    """
    if not data:
        logger.warning("No data provided for quality report generation.")
        return {"error": "No data provided"}

    total_records = len(data)
    valid_smiles_count = sum(1 for r in data if r.get("smiles_valid", False))
    invalid_smiles_count = total_records - valid_smiles_count
    
    # Check for missing key fields
    missing_tg = sum(1 for r in data if r.get("tg_k") is None)
    missing_modulus = sum(1 for r in data if r.get("modulus_gpa") is None)
    missing_composition = sum(1 for r in data if not r.get("composition"))
    
    # Unit distribution (heuristic based on original values if stored, otherwise assume harmonized)
    # Since we harmonized in place, we assume all are now K and GPa.
    # We can report the count of records that were successfully harmonized.
    
    report = {
        "report_generated_at": datetime.utcnow().isoformat(),
        "dataset_summary": {
            "total_records": total_records,
            "valid_records": total_records, # Assuming filtered list
            "valid_smiles_count": valid_smiles_count,
            "invalid_smiles_count": invalid_smiles_count,
            "smiles_validity_rate": valid_smiles_count / total_records if total_records > 0 else 0.0
        },
        "missing_data": {
            "missing_tg_k_count": missing_tg,
            "missing_modulus_gpa_count": missing_modulus,
            "missing_composition_count": missing_composition
        },
        "unit_harmonization": {
            "temperature_unit": "K (Harmonized)",
            "modulus_unit": "GPa (Harmonized)",
            "records_harmonized": total_records
        },
        "quality_metrics": {
            "completeness_score": (total_records - missing_tg - missing_modulus - missing_composition) / total_records if total_records > 0 else 0.0,
            "validity_score": valid_smiles_count / total_records if total_records > 0 else 0.0
        }
    }

    ensure_directories([report_path.parent])
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Data quality report generated at {report_path}")
    return report

def main():
    """
    Entry point for the ingestion script.
    Executes harmonization and generates the data quality report.
    """
    # Example paths - in a real pipeline, these would be passed as arguments or read from config
    raw_input = DATA_DIR / "raw" / "sample_polymer_data.json"
    harmonized_output = PROCESSED_DIR / "harmonized_data.json"
    report_output = PROCESSED_DIR / "data_quality_report.json"
    
    # Ensure directories exist
    ensure_directories([DATA_DIR / "raw", PROCESSED_DIR])
    
    # Check if raw data exists (if not, this might fail or fetch)
    if not raw_input.exists():
        logger.error(f"Raw data file not found at {raw_input}. Cannot proceed with ingestion.")
        # In a real scenario, we might trigger a fetch here if T019a passed
        return 1
    
    try:
        # Run Harmonization
        run_unit_harmonization_and_validation(raw_input, harmonized_output)
        
        # Load harmonized data to generate report
        with open(harmonized_output, 'r') as f:
            harmonized_data = json.load(f)
        
        # Generate Quality Report
        generate_data_quality_report(harmonized_data, report_output)
        
        return 0
    except Exception as e:
        logger.exception(f"Ingestion pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())