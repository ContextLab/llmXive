"""
Helper functions for the Visual Aesthetics study.
"""
import hashlib
import uuid
import os
import csv
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory."""
    # Assuming this file is at code/utils/helpers.py
    return Path(__file__).resolve().parents[2]


def ensure_data_dirs(project_root: Optional[Path] = None) -> None:
    """Ensure required data directories exist."""
    if project_root is None:
        project_root = get_project_root()
    (project_root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "data" / "consent").mkdir(parents=True, exist_ok=True)


def get_submissions_csv_path(project_root: Optional[Path] = None) -> Path:
    """Return the path to data/raw/submissions.csv."""
    if project_root is None:
        project_root = get_project_root()
    return project_root / "data" / "raw" / "submissions.csv"


def get_consent_log_path(project_root: Optional[Path] = None) -> Path:
    """Return the path to data/raw/consent_log.csv."""
    if project_root is None:
        project_root = get_project_root()
    return project_root / "data" / "raw" / "consent_log.csv"


def get_duplicate_audit_path(project_root: Optional[Path] = None) -> Path:
    """Return the path to data/raw/duplicate_audit.csv."""
    if project_root is None:
        project_root = get_project_root()
    return project_root / "data" / "raw" / "duplicate_audit.csv"


def generate_user_id() -> str:
    """Generate a unique participant ID (UUID v4)."""
    return str(uuid.uuid4())


def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using SHA-256.
    Returns a truncated hex string for privacy.
    """
    if not ip_address:
        return ""
    sha256_hash = hashlib.sha256(ip_address.encode('utf-8')).hexdigest()
    # Return first 16 chars for brevity, still unique enough for collision detection
    return sha256_hash[:16]


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime object as ISO 8601 string."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def log_consent_decision(
    user_id: str,
    decision: str,
    ip_hash: str,
    irb_protocol_id: str,
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log a consent decision to data/raw/consent_log.csv.

    Args:
        user_id: The participant's unique ID.
        decision: 'Agree' or 'Disagree'.
        ip_hash: Hashed IP address.
        irb_protocol_id: The IRB protocol ID.
        timestamp: Optional timestamp (defaults to now).
    """
    if timestamp is None:
        timestamp = datetime.now()

    ensure_data_dirs()
    path = get_consent_log_path()

    file_exists = path.exists()

    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'timestamp', 'user_id', 'decision', 'hashed_ip', 'irb_protocol_id'
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': format_timestamp(timestamp),
            'user_id': user_id,
            'decision': decision,
            'hashed_ip': ip_hash,
            'irb_protocol_id': irb_protocol_id
        })


def validate_rating_count(count: int, min_required: int = 8) -> bool:
    """Check if the rating count meets the minimum requirement."""
    return count >= min_required


def calculate_safe_truncation_length(max_length: int = 255) -> int:
    """Return the safe truncation length for metadata fields."""
    return max_length


def truncate_user_agent(user_agent: str, max_length: int = 255) -> str:
    """Truncate user agent string to max_length."""
    if not user_agent:
        return ""
    return user_agent[:max_length]


def get_current_csv_size(path: Path) -> int:
    """Return the size of the CSV file in bytes, or 0 if it doesn't exist."""
    if path.exists():
        return path.stat().st_size
    return 0


def check_duplicate_ip(
    ip_hash: str,
    submissions_path: Optional[Path] = None
) -> bool:
    """
    Check if an IP hash already exists in the submissions CSV.
    Note: This is a simple linear check. For large datasets, a DB or
    in-memory index is preferred.

    Args:
        ip_hash: The hashed IP to check.
        submissions_path: Optional path to submissions CSV.

    Returns:
        True if duplicate found, False otherwise.
    """
    if submissions_path is None:
        submissions_path = get_submissions_csv_path()

    if not submissions_path.exists():
        return False

    with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == ip_hash:
                return True
    return False


def get_education_code(education: str) -> int:
    """
    Convert education string to integer code.
    Mapping: High School=1, Bachelor's=2, Master's=3, PhD=4
    """
    mapping = {
        "High School": 1,
        "Bachelor's": 2,
        "Master's": 3,
        "PhD": 4
    }
    return mapping.get(education, 0)


def prepare_submission_row(
    participant_id: str,
    stimulus_id: str,
    credibility: int,
    professionalism: int,
    timestamp: datetime,
    hashed_ip: str,
    age: int,
    education_code: int,
    duplicate_flag: bool = False,
    session_status: str = "complete",
    submission_status: str = "submitted",
    user_agent: str = ""
) -> Dict[str, Any]:
    """Prepare a dictionary row for submission."""
    return {
        'participant_id': participant_id,
        'stimulus_id': stimulus_id,
        'credibility': credibility,
        'professionalism': professionalism,
        'timestamp': format_timestamp(timestamp),
        'hashed_ip': hashed_ip,
        'age': age,
        'education': education_code,
        'duplicate_flag': str(duplicate_flag).lower(),
        'session_status': session_status,
        'submission_status': submission_status,
        'user_agent': truncate_user_agent(user_agent)
    }


def append_to_submissions_csv(
    row: Dict[str, Any],
    path: Optional[Path] = None
) -> None:
    """Append a row to the submissions CSV."""
    if path is None:
        path = get_submissions_csv_path()

    ensure_data_dirs()
    file_exists = path.exists()

    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
        'session_status', 'submission_status', 'user_agent'
    ]

    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def save_submission(
    participant_id: str,
    stimulus_id: str,
    credibility: int,
    professionalism: int,
    hashed_ip: str,
    age: int,
    education: str,
    timestamp: Optional[datetime] = None,
    user_agent: str = "",
    path: Optional[Path] = None
) -> None:
    """
    Convenience function to save a single submission row.
    Calculates education code and prepares the row.
    """
    if timestamp is None:
        timestamp = datetime.now()

    education_code = get_education_code(education)
    row = prepare_submission_row(
        participant_id=participant_id,
        stimulus_id=stimulus_id,
        credibility=credibility,
        professionalism=professionalism,
        timestamp=timestamp,
        hashed_ip=hashed_ip,
        age=age,
        education_code=education_code,
        user_agent=user_agent
    )
    append_to_submissions_csv(row, path)
