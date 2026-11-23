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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = {'participant_id', 'condition', 'snippet_id', 'answer', 'latency_ms', 'timestamp'}
OUTPUT_PATH = Path("data/intermediate/responses.csv")

def validate_row(row: Dict[str, str], row_idx: int) -> List[str]:
    """
    Validate a single row of data.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    
    # Check for missing required columns
    missing_cols = REQUIRED_COLUMNS - set(row.keys())
    if missing_cols:
        errors.append(f"Row {row_idx}: Missing required columns: {missing_cols}")
        return errors  # Cannot validate further if structure is wrong

    # Validate participant_id is not empty
    if not row.get('participant_id', '').strip():
        errors.append(f"Row {row_idx}: Empty participant_id")

    # Validate condition is one of expected values
    condition = row.get('condition', '').strip()
    if condition and condition not in {'A', 'B', 'C', 'Code Only', 'Code+LLM', 'Code+Docstring'}:
        errors.append(f"Row {row_idx}: Invalid condition '{condition}'")

    # Validate answer is boolean-like
    answer = row.get('answer', '').strip().lower()
    if answer not in {'true', 'false', '1', '0', 'yes', 'no'}:
        errors.append(f"Row {row_idx}: Invalid answer value '{answer}'")

    # Validate latency_ms is numeric
    latency = row.get('latency_ms', '').strip()
    if latency:
        try:
            float(latency)
        except ValueError:
            errors.append(f"Row {row_idx}: Invalid latency_ms '{latency}'")

    # Validate timestamp is parseable (basic check)
    timestamp = row.get('timestamp', '').strip()
    if timestamp:
        try:
            # Try common formats
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Try other common formats if ISO fails
            try:
                datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                errors.append(f"Row {row_idx}: Unparseable timestamp '{timestamp}'")

    return errors

def normalize_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Normalize a validated row to standard types and formats.
    """
    normalized = {}
    
    # participant_id: string
    normalized['participant_id'] = row['participant_id'].strip()
    
    # condition: standardize to A, B, C
    condition = row['condition'].strip()
    if condition in {'Code Only', 'A'}:
        normalized['condition'] = 'A'
    elif condition in {'Code+LLM', 'B'}:
        normalized['condition'] = 'B'
    elif condition in {'Code+Docstring', 'C'}:
        normalized['condition'] = 'C'
    else:
        normalized['condition'] = condition.upper()  # Fallback, should be caught by validation
    
    # snippet_id: string
    normalized['snippet_id'] = row['snippet_id'].strip()
    
    # answer: boolean
    answer = row['answer'].strip().lower()
    normalized['answer'] = answer in {'true', '1', 'yes'}
    
    # latency_ms: float
    latency = row.get('latency_ms', '0').strip()
    normalized['latency_ms'] = float(latency) if latency else 0.0
    
    # timestamp: ISO format string
    timestamp = row.get('timestamp', '').strip()
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            normalized['timestamp'] = dt.isoformat()
        except ValueError:
            normalized['timestamp'] = timestamp  # Keep original if parsing fails
    else:
        normalized['timestamp'] = datetime.now().isoformat()
    
    return normalized

def ingest_responses(input_path: str) -> List[Dict[str, Any]]:
    """
    Ingest responses from a CSV file.
    Returns a list of normalized response dictionaries.
    Raises ValueError if the file cannot be read or is empty.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    responses = []
    errors = []
    
    logger.info(f"Reading responses from {input_path}")
    
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check header
        if not reader.fieldnames:
            raise ValueError(f"CSV file {input_path} has no header row")
        
        for idx, row in enumerate(reader, start=2):  # Start at 2 to account for header
            row_errors = validate_row(row, idx)
            
            if row_errors:
                errors.extend(row_errors)
                continue  # Skip invalid rows
            
            try:
                normalized = normalize_row(row)
                responses.append(normalized)
            except Exception as e:
                errors.append(f"Row {idx}: Normalization error: {str(e)}")
    
    if errors:
        logger.warning(f"Encountered {len(errors)} validation errors during ingestion:")
        for err in errors[:10]:  # Log first 10 errors
            logger.warning(f"  - {err}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more errors")
    
    if not responses:
        raise ValueError(f"No valid responses found in {input_path}")
    
    logger.info(f"Successfully ingested {len(responses)} valid responses")
    return responses

def save_responses(responses: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Save normalized responses to a CSV file.
    """
    if output_path is None:
        output_path = str(OUTPUT_PATH)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not responses:
        logger.warning("No responses to save")
        return
    
    # Define consistent field order
    fieldnames = ['participant_id', 'condition', 'snippet_id', 'answer', 'latency_ms', 'timestamp']
    
    logger.info(f"Saving {len(responses)} responses to {output_path}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)
    
    logger.info(f"Saved responses to {output_path}")

def main() -> None:
    """
    Main entry point for the ingestion script.
    Expects input CSV path as first argument, or uses default if not provided.
    """
    if len(sys.argv) < 2:
        # Default to a common survey export location if no argument provided
        # In a real deployment, this would be configured or passed explicitly
        default_input = "data/raw/survey_responses.csv"
        logger.info(f"No input path provided, attempting default: {default_input}")
        
        if not Path(default_input).exists():
            logger.error(f"Default input file not found: {default_input}")
            logger.error("Usage: python code/02_ingest_responses.py <input_csv_path>")
            sys.exit(1)
        
        input_path = default_input
    else:
        input_path = sys.argv[1]
    
    try:
        responses = ingest_responses(input_path)
        save_responses(responses)
        logger.info("Ingestion completed successfully")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
