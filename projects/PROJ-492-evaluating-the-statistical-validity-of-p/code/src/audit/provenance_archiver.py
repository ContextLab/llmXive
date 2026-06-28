"""
Provenance Archiver - Archives provenance metadata per Constitution Principle VII.

This module creates and maintains a provenance log tracking:
- URL: The source URL of the A/B test summary
- Repository identifier: Derived from the URL domain
- Fetch timestamp: When the data was fetched/extracted

Per Constitution Principle VII, all research artifacts must maintain
complete provenance tracking for reproducibility and auditability.
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from code.src.utils.helpers import domain_from_url
from code.src.utils.logger import get_default_logger, AuditLogger

# Configure module logger
logger = get_default_logger(__name__)

# Output path for provenance log
PROVENANCE_LOG_PATH = Path("data/provenance_log.csv")

# Required columns in provenance log
REQUIRED_COLUMNS = ["url", "repository_identifier", "fetch_timestamp"]

def extract_provenance_from_summary(summary: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract provenance metadata from an ABTestSummary dictionary.
    
    Args:
        summary: Dictionary containing extracted A/B test summary data
    
    Returns:
        Dictionary with url, repository_identifier, and fetch_timestamp
    
    Raises:
        ValueError: If required fields are missing
    """
    url = summary.get("url")
    if not url:
        raise ValueError("Summary missing required 'url' field for provenance")
    
    # Derive repository identifier from URL domain
    repository_identifier = domain_from_url(url)
    if not repository_identifier:
        raise ValueError(f"Could not derive repository identifier from URL: {url}")
    
    # Get fetch timestamp - prefer stored timestamp, fallback to current time
    fetch_timestamp = summary.get("fetch_timestamp")
    if not fetch_timestamp:
        # Use current UTC time as fallback
        fetch_timestamp = datetime.utcnow().isoformat() + "Z"
    
    return {
        "url": str(url),
        "repository_identifier": str(repository_identifier),
        "fetch_timestamp": str(fetch_timestamp)
    }

def archive_provenance(
    summaries_path: Path,
    output_path: Optional[Path] = None,
    force_overwrite: bool = False
) -> Path:
    """
    Archive provenance metadata from extracted summaries to CSV.
    
    This function reads extracted A/B test summaries and creates a provenance
    log per Constitution Principle VII, tracking URL, repository identifier,
    and fetch timestamp for each entry.
    
    Args:
        summaries_path: Path to JSON file containing extracted summaries
        output_path: Path for output CSV (defaults to PROVENANCE_LOG_PATH)
        force_overwrite: Whether to overwrite existing provenance log
    
    Returns:
        Path to the created provenance log CSV
    
    Raises:
        FileNotFoundError: If summaries file does not exist
        ValueError: If required provenance fields are missing
        IOError: If unable to write output file
    """
    output_path = output_path or PROVENANCE_LOG_PATH
    output_path = Path(output_path)
    
    # Validate input file exists
    if not summaries_path.exists():
        raise FileNotFoundError(
            f"Summaries file not found: {summaries_path}"
        )
    
    # Ensure data directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if output exists and force_overwrite is False
    if output_path.exists() and not force_overwrite:
        logger.warning(
            f"Provenance log already exists at {output_path}, skipping. "
            "Use force_overwrite=True to regenerate."
        )
        return output_path
    
    # Read extracted summaries
    with open(summaries_path, "r", encoding="utf-8") as f:
        summaries_data = json.load(f)
    
    # Handle both list and dict with 'summaries' key
    if isinstance(summaries_data, dict):
        summaries = summaries_data.get("summaries", [])
    elif isinstance(summaries_data, list):
        summaries = summaries_data
    else:
        raise ValueError(
            f"Unexpected summaries data format: {type(summaries_data)}"
        )
    
    if not summaries:
        logger.warning("No summaries found in input file, creating empty provenance log")
        # Write empty CSV with headers
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        return output_path
    
    # Extract provenance for each summary
    provenance_entries = []
    audit_logger = AuditLogger("provenance_archiver")
    
    for idx, summary in enumerate(summaries):
        try:
            provenance = extract_provenance_from_summary(summary)
            
            # Validate all required fields present
            for col in REQUIRED_COLUMNS:
                if not provenance.get(col):
                    raise ValueError(f"Missing {col} for summary at index {idx}")
            
            provenance_entries.append(provenance)
            
        except (ValueError, KeyError) as e:
            error_code = f"ERR-0{idx % 90 + 1:02d}"
            msg = f"Failed to extract provenance for summary {idx}: {str(e)}"
            audit_logger.log_error(error_code, msg)
            logger.warning(msg)
            # Continue processing remaining summaries
            continue
    
    # Write provenance log to CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(provenance_entries)
    
    logger.info(
        f"Archived {len(provenance_entries)} provenance entries to {output_path}"
    )
    
    return output_path

def validate_provenance_log(
    provenance_path: Optional[Path] = None
) -> tuple[bool, List[str]]:
    """
    Validate that provenance log exists and contains all required fields.
    
    Args:
        provenance_path: Path to provenance log CSV (defaults to PROVENANCE_LOG_PATH)
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    provenance_path = provenance_path or PROVENANCE_LOG_PATH
    provenance_path = Path(provenance_path)
    
    errors = []
    
    # Check file exists
    if not provenance_path.exists():
        errors.append(f"Provenance log not found at {provenance_path}")
        return False, errors
    
    # Read and validate CSV
    with open(provenance_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Check headers
        headers = reader.fieldnames
        if not headers:
            errors.append("Provenance log has no headers")
            return False, errors
        
        missing_cols = set(REQUIRED_COLUMNS) - set(headers)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return False, errors
        
        # Check each row has all required fields
        row_count = 0
        for row in reader:
            row_count += 1
            for col in REQUIRED_COLUMNS:
                if not row.get(col):
                    errors.append(
                        f"Row {row_count} missing required field: {col}"
                    )
    
    if errors:
        return False, errors
    
    logger.info(f"Provenance log validation passed ({row_count} rows)")
    return True, []

def main() -> int:
    """
    Main entry point for provenance archiver script.
    
    Usage:
        python -m code.src.audit.provenance_archiver [--input PATH] [--output PATH] [--force]
    
    Returns:
        0 on success, non-zero on error
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Archive provenance metadata from extracted A/B test summaries"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("output/extracted_summaries.json"),
        help="Path to extracted summaries JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=PROVENANCE_LOG_PATH,
        help="Path for output provenance CSV"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force overwrite existing provenance log"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate provenance log after creation"
    )
    
    args = parser.parse_args()
    
    try:
        # Archive provenance
        output_path = archive_provenance(
            summaries_path=args.input,
            output_path=args.output,
            force_overwrite=args.force
        )
        
        # Optionally validate
        if args.validate:
            is_valid, errors = validate_provenance_log(output_path)
            if not is_valid:
                for err in errors:
                    logger.error(err)
                return 1
        
        print(f"Successfully archived provenance to {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except IOError as e:
        logger.error(f"I/O error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
