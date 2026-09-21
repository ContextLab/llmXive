"""
Utility to generate mock data for benchmarking and development.
This script creates a synthetic `data/raw/submissions.csv` with N=250 participants.
"""
import os
import sys
import csv
import uuid
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np

def get_project_root():
    current = Path(__file__).resolve()
    while current.name != "PROJ-205-the-influence-of-visual-aesthetics-on-pe":
        current = current.parent
        if current == current.parent:
            raise RuntimeError("Could not find project root")
    return current

PROJECT_ROOT = get_project_root()

def get_submissions_csv_path():
    return PROJECT_ROOT / "data" / "raw" / "submissions.csv"

def generate_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_session_id():
    return str(uuid.uuid4())

def generate_timestamp(base_time=None):
    if base_time is None:
        base_time = datetime.now()
    # Add a random offset within the last 30 days
    offset = timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return (base_time - offset).isoformat()

def generate_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    ]
    return random.choice(agents)

def generate_mock_data(n_participants=250):
    """
    Generate synthetic mock data for benchmarking.
    Creates a CSV with N participants, each having 4 ratings (one per stimulus).
    """
    stimuli = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    rows = []
    
    base_time = datetime.now()
    
    # Define a fixed seed for reproducibility in testing
    random.seed(42)
    np.random.seed(42)
    
    for _ in range(n_participants):
        participant_id = generate_session_id()
        hashed_ip = uuid.uuid4().hex # Mock hash
        age = random.randint(18, 70)
        education = random.choice(["High School", "Bachelor's", "Master's", "PhD"])
        timestamp = generate_timestamp(base_time)
        user_agent = generate_user_agent()
        
        # Generate ratings: Normal distribution (mean=4, std=1.5)
        # Add a slight bias for Professional to make it interesting
        # Professional: mean=4.5, Minimalist: mean=4.0, Low-Quality: mean=2.5, Neutral: mean=3.5
        means = {
            "Professional": 4.5,
            "Minimalist": 4.0,
            "Low-Quality": 2.5,
            "Neutral": 3.5
        }
        
        for stimulus in stimuli:
            credibility = max(1, min(5, np.random.normal(means[stimulus], 1.0)))
            professionalism = max(1, min(5, np.random.normal(means[stimulus], 0.8)))
            
            rows.append({
                "participant_id": participant_id,
                "stimulus_id": stimulus,
                "credibility": round(credibility, 2),
                "professionalism": round(professionalism, 2),
                "timestamp": timestamp,
                "hashed_ip": hashed_ip,
                "age": age,
                "education": education,
                "user_agent": user_agent,
                "duplicate_flag": 0,
                "session_status": "complete",
                "submission_status": "submitted"
            })
    
    return rows

def main():
    output_path = get_submissions_csv_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating mock data for 250 participants...")
    data = generate_mock_data(250)
    
    fieldnames = [
        "participant_id", "stimulus_id", "credibility", "professionalism",
        "timestamp", "hashed_ip", "age", "education", "user_agent",
        "duplicate_flag", "session_status", "submission_status"
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"Mock data saved to {output_path}")

if __name__ == "__main__":
    main()