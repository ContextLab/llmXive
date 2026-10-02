"""
Utility functions for the project.
"""
import hashlib
import uuid
import os
import csv
import json
import yaml
from pathlib import Path
from datetime import datetime

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_data_dirs():
    """Ensure data directories exist."""
    root = get_project_root()
    (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (root / "data" / "consent").mkdir(parents=True, exist_ok=True)
    (root / "state").mkdir(parents=True, exist_ok=True)

def get_submissions_csv_path():
    """Return the path to the submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_consent_log_path():
    """Return the path to the consent log CSV."""
    return get_project_root() / "data" / "processed" / "consent_log.csv"

def get_duplicate_audit_path():
    """Return the path to the duplicate audit CSV."""
    return get_project_root() / "data" / "processed" / "duplicate_audit.csv"

def get_state_file_path():
    """Return the path to the state JSON file."""
    return get_project_root() / "state" / "app_state.json"

def get_checksum_store_path():
    """Return the path to the checksums JSON file."""
    return get_project_root() / "data" / "processed" / "checksums.json"

def get_excluded_audit_path():
    """Return the path to the excluded audit CSV."""
    return get_project_root() / "data" / "processed" / "excluded_audit.csv"

def generate_user_id():
    """Generate a unique user ID (UUID v4)."""
    return str(uuid.uuid4())

def hash_ip(ip_address):
    """
    Hash an IP address using SHA-256 with a salt.
    Salt is loaded from the IP_HASH_SALT environment variable.
    """
    salt = os.getenv("IP_HASH_SALT")
    if not salt:
        raise ValueError("IP_HASH_SALT environment variable is not set.")
    
    salted_ip = f"{salt}{ip_address}"
    return hashlib.sha256(salted_ip.encode('utf-8')).hexdigest()

def format_timestamp(dt):
    """Format a datetime object to ISO8601 string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def compute_consent_form_hash():
    """Compute the hash of the consent form content."""
    # Implementation would read the consent file and hash it
    pass

def truncate_user_agent(user_agent):
    """Truncate the user agent string for privacy."""
    if not user_agent:
        return "Unknown"
    return user_agent[:100]

def get_education_code(education_level):
    """Map education level string to a numeric code."""
    mapping = {
        "Less than High School": 0,
        "High School Graduate": 1,
        "Some College": 2,
        "Associate Degree": 3,
        "Bachelor's Degree": 4,
        "Master's Degree": 5,
        "Doctorate": 6
    }
    return mapping.get(education_level, -1)

def get_current_csv_size(csv_path):
    """Get the current size of a CSV file in bytes."""
    if os.path.exists(csv_path):
        return os.path.getsize(csv_path)
    return 0

def validate_rating_count(ratings_dict, min_count=4):
    """Validate that a minimum number of stimuli have been rated."""
    return len(ratings_dict) >= min_count

def check_duplicate_ip(hashed_ip):
    """Check if an IP hash already exists in the submissions."""
    # Simplified for this task; real implementation would scan the CSV
    return False

def prepare_submission_row(participant_id, age, education, timestamp, hashed_ip, 
                           browser_version, session_duration, stimulus_id, 
                           credibility, professionalism):
    """Prepare a dictionary row for CSV submission."""
    return {
        "participant_id": participant_id,
        "age": age,
        "education": education,
        "timestamp": timestamp,
        "hashed_ip": hashed_ip,
        "browser_version": browser_version,
        "session_duration": session_duration,
        "stimulus_id": stimulus_id,
        "credibility": credibility,
        "professionalism": professionalism
    }

def append_to_submissions_csv(row):
    """Append a row to the submissions CSV."""
    csv_path = get_submissions_csv_path()
    ensure_data_dirs()
    
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ["participant_id", "age", "education", "timestamp", "hashed_ip", 
                      "browser_version", "session_duration", "stimulus_id", 
                      "credibility", "professionalism"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)

def save_submission(row):
    """Save a submission row to the CSV."""
    append_to_submissions_csv(row)

def compute_file_checksum(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def store_data_checksum(file_path, checksum):
    """Store a checksum in the checksums JSON file."""
    checksums_path = get_checksum_store_path()
    ensure_data_dirs()
    
    checksums = {}
    if os.path.exists(checksums_path):
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    
    checksums[os.path.basename(file_path)] = checksum
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_data_checksum(file_path, stored_checksum):
    """Verify a file's checksum against a stored value."""
    current_checksum = compute_file_checksum(file_path)
    return current_checksum == stored_checksum

def write_audit_log(log_path, message):
    """Write a message to an audit log."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

def log_consent_decision(participant_id, decision, irb_protocol_id):
    """Log a consent decision."""
    log_path = get_consent_log_path()
    ensure_data_dirs()
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ["timestamp", "participant_id", "decision", "irb_protocol_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            "timestamp": format_timestamp(datetime.now()),
            "participant_id": participant_id,
            "decision": decision,
            "irb_protocol_id": irb_protocol_id
        })
