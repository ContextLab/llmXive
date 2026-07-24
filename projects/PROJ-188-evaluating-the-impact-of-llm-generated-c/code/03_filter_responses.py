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
        logging.FileHandler('data/intermediate/filter_responses.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_LATENCY_MS = 30000  # 30 seconds in milliseconds
MAX_MISSING_RATIO = 0.80  # 80%
TOTAL_QUESTIONS = 3

def load_responses(file_path: str) -> List[Dict[str, Any]]:
    """Load responses from a CSV file."""
    responses = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                if 'latency_ms' in row:
                    row['latency_ms'] = int(row['latency_ms'])
                if 'answer' in row:
                    row['answer'] = row['answer'].lower() == 'true'
                if 'missing_count' in row:
                    row['missing_count'] = int(row['missing_count'])
                responses.append(row)
        logger.info(f"Loaded {len(responses)} responses from {file_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading responses: {e}")
        raise
    return responses

def calculate_missing_count(row: Dict[str, Any]) -> int:
    """
    Calculate missing count for a participant.
    'Missing' is defined as unanswered questions.
    Denominator is total_questions = 3 per participant.
    """
    # If missing_count is already in the row, return it
    if 'missing_count' in row and row['missing_count'] is not None:
        return row['missing_count']
    
    # Otherwise, count missing fields based on expected columns
    # Expected answer columns: answer_1, answer_2, answer_3 (or similar)
    # For now, we assume the row has a 'missing_count' field from T022b
    # If not, we estimate based on available fields
    missing = 0
    for i in range(1, TOTAL_QUESTIONS + 1):
        key = f'answer_{i}'
        if key not in row or row[key] == '' or row[key] is None:
            missing += 1
    return missing

def is_valid_participant(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if a participant is valid based on:
    - Total time >= 30 seconds (latency_ms >= 30000)
    - Missing count < 80% of total questions (missing_count < 0.8 * 3 = 2.4, so <= 2)
    
    Returns (is_valid, reason)
    """
    # Check latency
    latency = row.get('latency_ms', 0)
    if latency < MIN_LATENCY_MS:
        return False, f"Latency too low: {latency}ms < {MIN_LATENCY_MS}ms"
    
    # Check missing count
    missing_count = calculate_missing_count(row)
    max_allowed_missing = int(MAX_MISSING_RATIO * TOTAL_QUESTIONS)
    if missing_count > max_allowed_missing:
        return False, f"Too many missing: {missing_count} > {max_allowed_missing}"
    
    return True, "Valid"

def filter_responses(responses: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter responses to remove invalid participants.
    Returns (valid_responses, excluded_responses)
    """
    valid = []
    excluded = []
    
    for row in responses:
        is_valid, reason = is_valid_participant(row)
        if is_valid:
            valid.append(row)
        else:
            excluded.append({'row': row, 'reason': reason})
            logger.warning(f"Excluding participant {row.get('participant_id', 'unknown')}: {reason}")
    
    logger.info(f"Filtered responses: {len(valid)} valid, {len(excluded)} excluded")
    return valid, excluded

def save_filtered_responses(responses: List[Dict[str, Any]], output_path: str) -> None:
    """Save filtered responses to a CSV file."""
    if not responses:
        logger.warning("No responses to save")
        return
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(responses[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)
    
    logger.info(f"Saved {len(responses)} filtered responses to {output_path}")

def save_exclusion_log(excluded: List[Dict[str, Any]], log_path: str) -> None:
    """Save exclusion log to a JSON file."""
    # Ensure output directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(excluded, f, indent=2, default=str)
    
    logger.info(f"Saved exclusion log with {len(excluded)} entries to {log_path}")

def main():
    """Main function to filter responses."""
    # Input and output paths
    input_path = 'data/intermediate/responses.csv'
    output_path = 'data/intermediate/responses_filtered.csv'
    exclusion_log_path = 'data/intermediate/exclusion_log.json'
    
    try:
        # Load responses
        logger.info(f"Loading responses from {input_path}")
        responses = load_responses(input_path)
        
        # Filter responses
        valid_responses, excluded_responses = filter_responses(responses)
        
        # Save filtered responses
        save_filtered_responses(valid_responses, output_path)
        
        # Save exclusion log
        save_exclusion_log(excluded_responses, exclusion_log_path)
        
        # Log summary
        logger.info(f"Total participants: {len(responses)}")
        logger.info(f"Valid participants: {len(valid_responses)}")
        logger.info(f"Excluded participants: {len(excluded_responses)}")
        
        if excluded_responses:
            logger.info("Exclusion reasons:")
            for exc in excluded_responses:
                logger.info(f"  - {exc['row'].get('participant_id', 'unknown')}: {exc['reason']}")
        
        logger.info("Filtering completed successfully")
        
    except Exception as e:
        logger.error(f"Error during filtering: {e}")
        raise

if __name__ == '__main__':
    main()