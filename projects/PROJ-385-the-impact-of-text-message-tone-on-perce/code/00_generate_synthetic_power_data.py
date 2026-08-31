"""
Generate synthetic datasets for power analysis simulation.

This script creates synthetic rating data with a known random-effects structure
(Participant, Stimulus) and a fixed effect size (0.25) to enable power analysis
for the Linear Mixed Model (LMM).

Output: data/processed/synthetic_power_datasets.zip
"""
import argparse
import csv
import io
import logging
import random
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np

# Import project configuration and logging
sys.path.insert(0, str(Path(__file__).parent))
from config import get_processed_data_dir
from logging_config import setup_logging, get_logger

# Constants for the simulation
N_PARTICIPANTS = 60
N_STIMULI = 20  # Assuming a reasonable number of stimuli for the factorial design
EFFECT_SIZE = 0.25
RANDOM_SEED = 42

def setup_simulation(seed: int = RANDOM_SEED) -> None:
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logging.info(f"Simulation seeded with {seed}")

def generate_stimulus_ids(n_stimuli: int) -> List[str]:
    """Generate unique stimulus identifiers."""
    return [f"stim_{i:03d}" for i in range(n_stimuli)]

def generate_participant_ids(n_participants: int) -> List[str]:
    """Generate unique participant identifiers."""
    return [f"sub_{i:03d}" for i in range(n_participants)]

def calculate_cue_intensity(
    emoji_count: int, punctuation_type: str, length_category: str,
    weights: Dict[str, float]
) -> float:
    """
    Calculate cue intensity based on the weighting scheme.
    Normalized to 0-1 range for simulation purposes.
    """
    # Normalize inputs to 0-1 scale for calculation
    e_norm = min(emoji_count / 3.0, 1.0)  # Assume max 3 emojis
    p_norm = 0.0
    if punctuation_type == "exclamation":
        p_norm = 1.0
    elif punctuation_type == "question":
        p_norm = 0.5
    elif punctuation_type == "period":
        p_norm = 0.2
    
    l_norm = 0.0
    if length_category == "long":
        l_norm = 1.0
    elif length_category == "medium":
        l_norm = 0.5
    elif length_category == "short":
        l_norm = 0.2

    return (e_norm * weights["emoji"] + 
            p_norm * weights["punctuation"] + 
            l_norm * weights["length"])

def simulate_rating(
    participant_id: str,
    stimulus_id: str,
    cue_intensity: float,
    relationship_type: str,
    effect_size: float,
    noise_scale: float = 0.5
) -> float:
    """
    Simulate a rating based on the LMM structure:
    Rating = Fixed_Effect + Random_Participant + Random_Stimulus + Error
    
    Fixed Effect: Beta * cue_intensity + Beta_interaction * (cue_intensity * relationship)
    """
    # Random effects (Normal distribution)
    participant_effect = np.random.normal(0, 0.3)
    stimulus_effect = np.random.normal(0, 0.2)
    
    # Fixed effects
    # Assume a base relationship effect (e.g., friend > acquaintance)
    relationship_effect = 0.1 if relationship_type == "friend" else 0.0
    
    # Interaction effect (the target of power analysis)
    interaction_term = cue_intensity * (1.0 if relationship_type == "friend" else 0.0)
    
    # Total score
    score = (
        3.0 +  # Intercept
        effect_size * cue_intensity +  # Main effect of cue intensity
        relationship_effect +  # Main effect of relationship
        effect_size * 0.5 * interaction_term +  # Interaction (scaled)
        participant_effect +
        stimulus_effect +
        np.random.normal(0, noise_scale)  # Residual error
    )
    
    # Clamp to 1-5 Likert scale
    return np.clip(score, 1.0, 5.0)

def generate_dataset(
    n_participants: int,
    n_stimuli: int,
    effect_size: float,
    relationship_types: List[str],
    seed: int
) -> List[Dict[str, Any]]:
    """Generate a full synthetic dataset."""
    random.seed(seed)
    np.random.seed(seed)
    
    stimuli = generate_stimulus_ids(n_stimuli)
    participants = generate_participant_ids(n_participants)
    
    # Define cue combinations for factorial design
    emoji_counts = [0, 1, 2]
    punctuation_types = ["period", "exclamation", "question"]
    length_categories = ["short", "medium", "long"]
    
    cue_configs = []
    for e in emoji_counts:
        for p in punctuation_types:
            for l in length_categories:
                cue_configs.append((e, p, l))
    
    # Use Equal Weight scheme as defined in T090
    weights = {"emoji": 0.333, "punctuation": 0.333, "length": 0.333}
    
    data_rows = []
    
    for p_id in participants:
        for s_id in stimuli:
            # Select a cue config (simplified: cycle through or random)
            config = random.choice(cue_configs)
            emoji_count, punct_type, length_cat = config
            cue_intensity = calculate_cue_intensity(emoji_count, punct_type, length_cat, weights)
            
            for rel_type in relationship_types:
                rating = simulate_rating(
                    p_id, s_id, cue_intensity, rel_type, effect_size
                )
                data_rows.append({
                    "participant_id": p_id,
                    "stimulus_id": s_id,
                    "relationship_type": rel_type,
                    "rating": round(rating, 2),
                    "cue_intensity": round(cue_intensity, 3),
                    "emoji_count": emoji_count,
                    "punctuation_type": punct_type,
                    "length_category": length_cat
                })
    
    return data_rows

def save_dataset_to_csv(data: List[Dict[str, Any]], filename: str) -> str:
    """Save dataset to a CSV string."""
    output = io.StringIO()
    if not data:
        return output.getvalue()
    
    fieldnames = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic datasets for power analysis simulation."
    )
    parser.add_argument(
        "--n-participants", type=int, default=N_PARTICIPANTS,
        help="Number of participants (default: 60)"
    )
    parser.add_argument(
        "--n-stimuli", type=int, default=N_STIMULI,
        help="Number of stimuli (default: 20)"
    )
    parser.add_argument(
        "--effect-size", type=float, default=EFFECT_SIZE,
        help="Target effect size (default: 0.25)"
    )
    parser.add_argument(
        "--seed", type=int, default=RANDOM_SEED,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output zip file path (default: data/processed/synthetic_power_datasets.zip)"
    )
    args = parser.parse_args()

    setup_logging()
    logger = get_logger(__name__)
    
    logger.info(f"Starting synthetic data generation for N={args.n_participants}, "
                f"K={args.n_stimuli}, effect_size={args.effect_size}")
    
    setup_simulation(args.seed)
    
    # Generate dataset
    dataset = generate_dataset(
        n_participants=args.n_participants,
        n_stimuli=args.n_stimuli,
        effect_size=args.effect_size,
        relationship_types=["friend", "acquaintance"],
        seed=args.seed
    )
    
    logger.info(f"Generated {len(dataset)} rows of synthetic data.")
    
    # Prepare output
    output_path = Path(args.output) if args.output else get_processed_data_dir() / "synthetic_power_datasets.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    csv_content = save_dataset_to_csv(dataset, "synthetic_ratings.csv")
    
    # Write to zip
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("synthetic_ratings.csv", csv_content)
    
    logger.info(f"Successfully wrote synthetic datasets to {output_path}")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
