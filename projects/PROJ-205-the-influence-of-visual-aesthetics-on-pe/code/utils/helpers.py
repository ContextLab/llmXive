import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs() -> None:
    """Ensure data/raw and data/processed directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)

def generate_user_id() -> str:
    """Generate a unique, non-PII user ID."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    This function is idempotent and deterministic for the same IP.
    """
    if not ip_address:
        raise ValueError("IP address cannot be empty")
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime object as an ISO 8601 string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def get_consent_log_path() -> Path:
    """Return the path to the consent log CSV."""
    return get_project_root() / "data" / "consent" / "consent_log.csv"

def log_consent_decision(user_id: str, decision: bool, protocol_id: str) -> None:
    """Log a consent decision to the consent log CSV."""
    path = get_consent_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = path.exists()
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'user_id', 'decision', 'irb_protocol_id'])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': format_timestamp(),
            'user_id': user_id,
            'decision': decision,
            'irb_protocol_id': protocol_id
        })

def validate_rating_count(count: int, required: int = 8) -> bool:
    """Validate that the number of ratings meets the requirement."""
    return count == required

def get_submissions_csv_path() -> Path:
    """Return the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def check_duplicate_ip(hashed_ip: str) -> bool:
    """
    Check if a hashed IP already exists in the submissions CSV.
    Returns True if a duplicate is found, False otherwise.
    Raises FileNotFoundError if the CSV does not exist yet.
    """
    csv_path = get_submissions_csv_path()
    
    if not csv_path.exists():
        # If no submissions exist yet, this is not a duplicate
        return False

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Check if the column exists first
            if 'hashed_ip' not in reader.fieldnames:
                return False
            
            for row in reader:
                if row.get('hashed_ip') == hashed_ip:
                    return True
        return False
    except Exception as e:
        # If we can't read the file for any reason, fail loudly
        raise RuntimeError(f"Failed to check duplicate IP in {csv_path}: {e}")

def get_current_csv_size() -> int:
    """Get the current size of the submissions CSV in bytes."""
    csv_path = get_submissions_csv_path()
    if not csv_path.exists():
        return 0
    return csv_path.stat().st_size

def calculate_safe_truncation_length(current_size: int, max_size_bytes: int = 5 * 1024 * 1024, estimated_rows: int = 250) -> int:
    """
    Calculate a safe truncation length for user_agent strings to keep CSV under 5MB.
    This is a heuristic based on estimated remaining rows.
    """
    if estimated_rows <= 0:
        return 255 # Default max
    
    available_bytes = max_size_bytes - current_size
    if available_bytes <= 0:
        return 10 # Fallback if already over limit
    
    # Assume average other row size is ~500 bytes
    estimated_other_data = estimated_rows * 500
    remaining_for_ua = max(0, available_bytes - estimated_other_data)
    
    # Distribute remaining space among rows
    safe_len = int(remaining_for_ua / estimated_rows)
    return max(10, min(safe_len, 255))

def truncate_user_agent(ua_string: str, max_length: int) -> str:
    """Truncate a user agent string to a safe length."""
    if not ua_string:
        return ""
    if len(ua_string) <= max_length:
        return ua_string
    return ua_string[:max_length]

def prepare_submission_row(
    user_id: str,
    condition: str,
    credibility_rating: int,
    professionalism_rating: int,
    timestamp: str,
    device_info: str,
    hashed_ip: str,
    age: int,
    education_code: int,
    submission_status: str = "complete",
    session_timeout: bool = False
) -> Dict[str, Any]:
    """Prepare a dictionary row for the submissions CSV."""
    return {
        'user_id': user_id,
        'condition': condition,
        'credibility_rating': credibility_rating,
        'professionalism_rating': professionalism_rating,
        'timestamp': timestamp,
        'device_info': device_info,
        'hashed_ip': hashed_ip,
        'age': age,
        'education_code': education_code,
        'submission_status': submission_status,
        'session_timeout': session_timeout
    }

def append_to_submissions_csv(row: Dict[str, Any]) -> None:
    """Append a row to the submissions CSV."""
    ensure_data_dirs()
    csv_path = get_submissions_csv_path()
    
    fieldnames = [
        'user_id', 'condition', 'credibility_rating', 'professionalism_rating',
        'timestamp', 'device_info', 'hashed_ip', 'age', 'education_code',
        'submission_status', 'session_timeout'
    ]
    
    file_exists = csv_path.exists()
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(
    user_id: str,
    condition: str,
    credibility_rating: int,
    professionalism_rating: int,
    timestamp: str,
    device_info: str,
    raw_ip: str,
    age: int,
    education_code: int,
    submission_status: str = "complete",
    session_timeout: bool = False
) -> None:
    """
    Main entry point for saving a submission.
    1. Hashes the raw IP.
    2. Checks for duplicates.
    3. Prepares the row with the duplicate flag.
    4. Appends to CSV.
    """
    if not raw_ip:
        raise ValueError("Raw IP address is required for submission")
    
    hashed_ip = hash_ip(raw_ip)
    is_duplicate = check_duplicate_ip(hashed_ip)
    
    # Note: The task description says "Write the hashed IP and a duplicate_flag".
    # We are adding 'duplicate_flag' to the row.
    row = prepare_submission_row(
        user_id=user_id,
        condition=condition,
        credibility_rating=credibility_rating,
        professionalism_rating=professionalism_rating,
        timestamp=timestamp,
        device_info=device_info,
        hashed_ip=hashed_ip,
        age=age,
        education_code=education_code,
        submission_status=submission_status,
        session_timeout=session_timeout
    )
    row['duplicate_flag'] = is_duplicate
    
    append_to_submissions_csv(row)
