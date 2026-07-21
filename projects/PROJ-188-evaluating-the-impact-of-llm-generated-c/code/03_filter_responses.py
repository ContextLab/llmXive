import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/filter_responses.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_LATENCY_MS = 30000  # 30 seconds in milliseconds
MAX_MISSING_RATIO = 0.80  # 80% missing threshold

def load_responses(input_path: str) -> List[Dict[str, Any]]:
    """
    Load responses from a CSV file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries representing each response row.
    """
    responses = []
    path = Path(input_path)
    
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        return responses
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                try:
                    row['latency_ms'] = int(row.get('latency_ms', 0))
                except (ValueError, TypeError):
                    row['latency_ms'] = 0
                
                try:
                    row['missing_count'] = int(row.get('missing_count', 0))
                except (ValueError, TypeError):
                    row['missing_count'] = 0
                
                # Determine total questions if not present (default 3 for this study)
                if 'total_questions' not in row:
                    row['total_questions'] = 3
                
                responses.append(row)
        
        logger.info(f"Loaded {len(responses)} responses from {input_path}")
    except Exception as e:
        logger.error(f"Error loading responses: {e}")
        raise
    
    return responses

def calculate_missing_count(row: Dict[str, Any]) -> int:
    """
    Calculate missing count for a response row.
    Note: This task assumes missing_count is already present in the row 
    (from T022b), but provides this function for completeness.
    
    Args:
        row: A response dictionary.
        
    Returns:
        The missing count integer.
    """
    return int(row.get('missing_count', 0))

def is_valid_participant(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Determine if a participant is valid based on filtering criteria.
    
    Criteria:
    - Total time (latency_ms) must be >= 30000ms (30 seconds)
    - Missing count must be <= 80% of total questions
    
    Args:
        row: A response dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_reasons_if_invalid)
    """
    reasons = []
    
    latency = row.get('latency_ms', 0)
    if latency < MIN_LATENCY_MS:
        reasons.append(f"latency < {MIN_LATENCY_MS}ms ({latency}ms)")
    
    missing_count = calculate_missing_count(row)
    total_questions = row.get('total_questions', 3)
    max_allowed_missing = int(MAX_MISSING_RATIO * total_questions)
    
    if missing_count > max_allowed_missing:
        reasons.append(f"missing_count > {max_allowed_missing} ({missing_count})")
    
    return len(reasons) == 0, reasons

def filter_responses(responses: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter responses to remove invalid participants.
    
    Args:
        responses: List of response dictionaries.
        
    Returns:
        Tuple of (valid_responses, excluded_responses)
    """
    valid = []
    excluded = []
    
    for row in responses:
        is_valid, reasons = is_valid_participant(row)
        if is_valid:
            valid.append(row)
        else:
            row['_exclusion_reasons'] = reasons
            excluded.append(row)
    
    logger.info(f"Filtering complete: {len(valid)} valid, {len(excluded)} excluded")
    return valid, excluded

def save_filtered_responses(responses: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save filtered responses to a CSV file.
    
    Args:
        responses: List of valid response dictionaries.
        output_path: Path to the output CSV file.
    """
    if not responses:
        logger.warning("No responses to save.")
        return
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(responses[0].keys())
    # Remove internal exclusion reasons from output
    if '_exclusion_reasons' in fieldnames:
        fieldnames.remove('_exclusion_reasons')
    
    try:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in responses:
                # Clean up internal fields before writing
                clean_row = {k: v for k, v in row.items() if not k.startswith('_')}
                writer.writerow(clean_row)
        
        logger.info(f"Saved {len(responses)} valid responses to {output_path}")
    except Exception as e:
        logger.error(f"Error saving filtered responses: {e}")
        raise

def save_exclusion_log(excluded: List[Dict[str, Any]], log_path: str) -> None:
    """
    Save exclusion details to a JSON log file.
    
    Args:
        excluded: List of excluded response dictionaries.
        log_path: Path to the exclusion log JSON file.
    """
    if not excluded:
        logger.info("No exclusions to log.")
        return
    
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare log data
    log_data = []
    for row in excluded:
        entry = {
            'participant_id': row.get('participant_id', 'unknown'),
            'condition': row.get('condition', 'unknown'),
            'snippet_id': row.get('snippet_id', 'unknown'),
            'latency_ms': row.get('latency_ms', 0),
            'missing_count': row.get('missing_count', 0),
            'exclusion_reasons': row.get('_exclusion_reasons', [])
        }
        log_data.append(entry)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Saved exclusion log with {len(excluded)} entries to {log_path}")
    except Exception as e:
        logger.error(f"Error saving exclusion log: {e}")
        raise

def main():
    """
    Main entry point for filtering responses.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / 'data' / 'intermediate' / 'responses.csv'
    output_path = base_dir / 'data' / 'intermediate' / 'responses_filtered.csv'
    exclusion_log_path = base_dir / 'data' / 'intermediate' / 'exclusion_log.json'
    
    logger.info(f"Starting response filtering. Input: {input_path}")
    
    # Load responses
    responses = load_responses(str(input_path))
    if not responses:
        logger.warning("No responses loaded. Exiting.")
        return
    
    # Filter responses
    valid_responses, excluded_responses = filter_responses(responses)
    
    # Save outputs
    save_filtered_responses(valid_responses, str(output_path))
    save_exclusion_log(excluded_responses, str(exclusion_log_path))
    
    # Log summary
    total = len(responses)
    valid_count = len(valid_responses)
    excluded_count = len(excluded_responses)
    logger.info(f"Summary: {total} total, {valid_count} valid ({valid_count/total:.1%}), {excluded_count} excluded ({excluded_count/total:.1%})")
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} participants. See {exclusion_log_path} for details.")

if __name__ == '__main__':
    main()