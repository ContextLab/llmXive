"""
Utility functions for the Visual Aesthetics Credibility Survey.
Handles ID generation, hashing, CSV operations, and consent logging.
"""
import hashlib
import uuid
import os
import csv
import json
import yaml
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import local project root logic
def get_project_root() -> Path:
    """Get the absolute path to the project root."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs() -> None:
    """Ensure all required data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (root / "data" / "consent").mkdir(parents=True, exist_ok=True)
    (root / "state" / "projects").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path() -> Path:
    """Return the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_consent_log_path() -> Path:
    """Return the path to the consent log CSV."""
    return get_project_root() / "data" / "raw" / "consent_log.csv"

def get_duplicate_audit_path() -> Path:
    """Return the path to the duplicate audit JSON."""
    return get_project_root() / "data" / "processed" / "duplicate_audit.json"

def get_state_file_path() -> Path:
    """Return the path to the session state file."""
    return get_project_root() / "state" / "projects" / "session_state.json"

def generate_user_id() -> str:
    """Generate a unique UUID v4 for a participant."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str, salt: Optional[str] = None) -> str:
    """
    Hash an IP address using SHA-256 with a salt.
    
    Args:
        ip_address: The raw IP address string.
        salt: Optional salt string. If None, attempts to load from 
              IP_HASH_SALT environment variable.
    
    Returns:
        Hex digest of the hash.
    
    Raises:
        ValueError: If salt is missing in both arguments and environment.
    """
    if salt is None:
        salt = os.environ.get("IP_HASH_SALT")
        if not salt:
            raise ValueError(
                "IP_HASH_SALT environment variable is not set. "
                "Please set it in your .env file."
            )
    
    # Combine salt and IP
    salted_string = f"{salt}{ip_address}"
    return hashlib.sha256(salted_string.encode('utf-8')).hexdigest()

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime object to a standard ISO string."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def compute_consent_form_hash(text: str) -> str:
    """Compute SHA-256 hash of the consent text for verification."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def log_consent_decision(
    user_id: str, 
    decision: str, 
    protocol_id: str,
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log a consent decision to the consent log CSV.
    
    Args:
        user_id: The participant ID.
        decision: 'agreed' or 'declined'.
        protocol_id: The IRB protocol ID.
        timestamp: Optional timestamp (defaults to now).
    """
    ensure_data_dirs()
    path = get_consent_log_path()
    
    fieldnames = ['timestamp', 'user_id', 'decision', 'IRB_PROTOCOL_ID']
    row = {
        'timestamp': format_timestamp(timestamp),
        'user_id': user_id,
        'decision': decision,
        'IRB_PROTOCOL_ID': protocol_id
    }
    
    # Check if file exists to determine if header is needed
    write_header = not path.exists()
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

def validate_rating_count(ratings: Dict[str, Any]) -> bool:
    """
    Validate that a participant has rated at least 4 stimuli.
    
    Args:
        ratings: Dictionary of stimulus_id -> rating values.
    
    Returns:
        True if count >= 4, False otherwise.
    """
    return len([k for k, v in ratings.items() if v is not None]) >= 4

def calculate_safe_truncation_length(max_length: int = 100) -> int:
    """
    Calculate a safe truncation length for metadata fields.
    
    Args:
        max_length: Maximum allowed length.
    
    Returns:
        Safe length (max_length - 1 to ensure no overflow).
    """
    return max_length - 1

def truncate_user_agent(user_agent: str, max_length: int = 100) -> str:
    """
    Truncate a user agent string to a safe length.
    
    Args:
        user_agent: The raw user agent string.
        max_length: Maximum length to truncate to.
    
    Returns:
        Truncated string.
    """
    safe_len = calculate_safe_truncation_length(max_length)
    return user_agent[:safe_len]

def get_education_code(education: str) -> str:
    """
    Map education string to a standardized code.
    
    Args:
        education: Raw education string.
    
    Returns:
        Standardized code (e.g., 'HS', 'BA', 'GR').
    """
    education_lower = education.lower()
    if 'high school' in education_lower or 'ged' in education_lower:
        return 'HS'
    elif 'bachelor' in education_lower or 'ba' in education_lower:
        return 'BA'
    elif 'master' in education_lower or 'ma' in education_lower:
        return 'MA'
    elif 'phd' in education_lower or 'doctorate' in education_lower:
        return 'PHD'
    elif 'some college' in education_lower:
        return 'SC'
    else:
        return 'UNKNOWN'

