"""
Ingest real participant data from a deployed survey or CSV into data/intermediate/responses.csv.

This script expects a source CSV file containing real survey responses.
It validates the required columns, normalizes the data, and writes the
standardized output to data/intermediate/responses.csv.

Source CSV expected columns:
- participant_id
- condition (A, B, or C)
- snippet_id
- answer (boolean or 0/1)
- latency_ms (integer/float)
- timestamp (ISO format or Unix timestamp)

Output:
- data/intermediate/responses.csv with standardized columns and types.
"""
import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_PATH = Path("data/intermediate/responses.csv")
REQUIRED_COLUMNS = {'participant_id', 'condition', 'snippet_id', 'answer', 'latency_ms', 'timestamp'}

def validate_row(row: Dict[str, str], row_num: int) -> Optional[str]:
    """Validate a single row of data."""
    # Check for missing required columns
    for col in REQUIRED_COLUMNS:
        if col not in row or not row[col]:
            return f"Row {row_num}: Missing required column '{col}'"

    # Validate condition
    if row['condition'] not in ['A', 'B', 'C']:
        return f"Row {row_num}: Invalid condition '{row['condition']}' (expected A, B, or C)"

    # Validate answer (should be boolean or 0/1)
    answer = row['answer'].lower().strip()
    if answer not in ['true', 'false', '1', '0', 'yes', 'no']:
        return f"Row {row_num}: Invalid answer value '{row['answer']}'"

    # Validate latency_ms (should be numeric)
    try:
        float(row['latency_ms'])
    except ValueError:
        return f"Row {row_num}: Invalid latency_ms value '{row['latency_ms']}'"

    # Validate timestamp (try to parse)
    try:
        # Try ISO format first
        datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try Unix timestamp
            float(row['timestamp'])
        except ValueError:
            return f"Row {row_num}: Invalid timestamp format '{row['timestamp']}'"

    return None

def normalize_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Normalize a row to the standard format."""
    # Normalize answer to boolean
    answer = row['answer'].lower().strip()
    normalized_answer = answer in ['true', '1', 'yes']

    # Normalize latency to float
    latency = float(row['latency_ms'])

    # Normalize timestamp to ISO format
    try:
        dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
        normalized_timestamp = dt.isoformat()
    except ValueError:
        # Unix timestamp
        normalized_timestamp = datetime.fromtimestamp(float(row['timestamp'])).isoformat()

    return {
        'participant_id': row['participant_id'].strip(),
        'condition': row['condition'].strip().upper(),
        'snippet_id': row['snippet_id'].strip(),
        'answer': normalized_answer,
        'latency_ms': latency,
        'timestamp': normalized_timestamp
    }

def ingest_responses(source_path: str) -> List[Dict[str, Any]]:
    """Ingest responses from a source CSV file."""
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if not source.suffix.lower() == '.csv':
        raise ValueError(f"Source file must be a CSV: {source_path}")

    normalized_rows = []
    errors = []

    with open(source, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate header
        header = set(reader.fieldnames) if reader.fieldnames else set()
        missing_cols = REQUIRED_COLUMNS - header
        if missing_cols:
            raise ValueError(f"Source CSV missing required columns: {missing_cols}")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            error = validate_row(row, row_num)
            if error:
                errors.append(error)
                logger.warning(error)
                continue

            try:
                normalized = normalize_row(row)
                normalized_rows.append(normalized)
            except Exception as e:
                error_msg = f"Row {row_num}: Error normalizing row - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

    if errors:
        logger.warning(f"Ingested {len(normalized_rows)} valid rows with {len(errors)} errors")
    else:
        logger.info(f"Ingested {len(normalized_rows)} valid rows")

    return normalized_rows

def save_responses(responses: List[Dict[str, Any]], output_path: Path) -> None:
    """Save normalized responses to the output CSV."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not responses:
        logger.warning("No valid responses to save")
        # Write empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        return

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        
        for response in responses:
            # Convert boolean to string for CSV
            row = response.copy()
            row['answer'] = 'True' if response['answer'] else 'False'
            writer.writerow(row)

    logger.info(f"Saved {len(responses)} responses to {output_path}")

def main():
    """Main entry point for the script."""
    # Default source path can be overridden by environment variable or argument
    source_path = os.environ.get('RESPONSES_SOURCE', 'data/raw/survey_responses.csv')
    
    if len(sys.argv) > 1:
        source_path = sys.argv[1]

    logger.info(f"Starting response ingestion from: {source_path}")

    try:
        responses = ingest_responses(source_path)
        save_responses(responses, OUTPUT_PATH)
        logger.info("Ingestion completed successfully")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please provide a valid source CSV file with real participant data")
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()