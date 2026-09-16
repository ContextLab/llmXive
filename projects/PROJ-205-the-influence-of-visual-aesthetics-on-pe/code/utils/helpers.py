"""
Helper utilities for the Visual Aesthetics Credibility Survey project.
Provides functions for ID generation, data formatting, CSV handling, and IP hashing.
"""
import hashlib
import uuid
import os
import csv
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Constants
USER_AGENT_MAX_LENGTH = 255
SUBMISSIONS_FILENAME = "submissions.csv"
SUBMISSIONS_PATH = "data/raw/submissions.csv"
CONSENT_LOG_PATH = "data/consent/consent_log.csv"
DUPLICATE_AUDIT_PATH = "data/raw/duplicate_audit.csv"

# Education mapping (Ordinal)
EDUCATION_MAPPING = {
    "High School": 1,
    "Bachelor's": 2,
    "Master's": 3,
    "PhD": 4
}

def get_project_root() -> Path:
    """Returns the root directory of the project (parent of 'code')."""
    current_file = Path(__file__).resolve()
    # Assuming this file is at code/utils/helpers.py
    return current_file.parent.parent.parent

def ensure_data_dirs() -> None:
    """Creates necessary data directories if they don't exist."""
    root = get_project_root()
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    consent_dir = root / "data" / "consent"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    consent_dir.mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path() -> Path:
    """Returns the absolute path to the submissions CSV file."""
    root = get_project_root()
    return root / SUBMISSIONS_PATH

def get_consent_log_path() -> Path:
    """Returns the absolute path to the consent log CSV file."""
    root = get_project_root()
    return root / "data" / "consent" / "consent_log.csv"

def get_duplicate_audit_path() -> Path:
    """Returns the absolute path to the duplicate audit CSV file."""
    root = get_project_root()
    return root / "data" / "raw" / "duplicate_audit.csv"

def generate_user_id() -> str:
    """Generates a unique participant ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hashes an IP address using SHA-256 for privacy compliance.
    Returns the hexadecimal digest.
    """
    if not ip_address:
        raise ValueError("IP address cannot be empty")
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Formats a datetime object to ISO 8601 string. Defaults to now."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def log_consent_decision(user_id: str, decision: bool, irb_protocol_id: str) -> None:
    """
    Logs a consent decision to the consent log CSV.
    decision: True for 'I Agree', False for 'I Do Not Agree'
    """
    ensure_data_dirs()
    path = get_consent_log_path()
    timestamp = format_timestamp()
    
    file_exists = path.exists()
    
    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'user_id', 'decision', 'irb_protocol_id'])
        
        writer.writerow([
            timestamp,
            user_id,
            "Agreed" if decision else "Denied",
            irb_protocol_id
        ])

def validate_rating_count(count: int, min_required: int = 8) -> bool:
    """Validates that the number of ratings meets the minimum requirement."""
    return count >= min_required

def calculate_safe_truncation_length(max_length: int = USER_AGENT_MAX_LENGTH) -> int:
    """Returns the safe truncation length for metadata fields."""
    return max_length

def truncate_user_agent(user_agent: str, max_length: int = USER_AGENT_MAX_LENGTH) -> str:
    """Truncates the user agent string to the specified maximum length."""
    if not user_agent:
        return ""
    return user_agent[:max_length]

def get_education_code(education_str: str) -> int:
    """
    Converts education string to ordinal code.
    Raises KeyError if invalid.
    """
    return EDUCATION_MAPPING[education_str]

def get_current_csv_size(path: Path) -> int:
    """Returns the size of the file in bytes, or 0 if it doesn't exist."""
    if path.exists():
        return path.stat().st_size
    return 0

def check_duplicate_ip(hashed_ip: str, current_path: Path) -> bool:
    """
    Checks if a hashed IP already exists in the submissions CSV.
    Returns True if duplicate found, False otherwise.
    """
    if not current_path.exists():
        return False
    
    try:
        with open(current_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('hashed_ip') == hashed_ip:
                    return True
    except Exception:
        # If file is corrupted or unreadable, assume safe to proceed or handle externally
        pass
    return False

def prepare_submission_row(
    participant_id: str,
    stimulus_id: str,
    credibility: int,
    professionalism: int,
    timestamp: str,
    hashed_ip: str,
    age: int,
    education_code: int,
    duplicate_flag: bool,
    session_status: str,
    submission_status: str,
    user_agent: str = ""
) -> Dict[str, Any]:
    """
    Prepares a dictionary row for the submissions CSV.
    Handles truncation of user_agent.
    """
    return {
        "participant_id": participant_id,
        "stimulus_id": stimulus_id,
        "credibility": credibility,
        "professionalism": professionalism,
        "timestamp": timestamp,
        "hashed_ip": hashed_ip,
        "age": age,
        "education": education_code,
        "duplicate_flag": duplicate_flag,
        "session_status": session_status,
        "submission_status": submission_status,
        "user_agent": truncate_user_agent(user_agent)
    }

def append_to_submissions_csv(row_data: Dict[str, Any]) -> None:
    """
    Appends a single row to the submissions CSV file.
    Creates the file with headers if it does not exist.
    """
    ensure_data_dirs()
    path = get_submissions_csv_path()
    
    fieldnames = [
        "participant_id", "stimulus_id", "credibility", "professionalism",
        "timestamp", "hashed_ip", "age", "education", "duplicate_flag",
        "session_status", "submission_status", "user_agent"
    ]
    
    file_exists = path.exists()
    
    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)

def save_submission(
    participant_id: str,
    stimulus_id: str,
    credibility: int,
    professionalism: int,
    hashed_ip: str,
    age: int,
    education_str: str,
    session_status: str,
    submission_status: str,
    user_agent: str = "",
    timestamp: Optional[datetime] = None
) -> None:
    """
    High-level function to save a single submission to the CSV.
    Handles education mapping, timestamp formatting, and duplicate checking.
    """
    education_code = get_education_code(education_str)
    ts = format_timestamp(timestamp)
    
    # Check for duplicate IP
    path = get_submissions_csv_path()
    is_duplicate = check_duplicate_ip(hashed_ip, path)
    
    row = prepare_submission_row(
        participant_id=participant_id,
        stimulus_id=stimulus_id,
        credibility=credibility,
        professionalism=professionalism,
        timestamp=ts,
        hashed_ip=hashed_ip,
        age=age,
        education_code=education_code,
        duplicate_flag=is_duplicate,
        session_status=session_status,
        submission_status=submission_status,
        user_agent=user_agent
    )
    
    append_to_submissions_csv(row)

def write_audit_log(duplicates: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """
    Writes duplicate detection results to the audit log CSV.
    """
    if output_path is None:
        output_path = get_duplicate_audit_path()
    
    ensure_data_dirs()
    
    fieldnames = ["hashed_ip", "count", "participant_ids", "first_seen", "last_seen"]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for dup in duplicates:
            writer.writerow(dup)