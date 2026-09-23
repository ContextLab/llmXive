"""
Utility to generate mock data for benchmarking and development.

This script generates a synthetic dataset for the survey system.
It is intended for testing the analysis pipeline when real data is not available.

IMPORTANT: This script MUST be executed to populate data/raw/submissions.csv
for the analysis pipeline to run.
"""
import os
import sys
import csv
import uuid
import random
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Constants
PARTICIPANT_COUNT = 250
RANDOM_SEED = 42
STIMULI_CONDITIONS = ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']
EDUCATION_LEVELS = ['High School', 'Some College', 'Bachelor\'s Degree', 'Master\'s Degree', 'PhD']

# Ensure reproducibility
random.seed(RANDOM_SEED)

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def get_submissions_csv_path():
    """Get the path to the submissions CSV file."""
    return get_project_root() / 'data' / 'raw' / 'submissions.csv'

def get_state_file_path():
    """Get the path to the project state YAML file."""
    return get_project_root() / 'state' / 'projects' / 'PROJ-205-the-influence-of-visual-aesthetics-on-pe.yaml'

def generate_ip():
    """Generate a realistic-looking IP address."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def generate_timestamp(base_time=None):
    """Generate a realistic timestamp."""
    if base_time is None:
        base_time = datetime.now() - timedelta(days=30)
    
    offset = timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return (base_time + offset).isoformat()

def generate_user_agent():
    """Generate a realistic User-Agent string."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(browsers)

def generate_mock_data():
    """Generate mock survey submission data."""
    data = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(PARTICIPANT_COUNT):
        participant_id = generate_session_id()
        hashed_ip = hashlib.sha256(f"mock_salt_{generate_ip()}".encode()).hexdigest()
        age = random.randint(18, 75)
        education = random.choice(EDUCATION_LEVELS)
        timestamp = generate_timestamp(base_time)
        user_agent = generate_user_agent()
        
        # Generate ratings for each stimulus (simulating a completed survey)
        for stimulus in STIMULI_CONDITIONS:
            # Simulate ratings with some noise based on stimulus type
            base_credibility = 4.0 if stimulus == 'Professional' else 3.0 if stimulus == 'Minimalist' else 2.0 if stimulus == 'Low-Quality' else 3.5
            base_professionalism = 4.5 if stimulus == 'Professional' else 3.5 if stimulus == 'Minimalist' else 1.5 if stimulus == 'Low-Quality' else 3.0
            
            credibility = max(1, min(5, base_credibility + random.gauss(0, 0.5)))
            professionalism = max(1, min(5, base_professionalism + random.gauss(0, 0.5)))
            
            row = {
                'participant_id': participant_id,
                'stimulus_id': stimulus,
                'credibility': round(credibility, 2),
                'professionalism': round(professionalism, 2),
                'timestamp': timestamp,
                'hashed_ip': hashed_ip,
                'age': age,
                'education': education,
                'user_agent': user_agent[:255],  # Truncate to 255 chars
                'duplicate_flag': 'False',
                'session_status': 'complete',
                'submission_status': 'success'
            }
            data.append(row)
    
    return data

def compute_sha256_checksum(filepath):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(checksum):
    """Update the project state file with the artifact checksum."""
    state_path = get_state_file_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing state or create new
    state_data = {}
    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception:
            state_data = {}
    
    # Update artifact hash
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    state_data['artifact_hashes']['submissions_csv'] = checksum
    state_data['artifact_hashes']['last_updated'] = datetime.now().isoformat()
    
    # Write back
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def main():
    """Main entry point."""
    print("Generating mock survey data...")
    
    # Ensure data directory exists
    csv_path = get_submissions_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    data = generate_mock_data()
    
    # Write to CSV
    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'user_agent',
        'duplicate_flag', 'session_status', 'submission_status'
    ]
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Generated {len(data)} rows in {csv_path}")
    
    # Compute and record checksum
    checksum = compute_sha256_checksum(csv_path)
    update_state_file(checksum)
    print(f"Recorded SHA-256 checksum: {checksum}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
