"""
Unit-test helper to generate a small synthetic pilot dataset.

This script is for pipeline validation and unit testing ONLY.
It does NOT produce research-grade results.

Usage:
    python code/analysis/generate_synthetic_data.py --output data/tests/synthetic_pilot_sample.csv --n_participants 5 --n_stimuli 10
"""
import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_all_seeds, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EMOTIONS = [
    'neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised'
]

def generate_synthetic_pilot_sample(
    output_path: Path,
    n_participants: int = 5,
    n_stimuli: int = 10,
    seed: int = 42
) -> None:
    """
    Generate a small synthetic pilot dataset for unit testing.
    
    Args:
        output_path: Where to write the CSV file.
        n_participants: Number of simulated participants.
        n_stimuli: Number of stimuli to simulate responses for per participant.
        seed: Random seed for reproducibility.
    """
    set_all_seeds(seed)
    logger.info(f"Generating synthetic pilot sample: {n_participants} participants, {n_stimuli} stimuli each")
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    rows = []
    
    # Generate stimuli IDs
    stimulus_ids = [f"stim_{i:04d}" for i in range(n_stimuli)]
    participant_ids = [f"sub_{i:03d}" for i in range(1, n_participants + 1)]
    
    for p_id in participant_ids:
        for s_id in stimulus_ids:
            # Randomly select emotion and parameters
            emotion = random.choice(EMOTIONS)
            flanker_count = random.choice([0, 4, 8, 12])
            eccentricity = random.choice([2, 4, 6, 8])
            
            # Simulate accuracy based on crowding (simplified model)
            # Higher flanker count and eccentricity -> lower accuracy
            base_acc = 0.9
            crowding_penalty = (flanker_count * 0.01) + (eccentricity * 0.02)
            prob_correct = max(0.4, base_acc - crowding_penalty)
            
            is_correct = random.random() < prob_correct
            accuracy = 1 if is_correct else 0
            
            # Generate response label (simplified: correct or random wrong)
            if is_correct:
                response_label = emotion
            else:
                response_label = random.choice([e for e in EMOTIONS if e != emotion])
            
            timestamp = datetime.now().isoformat()
            
            rows.append({
                'participant_id': p_id,
                'stimulus_id': s_id,
                'emotion_label': emotion,
                'response_label': response_label,
                'accuracy': accuracy,
                'flanker_count': flanker_count,
                'eccentricity': eccentricity,
                'timestamp': timestamp
            })
    
    # Write CSV
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'participant_id', 'stimulus_id', 'emotion_label', 'response_label',
            'accuracy', 'flanker_count', 'eccentricity', 'timestamp'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully wrote {len(rows)} rows to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate a small synthetic pilot dataset for unit testing."
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('data/tests/synthetic_pilot_sample.csv'),
        help='Output CSV path'
    )
    parser.add_argument(
        '--n_participants', '-p',
        type=int,
        default=5,
        help='Number of simulated participants'
    )
    parser.add_argument(
        '--n_stimuli', '-s',
        type=int,
        default=10,
        help='Number of stimuli per participant'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    
    args = parser.parse_args()
    generate_synthetic_pilot_sample(
        output_path=args.output,
        n_participants=args.n_participants,
        n_stimuli=args.n_stimuli,
        seed=args.seed
    )

if __name__ == '__main__':
    main()