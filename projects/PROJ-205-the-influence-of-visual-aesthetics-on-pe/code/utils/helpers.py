import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List

# Constants for data size constraints
# SC-005: Ensure data/raw/submissions.csv remains < 5MB for N=250
# 5MB = 5 * 1024 * 1024 bytes
MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024
# Target safe size to trigger truncation before hitting hard limit (e.g., 4.5MB)
TARGET_SAFE_SIZE_BYTES = int(MAX_CSV_SIZE_BYTES * 0.9)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs() -> None:
    """Ensure required data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)

def generate_user_id() -> str:
    """Generate a unique, anonymous participant ID."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    Returns the hexadecimal digest.
    """
    if not ip_address:
        return ""
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()

def get_consent_log_path() -> Path:
    """Return path to the consent log file."""
    return get_project_root() / "data" / "consent" / "consent_log.csv"

def log_consent_decision(user_id: str, decision: str, protocol_id: str) -> None:
    """Log a consent decision to the consent log file."""
    path = get_consent_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'user_id', 'decision', 'irb_protocol_id'])
        writer.writerow([format_timestamp(), user_id, decision, protocol_id])

def validate_rating_count(count: int, expected: int = 8) -> bool:
    """Validate that the rating count meets the expected minimum."""
    return count >= expected

def truncate_user_agent(user_agent: Optional[str], max_length: int = 255) -> str:
    """
    Truncate user_agent string to max_length to control CSV size.
    Exclude large binary blobs or non-string data.
    If input is None or empty, return empty string.
    """
    if not user_agent:
        return ""
    if not isinstance(user_agent, str):
        # If it's not a string, try to convert, but if that fails or is huge, truncate
        try:
            user_agent = str(user_agent)
        except Exception:
            return ""
    
    # Basic check for binary blob indicators (null bytes)
    if '\x00' in user_agent:
        return ""
    
    if len(user_agent) > max_length:
        return user_agent[:max_length]
    return user_agent

def check_duplicate_ip(hashed_ip: str, submissions_path: Path) -> bool:
    """
    Check if a hashed IP already exists in the submissions CSV.
    Returns True if duplicate found, False otherwise.
    """
    if not submissions_path.exists():
        return False
    
    with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == hashed_ip:
                return True
    return False

def get_current_csv_size(submissions_path: Path) -> int:
    """Get the current size of the submissions CSV in bytes."""
    if not submissions_path.exists():
        return 0
    return submissions_path.stat().st_size

def calculate_safe_truncation_length(submissions_path: Path, current_row_count: int = 0) -> int:
    """
    Calculate the maximum safe truncation length for user_agent to keep CSV < 5MB.
    
    This function estimates the remaining space per row based on the target safe size
    and the number of expected total rows (N=250).
    
    Args:
        submissions_path: Path to the submissions CSV.
        current_row_count: Number of rows already written (excluding header).
        
    Returns:
        An integer representing the safe max length for user_agent.
    """
    # Estimate average row size excluding user_agent
    # Typical row: timestamp(30) + user_id(36) + condition(15) + ratings(8*2) + demographics(10) + ip(64) + flags(10) + newlines ≈ 200 bytes
    # This is a conservative estimate.
    base_row_overhead = 200 
    
    # Target total size
    target_total = TARGET_SAFE_SIZE_BYTES
    
    # Current size
    current_size = get_current_csv_size(submissions_path)
    
    # Estimate remaining rows to reach N=250
    # If current_row_count is 0, we assume we are starting fresh and planning for 250
    # If we have data, we estimate based on current count vs 250 cap, or just project linear growth
    # For safety, we assume we will hit N=250 total.
    remaining_rows = 250 - current_row_count
    if remaining_rows <= 0:
        remaining_rows = 1 # Just process the current one if we are over limit
    
    # Calculate available space for all columns in remaining rows
    available_space = target_total - current_size
    
    # Calculate average space per row available
    if remaining_rows > 0:
        space_per_row = available_space / remaining_rows
    else:
        space_per_row = 100 # Fallback if over limit
    
    # Subtract base overhead to find space for user_agent
    space_for_ua = space_per_row - base_row_overhead
    
    # Add CSV overhead (commas, quotes, newlines) - roughly 5 bytes per field
    # user_agent is one field, so add ~5 bytes
    space_for_ua -= 5
    
    # Ensure we don't return a negative or absurdly small number
    # Minimum useful truncation is 50 chars, max is standard 255
    safe_length = int(max(50, min(space_for_ua, 255)))
    
    return safe_length

def prepare_submission_row(
    user_id: str,
    condition: str,
    ratings: Dict[str, int],
    demographics: Dict[str, Any],
    hashed_ip: str,
    timestamp: str,
    device_info: Dict[str, str],
    duplicate_flag: bool,
    submission_status: str = 'complete',
    session_timeout: bool = False
) -> Dict[str, Any]:
    """
    Prepare a submission row dictionary with proper truncation for user_agent.
    
    This function implements T023e: Truncates user_agent and ensures size constraints.
    """
    # Extract user_agent from device_info
    user_agent = device_info.get('user_agent', '')
    
    # Calculate safe truncation length based on current file state
    root = get_project_root()
    submissions_path = root / "data" / "raw" / "submissions.csv"
    
    # Count current rows to estimate remaining space
    current_rows = 0
    if submissions_path.exists():
        with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # Skip header
            current_rows = sum(1 for _ in reader)
    
    safe_len = calculate_safe_truncation_length(submissions_path, current_rows)
    
    # Truncate the user_agent
    truncated_ua = truncate_user_agent(user_agent, safe_len)
    
    # Build the row
    row = {
        'timestamp': timestamp,
        'user_id': user_id,
        'condition': condition,
        'credibility_1': ratings.get('credibility_1', ''),
        'professionalism_1': ratings.get('professionalism_1', ''),
        'credibility_2': ratings.get('credibility_2', ''),
        'professionalism_2': ratings.get('professionalism_2', ''),
        'credibility_3': ratings.get('credibility_3', ''),
        'professionalism_3': ratings.get('professionalism_3', ''),
        'credibility_4': ratings.get('credibility_4', ''),
        'professionalism_4': ratings.get('professionalism_4', ''),
        'age': demographics.get('age', ''),
        'education': demographics.get('education', ''),
        'hashed_ip': hashed_ip,
        'duplicate_flag': int(duplicate_flag),
        'session_timeout': int(session_timeout),
        'submission_status': submission_status,
        'device_type': device_info.get('device_type', ''),
        'browser': device_info.get('browser', ''),
        'os': device_info.get('os', ''),
        'user_agent': truncated_ua
    }
    
    return row

def append_to_submissions_csv(row: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Append a submission row to the CSV file.
    Creates the file and header if it doesn't exist.
    """
    if path is None:
        root = get_project_root()
        path = root / "data" / "raw" / "submissions.csv"
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'timestamp', 'user_id', 'condition',
        'credibility_1', 'professionalism_1',
        'credibility_2', 'professionalism_2',
        'credibility_3', 'professionalism_3',
        'credibility_4', 'professionalism_4',
        'age', 'education',
        'hashed_ip', 'duplicate_flag',
        'session_timeout', 'submission_status',
        'device_type', 'browser', 'os', 'user_agent'
    ]
    
    file_exists = path.exists()
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(
    user_id: str,
    condition: str,
    ratings: Dict[str, int],
    demographics: Dict[str, Any],
    hashed_ip: str,
    device_info: Dict[str, str],
    duplicate_flag: bool = False,
    submission_status: str = 'complete',
    session_timeout: bool = False
) -> None:
    """
    Main entry point to save a full submission.
    Handles truncation and file appending.
    """
    timestamp = format_timestamp()
    
    row = prepare_submission_row(
        user_id=user_id,
        condition=condition,
        ratings=ratings,
        demographics=demographics,
        hashed_ip=hashed_ip,
        timestamp=timestamp,
        device_info=device_info,
        duplicate_flag=duplicate_flag,
        submission_status=submission_status,
        session_timeout=session_timeout
    )
    
    append_to_submissions_csv(row)
