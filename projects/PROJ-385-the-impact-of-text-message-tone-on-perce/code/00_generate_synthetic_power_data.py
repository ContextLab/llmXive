"""
Synthetic Power-Analysis Dataset Generator.

Generates synthetic datasets for power analysis based on the specified parameters:
- Variance components: sigma_participant=0.5, sigma_stimulus=0.3, residual=1.0
- Effect size: 0.25
- N participants: 60
- Uses RANDOM_SEED from config.py for reproducibility.

Outputs a ZIP file containing CSVs with the synthetic data.
"""
import argparse
import csv
import io
import logging
import random
import sys
import zipfile
import json
import hashlib
from pathlib import Path

# Local imports based on provided API surface
from config import get_processed_data_dir, RANDOM_SEED
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def setup_simulation(seed: int):
    """Initialize random state for reproducibility."""
    random.seed(seed)
    logger.info(f"Simulation initialized with seed: {seed}")

def generate_stimulus_ids(n_stimuli: int) -> list:
    """Generate unique stimulus IDs."""
    return [f"STIM_{i:04d}" for i in range(n_stimuli)]

def generate_participant_ids(n_participants: int) -> list:
    """Generate unique participant IDs (Prolific-style)."""
    return [f"P{random.randint(100000, 999999)}" for _ in range(n_participants)]

def calculate_cue_intensity(emoji_count: int, punct_type: str, length_cat: str, weights: dict) -> float:
    """
    Calculate cue intensity based on features and weights.
    Tuple order: (emoji, punctuation, length)
    """
    # Normalize inputs to 0-1 scale for calculation
    emoji_score = min(emoji_count, 2) / 2.0
    punct_score = 1.0 if punct_type == "Excessive" else 0.0
    length_score = 1.0 if length_cat == "Long" else 0.0

    # Apply weights
    intensity = (
        weights['emoji'] * emoji_score +
        weights['punctuation'] * punct_score +
        weights['length'] * length_score
    )
    return intensity

def simulate_rating(participant_id: str, stimulus_id: str, cue_intensity: float, 
                    relationship: str, params: dict) -> float:
    """
    Simulate a rating based on a linear mixed model structure.
    
    Model: rating ~ relationship * cue_intensity + (1|participant) + (1|stimulus) + residual
    Effect size 0.25 is simulated as the coefficient for the interaction or main effect
    depending on the specific power analysis goal. Here we model the interaction effect.
    """
    # Fixed effects
    intercept = 3.0
    beta_relationship = 0.2 if relationship == "friend" else 0.0
    beta_cue = 0.5
    beta_interaction = 0.25  # Target effect size

    # Linear predictor
    fixed_effect = intercept + beta_relationship + (beta_cue * cue_intensity) + (beta_interaction * cue_intensity * (1 if relationship == "friend" else 0))

    # Random effects
    # Map IDs to random values for reproducibility within this run
    p_idx = int(participant_id[1:]) % 1000000 # Simple hash
    random.seed(p_idx + params['seed'])
    u_participant = random.gauss(0, params['sigma_participant'])
    
    s_idx = int(stimulus_id.split('_')[1])
    random.seed(s_idx + params['seed'])
    u_stimulus = random.gauss(0, params['sigma_stimulus'])

    # Residual
    random.seed(int(stimulus_id.split('_')[1]) + int(participant_id[1:]) + params['seed'])
    e_residual = random.gauss(0, params['residual'])

    rating = fixed_effect + u_participant + u_stimulus + e_residual
    return round(rating, 2)

def generate_dataset(n_participants: int, n_stimuli: int, params: dict) -> list:
    """Generate the full synthetic dataset."""
    setup_simulation(params['seed'])
    participants = generate_participant_ids(n_participants)
    stimuli = generate_stimulus_ids(n_stimuli)
    
    # Define cue variations for factorial design
    emoji_counts = [0, 1, 2]
    punct_types = ["Standard", "Excessive"]
    length_cats = ["Short", "Long"]
    relationships = ["friend", "acquaintance"]
    
    # Weights for calculation (Equal distribution for baseline)
    weights = {'emoji': 0.3333333333, 'punctuation': 0.3333333333, 'length': 0.3333333334}

    data_rows = []
    
    # Create a full factorial design for stimuli
    stimulus_features = []
    for e in emoji_counts:
        for p in punct_types:
            for l in length_cats:
                for r in relationships:
                    cue = calculate_cue_intensity(e, p, l, weights)
                    stimulus_features.append({
                        'stimulus_id': f"STIM_{len(stimulus_features):04d}",
                        'text': f"Message {len(stimulus_features)}",
                        'emoji_count': e,
                        'punctuation_type': p,
                        'length_category': l,
                        'relationship': r,
                        'cue_intensity': round(cue, 4)
                    })
    
    # Generate ratings for each participant for each stimulus
    # To keep N manageable for the zip but representative, we sample or iterate
    # Task requires N=60 participants.
    
    rows = []
    for p_id in participants:
        for s_feat in stimulus_features:
            s_id = s_feat['stimulus_id']
            cue = s_feat['cue_intensity']
            rel = s_feat['relationship']
            
            rating = simulate_rating(p_id, s_id, cue, rel, params)
            rows.append({
                'participant_id': p_id,
                'stimulus_id': s_id,
                'relationship_type': rel,
                'cue_intensity': cue,
                'rating': rating,
                'text': s_feat['text']
            })
    
    return rows

def save_dataset_to_csv(data: list, output_path: Path):
    """Save dataset to CSV."""
    if not data:
        logger.warning("No data to save.")
        return
    
    fieldnames = data[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Saved dataset to {output_path}")

def save_checksums(checksums: dict, output_path: Path):
    """Save checksums to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksums to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic power analysis datasets.")
    parser.add_argument("--n_participants", type=int, default=60, help="Number of participants (N)")
    parser.add_argument("--n_stimuli", type=int, default=12, help="Number of stimuli")
    parser.add_argument("--output_zip", type=str, default="data/processed/synthetic_power_datasets.zip", help="Output ZIP path")
    parser.add_argument("--output_checksums", type=str, default="data/checksums.json", help="Output checksums JSON path")
    args = parser.parse_args()

    setup_logging()
    
    # Parameters from task description
    params = {
        'seed': RANDOM_SEED,
        'sigma_participant': 0.5,
        'sigma_stimulus': 0.3,
        'residual': 1.0,
        'effect_size': 0.25
    }

    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = processed_dir / "synthetic_power_data.csv"
    zip_path = Path(args.output_zip)
    checksums_path = Path(args.output_checksums)

    logger.info(f"Generating synthetic dataset with N={args.n_participants}...")
    data = generate_dataset(args.n_participants, args.n_stimuli, params)
    
    logger.info(f"Saving CSV to {csv_path}...")
    save_dataset_to_csv(data, csv_path)

    # Compute checksum of the CSV
    sha256_hash = hashlib.sha256()
    with open(csv_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    csv_checksum = sha256_hash.hexdigest()

    # Create ZIP file
    logger.info(f"Creating ZIP archive {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_path, csv_path.name)
    
    # Compute checksum of ZIP
    sha256_zip = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_zip.update(byte_block)
    zip_checksum = sha256_zip.hexdigest()

    # Update checksums file
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    
    checksums["synthetic_power_data.csv"] = csv_checksum
    checksums["synthetic_power_datasets.zip"] = zip_checksum
    
    save_checksums(checksums, checksums_path)

    logger.info("Synthetic power analysis datasets generated successfully.")
    print(f"Output: {zip_path}")
    print(f"Checksum (ZIP): {zip_checksum}")

if __name__ == "__main__":
    main()
