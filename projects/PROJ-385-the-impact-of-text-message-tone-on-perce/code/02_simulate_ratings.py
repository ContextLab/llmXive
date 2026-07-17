"""
Module: 02_simulate_ratings.py
Task: T014 [US1] Implement mock Prolific data collection.

This script simulates a Prolific data collection session. It reads the target
sample size (N) from the power analysis results, generates valid Prolific IDs
(mocked format), simulates ratings for 24 stimuli per participant across
randomized relationship contexts, and writes the results to data/raw/ratings.csv.

It does NOT fetch real data from an external API; it simulates the *structure*
of the data collection process as defined in the user story for a simulated study.
"""
import csv
import json
import os
import random
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling module as per API surface
from config import get_project_root, get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PROLIFIC_ID_PATTERN = re.compile(r'^P-[A-Z0-9]{8}$')
TOTAL_STIMULI = 24  # 3 emoji * 2 punct * 2 length * 2 contexts
LIKERT_MIN = 1
LIKERT_MAX = 5
RELATIONSHIPS = ['friend', 'acquaintance']

def load_power_analysis_results() -> int:
    """
    Reads the target N from data/processed/power_analysis_results.json.
    Returns the number of participants to simulate.
    """
    processed_dir = get_processed_data_dir()
    power_file = processed_dir / "power_analysis_results.json"
    
    if not power_file.exists():
        logger.error(f"Power analysis file not found: {power_file}")
        raise FileNotFoundError(f"Required power analysis file missing: {power_file}")
    
    with open(power_file, 'r') as f:
        data = json.load(f)
    
    n_required = data.get('results', {}).get('required_participants')
    if n_required is None:
        logger.error("required_participants not found in power analysis results.")
        raise KeyError("Missing 'required_participants' in power analysis results.")
    
    logger.info(f"Loaded target N={n_required} from power analysis.")
    return n_required

def generate_prolific_id() -> str:
    """
    Generates a mock Prolific ID in the format P-XXXXXXXX.
    """
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
    return f"P-{random_suffix}"

def validate_prolific_id(pid: str) -> bool:
    """
    Validates that a Prolific ID matches the expected regex format.
    """
    return bool(PROLIFIC_ID_PATTERN.match(pid))

def simulate_rating(stimulus_id: str, context: str) -> int:
    """
    Simulates a Likert score (1-5) for a given stimulus and context.
    Uses a simple heuristic based on context and random noise to create
    realistic-looking variance without requiring real human input.
    """
    # Base score
    base = 3.0
    
    # Add slight bias based on context (simulating the "effect" we study)
    if context == 'friend':
        base += 0.5
    else:
        base -= 0.2
    
    # Add random noise
    noise = random.gauss(0, 0.8)
    score = base + noise
    
    # Clip to Likert scale
    score = max(LIKERT_MIN, min(LIKERT_MAX, score))
    
    return int(round(score))

def generate_ratings(n_participants: int) -> List[Dict[str, Any]]:
    """
    Generates the full dataset of ratings.
    Each participant rates all 24 stimuli in a randomized order.
    """
    ratings = []
    used_ids = set()
    
    logger.info(f"Generating ratings for {n_participants} participants...")
    
    for i in range(n_participants):
        # Generate unique P-ID
        while True:
            pid = generate_prolific_id()
            if pid not in used_ids:
                used_ids.add(pid)
                break
        
        if not validate_prolific_id(pid):
            raise ValueError(f"Generated invalid Prolific ID: {pid}")
        
        # Randomize relationship context for this participant's session
        # (Simulating the randomization requirement from T017)
        participant_context = random.choice(RELATIONSHIPS)
        
        # Log randomization
        log_randomization(pid, participant_context)
        
        # Generate ratings for all 24 stimuli
        # Stimulus IDs are assumed to be S001 to S024 based on T013 output
        for s_idx in range(1, TOTAL_STIMULI + 1):
            stimulus_id = f"S{s_idx:03d}"
            score = simulate_rating(stimulus_id, participant_context)
            
            ratings.append({
                'participant_id': pid,
                'stimulus_id': stimulus_id,
                'relationship_context': participant_context,
                'rating': score
            })
    
    logger.info(f"Generated {len(ratings)} rating records.")
    return ratings

def log_randomization(participant_id: str, context: str):
    """
    Logs the randomization of relationship context for a participant.
    """
    log_dir = get_project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "randomization_log.csv"
    
    file_exists = os.path.exists(log_file)
    
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['participant_id', 'assigned_context'])
        writer.writerow([participant_id, context])

def save_ratings(ratings: List[Dict[str, Any]]):
    """
    Saves the generated ratings to data/raw/ratings.csv.
    """
    raw_dir = get_raw_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_file = raw_dir / "ratings.csv"
    
    fieldnames = ['participant_id', 'stimulus_id', 'relationship_context', 'rating']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ratings)
    
    logger.info(f"Saved {len(ratings)} ratings to {output_file}")

def main():
    """
    Main entry point for the simulation script.
    """
    setup_logging()
    logger.info("Starting mock Prolific data collection (T014)...")
    
    try:
        # 1. Load target N
        n_participants = load_power_analysis_results()
        
        # 2. Generate ratings
        ratings = generate_ratings(n_participants)
        
        # 3. Save to CSV
        save_ratings(ratings)
        
        logger.info("Task T014 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T014 failed: {e}")
        raise

if __name__ == "__main__":
    main()
