import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List
import ipaddress

# Constants
DATA_RAW_DIR = "data/raw"
SUBMISSIONS_FILE = "data/raw/submissions.csv"
CONSENT_LOG_FILE = "data/consent/consent_log.csv"

def ensure_data_dirs():
    """Ensure required data directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/consent", exist_ok=True)

def generate_user_id() -> str:
    """Generate a unique, random participant ID."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    Returns the hex digest.
    """
    if not ip_address:
        return ""
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()

def get_consent_log_path() -> str:
    """Return path to consent log file."""
    return CONSENT_LOG_FILE

def log_consent_decision(user_id: str, decision: str, protocol_id: str):
    """Log a consent decision to the consent log."""
    ensure_data_dirs()
    timestamp = format_timestamp()
    with open(CONSENT_LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, user_id, decision, protocol_id])

def validate_rating_count(count: int) -> bool:
    """Check if rating count meets minimum requirement (8)."""
    return count >= 8

def truncate_user_agent(user_agent: str, max_length: int = 255) -> str:
    """Truncate user agent string to safe length."""
    if not user_agent:
        return ""
    return user_agent[:max_length]

def check_duplicate_ip(hashed_ip: str) -> bool:
    """
    Check if a hashed IP already exists in submissions.
    Returns True if duplicate found.
    """
    if not hashed_ip:
        return False
    
    if not os.path.exists(SUBMISSIONS_FILE):
        return False
    
    try:
        with open(SUBMISSIONS_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('hashed_ip') == hashed_ip:
                    return True
        return False
    except Exception:
        return False

def prepare_submission_row(
    user_id: str,
    condition: str,
    ratings: Dict[str, int],
    timestamp: str,
    device_info: str,
    hashed_ip: str,
    age: int,
    education: int,
    session_timeout: bool = False,
    submission_status: str = 'complete'
) -> Dict[str, Any]:
    """
    Prepare a submission row dictionary with all required fields.
    
    Args:
        user_id: Unique participant identifier
        condition: Stimulus condition name
        ratings: Dict of rating categories to values
        timestamp: ISO timestamp string
        device_info: Device/browser info string
        hashed_ip: Hashed IP address
        age: Participant age (integer)
        education: Education level code (1-4)
        session_timeout: Boolean flag for browser close/timeout
        submission_status: 'complete' or 'excluded'
    
    Returns:
        Dictionary ready for CSV writing
    """
    # Flatten ratings into columns
    row = {
        'user_id': user_id,
        'condition': condition,
        'credibility_rating': ratings.get('credibility', 0),
        'professionalism_rating': ratings.get('professionalism', 0),
        'timestamp': timestamp,
        'device_info': device_info,
        'hashed_ip': hashed_ip,
        'age': age,
        'education': education,
        'session_timeout': str(session_timeout).lower(),
        'submission_status': submission_status,
        'rating_count': len(ratings)
    }
    return row

def append_to_submissions_csv(row: Dict[str, Any]):
    """
    Append a submission row to the CSV file.
    
    Args:
        row: Dictionary containing submission data
    """
    ensure_data_dirs()
    
    file_exists = os.path.exists(SUBMISSIONS_FILE)
    fieldnames = [
        'user_id', 'condition', 'credibility_rating', 'professionalism_rating',
        'timestamp', 'device_info', 'hashed_ip', 'age', 'education',
        'session_timeout', 'submission_status', 'rating_count'
    ]
    
    with open(SUBMISSIONS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(
    user_id: str,
    condition: str,
    ratings: Dict[str, int],
    timestamp: str,
    device_info: str,
    raw_ip: Optional[str],
    age: int,
    education: int,
    session_timeout: bool = False,
    submission_status: str = 'complete'
):
    """
    Complete submission workflow: hash IP, check duplicates, prepare row, save to CSV.
    
    Args:
        user_id: Unique participant identifier
        condition: Stimulus condition name
        ratings: Dict of rating categories to values
        timestamp: ISO timestamp string
        device_info: Device/browser info string
        raw_ip: Raw IP address (will be hashed immediately)
        age: Participant age (integer)
        education: Education level code (1-4)
        session_timeout: Boolean flag for browser close/timeout
        submission_status: 'complete' or 'excluded'
    """
    # Hash IP immediately - never store raw
    hashed_ip = hash_ip(raw_ip) if raw_ip else ""
    
    # Check for duplicates only if we have a valid IP
    is_duplicate = check_duplicate_ip(hashed_ip) if hashed_ip else False
    
    # Prepare the row with session flags
    row = prepare_submission_row(
        user_id=user_id,
        condition=condition,
        ratings=ratings,
        timestamp=timestamp,
        device_info=device_info,
        hashed_ip=hashed_ip,
        age=age,
        education=education,
        session_timeout=session_timeout,
        submission_status=submission_status
    )
    
    # Add duplicate flag to the row for analysis
    row['is_duplicate'] = str(is_duplicate).lower()
    
    # Append to CSV
    append_to_submissions_csv(row)
