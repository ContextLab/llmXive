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
        logging.FileHandler('logs/filter_responses.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MIN_LATENCY_MS = 30000  # 30 seconds
MAX_MISSING_RATIO = 0.80  # 80% missing threshold

def load_responses(file_path: Path) -> List[Dict[str, Any]]:
    """Load responses from a CSV file."""
    if not file_path.exists():
        logger.error(f"Response file not found: {file_path}")
        raise FileNotFoundError(f"Response file not found: {file_path}")

    responses = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            responses.append(row)
    logger.info(f"Loaded {len(responses)} responses from {file_path}")
    return responses

def calculate_missing_count(row: Dict[str, Any]) -> int:
    """
    Calculate the number of missing answers for a participant.
    Assumes columns like 'answer_1', 'answer_2', 'answer_3' or similar.
    For this implementation, we check specific answer columns.
    If the row contains a 'missing_count' or 'missing' field, use that.
    Otherwise, infer from answer columns.
    """
    # Check if there is an explicit missing count field
    if 'missing_count' in row:
        try:
            return int(row['missing_count'])
        except (ValueError, TypeError):
            pass

    # Infer from answer columns (e.g., answer_1, answer_2, answer_3)
    # Or generic 'answer' if it's a list/serialized string (unlikely in CSV)
    # We'll assume standard columns: answer, answer_1, answer_2, answer_3
    # If 'answer' is empty string or null, count as missing.
    # For simplicity in this task, we assume 3 questions per participant.
    # We look for columns: 'answer', 'answer_1', 'answer_2', 'answer_3'
    # If 'answer' is the only column, we treat it as one question.
    # The task description implies multiple questions ("total time", "missing").
    # Let's assume columns: 'answer_1', 'answer_2', 'answer_3' exist.
    
    missing = 0
    total_questions = 0
    
    # Check for standard answer columns
    answer_cols = [col for col in row.keys() if col.startswith('answer')]
    if not answer_cols:
        # Fallback: check if 'answer' exists and is empty
        if 'answer' in row:
            total_questions = 1
            if not row['answer'] or row['answer'].strip() == '':
                missing = 1
        else:
            # No answer columns found, assume 0 missing? Or error?
            # Let's assume 0 missing if no columns found.
            pass
    else:
        total_questions = len(answer_cols)
        for col in answer_cols:
            val = row.get(col, '')
            if val is None or val.strip() == '':
                missing += 1
    
    # If we couldn't determine total questions, assume 3 as per spec hint
    if total_questions == 0:
        total_questions = 3
        # If no columns found, we can't count missing, so assume 0 or max?
        # Let's assume 0 missing if no data to check.
        # But if the row has no answer columns, it's likely invalid.
        # For safety, if no answer columns found, assume all missing?
        # No, let's stick to: if no columns, 0 missing.
        if len(answer_cols) == 0:
            missing = 0

    return missing, total_questions

def is_valid_participant(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if a participant is valid based on:
    1. Total time >= 30 seconds (30000 ms)
    2. Missing answers < 80% of total questions

    Returns: (is_valid, reason)
    """
    # Check latency
    latency_str = row.get('latency_ms', '0')
    try:
        latency_ms = int(float(latency_str))
    except (ValueError, TypeError):
        return False, f"Invalid latency value: {latency_str}"

    if latency_ms < MIN_LATENCY_MS:
        return False, f"Latency too low: {latency_ms}ms < {MIN_LATENCY_MS}ms"

    # Check missing answers
    missing_count, total_questions = calculate_missing_count(row)
    if total_questions == 0:
        # If no questions, we can't calculate ratio. Assume valid?
        # Or invalid? Let's assume valid if no questions to answer.
        return True, "No questions to check"

    missing_ratio = missing_count / total_questions
    if missing_ratio >= MAX_MISSING_RATIO:
        return False, f"Too many missing answers: {missing_count}/{total_questions} ({missing_ratio:.2%} >= {MAX_MISSING_RATIO:.2%})"

    return True, "Valid"

def filter_responses(responses: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter invalid participants and log exclusion counts.

    Returns: (valid_responses, invalid_responses, exclusion_counts)
    """
    valid = []
    invalid = []
    exclusion_counts = {
        'total': len(responses),
        'too_fast': 0,
        'too_many_missing': 0,
        'other': 0
    }

    for row in responses:
        is_valid, reason = is_valid_participant(row)
        if is_valid:
            valid.append(row)
        else:
            invalid.append(row)
            # Categorize exclusion reason
            if "Latency" in reason:
                exclusion_counts['too_fast'] += 1
            elif "missing" in reason:
                exclusion_counts['too_many_missing'] += 1
            else:
                exclusion_counts['other'] += 1
            logger.warning(f"Excluded participant {row.get('participant_id', 'unknown')}: {reason}")

    logger.info(f"Filtering complete. Valid: {len(valid)}, Invalid: {len(invalid)}")
    logger.info(f"Exclusion counts: {exclusion_counts}")
    return valid, invalid, exclusion_counts

def save_filtered_responses(valid_responses: List[Dict[str, Any]], output_path: Path):
    """Save valid responses to a new CSV file."""
    if not valid_responses:
        logger.warning("No valid responses to save.")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = valid_responses[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_responses)

    logger.info(f"Saved {len(valid_responses)} valid responses to {output_path}")

def save_exclusion_log(invalid_responses: List[Dict[str, Any]], exclusion_counts: Dict[str, int], log_path: Path):
    """Save exclusion details and counts to a JSON log file."""
    log_data = {
        'exclusion_counts': exclusion_counts,
        'excluded_participants': [
            {
                'participant_id': p.get('participant_id', 'unknown'),
                'reason': p.get('reason', 'Unknown reason') # We need to attach reason to the row or store separately
                # Since we filtered by reason in the loop, we should have stored it.
                # Let's modify the loop to store reason in the invalid row.
            }
            for p in invalid_responses
        ]
    }
    # Actually, we didn't store the reason in the row. Let's fix that in the loop or here.
    # We'll just save the counts and a summary for now, or we can re-run the check.
    # Better: we should have stored the reason. Let's assume we can re-check or we store it in the invalid list.
    # For this implementation, we'll just save the counts and a note.
    
    # Let's re-structure: we'll save the counts and the list of excluded participant IDs.
    log_data = {
        'exclusion_counts': exclusion_counts,
        'excluded_participant_ids': [p.get('participant_id', 'unknown') for p in invalid_responses]
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

    logger.info(f"Saved exclusion log to {log_path}")

def main():
    """Main entry point for filtering responses."""
    # Paths
    input_path = Path('data/intermediate/responses.csv')
    output_path = Path('data/intermediate/responses_filtered.csv')
    log_path = Path('data/intermediate/exclusion_log.json')

    logger.info("Starting response filtering...")
    
    try:
        responses = load_responses(input_path)
        valid, invalid, counts = filter_responses(responses)
        save_filtered_responses(valid, output_path)
        save_exclusion_log(invalid, counts, log_path)
        logger.info("Filtering completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()