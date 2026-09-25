import hashlib
import uuid
import os
import csv
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# --- Constants & Paths ---

def get_project_root() -> Path:
    """Returns the root path of the project (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs() -> None:
    """Creates data directories if they do not exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (root / "state" / "projects").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path() -> Path:
    """Returns the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_consent_log_path() -> Path:
    """Returns the path to the consent log CSV."""
    return get_project_root() / "data" / "raw" / "consent_log.csv"

def get_duplicate_audit_path() -> Path:
    """Returns the path to the duplicate audit CSV."""
    return get_project_root() / "data" / "raw" / "duplicate_audit.csv"

def get_state_file_path() -> Path:
    """Returns the path to the project state YAML file."""
    project_id = "PROJ-205-the-influence-of-visual-aesthetics-on-pe"
    return get_project_root() / "state" / "projects" / f"{project_id}.yaml"

# --- Helper Functions ---

def generate_user_id() -> str:
    """Generates a unique participant ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address: str, salt: str = "project_salt_2024") -> str:
    """
    Hashes an IP address using SHA-256 with a salt to prevent reverse lookup.
    
    Args:
        ip_address: The raw IP address string.
        salt: The salt string to prepend.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    if not ip_address:
        raise ValueError("IP address cannot be empty")
    salted = f"{salt}{ip_address}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Formats a datetime object to ISO 8601 string."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def compute_consent_form_hash() -> str:
    """Computes SHA-256 hash of the IRB consent file for version tracking."""
    path = get_project_root() / "data" / "consent" / "irb_approved.txt"
    if not path.exists():
        raise FileNotFoundError(f"Consent file not found: {path}")
    content = path.read_text(encoding='utf-8')
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def log_consent_decision(user_id: str, decision: bool, irb_protocol_id: str) -> None:
    """Logs a consent decision to the consent_log.csv."""
    ensure_data_dirs()
    path = get_consent_log_path()
    file_exists = os.path.exists(path)
    
    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'user_id', 'decision', 'irb_protocol_id'])
        
        writer.writerow([
            format_timestamp(),
            user_id,
            'Agreed' if decision else 'Declined',
            irb_protocol_id
        ])

def validate_rating_count(ratings: Dict[str, Any], min_stimuli: int = 4) -> bool:
    """Validates that the participant has rated the minimum number of stimuli."""
    # Assuming ratings dict keys are stimulus IDs or similar
    return len(ratings) >= min_stimuli

def calculate_safe_truncation_length(max_len: int = 255) -> int:
    """Returns a safe truncation length for metadata fields."""
    return max_len

def truncate_user_agent(user_agent: str, max_len: int = 255) -> str:
    """Truncates user agent string to a safe length."""
    return user_agent[:max_len] if len(user_agent) > max_len else user_agent

def get_education_code(education: str) -> str:
    """Maps education string to a code."""
    mapping = {
        'High School': 'HS',
        'Bachelor': 'B',
        'Master': 'M',
        'PhD': 'P'
    }
    return mapping.get(education, 'U')

def get_current_csv_size(path: Optional[Path] = None) -> int:
    """Returns the current size of the CSV file in bytes."""
    if path is None:
        path = get_submissions_csv_path()
    if not path.exists():
        return 0
    return path.stat().st_size

def check_duplicate_ip(hashed_ip: str, path: Optional[Path] = None) -> bool:
    """Checks if a hashed IP already exists in the submissions CSV."""
    if path is None:
        path = get_submissions_csv_path()
    if not path.exists():
        return False
    
    with open(path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == hashed_ip:
                return True
    return False

def prepare_submission_row(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepares a row for CSV submission, ensuring types are correct."""
    row = {
        'participant_id': data.get('participant_id'),
        'stimulus_id': data.get('stimulus_id'),
        'credibility': data.get('credibility'),
        'professionalism': data.get('professionalism'),
        'timestamp': format_timestamp(),
        'hashed_ip': data.get('hashed_ip'),
        'age': data.get('age'),
        'education': data.get('education'),
        'duplicate_flag': data.get('duplicate_flag', False),
        'session_status': data.get('session_status', 'complete'),
        'submission_status': data.get('submission_status', 'complete'),
        'hashed_user_agent': data.get('hashed_user_agent')
    }
    return row

def append_to_submissions_csv(row: Dict[str, Any]) -> None:
    """Appends a single row to the submissions CSV."""
    ensure_data_dirs()
    path = get_submissions_csv_path()
    file_exists = os.path.exists(path)
    
    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
        'session_status', 'submission_status', 'hashed_user_agent'
    ]
    
    with open(path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(data_list: List[Dict[str, Any]]) -> None:
    """Saves a list of submission rows to the CSV."""
    for row in data_list:
        append_to_submissions_csv(row)

def write_audit_log(audit_results: List[Dict[str, Any]], output_path: Path) -> None:
    """Writes audit results to a CSV file."""
    ensure_data_dirs()
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    file_exists = os.path.exists(output_path)
    fieldnames = list(audit_results[0].keys()) if audit_results else []
    
    with open(output_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(audit_results)

# --- NEW: T057 Data Integrity Checksums ---

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes a SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hex digest of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {e}")

def store_data_checksum(checksum: str) -> None:
    """
    Stores the data checksum in the project state YAML file.
    
    Args:
        checksum: The SHA-256 checksum string to store.
    """
    state_path = get_state_file_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            state = {}
    else:
        state = {}
    
    # Ensure structure exists
    if 'data_checksums' not in state:
        state['data_checksums'] = {}
    
    # Update checksum for submissions.csv
    submissions_path = get_submissions_csv_path()
    state['data_checksums']['submissions.csv'] = {
        'checksum': checksum,
        'timestamp': format_timestamp(),
        'file_path': str(submissions_path)
    }
    
    # Write back
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def verify_data_checksum() -> bool:
    """
    Verifies the checksum of submissions.csv against the stored value in state.
    
    Returns:
        True if checksum matches or no stored checksum exists.
        
    Raises:
        RuntimeError: If checksum mismatches (data integrity violation).
    """
    state_path = get_state_file_path()
    submissions_path = get_submissions_csv_path()
    
    if not submissions_path.exists():
        # If file doesn't exist, nothing to verify
        return True
    
    # Load stored state
    if not state_path.exists():
        # No stored checksum, cannot verify
        return True
        
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return True # Corrupt state, skip verification
    
    stored_checksums = state.get('data_checksums', {})
    stored_info = stored_checksums.get('submissions.csv', {})
    stored_checksum = stored_info.get('checksum')
    
    if not stored_checksum:
        # No checksum stored, nothing to verify
        return True
    
    # Compute current checksum
    try:
        current_checksum = compute_file_checksum(submissions_path)
    except (FileNotFoundError, IOError):
        raise RuntimeError("Could not compute current checksum for verification.")
    
    if current_checksum != stored_checksum:
        raise RuntimeError(
            f"DATA INTEGRITY FAILURE: Checksum mismatch for {submissions_path}. "
            f"Stored: {stored_checksum}, Current: {current_checksum}. "
            f"Data may have been tampered with or corrupted."
        )
    
    return True

# --- End T057 ---