def get_current_csv_size() -> int:
    """
    Get the current size of the submissions CSV in bytes.
    
    Returns:
        File size in bytes.
    """
    path = get_submissions_csv_path()
    if not path.exists():
        return 0
    return path.stat().st_size

def check_duplicate_ip(hashed_ip: str) -> bool:
    """
    Check if a hashed IP has already been submitted.
    
    Args:
        hashed_ip: The hashed IP string.
    
    Returns:
        True if duplicate, False otherwise.
    """
    path = get_submissions_csv_path()
    if not path.exists():
        return False
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == hashed_ip:
                return True
    return False

def prepare_submission_row(
    participant_id: str,
    age: int,
    education: str,
    hashed_ip: str,
    user_agent: str,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Prepare a row for submission to the CSV.
    
    Args:
        participant_id: Unique participant ID.
        age: Participant age.
        education: Education level string.
        hashed_ip: Hashed IP address.
        user_agent: Raw user agent string.
        timestamp: Optional timestamp.
    
    Returns:
        Dictionary ready for CSV writing.
    """
    return {
        'participant_id': participant_id,
        'age': age,
        'education': get_education_code(education),
        'timestamp': format_timestamp(timestamp),
        'hashed_ip': hashed_ip,
        'user_agent_hash': hashlib.sha256(user_agent.encode('utf-8')).hexdigest()
    }

def append_to_submissions_csv(row: Dict[str, Any]) -> None:
    """
    Append a row to the submissions CSV using atomic write.
    
    Args:
        row: Dictionary of field values.
    
    Raises:
        IOError: If disk is full or write fails.
    """
    ensure_data_dirs()
    path = get_submissions_csv_path()
    fieldnames = ['participant_id', 'age', 'education', 'timestamp', 'hashed_ip', 'user_agent_hash']
    
    # Atomic write: write to temp file, then rename
    try:
        # Determine if header is needed
        write_header = not path.exists()
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False, 
            newline='', 
            encoding='utf-8',
            dir=path.parent
        ) as tmp_file:
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
            tmp_name = tmp_file.name
        
        # Rename to final path
        os.replace(tmp_name, path)
        
    except OSError as e:
        # Clean up temp file if it exists
        if 'tmp_name' in locals() and os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise IOError(f"Failed to write to submissions CSV: {e}") from e

def save_submission(
    participant_id: str,
    age: int,
    education: str,
    hashed_ip: str,
    user_agent: str,
    timestamp: Optional[datetime] = None
) -> None:
    """
    High-level function to save a complete submission.
    
    Args:
        participant_id: Unique participant ID.
        age: Participant age.
        education: Education level string.
        hashed_ip: Hashed IP address.
        user_agent: Raw user agent string.
        timestamp: Optional timestamp.
    """
    row = prepare_submission_row(
        participant_id, age, education, hashed_ip, user_agent, timestamp
    )
    append_to_submissions_csv(row)

def write_audit_log(
    audit_type: str, 
    details: Dict[str, Any], 
    timestamp: Optional[datetime] = None
) -> None:
    """
    Write an audit log entry to the processed directory.
    
    Args:
        audit_type: Type of audit (e.g., 'duplicate_check', 'integrity').
        details: Dictionary of audit details.
        timestamp: Optional timestamp.
    """
    ensure_data_dirs()
    path = get_project_root() / "data" / "processed" / "audit_log.json"
    
    entry = {
        'timestamp': format_timestamp(timestamp),
        'audit_type': audit_type,
        'details': details
    }
    
    # Load existing log if it exists
    log = []
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []
    
    log.append(entry)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hex digest of the checksum.
    
    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def store_data_checksum(file_path: Path, checksum: str) -> None:
    """
    Store a checksum in the state directory.
    
    Args:
        file_path: Path to the file being checksummed.
        checksum: The checksum string.
    """
    ensure_data_dirs()
    state_path = get_project_root() / "state" / "projects" / "checksums.json"
    
    checksums = {}
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            checksums = json.load(f)
    
    checksums[str(file_path)] = checksum
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def verify_data_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
    
    Returns:
        True if checksums match, False otherwise.
    
    Raises:
        FileNotFoundError: If file does not exist.
    """
    actual = compute_file_checksum(file_path)
    return actual == expected_checksum