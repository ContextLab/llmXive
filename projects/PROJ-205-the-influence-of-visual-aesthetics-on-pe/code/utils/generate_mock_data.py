"""
Generate synthetic mock data for benchmarking the analysis pipeline.

This script creates a synthetic `data/raw/submissions.csv` file with N=250
participants. The data includes all required fields defined in the project
schema. The ratings are drawn from a normal distribution (mean=4, std=1.5)
as specified for benchmarking purposes.

IMPORTANT: This data is strictly for benchmarking the pipeline execution
and performance (e.g., T043b runtime tests). It is NOT real experimental data.
"""
import os
import sys
import csv
import uuid
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    get_submissions_csv_path,
    generate_user_id,
    hash_ip,
    get_education_code
)

# Constants
N_PARTICIPANTS = 250
RATING_MEAN = 4.0
RATING_STD = 1.5
STIMULI_CONDITIONS = ['professional', 'minimalist', 'low_quality', 'neutral']
EDUCATION_OPTIONS = ['High School', "Bachelor's", "Master's", 'PhD']
TIMEZONE_OFFSET_HOURS = -5  # Approximate US Eastern

def generate_ip():
    """Generate a realistic-looking but synthetic IP address."""
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def generate_session_id():
    """Generate a UUID v4 for the session."""
    return str(uuid.uuid4())

def generate_timestamp(base_time, offset_minutes):
    """Generate a timestamp string."""
    dt = base_time + timedelta(minutes=offset_minutes)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def generate_user_agent():
    """Generate a synthetic user agent string."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(browsers)

def generate_mock_data(output_path):
    """
    Generate the mock submissions CSV.

    Args:
        output_path: Path to write the CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Base time for timestamps (simulating data collected over a few days)
    base_time = datetime.now() - timedelta(days=3)

    # Header
    header = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
        'session_status', 'submission_status', 'user_agent'
    ]

    rows = []
    seen_ips = set()

    for i in range(N_PARTICIPANTS):
        participant_id = generate_session_id()
        ip = generate_ip()
        hashed_ip = hash_ip(ip)
        
        # Simulate some duplicates for testing (approx 2%)
        if i > 0 and i % 50 == 0 and seen_ips:
            # Reuse an existing IP to create a duplicate
            ip = random.choice(list(seen_ips))
            hashed_ip = hash_ip(ip)
            duplicate_flag = 1
        else:
            duplicate_flag = 0
            seen_ips.add(ip)

        age = random.randint(18, 75)
        education_str = random.choice(EDUCATION_OPTIONS)
        education_code = get_education_code(education_str)
        
        # Generate ratings from normal distribution
        credibility = round(random.gauss(RATING_MEAN, RATING_STD), 2)
        professionalism = round(random.gauss(RATING_MEAN, RATING_STD), 2)
        
        # Clamp ratings to valid Likert range [1, 7]
        credibility = max(1.0, min(7.0, credibility))
        professionalism = max(1.0, min(7.0, professionalism))

        stimulus_id = STIMULI_CONDITIONS[i % len(STIMULI_CONDITIONS)]
        
        # Increment time slightly for each row
        current_time = generate_timestamp(base_time, i * 5)
        
        user_agent = generate_user_agent()
        
        row = [
            participant_id,
            stimulus_id,
            credibility,
            professionalism,
            current_time,
            hashed_ip,
            age,
            education_code,
            duplicate_flag,
            'complete', # session_status
            'submitted', # submission_status
            user_agent
        ]
        rows.append(row)

    # Write to CSV
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Successfully generated mock data: {output_path}")
    print(f"Total participants: {N_PARTICIPANTS}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

def main():
    output_path = get_submissions_csv_path()
    generate_mock_data(output_path)

if __name__ == "__main__":
    main()