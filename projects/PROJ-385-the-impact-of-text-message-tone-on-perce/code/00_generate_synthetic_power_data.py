import argparse
import csv
import io
import logging
import random
import sys
from pathlib import Path

# Import from existing project modules to get paths
# The API surface indicates these exist in config.py
try:
    from config import get_processed_data_dir
except ImportError:
    # Fallback for standalone execution if config isn't in path yet
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_processed_data_dir

from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def setup_simulation(seed: int = 42):
    """Initialize random state for reproducibility."""
    random.seed(seed)
    logger.info(f"Simulation seeded with {seed}")

def generate_stimulus_ids(n_stimuli: int) -> list:
    """Generate unique stimulus identifiers."""
    return [f"stim_{i:03d}" for i in range(1, n_stimuli + 1)]

def generate_participant_ids(n_participants: int) -> list:
    """Generate unique participant identifiers."""
    return [f"part_{i:03d}" for i in range(1, n_participants + 1)]

def calculate_cue_intensity(emoji_count: int, punctuation_type: str, length: int, weights: dict) -> float:
    """
    Calculate cue intensity based on features and weights.
    Normalized to roughly 0-1 range for simulation.
    """
    # Simple normalization logic for synthetic generation
    emoji_score = min(emoji_count, 3) / 3.0
    punct_score = 1.0 if punctuation_type in ['exclamation', 'question'] else 0.5
    len_score = min(length, 50) / 50.0

    intensity = (
        weights['emoji'] * emoji_score +
        weights['punctuation'] * punct_score +
        weights['length'] * len_score
    )
    return intensity

def simulate_rating(
    participant_id: str,
    stimulus_id: str,
    relationship: str,
    cue_intensity: float,
    effect_size: float,
    noise_scale: float = 0.5
) -> float:
    """
    Simulate a rating based on a linear mixed model structure.
    rating = intercept + effect_size * cue_intensity + noise
    """
    base_rating = 3.0
    # Relationship effect (friend > acquaintance)
    rel_effect = 0.5 if relationship == 'friend' else -0.2
    
    # Main effect of cue intensity
    intensity_effect = effect_size * cue_intensity

    # Random noise (simulating residual + random effects for simplicity in generation)
    noise = random.gauss(0, noise_scale)

    rating = base_rating + rel_effect + intensity_effect + noise
    # Clamp to 1-5 scale
    return max(1.0, min(5.0, rating))

def generate_dataset(
    n_participants: int,
    n_stimuli: int,
    effect_size: float,
    relationship_contexts: list,
    weights: dict,
    seed: int
) -> list:
    """
    Generate the full synthetic dataset for power analysis.
    Returns a list of dictionaries representing rows.
    """
    setup_simulation(seed)
    
    stimulus_ids = generate_stimulus_ids(n_stimuli)
    participant_ids = generate_participant_ids(n_participants)
    
    data = []
    
    # Fully within-subjects: every participant sees every stimulus in every context
    for p_id in participant_ids:
        for s_id in stimulus_ids:
            for rel in relationship_contexts:
                # Generate synthetic features for this stimulus
                emoji_count = random.randint(0, 3)
                punct_type = random.choice(['period', 'exclamation', 'question'])
                length = random.randint(10, 60)
                
                cue_intensity = calculate_cue_intensity(emoji_count, punct_type, length, weights)
                
                rating = simulate_rating(
                    p_id, s_id, rel, cue_intensity, effect_size
                )
                
                data.append({
                    'participant_id': p_id,
                    'stimulus_id': s_id,
                    'relationship_type': rel,
                    'emoji_count': emoji_count,
                    'punctuation_type': punct_type,
                    'length': length,
                    'cue_intensity': round(cue_intensity, 4),
                    'rating': round(rating, 2)
                })
    
    return data

def save_dataset_to_csv(data: list, output_path: Path):
    """Save the generated dataset to a CSV file."""
    if not data:
        raise ValueError("Cannot save empty dataset")
        
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def main():
    """
    Main entry point for generating synthetic power analysis datasets.
    Creates datasets for the three weighting schemes defined in T090.
    """
    # Configuration matching T090 requirements
    n_participants = 60
    n_stimuli = 20
    effect_size = 0.25
    relationships = ['friend', 'acquaintance']
    seed = 42
    
    # Define the three weighting schemes exactly as per T090
    schemes = {
        'equal': {'emoji': 0.33, 'punctuation': 0.33, 'length': 0.34},
        'emoji_dominant': {'emoji': 0.6, 'punctuation': 0.2, 'length': 0.2},
        'punctuation_dominant': {'emoji': 0.2, 'punctuation': 0.6, 'length': 0.2}
    }
    
    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_files = []
    
    for scheme_name, weights in schemes.items():
        logger.info(f"Generating dataset for scheme: {scheme_name}")
        data = generate_dataset(
            n_participants, n_stimuli, effect_size, relationships, weights, seed
        )
        
        filename = f"synthetic_power_{scheme_name}.csv"
        output_path = processed_dir / filename
        save_dataset_to_csv(data, output_path)
        output_files.append(filename)
    
    # Zip all generated files into the required archive
    zip_path = processed_dir / "synthetic_power_datasets.zip"
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in output_files:
            file_path = processed_dir / fname
            zf.write(file_path, arcname=fname)
            # Remove individual CSVs after zipping to keep directory clean
            file_path.unlink()
    
    logger.info(f"Created zip archive: {zip_path}")
    logger.info(f"Archived files: {output_files}")

if __name__ == '__main__':
    setup_logging()
    main()
