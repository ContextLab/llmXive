import os
import json
import random
import uuid
import argparse
import numpy as np
from datetime import datetime

from stimulus_loader import get_stimuli_paths, load_metadata

# Pin random seed
RANDOM_SEED = 42

def set_seed(seed: int = RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)

def generate_participant_id():
    return str(uuid.uuid4())

def simulate_incom_score():
    # INCOM score: 0-60, roughly normal distribution centered at 30
    return int(np.clip(np.random.normal(30, 10), 0, 60))

def simulate_usage_frequency():
    # Weekly usage: 0-40 hours, skewed distribution
    return round(np.random.exponential(5), 2)

def simulate_biss_score(origin: str):
    # BISS score: 1-7
    # Base score
    base = 4.0
    # AI images might induce slightly higher social comparison (higher BISS)
    if origin == 'AI':
        return round(np.clip(base + np.random.normal(0.5, 0.8), 1, 7), 1)
    else:
        return round(np.clip(base + np.random.normal(0.0, 0.8), 1, 7), 1)

def simulate_session(participant_id: str, stimuli_dir: str, n_images: int = 40):
    # Load stimuli metadata to ensure we have real image paths
    # We need to find actual image files to reference
    ai_paths, human_paths = get_stimuli_paths(stimuli_dir)
    
    if not ai_paths or not human_paths:
        raise FileNotFoundError(f"No stimuli found in {stimuli_dir}. Run T001/T007 first.")

    session_data = []
    
    # Randomize order
    all_stimuli = []
    for p in ai_paths:
        all_stimuli.append({'path': p, 'origin': 'AI'})
    for p in human_paths:
        all_stimuli.append({'path': p, 'origin': 'Human'})
    
    random.shuffle(all_stimuli)
    # Take first n_images
    session_stimuli = all_stimuli[:n_images]

    # Collect covariates
    incom = simulate_incom_score()
    usage = simulate_usage_frequency()

    for i, stim in enumerate(session_stimuli):
        # Simulate response
        biss = simulate_biss_score(stim['origin'])
        
        record = {
            "participant_id": participant_id,
            "stimulus_id": os.path.basename(stim['path']),
            "origin": stim['origin'],
            "timestamp": datetime.now().isoformat(),
            "BISS_score": biss,
            "INCOM_score": incom,
            "usage_frequency": usage,
            "is_complete": True # Assuming full session for simulation
        }
        session_data.append(record)
    
    return session_data

def write_session_file(session_data: list, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'a') as f: # Append mode for batch
        for record in session_data:
            f.write(json.dumps(record) + '\n')

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic participant data for testing.')
    # T044 Fix: Changed --n-participants to --n to match usage
    parser.add_argument('--n', type=int, default=10, help='Number of participants to simulate')
    parser.add_argument('--output', type=str, default='data/raw/mock_responses.jsonl', help='Output file path')
    parser.add_argument('--seed', type=int, default=RANDOM_SEED, help='Random seed')
    parser.add_argument('--stimuli-dir', type=str, default='data/stimuli', help='Path to stimuli directory')
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    # Clear output file if exists to avoid appending to old data in test runs
    if os.path.exists(args.output):
        os.remove(args.output)
        
    print(f"Generating {args.n} synthetic participant sessions...")
    print(f"WARNING: This is SYNTHETIC data for TESTING ONLY. Do not use for real analysis.")
    
    for i in range(args.n):
        pid = generate_participant_id()
        session = simulate_session(pid, args.stimuli_dir)
        write_session_file(session, args.output)
        
    print(f"Data written to {args.output}")

if __name__ == "__main__":
    main()
