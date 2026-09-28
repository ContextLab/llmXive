import os
import sys
import json
import logging
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_seed, set_all_seeds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load stimuli manifest from JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Handle different manifest formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'stimuli' in data:
            return data['stimuli']
        # If it's a single dict with stimulus properties, wrap it
        return [data]
    else:
        raise ValueError(f"Unexpected manifest format: {type(data)}")

def calculate_base_accuracy(emotion: str, flanker_count: int, eccentricity: float) -> float:
    """
    Calculate base accuracy for a stimulus based on conditions.
    
    This simulates realistic human performance:
    - Higher accuracy for fewer flankers
    - Lower accuracy for higher eccentricity
    - Variation by emotion (some emotions are harder to recognize)
    
    Args:
        emotion: Emotion category
        flanker_count: Number of flankers
        eccentricity: Visual eccentricity in degrees
    
    Returns:
        Base accuracy probability (0.0 to 1.0)
    """
    # Base accuracy starts at 0.85
    base_acc = 0.85
    
    # Adjust for flanker count (crowding effect)
    # More flankers = lower accuracy
    flanker_penalty = min(0.05 * (flanker_count - 1), 0.3)
    base_acc -= flanker_penalty
    
    # Adjust for eccentricity
    # Higher eccentricity = lower accuracy
    ecc_penalty = min(0.02 * eccentricity, 0.2)
    base_acc -= ecc_penalty
    
    # Emotion-specific adjustments
    emotion_difficulty = {
        'neutral': 0.0,      # Easiest
        'happy': 0.0,        # Easy
        'sad': -0.02,        # Slightly harder
        'angry': -0.03,      # Harder
        'fear': -0.05,       # Hard
        'disgust': -0.06,    # Harder
        'surprise': -0.02,   # Slightly harder
        'contempt': -0.08    # Hardest
    }
    
    base_acc += emotion_difficulty.get(emotion.lower(), 0.0)
    
    # Clamp to valid range
    return max(0.2, min(0.98, base_acc))

def generate_response(
    stimulus: Dict[str, Any],
    participant_id: int,
    seed: int
) -> Dict[str, Any]:
    """
    Generate a single response for a stimulus by a participant.
    
    Args:
        stimulus: Stimulus metadata
        participant_id: Unique participant identifier
        seed: Random seed for this response
    
    Returns:
        Response record dictionary
    """
    # Set seed for this specific response to ensure reproducibility
    random.seed(seed)
    
    emotion = stimulus.get('emotion', 'neutral')
    flanker_count = stimulus.get('flanker_count', 0)
    eccentricity = stimulus.get('eccentricity', 0.0)
    stimulus_id = stimulus.get('stimulus_id', stimulus.get('filename', 'unknown'))
    
    # Calculate base accuracy
    base_acc = calculate_base_accuracy(emotion, flanker_count, eccentricity)
    
    # Add participant-specific variability
    # Some participants are generally more accurate than others
    participant_bias = random.gauss(0, 0.05)
    adjusted_acc = max(0.2, min(0.98, base_acc + participant_bias))
    
    # Generate response
    is_correct = random.random() < adjusted_acc
    
    if is_correct:
        response_label = emotion
    else:
        # Generate a plausible wrong response
        all_emotions = ['neutral', 'happy', 'sad', 'angry', 'fear', 'disgust', 'surprise', 'contempt']
        wrong_emotions = [e for e in all_emotions if e != emotion]
        response_label = random.choice(wrong_emotions)
    
    # Generate timestamp (simulated)
    timestamp = f"2024-01-{random.randint(1, 28):02d}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
    
    return {
        'participant_id': participant_id,
        'stimulus_id': stimulus_id,
        'true_label': emotion,
        'response_label': response_label,
        'accuracy': 1 if is_correct else 0,
        'flanker_count': flanker_count,
        'eccentricity': eccentricity,
        'timestamp': timestamp
    }

def generate_synthetic_responses(
    stimuli: List[Dict[str, Any]],
    num_participants: int,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Generate synthetic responses for all stimuli from multiple participants.
    
    Args:
        stimuli: List of stimulus metadata
        num_participants: Number of simulated participants
        seed: Base random seed
    
    Returns:
        List of all response records
    """
    set_all_seeds(seed)
    all_responses = []
    
    for participant_id in range(1, num_participants + 1):
        for stimulus in stimuli:
            # Create a unique seed for this participant-stimulus combination
            response_seed = seed + participant_id * 10000 + hash(stimulus.get('stimulus_id', '')) % 10000
            
            response = generate_response(stimulus, participant_id, response_seed)
            all_responses.append(response)
    
    logger.info(f"Generated {len(all_responses)} responses for {num_participants} participants")
    return all_responses

def save_responses(responses: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save responses to a CSV file.
    
    Args:
        responses: List of response records
        output_path: Path to output CSV file
    """
    if not responses:
        logger.warning("No responses to save")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    import csv
    fieldnames = [
        'participant_id', 
        'stimulus_id', 
        'true_label', 
        'response_label', 
        'accuracy',
        'flanker_count', 
        'eccentricity', 
        'timestamp'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(responses)
    
    logger.info(f"Saved {len(responses)} responses to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic pilot data for visual crowding research"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/interim/stimuli_manifest.json",
        help="Path to stimuli manifest JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/interim/raw_synthetic_responses.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=10,
        help="Number of simulated participants"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    
    args = parser.parse_args()
    
    try:
        stimuli = load_manifest(Path(args.manifest))
        logger.info(f"Loaded {len(stimuli)} stimuli")
        
        responses = generate_synthetic_responses(
            stimuli=stimuli,
            num_participants=args.participants,
            seed=args.seed
        )
        
        save_responses(responses, Path(args.output))
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
