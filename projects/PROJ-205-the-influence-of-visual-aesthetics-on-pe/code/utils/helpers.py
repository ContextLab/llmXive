import hashlib
import uuid
import os
import csv
import json
import yaml
import random
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Global seed enforcement
_SEED_SET = False

def set_reproducibility_seed(seed: Optional[int] = None) -> int:
    """
    Sets the global random seed for numpy and python random modules.
    
    Args:
        seed: The seed value. If None, reads from RANDOM_SEED env var, 
              defaulting to 42.
    
    Returns:
        The seed value that was set.
    
    Raises:
        ValueError: If the seed value is not a valid integer.
    """
    global _SEED_SET
    
    if seed is None:
        seed_str = os.environ.get("RANDOM_SEED")
        if seed_str is not None:
            try:
                seed = int(seed_str)
            except ValueError:
                raise ValueError(f"RANDOM_SEED environment variable must be an integer, got: {seed_str}")
        else:
            seed = 42
    
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got: {type(seed)}")
    
    # Set seeds
    random.seed(seed)
    np.random.seed(seed)
    
    _SEED_SET = True
    return seed

def is_seed_set() -> bool:
    """Returns True if the reproducibility seed has been set."""
    return _SEED_SET

# Existing helper functions (preserved from original file)
def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs() -> None:
    """Ensures that data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (root / "data" / "consent").mkdir(parents=True, exist_ok=True)
    (root / "data" / "backups").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path() -> Path:
    """Returns the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_consent_log_path() -> Path:
    """Returns the path to the consent log CSV file."""
    return get_project_root() / "data" / "processed" / "consent_log.csv"

def get_duplicate_audit_path() -> Path:
    """Returns the path to the duplicate audit CSV file."""
    return get_project_root() / "data" / "processed" / "duplicate_audit.csv"

def get_state_file_path() -> Path:
    """Returns the path to the state JSON file."""
    return get_project_root() / "state" / "project_state.json"

def get_checksum_store_path() -> Path:
    """Returns the path to the checksum store JSON file."""
    return get_project_root() / "data" / "raw" / ".checksums.json"

def get_excluded_audit_path() -> Path:
    """Returns the path to the excluded audit CSV file."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def generate_user_id() -> str:
    """Generates a unique user ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str) -> str:
    """
    Hashes an IP address using PBKDF2 with SHA-256.
    
    Args:
        ip_address: The IP address to hash.
    
    Returns:
        The hashed IP address as a hex string.
    
    Raises:
        ValueError: If the IP_HASH_SALT environment variable is not set.
    """
    salt_str = os.environ.get("IP_HASH_SALT")
    if not salt_str:
        raise ValueError("IP_HASH_SALT environment variable must be set for IP hashing")
    
    salt = salt_str.encode('utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', ip_address.encode('utf-8'), salt, 100000)
    return dk.hex()

def format_timestamp(dt) -> str:
    """Formats a datetime object to ISO8601 string."""
    from datetime import datetime
    if isinstance(dt, str):
        return dt
    return dt.isoformat()

def compute_consent_form_hash() -> str:
    """Computes the SHA-256 hash of the consent form content."""
    consent_path = get_project_root() / "data" / "consent" / "irb_approved.txt"
    if not consent_path.exists():
        raise FileNotFoundError(f"Consent file not found: {consent_path}")
    
    with open(consent_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def truncate_user_agent(user_agent: str, max_length: int = 100) -> str:
    """Truncates a user agent string to a maximum length."""
    if len(user_agent) <= max_length:
        return user_agent
    return user_agent[:max_length] + "..."

def get_education_code(education: str) -> str:
    """Maps education level to a standardized code."""
    education_map = {
        "High School": "HS",
        "Some College": "SC",
        "Bachelor's Degree": "BA",
        "Master's Degree": "MA",
        "Doctorate": "PhD",
        "Other": "OTH"
    }
    return education_map.get(education, "OTH")

def get_current_csv_size(csv_path: Path) -> int:
    """Returns the current size of a CSV file in bytes."""
    if not csv_path.exists():
        return 0
    return csv_path.stat().st_size

def validate_rating_count(ratings: List[float], min_required: int = 4) -> bool:
    """Validates that the number of ratings meets the minimum requirement."""
    return len(ratings) >= min_required

def check_duplicate_ip(hashed_ip: str, existing_hashes: List[str]) -> bool:
    """Checks if a hashed IP already exists in the list."""
    return hashed_ip in existing_hashes

def prepare_submission_row(
    participant_id: str,
    age: int,
    education: str,
    hashed_ip: str,
    browser_version: str,
    session_duration: int,
    timestamp: str
) -> Dict[str, Any]:
    """Prepares a submission row for CSV export."""
    return {
        "participant_id": participant_id,
        "age": age,
        "education": education,
        "hashed_ip": hashed_ip,
        "browser_version": browser_version,
        "session_duration": session_duration,
        "timestamp": timestamp
    }

def append_to_submissions_csv(row: Dict[str, Any]) -> None:
    """Appends a row to the submissions CSV file."""
    ensure_data_dirs()
    csv_path = get_submissions_csv_path()
    
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(
    participant_id: str,
    age: int,
    education: str,
    ratings: Dict[str, float],
    stimulus_order: List[str],
    hashed_ip: str,
    browser_version: str,
    session_duration: int
) -> None:
    """Saves a complete survey submission."""
    timestamp = format_timestamp(datetime.now())
    
    # Prepare base row
    row = prepare_submission_row(
        participant_id, age, education, hashed_ip,
        browser_version, session_duration, timestamp
    )
    
    # Add ratings
    for stimulus, rating in ratings.items():
        row[f"rating_{stimulus}"] = rating
    
    # Add stimulus order
    row["stimulus_order"] = ",".join(stimulus_order)
    
    append_to_submissions_csv(row)

def compute_file_checksum(file_path: Path) -> str:
    """Computes the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def store_data_checksum(file_path: Path, checksum: str) -> None:
    """Stores a file checksum in the checksum store."""
    checksum_path = get_checksum_store_path()
    
    checksums = {}
    if checksum_path.exists():
        with open(checksum_path, 'r', encoding='utf-8') as f:
            checksums = json.load(f)
    
    checksums[file_path.name] = {
        "checksum": checksum,
        "timestamp": format_timestamp(datetime.now())
    }
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def verify_data_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verifies the checksum of a file against an expected value."""
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum

def write_audit_log(log_path: Path, entries: List[Dict[str, Any]]) -> None:
    """Writes audit log entries to a CSV file."""
    ensure_data_dirs()
    
    file_exists = log_path.exists()
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        if entries:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            if not file_exists:
                writer.writeheader()
            for entry in entries:
                writer.writerow(entry)

def log_consent_decision(
    user_id: str,
    decision: str,
    irb_protocol_id: str
) -> None:
    """Logs a consent decision to the consent log."""
    timestamp = format_timestamp(datetime.now())
    
    row = {
        "timestamp": timestamp,
        "user_id": user_id,
        "decision": decision,
        "IRB_PROTOCOL_ID": irb_protocol_id
    }
    
    consent_log_path = get_consent_log_path()
    append_to_submissions_csv(row)  # Reusing the append function for simplicity

# Import datetime for format_timestamp
from datetime import datetime
