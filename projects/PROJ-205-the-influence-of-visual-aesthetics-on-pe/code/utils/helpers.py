import hashlib
import uuid
import os
import csv
import json
from datetime import datetime
from pathlib import Path
from utils.config import get_project_root, get_consent_file_path

def get_project_root():
    """Return the project root directory path."""
    return get_project_root()

def ensure_data_dirs():
    """Ensure data/raw and data/processed directories exist."""
    root = get_project_root()
    Path(root, "data", "raw").mkdir(parents=True, exist_ok=True)
    Path(root, "data", "processed").mkdir(parents=True, exist_ok=True)
    Path(root, "data", "consent").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path():
    """Return the path to the submissions CSV file."""
    root = get_project_root()
    return os.path.join(root, "data", "raw", "submissions.csv")

def get_consent_log_path():
    """Return the path to the consent log CSV file."""
    root = get_project_root()
    return os.path.join(root, "data", "raw", "consent_log.csv")

def get_duplicate_audit_path():
    """Return the path to the duplicate audit CSV file."""
    root = get_project_root()
    return os.path.join(root, "data", "raw", "duplicate_audit.csv")

def generate_user_id():
    """Generate a unique user ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address):
    """
    Hash an IP address using SHA-256.
    This is used for privacy-preserving identity tracking.
    """
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()

def format_timestamp(dt=None):
    """Format a datetime object as an ISO 8601 string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def compute_consent_form_hash():
    """
    Compute a SHA-256 hash of the IRB-approved consent form file.
    This hash is used for internal version tracking ONLY.
    The full text must be displayed to participants; the hash is never shown.
    
    Returns:
        str: The hexadecimal SHA-256 hash of the consent form file.
        
    Raises:
        FileNotFoundError: If the consent form file does not exist.
        IOError: If the file cannot be read.
    """
    consent_path = get_consent_file_path()
    if not os.path.exists(consent_path):
        raise FileNotFoundError(f"Consent form file not found: {consent_path}")
    
    with open(consent_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def log_consent_decision(user_id, decision, irb_protocol_id, consent_form_hash=None):
    """
    Log a consent decision to the consent log CSV.
    
    Args:
        user_id (str): The unique participant ID.
        decision (str): 'agreed' or 'declined'.
        irb_protocol_id (str): The IRB protocol ID.
        consent_form_hash (str, optional): SHA-256 hash of the consent form for version tracking.
    """
    ensure_data_dirs()
    log_path = get_consent_log_path()
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'user_id', 'decision', 'irb_protocol_id', 'consent_form_hash'])
        
        writer.writerow([
            format_timestamp(),
            user_id,
            decision,
            irb_protocol_id,
            consent_form_hash or "N/A"
        ])

def validate_rating_count(ratings):
    """
    Validate that the required number of ratings are present.
    
    Args:
        ratings (list): List of rating values.
        
    Returns:
        bool: True if all ratings are present and valid, False otherwise.
    """
    return len(ratings) == 4 and all(r is not None for r in ratings)

def calculate_safe_truncation_length(max_length=255):
    """
    Calculate a safe truncation length for metadata fields.
    
    Args:
        max_length (int): Maximum allowed length.
        
    Returns:
        int: The safe length to use.
    """
    return min(max_length, 255)

def truncate_user_agent(user_agent, max_length=255):
    """
    Truncate a user agent string to a safe length.
    
    Args:
        user_agent (str): The user agent string.
        max_length (int): Maximum allowed length.
        
    Returns:
        str: The truncated user agent string.
    """
    if not user_agent:
        return ""
    return user_agent[:calculate_safe_truncation_length(max_length)]

def get_education_code(education):
    """
    Convert education level to a numeric code for analysis.
    
    Args:
        education (str): Education level string.
        
    Returns:
        int: Numeric code (1=High School, 2=Bachelor's, 3=Master's, 4=PhD).
    """
    mapping = {
        "High School": 1,
        "Bachelor's": 2,
        "Master's": 3,
        "PhD": 4
    }
    return mapping.get(education, 0)

def get_current_csv_size(file_path):
    """
    Get the current size of a CSV file in bytes.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        int: Size in bytes, or 0 if file does not exist.
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def check_duplicate_ip(ip_hash, existing_hashes):
    """
    Check if an IP hash already exists in the dataset.
    
    Args:
        ip_hash (str): The SHA-256 hash of the IP address.
        existing_hashes (set): Set of existing IP hashes.
        
    Returns:
        bool: True if duplicate, False otherwise.
    """
    return ip_hash in existing_hashes

def prepare_submission_row(participant_id, stimulus_id, credibility, professionalism, 
                           timestamp, hashed_ip, age, education, user_agent, 
                           session_status, submission_status):
    """
    Prepare a row for the submissions CSV.
    
    Args:
        participant_id (str): Unique participant ID.
        stimulus_id (str): Stimulus condition identifier.
        credibility (int): Credibility rating.
        professionalism (int): Professionalism rating.
        timestamp (str): ISO 8601 timestamp.
        hashed_ip (str): SHA-256 hash of IP address.
        age (int): Participant age.
        education (str): Education level.
        user_agent (str): Browser user agent string.
        session_status (str): Session status (e.g., 'complete', 'timeout').
        submission_status (str): Submission status (e.g., 'submitted', 'incomplete').
        
    Returns:
        dict: Dictionary representing the CSV row.
    """
    return {
        'participant_id': participant_id,
        'stimulus_id': stimulus_id,
        'credibility': credibility,
        'professionalism': professionalism,
        'timestamp': timestamp,
        'hashed_ip': hashed_ip,
        'age': age,
        'education': education,
        'user_agent': truncate_user_agent(user_agent),
        'duplicate_flag': 'N/A',  # Will be set by audit script
        'session_status': session_status,
        'submission_status': submission_status
    }

def append_to_submissions_csv(row_data):
    """
    Append a row to the submissions CSV file.
    
    Args:
        row_data (dict): Row data dictionary.
    """
    ensure_data_dirs()
    file_path = get_submissions_csv_path()
    file_exists = os.path.exists(file_path)
    
    fieldnames = ['participant_id', 'stimulus_id', 'credibility', 'professionalism', 
                  'timestamp', 'hashed_ip', 'age', 'education', 'user_agent', 
                  'duplicate_flag', 'session_status', 'submission_status']
    
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)

def save_submission(participant_id, stimulus_id, credibility, professionalism, 
                    timestamp, hashed_ip, age, education, user_agent, 
                    session_status='complete', submission_status='submitted'):
    """
    Save a complete survey submission to the CSV.
    
    Args:
        participant_id (str): Unique participant ID.
        stimulus_id (str): Stimulus condition identifier.
        credibility (int): Credibility rating.
        professionalism (int): Professionalism rating.
        timestamp (str): ISO 8601 timestamp.
        hashed_ip (str): SHA-256 hash of IP address.
        age (int): Participant age.
        education (str): Education level.
        user_agent (str): Browser user agent string.
        session_status (str): Session status.
        submission_status (str): Submission status.
    """
    row_data = prepare_submission_row(
        participant_id, stimulus_id, credibility, professionalism,
        timestamp, hashed_ip, age, education, user_agent,
        session_status, submission_status
    )
    append_to_submissions_csv(row_data)

def write_audit_log(audit_data, output_path):
    """
    Write an audit log to a JSON file.
    
    Args:
        audit_data (dict): Audit data dictionary.
        output_path (str): Path to the output JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, default=str)
