"""
Utility functions for the project.
"""
import os
import csv
import json
import yaml
import uuid
import hashlib
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import secrets


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def ensure_data_dirs():
    """Ensure all required data directories exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "backups",
        root / "data" / "consent",
        root / "state",
        root / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def get_submissions_csv_path() -> Path:
    """Return the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"


def get_cleaned_csv_path() -> Path:
    """Return the path to the cleaned CSV."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"


def get_consent_log_path() -> Path:
    """Return the path to the consent log."""
    return get_project_root() / "data" / "raw" / "consent_log.csv"


def get_excluded_audit_path() -> Path:
    """Return the path to the excluded audit log."""
    return get_project_root() / "data" / "processed" / "excluded_audit_log.csv"


def get_duplicate_audit_path() -> Path:
    """Return the path to the duplicate audit log."""
    return get_project_root() / "data" / "processed" / "duplicate_audit_log.csv"


def get_state_file_path() -> Path:
    """Return the path to the state file."""
    return get_project_root() / "state" / "app_state.json"


def get_checksum_store_path() -> Path:
    """Return the path to the checksum store."""
    return get_project_root() / "data" / "raw" / ".checksums.json"


def hash_ip(ip_address: str) -> str:
    """
    Hash an IP address using PBKDF2 with SHA-256.
    
    Requirements:
    - Minimum 100,000 iterations
    - Salt loaded from IP_HASH_SALT environment variable
    - Fail loudly if salt is not set
    """
    salt_str = os.getenv("IP_HASH_SALT")
    if not salt_str:
        raise ValueError("IP_HASH_SALT environment variable is not set. Cannot hash IP.")
    
    salt = salt_str.encode('utf-8')
    ip_bytes = ip_address.encode('utf-8')
    
    # PBKDF2 with SHA-256, 100,000 iterations
    dk = hashlib.pbkdf2_hmac('sha256', ip_bytes, salt, 100000)
    return dk.hex()


def generate_user_id() -> str:
    """Generate a unique user ID (UUID v4)."""
    return str(uuid.uuid4())


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def store_data_checksum(data: Dict[str, Any], filepath: Path):
    """Store data checksums in a JSON file."""
    checksums = {}
    if filepath.exists():
        with open(filepath, 'r') as f:
            try:
                checksums = json.load(f)
            except json.JSONDecodeError:
                checksums = {}
    
    # Update with new data
    for key, value in data.items():
        checksums[key] = value
    
    with open(filepath, 'w') as f:
        json.dump(checksums, f, indent=2)


def load_checksums(filepath: Path) -> Dict[str, Any]:
    """Load checksums from a JSON file."""
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def verify_data_checksum(filepath: Path, expected_hash: str) -> bool:
    """Verify the checksum of a file against an expected hash."""
    actual_hash = compute_file_checksum(filepath)
    return actual_hash == expected_hash


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime object to ISO8601 string."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def get_education_code(education: str) -> str:
    """Map education string to a standardized code."""
    mapping = {
        "High School": "HS",
        "Bachelor": "B",
        "Master": "M",
        "PhD": "P",
        "Other": "O"
    }
    return mapping.get(education, "O")


def get_current_csv_size(filepath: Path) -> int:
    """Get the current size of a CSV file in rows."""
    if not filepath.exists():
        return 0
    with open(filepath, 'r') as f:
        return sum(1 for _ in f) - 1  # Subtract header


def validate_rating_count(count: int, min_required: int = 4) -> bool:
    """Validate that the number of ratings meets the minimum requirement."""
    return count >= min_required


def check_duplicate_ip(hashed_ip: str, existing_hashes: List[str]) -> bool:
    """Check if a hashed IP already exists in the list."""
    return hashed_ip in existing_hashes


def prepare_submission_row(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a submission row for CSV export."""
    return {
        "participant_id": data.get("participant_id"),
        "age": data.get("age"),
        "education": data.get("education"),
        "timestamp": data.get("timestamp"),
        "hashed_ip": data.get("hashed_ip"),
        "browser_version": data.get("browser_version"),
        "session_start_time": data.get("session_start_time"),
        "stimulus_id": data.get("stimulus_id"),
        "credibility_rating": data.get("credibility_rating"),
        "professionalism_rating": data.get("professionalism_rating")
    }


