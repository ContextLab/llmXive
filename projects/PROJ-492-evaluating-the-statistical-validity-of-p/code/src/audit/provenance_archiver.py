import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger("provenance_archiver")

def extract_provenance_from_summary(summary: Dict[str, Any], url: str) -> Dict[str, Any]:
    """
    Extract provenance metadata from an ABTestSummary dict.
    Returns a dict with url, repository_identifier, and fetch_timestamp.
    """
    repo_id = summary.get("source_id") or summary.get("repository_id") or "unknown"
    timestamp = summary.get("extracted_at") or datetime.utcnow().isoformat()
    
    return {
        "url": url,
        "repository_identifier": str(repo_id),
        "fetch_timestamp": timestamp
    }

def archive_provenance(
    summaries: List[Dict[str, Any]], 
    urls: List[str], 
    output_path: Path
) -> None:
    """
    Archive provenance metadata for a list of summaries to a CSV file.
    Ensures every row has url, repository_identifier, and fetch_timestamp.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for url, summary in zip(urls, summaries):
        row = extract_provenance_from_summary(summary, url)
        rows.append(row)
    
    if not rows:
        logger.warning("No provenance records to archive.")
        return

    fieldnames = ["url", "repository_identifier", "fetch_timestamp"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Archived {len(rows)} provenance records to {output_path}")

def validate_provenance_log(path: Path) -> bool:
    """
    Validate that the provenance log exists and contains required fields in every row.
    Returns True if valid, raises AssertionError otherwise.
    """
    if not path.exists():
        raise FileNotFoundError(f"Provenance log not found: {path}")
    
    required_fields = {"url", "repository_identifier", "fetch_timestamp"}
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        if reader.fieldnames is None:
            raise ValueError("Provenance log is empty or has no header")
        
        header_set = set(reader.fieldnames)
        missing = required_fields - header_set
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        row_count = 0
        for row_num, row in enumerate(reader, start=2):
            row_count += 1
            for field in required_fields:
                if not row.get(field) or not row[field].strip():
                    raise ValueError(
                        f"Row {row_num} has empty value for required field '{field}'"
                    )
        
        if row_count == 0:
            raise ValueError("Provenance log contains no data rows")
    
    logger.info(f"Provenance log validation passed ({row_count} rows).")
    return True

def main():
    """
    Entry point for manual execution or CLI integration.
    Expects arguments: --input-json <path> --input-csv <path> --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive provenance from extracted summaries.")
    parser.add_argument("--input-json", required=True, help="Path to extracted summaries JSON")
    parser.add_argument("--input-csv", required=True, help="Path to URLs CSV (for mapping)")
    parser.add_argument("--output", required=True, help="Output path for provenance_log.csv")
    args = parser.parse_args()
    
    with open(args.input_json, "r", encoding="utf-8") as f:
        summaries = json.load(f)
    
    with open(args.input_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        urls = [row["url"] for row in reader]
    
    output_path = Path(args.output)
    archive_provenance(summaries, urls, output_path)
    validate_provenance_log(output_path)

if __name__ == "__main__":
    main()
