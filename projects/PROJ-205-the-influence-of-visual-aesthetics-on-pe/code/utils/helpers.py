import hashlib
import uuid
import os
import csv
import json
from datetime import datetime
from pathlib import Path

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_data_dirs():
    """Ensure required data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path():
    """Return the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_consent_log_path():
    """Return the path to the consent log file."""
    return get_project_root() / "data" / "consent" / "consent_log.csv"

def get_duplicate_audit_path():
    """Return the path to the duplicate audit file."""
    return get_project_root() / "data" / "raw" / "duplicate_audit.csv"

def generate_user_id():
    """Generate a unique user ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address, salt="project_salt_2024"):
    """Hash an IP address using SHA-256 with a salt to prevent reverse lookup."""
    if not ip_address:
        raise ValueError("IP address cannot be empty")
    salted_ip = f"{ip_address}{salt}"
    return hashlib.sha256(salted_ip.encode('utf-8')).hexdigest()

def format_timestamp(dt=None):
    """Format a datetime object as an ISO string, or current time if None."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def compute_consent_form_hash(file_path):
    """Compute SHA-256 hash of the consent form file for version tracking."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Consent file not found: {file_path}")
    content = path.read_text()
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def log_consent_decision(timestamp, user_id, decision, irb_protocol_id):
    """Log a consent decision to the consent log file."""
    ensure_data_dirs()
    log_path = get_consent_log_path()
    
    file_exists = log_path.exists()
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'user_id', 'decision', 'irb_protocol_id'])
        writer.writerow([timestamp, user_id, decision, irb_protocol_id])

def validate_rating_count(ratings, min_stimuli=4):
    """Validate that the required number of stimuli have been rated."""
    return len(ratings) >= min_stimuli * 2  # 2 ratings per stimulus

def calculate_safe_truncation_length(max_length=255):
    """Return the safe truncation length for metadata fields."""
    return max_length

def truncate_user_agent(user_agent, max_length=255):
    """Truncate user agent string to a safe length."""
    if not user_agent:
        return ""
    return str(user_agent)[:max_length]

def get_education_code(education_text):
    """Map education text to a numeric code."""
    education_map = {
        "Less than High School": 1,
        "High School Diploma": 2,
        "Some College": 3,
        "Associate Degree": 4,
        "Bachelor's Degree": 5,
        "Master's Degree": 6,
        "Doctoral Degree": 7
    }
    return education_map.get(education_text, 0)

def get_current_csv_size(file_path):
    """Get the current size of the CSV file in bytes."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def check_duplicate_ip(hashed_ip, file_path=None):
    """Check if a hashed IP already exists in the submissions file."""
    if file_path is None:
        file_path = get_submissions_csv_path()
    
    if not os.path.exists(file_path):
        return False
        
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('hashed_ip') == hashed_ip:
                return True
    return False

def prepare_submission_row(participant_id, stimulus_id, credibility, professionalism, 
                         timestamp, hashed_ip, age, education, user_agent,
                         duplicate_flag, session_status, submission_status):
    """Prepare a dictionary row for submission CSV."""
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
        'duplicate_flag': duplicate_flag,
        'session_status': session_status,
        'submission_status': submission_status
    }

def append_to_submissions_csv(row, file_path=None):
    """Append a row to the submissions CSV file."""
    if file_path is None:
        file_path = get_submissions_csv_path()
        
    ensure_data_dirs()
    
    file_exists = file_path.exists()
    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'user_agent',
        'duplicate_flag', 'session_status', 'submission_status'
    ]
    
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def save_submission(participant_id, stimulus_id, credibility, professionalism, 
                   timestamp, hashed_ip, age, education, user_agent,
                   duplicate_flag, session_status, submission_status):
    """Save a complete submission to the CSV file."""
    row = prepare_submission_row(
        participant_id, stimulus_id, credibility, professionalism,
        timestamp, hashed_ip, age, education, user_agent,
        duplicate_flag, session_status, submission_status
    )
    append_to_submissions_csv(row)

def write_audit_log(audit_data, output_path):
    """Write audit data to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, default=str)
