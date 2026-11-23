"""
Utility to generate mock data for benchmarking and development.

This script generates a synthetic dataset for the survey system
to allow testing of the analysis pipeline without real data collection.
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

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_submissions_csv_path():
    """Get the path to the raw submissions CSV."""
    return get_project_root() / 'data' / 'raw' / 'submissions.csv'

def get_state_file_path():
    """Get the path to the project state YAML."""
    return get_project_root() / 'state' / 'projects' / 'PROJ-205-the-influence-of-visual-aesthetics-on-pe.yaml'

def generate_ip():
    """Generate a realistic-looking IPv4 address."""
    # Generate a private range IP to avoid real collisions
    # Using 10.x.x.x or 192.168.x.x ranges
    first_octet = random.choice([10, 192])
    if first_octet == 10:
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    else:
        return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def generate_timestamp():
    """Generate a realistic timestamp within the last 30 days."""
    now = datetime.now()
    random_days_ago = random.randint(0, 30)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    target_time = now - timedelta(days=random_days_ago, hours=random_hours, minutes=random_minutes, seconds=random_seconds)
    return target_time.isoformat()

def generate_user_agent():
    """Generate a realistic User-Agent string."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(browsers)

def generate_mock_data(n_participants=250):
    """
    Generate N mock survey submissions.
    
    Args:
        n_participants: Number of unique participants to generate.
        
    Returns:
        List of dictionaries representing the raw CSV rows.
    """
    rows = []
    stimuli_conditions = ['Professional', 'Minimalist', 'Low-Quality', 'Neutral']
    
    # Create a pool of unique IPs to ensure some duplicates exist for testing
    # We will reuse a few IPs to simulate duplicates
    unique_ips = [generate_ip() for _ in range(n_participants - 10)]
    # Add 10 IPs that will be duplicated (2-3 times each)
    duplicate_ips = [generate_ip() for _ in range(5)]
    ip_pool = unique_ips + duplicate_ips * 3 
    
    # Shuffle to mix duplicates
    random.shuffle(ip_pool)
    
    for i in range(n_participants):
        participant_id = str(uuid.uuid4())
        # Use deterministic hash for IP to simulate duplicates for specific participants
        # For simplicity, we just cycle through the pool
        ip = ip_pool[i % len(ip_pool)]
        hashed_ip = hashlib.sha256(ip.encode()).hexdigest()
        
        age = random.randint(18, 70)
        education = random.choice(['High School', 'Bachelor', 'Master', 'PhD'])
        user_agent = generate_user_agent()
        hashed_user_agent = hashlib.sha256(user_agent.encode()).hexdigest()
        
        # Generate ratings for each stimulus
        # Simulate a slight effect: Professional > Neutral > Minimalist > Low-Quality
        base_scores = {
            'Professional': 4.2,
            'Neutral': 3.8,
            'Minimalist': 3.5,
            'Low-Quality': 2.1
        }
        
        for stimulus in stimuli_conditions:
            # Add some noise
            score = base_scores[stimulus] + random.gauss(0, 0.8)
            score = max(1.0, min(5.0, score)) # Clamp between 1 and 5
            
            row = {
                'participant_id': participant_id,
                'stimulus_id': stimulus,
                'credibility': round(score, 2),
                'professionalism': round(score + random.gauss(0, 0.5), 2), # Correlated
                'timestamp': generate_timestamp(),
                'hashed_ip': hashed_ip,
                'age': age,
                'education': education,
                'duplicate_flag': 'False', # Will be updated by audit
                'session_status': 'complete',
                'submission_status': 'submitted',
                'hashed_user_agent': hashed_user_agent
            }
            rows.append(row)
    
    return rows

def compute_sha256_checksum(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(checksum):
    """Update the project state file with the artifact checksum."""
    state_path = get_state_file_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state = {}
    if state_path.exists():
        import yaml
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    state['artifact_hashes']['submissions_csv'] = checksum
    
    with open(state_path, 'w') as f:
        import yaml
        yaml.dump(state, f)

def main():
    """Main entry point to generate mock data."""
    print("Generating mock survey data...")
    
    # Ensure data directories exist
    data_raw_dir = get_project_root() / 'data' / 'raw'
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    rows = generate_mock_data(n_participants=250)
    
    # Write to CSV
    csv_path = get_submissions_csv_path()
    fieldnames = ['participant_id', 'stimulus_id', 'credibility', 'professionalism', 
                  'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag', 
                  'session_status', 'submission_status', 'hashed_user_agent']
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated {len(rows)} rows in {csv_path}")
    
    # Compute checksum
    checksum = compute_sha256_checksum(csv_path)
    print(f"Checksum: {checksum}")
    
    # Update state
    update_state_file(checksum)
    print(f"State updated at {get_state_file_path()}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())