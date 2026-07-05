"""
Script to generate the provenance log from existing extraction artifacts
and then validate it against the schema requirements (T020d).

This script assumes:
1. data/synthetic/synthetic_validation.csv exists (from T026)
2. output/audit_report.json exists (from T025/T032 pipeline)

It reconstructs the provenance log by reading the audit report (which contains
the original URLs and source identifiers) and writing data/provenance_log.csv.
Then it runs the validation checks.
"""
import csv
import json
import sys
from pathlib import Path
from datetime import datetime

# Add code directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code.src.utils.logger import get_default_logger

logger = get_default_logger("provenance_validation_runner")

def load_audit_records(path: Path) -> list:
    """Load audit records from the JSON report."""
    if not path.exists():
        logger.error(f"Audit report not found: {path}")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both list format and dict with 'records' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "records" in data:
        return data["records"]
    else:
        logger.error("Unexpected audit report format")
        return []

def generate_provenance_log(audit_records: list, output_path: Path) -> None:
    """
    Generate the provenance log CSV from audit records.
    Each record in audit_report.json should contain 'url' and 'source_id' (or similar).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for record in audit_records:
        url = record.get("url") or record.get("source_url")
        repo_id = record.get("source_id") or record.get("repository_id") or "unknown"
        timestamp = record.get("validated_at") or datetime.utcnow().isoformat()
        
        if not url:
            logger.warning(f"Skipping record with missing URL: {record.get('id', 'unknown')}")
            continue
        
        rows.append({
            "url": str(url),
            "repository_identifier": str(repo_id),
            "fetch_timestamp": str(timestamp)
        })
    
    if not rows:
        logger.error("No valid provenance records generated.")
        return

    fieldnames = ["url", "repository_identifier", "fetch_timestamp"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Generated provenance log with {len(rows)} rows at {output_path}")

def validate_provenance_log(path: Path) -> bool:
    """
    Validate the provenance log has required fields in every row.
    """
    if not path.exists():
        logger.error(f"Provenance log not found: {path}")
        return False

    required_fields = {"url", "repository_identifier", "fetch_timestamp"}
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        if reader.fieldnames is None:
            logger.error("Provenance log is empty or has no header")
            return False
        
        header_set = set(reader.fieldnames)
        missing = required_fields - header_set
        if missing:
            logger.error(f"Missing required columns in header: {missing}")
            return False
        
        row_count = 0
        for row_num, row in enumerate(reader, start=2):
            row_count += 1
            for field in required_fields:
                value = row.get(field)
                if value is None or str(value).strip() == "":
                    logger.error(f"Row {row_num} has empty value for '{field}'")
                    return False
        
        if row_count == 0:
            logger.error("Provenance log has no data rows")
            return False

    logger.info(f"Validation passed: {row_count} rows with all required fields.")
    return True

def main():
    audit_report_path = PROJECT_ROOT / "output" / "audit_report.json"
    output_path = PROJECT_ROOT / "data" / "provenance_log.csv"
    
    logger.info("Loading audit records...")
    records = load_audit_records(audit_report_path)
    
    if not records:
        logger.error("Failed to load audit records. Cannot generate provenance log.")
        sys.exit(1)
    
    logger.info("Generating provenance log...")
    generate_provenance_log(records, output_path)
    
    logger.info("Validating provenance log...")
    if validate_provenance_log(output_path):
        logger.info("SUCCESS: Provenance log is valid.")
        sys.exit(0)
    else:
        logger.error("FAILED: Provenance log validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()