def append_to_submissions_csv(row: Dict[str, Any], filepath: Optional[Path] = None):
    """Append a row to the submissions CSV."""
    if filepath is None:
        filepath = get_submissions_csv_path()
    
    ensure_data_dirs()
    
    file_exists = filepath.exists()
    
    with open(filepath, 'a', newline='') as f:
        fieldnames = [
            "participant_id", "age", "education", "timestamp", "hashed_ip",
            "browser_version", "session_start_time", "stimulus_id",
            "credibility_rating", "professionalism_rating"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)


def save_submission(data: Dict[str, Any], filepath: Optional[Path] = None):
    """Save a submission to the CSV with atomic write."""
    if filepath is None:
        filepath = get_submissions_csv_path()
    
    ensure_data_dirs()
    
    # Prepare the row
    row = prepare_submission_row(data)
    
    # Atomic write
    write_atomic(filepath, row)


def write_audit_log(message: str, filepath: Path):
    """Write an entry to an audit log."""
    entry = {
        "timestamp": format_timestamp(),
        "message": message
    }
    
    logs = []
    if filepath.exists():
        with open(filepath, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.append(entry)
    
    with open(filepath, 'w') as f:
        json.dump(logs, f, indent=2)


def log_consent_decision(user_id: str, decision: str, irb_protocol_id: str, filepath: Optional[Path] = None):
    """Log a consent decision."""
    if filepath is None:
        filepath = get_consent_log_path()
    
    ensure_data_dirs()
    
    row = {
        "timestamp": format_timestamp(),
        "user_id": user_id,
        "decision": decision,
        "irb_protocol_id": irb_protocol_id
    }
    
    file_exists = filepath.exists()
    
    with open(filepath, 'a', newline='') as f:
        fieldnames = ["timestamp", "user_id", "decision", "irb_protocol_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)


def compute_consent_form_hash(filepath: Path) -> str:
    """Compute the hash of the consent form file."""
    return compute_file_checksum(filepath)


def truncate_user_agent(user_agent: str, max_length: int = 100) -> str:
    """Truncate the user agent string to a maximum length."""
    return user_agent[:max_length] if len(user_agent) > max_length else user_agent


def write_atomic(filepath: Path, data: Dict[str, Any]):
    """
    Write data to a CSV file atomically.
    
    Writes to a temporary file first, then renames to the target path.
    """
    ensure_data_dirs()
    
    tmp_path = Path(str(filepath) + ".tmp")
    
    file_exists = filepath.exists()
    
    with open(tmp_path, 'w', newline='') as f:
        fieldnames = [
            "participant_id", "age", "education", "timestamp", "hashed_ip",
            "browser_version", "session_start_time", "stimulus_id",
            "credibility_rating", "professionalism_rating"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        # If file exists, we need to read existing rows and append new one
        # But for atomic write of a single row, we assume append mode logic
        # However, to be truly atomic for append, we should read, add, write all
        if file_exists:
            existing_rows = []
            with open(filepath, 'r') as read_f:
                reader = csv.DictReader(read_f)
                existing_rows = list(reader)
            
            existing_rows.append(data)
            writer.writerows(existing_rows)
        else:
            writer.writerow(data)
    
    # Atomic rename
    os.rename(tmp_path, filepath)


def set_reproducibility_seed(seed_value: Optional[int] = None):
    """
    Set the global random seed for reproducibility.
    
    Reads seed from RANDOM_SEED environment variable (default 42).
    """
    if seed_value is None:
        seed_value = int(os.getenv("RANDOM_SEED", 42))
    
    random.seed(seed_value)
    np.random.seed(seed_value)
    os.environ['PYTHONHASHSEED'] = str(seed_value)


def is_seed_set() -> bool:
    """Check if the reproducibility seed has been set."""
    return os.environ.get('PYTHONHASHSEED') is not None


def create_backup(source_path: Path, backup_dir: Path) -> Path:
    """
    Create a backup of a file.
    
    Args:
        source_path: Path to the source file.
        backup_dir: Directory to store the backup.
        
    Returns:
        Path to the backup file.
    """
    import shutil
    from datetime import datetime
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
    backup_path = backup_dir / backup_filename
    
    shutil.copy2(source_path, backup_path)
    return backup_path


def backup_on_write(source_path: Path, backup_dir: Optional[Path] = None):
    """
    Trigger a backup after a write operation.
    
    Args:
        source_path: Path to the source file.
        backup_dir: Optional directory for backups. Defaults to data/backups.
    """
    from code.utils.backup import get_backup_dir
    
    if backup_dir is None:
        backup_dir = get_backup_dir()
    
    create_backup(source_path, backup_dir)
