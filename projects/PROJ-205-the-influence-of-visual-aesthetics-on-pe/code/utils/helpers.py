import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List

# Constants
DATA_RAW_DIR = "data/raw"
SUBMISSIONS_FILE = os.path.join(DATA_RAW_DIR, "submissions.csv")
CSV_HEADER = [
    "timestamp", "user_id", "ip_hash", "duplicate_flag", 
    "condition", "credibility_rating", "professionalism_rating",
    "age", "education_code", "user_agent", "session_timeout",
    "submission_status", "rating_count"
]

def ensure_data_dirs():
    """Ensure data/raw and data/processed directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

def generate_user_id():
    """Generate a unique anonymous user ID."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    Returns the hexadecimal digest.
    """
    if not ip_address:
        return ""
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp():
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()

def get_consent_log_path():
    """Return path to consent log file."""
    return os.path.join(DATA_RAW_DIR, "consent_log.csv")

def log_consent_decision(user_id: str, decision: str, protocol_id: str):
    """Log consent decision to consent_log.csv."""
    ensure_data_dirs()
    log_path = get_consent_log_path()
    file_exists = os.path.isfile(log_path)
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "user_id", "decision", "protocol_id"])
        writer.writerow([format_timestamp(), user_id, decision, protocol_id])

def validate_rating_count(ratings: List[Any]) -> bool:
    """Check if the number of ratings is exactly 8 (4 stimuli * 2 ratings)."""
    return len(ratings) == 8

def truncate_user_agent(user_agent: str, max_length: int = 200) -> str:
    """Truncate user agent string to prevent CSV bloat."""
    if not user_agent:
        return ""
    return user_agent[:max_length]

def check_duplicate_ip(ip_hash: str) -> bool:
    """
    Check if the hashed IP already exists in submissions.csv.
    Returns True if a duplicate is found, False otherwise.
    """
    if not ip_hash:
        return False
    
    if not os.path.exists(SUBMISSIONS_FILE):
        return False
    
    try:
        with open(SUBMISSIONS_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Ensure the column exists before checking
            if 'ip_hash' not in reader.fieldnames:
                return False
            
            for row in reader:
                if row.get('ip_hash') == ip_hash:
                    return True
    except Exception:
        # If file is corrupted or locked, assume no duplicate to allow submission
        # but log warning in a real system
        return False
    
    return False

def prepare_submission_row(
    user_id: str, 
    ip_hash: str, 
    condition: str, 
    ratings: Dict[str, int], 
    age: int, 
    education_code: int, 
    user_agent: str,
    session_timeout: bool = False,
    submission_status: str = 'complete'
) -> Dict[str, Any]:
    """
    Prepare a dictionary row for submission CSV.
    Calculates duplicate_flag based on existing records.
    """
    is_duplicate = check_duplicate_ip(ip_hash)
    
    # Flatten ratings
    credibility = ratings.get('credibility', 0)
    professionalism = ratings.get('professionalism', 0)
    
    return {
        "timestamp": format_timestamp(),
        "user_id": user_id,
        "ip_hash": ip_hash,
        "duplicate_flag": 1 if is_duplicate else 0,
        "condition": condition,
        "credibility_rating": credibility,
        "professionalism_rating": professionalism,
        "age": age,
        "education_code": education_code,
        "user_agent": truncate_user_agent(user_agent),
        "session_timeout": str(session_timeout).lower(),
        "submission_status": submission_status,
        "rating_count": 2 # Assuming one row per stimulus in a wider schema, or 8 if aggregated
    }

def append_to_submissions_csv(row: Dict[str, Any]):
    """Append a single submission row to submissions.csv."""
    ensure_data_dirs()
    file_exists = os.path.isfile(SUBMISSIONS_FILE)
    
    with open(SUBMISSIONS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(
    user_id: str,
    ip_hash: str,
    condition: str,
    ratings: Dict[str, int],
    age: int,
    education_code: int,
    user_agent: str,
    session_timeout: bool = False,
    submission_status: str = 'complete'
):
    """
    High-level function to prepare and save a submission.
    Handles duplicate checking and CSV writing.
    """
    row = prepare_submission_row(
        user_id=user_id,
        ip_hash=ip_hash,
        condition=condition,
        ratings=ratings,
        age=age,
        education_code=education_code,
        user_agent=user_agent,
        session_timeout=session_timeout,
        submission_status=submission_status
    )
    append_to_submissions_csv(row)
    return row["duplicate_flag"] == 1
