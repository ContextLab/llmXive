"""
Mock Data Generator for Benchmarking (T043a)

Generates a synthetic `data/raw/submissions.csv` with N=250 participants.
This is used ONLY for benchmarking and testing the pipeline when real data
is not yet available. It is NOT used for the actual analysis of the study.

Schema matches: data/raw/submissions.csv
"""

import os
import sys
import csv
import uuid
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

def get_project_root():
    """Return the root path of the project."""
    current = Path(__file__).resolve()
    while not current.joinpath("project_root_marker").exists():
        current = current.parent
        if current == current.parent:
            return Path(__file__).resolve().parent.parent.parent
    return current

PROJECT_ROOT = get_project_root()
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SUBMISSIONS_PATH = RAW_DATA_DIR / "submissions.csv"

# Stimulus conditions
CONDITIONS = ['professional', 'minimalist', 'low_quality', 'neutral']

def generate_ip():
    """Generate a realistic-looking but fake IP address."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_session_id():
    """Generate a random session ID."""
    return str(uuid.uuid4())

def generate_timestamp(base_time=None):
    """Generate a timestamp string."""
    if base_time is None:
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))
    offset = timedelta(seconds=random.randint(0, 86400))
    return (base_time + offset).isoformat()

def generate_user_agent():
    """Generate a realistic user agent string."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(browsers)

def hash_ip(ip):
    """Generate a deterministic hash for the IP (mocking the real helper)."""
    return f"hash_{hash(ip) % 1000000}"

def generate_mock_data(n=250):
    """
    Generate N rows of mock submission data.
    Includes some intentional duplicates for testing the audit script.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
        'session_status', 'submission_status', 'user_agent'
    ]

    rows = []
    base_time = datetime.now() - timedelta(days=30)

    # Generate unique IPs first
    unique_ips = [generate_ip() for _ in range(n - 10)]  # Reserve 10 for duplicates
    ip_list = unique_ips.copy()

    # Add 10 duplicate IPs (2 entries each) to simulate 5 duplicate users
    for _ in range(5):
        ip_list.append(unique_ips[random.randint(0, len(unique_ips)-1)])

    random.shuffle(ip_list)

    for i in range(n):
        participant_id = str(uuid.uuid4())
        stimulus = random.choice(CONDITIONS)
        
        # Simulate ratings: Professional/Neutral higher than Low Quality
        if stimulus in ['professional', 'neutral']:
            cred = int(random.gauss(5.5, 1.2))
            prof = int(random.gauss(5.8, 1.0))
        elif stimulus == 'minimalist':
            cred = int(random.gauss(4.5, 1.5))
            prof = int(random.gauss(4.8, 1.2))
        else: # low_quality
            cred = int(random.gauss(2.5, 1.0))
            prof = int(random.gauss(2.2, 0.8))

        # Clamp ratings to 1-7
        cred = max(1, min(7, cred))
        prof = max(1, min(7, prof))

        age = random.randint(18, 75)
        education = random.choice([1, 2, 3, 4]) # 1: HS, 2: Bach, 3: Mast, 4: PhD
        
        ip = ip_list[i]
        hashed_ip = hash_ip(ip)
        
        # Determine if this is a duplicate (for testing)
        # In a real audit, this would be detected by IP count > 1
        is_dup = ip_list.count(ip) > 1 and ip_list.index(ip) != i
        
        row = {
            'participant_id': participant_id,
            'stimulus_id': stimulus,
            'credibility': cred,
            'professionalism': prof,
            'timestamp': generate_timestamp(base_time),
            'hashed_ip': hashed_ip,
            'age': age,
            'education': education,
            'duplicate_flag': 'TRUE' if is_dup else 'FALSE',
            'session_status': 'complete',
            'submission_status': 'submitted',
            'user_agent': generate_user_agent()
        }
        rows.append(row)

    with open(SUBMISSIONS_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {n} mock submissions at {SUBMISSIONS_PATH}")
    return SUBMISSIONS_PATH

def main():
    """Main entry point for mock data generation."""
    n = 250
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            pass
    
    print(f"Generating {n} mock data points...")
    generate_mock_data(n)
    print("Done.")

if __name__ == "__main__":
    main()
