import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Constants
USER_AGENT_MAX_LENGTH = 255
SUBMISSIONS_FILENAME = "submissions.csv"
CONSENT_LOG_FILENAME = "consent_log.csv"
DUPLICATE_AUDIT_FILENAME = "duplicate_audit.csv"


def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    # Assuming the code structure is code/utils/helpers.py, project root is 3 levels up
    return Path(__file__).resolve().parent.parent.parent


def ensure_data_dirs() -> None:
    """Ensure raw and processed data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)


def get_submissions_csv_path() -> Path:
    """Return the full path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / SUBMISSIONS_FILENAME


def get_consent_log_path() -> Path:
    """Return the full path to the consent log CSV file."""
    return get_project_root() / "data" / "raw" / CONSENT_LOG_FILENAME


def get_duplicate_audit_path() -> Path:
    """Return the full path to the duplicate audit CSV file."""
    return get_project_root() / "data" / "raw" / DUPLICATE_AUDIT_FILENAME


def generate_user_id() -> str:
    """Generate a unique UUID v4 for a participant."""
    return str(uuid.uuid4())


def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    Returns the hex digest.
    """
    if not ip_address:
        return ""
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime object to ISO 8601 string."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def log_consent_decision(
    user_id: str,
    decision: str,
    irb_protocol_id: str,
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log a consent decision to the consent log CSV.
    decision: 'agreed' or 'withdrawn'
    """
    ensure_data_dirs()
    path = get_consent_log_path()
    fieldnames = ['timestamp', 'user_id', 'decision', 'irb_protocol_id']

    file_exists = path.exists()

    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'timestamp': format_timestamp(timestamp),
            'user_id': user_id,
            'decision': decision,
            'irb_protocol_id': irb_protocol_id
        })


def validate_rating_count(count: int, minimum: int = 8) -> bool:
    """Check if the number of ratings meets the minimum requirement."""
    return count >= minimum


def calculate_safe_truncation_length(current_length: int, max_length: int = USER_AGENT_MAX_LENGTH) -> int:
    """Calculate the safe length to truncate a string, ensuring it doesn't exceed max_length."""
    return min(current_length, max_length)


def truncate_user_agent(user_agent: str) -> str:
    """Truncate user_agent string to USER_AGENT_MAX_LENGTH characters."""
    if not user_agent:
        return ""
    return user_agent[:USER_AGENT_MAX_LENGTH]


def get_current_csv_size(path: Path) -> int:
    """Get the current size of a CSV file in bytes."""
    if path.exists():
        return path.stat().st_size
    return 0


def check_duplicate_ip(
    submissions_path: Path,
    target_ip_hash: str
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if a hashed IP already exists in the submissions CSV.
    Returns (is_duplicate, list_of_matching_rows).
    """
    if not submissions_path.exists():
        return False, []

    duplicates = []
    with open(submissions_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == target_ip_hash:
                duplicates.append(row)

    return len(duplicates) > 0, duplicates


def get_education_code(education_label: str) -> int:
    """
    Convert education label to an integer code.
    Mapping:
      High School -> 1
      Bachelor's -> 2
      Master's -> 3
      PhD -> 4
    Returns 0 if label is unknown.
    """
    mapping = {
        "High School": 1,
        "Bachelor's": 2,
        "Master's": 3,
        "PhD": 4
    }
    return mapping.get(education_label, 0)


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
    submission_status: str
) -> Dict[str, Any]:
    """
    Prepare a dictionary row for the submissions CSV.
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
        "submission_status": submission_status
    }


def append_to_submissions_csv(row: Dict[str, Any]) -> None:
    """
    Append a single row to the submissions CSV.
    Creates the file and header if it doesn't exist.
    """
    ensure_data_dirs()
    path = get_submissions_csv_path()
    fieldnames = [
        "participant_id", "stimulus_id", "credibility", "professionalism",
        "timestamp", "hashed_ip", "age", "education",
        "duplicate_flag", "session_status", "submission_status"
    ]

    file_exists = path.exists()

    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def save_submission(
    participant_id: str,
    stimulus_id: str,
    credibility: int,
    professionalism: int,
    timestamp: str,
    hashed_ip: str,
    age: int,
    education_label: str,
    duplicate_flag: bool,
    session_status: str,
    submission_status: str
) -> None:
    """
    High-level function to save a single submission to the CSV.
    Converts education label to code and truncates user agent if needed (handled by caller).
    """
    education_code = get_education_code(education_label)
    row = prepare_submission_row(
        participant_id=participant_id,
        stimulus_id=stimulus_id,
        credibility=credibility,
        professionalism=professionalism,
        timestamp=timestamp,
        hashed_ip=hashed_ip,
        age=age,
        education_code=education_code,
        duplicate_flag=duplicate_flag,
        session_status=session_status,
        submission_status=submission_status
    )
    append_to_submissions_csv(row)
