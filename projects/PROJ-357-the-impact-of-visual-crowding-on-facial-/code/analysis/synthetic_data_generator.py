import os
import sys
import json
import logging
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_seed, set_all_seeds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the stimuli manifest."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def calculate_base_accuracy(flanker_count: int, eccentricity: float, emotion: str) -> float:
    """
    Calculate base accuracy based on crowding parameters.
    
    Logic:
    - Higher flanker count -> lower accuracy (crowding effect)
    - Higher eccentricity -> lower accuracy (peripheral vision degradation)
    - Some emotions (e.g., fear) might be harder to recognize than others (e.g., happy)
    
    Returns:
        Base probability of correct classification (0.0 to 1.0)
    """
    # Base accuracy for ideal conditions (low crowding)
    base = 0.95
    
    # Crowding penalty: more flankers reduce accuracy
    # Assuming flanker_count >= 3
    crowding_penalty = (flanker_count - 3) * 0.04
    
    # Eccentricity penalty: further from center reduces accuracy
    # Assuming eccentricity in degrees, typical range 2-10
    ecc_penalty = (eccentricity - 2) * 0.03
    
    # Emotion difficulty modifier (simplified)
    emotion_difficulty = {
        "happy": 0.0,
        "sad": 0.02,
        "angry": 0.03,
        "fear": 0.05,
        "disgust": 0.04,
        "surprise": 0.02,
        "neutral": 0.01,
        "contempt": 0.05
    }
    emo_penalty = emotion_difficulty.get(emotion.lower(), 0.03)
    
    # Calculate final probability, clamped between 0.6 and 0.99
    accuracy = base - crowding_penalty - ecc_penalty - emo_penalty
    return max(0.6, min(0.99, accuracy))

def generate_response(true_label: str, base_accuracy: float, seed: int) -> str:
    """
    Generate a single response label.
    
    Args:
        true_label: The correct emotion label
        base_accuracy: Probability of correct response
        seed: Random state for this specific trial (derived from global seed)
    
    Returns:
        Predicted emotion label string
    """
    random.seed(seed)
    
    if random.random() < base_accuracy:
        return true_label
    
    # If incorrect, choose a random wrong label
    all_emotions = ["happy", "sad", "angry", "fear", "disgust", "surprise", "neutral", "contempt"]
    wrong_options = [e for e in all_emotions if e != true_label]
    return random.choice(wrong_options)

def generate_synthetic_responses(stimuli_list: List[Dict], num_participants: int, seed: int) -> List[Dict]:
    """
    Generate synthetic recognition responses for all stimuli and participants.
    
    Args:
        stimuli_list: List of stimulus metadata dictionaries
        num_participants: Number of simulated observers
        seed: Base random seed
    
    Returns:
        List of response records
    """
    set_all_seeds(seed)
    responses = []
    
    emotions = ["happy", "sad", "angry", "fear", "disgust", "surprise", "neutral", "contempt"]
    
    for p_idx in range(1, num_participants + 1):
        participant_id = f"sub_{p_idx:03d}"
        
        for s_idx, stimulus in enumerate(stimuli_list):
            stimulus_id = stimulus.get('file_path', f"stim_{s_idx:04d}")
            # Extract metadata from stimulus object or filename if needed
            # Assuming manifest structure has these keys directly
            emotion = stimulus.get('emotion', 'neutral')
            flanker_count = stimulus.get('flanker_count', 3)
            eccentricity = stimulus.get('eccentricity', 4.0)
            
            # Calculate base accuracy for this trial
            base_acc = calculate_base_accuracy(flanker_count, eccentricity, emotion)
            
            # Generate a unique seed for this specific trial response
            trial_seed = seed + p_idx * 10000 + s_idx
            response_label = generate_response(emotion, base_acc, trial_seed)
            
            # Determine accuracy (1 if correct, 0 if incorrect)
            is_correct = 1 if response_label == emotion else 0
            
            record = {
                "participant_id": participant_id,
                "stimulus_id": stimulus_id,
                "true_label": emotion,
                "response_label": response_label,
                "accuracy": is_correct,
                "flanker_count": flanker_count,
                "eccentricity": eccentricity,
                "stimulus_emotion": emotion
            }
            responses.append(record)
    
    return responses

def save_responses(responses: List[Dict], output_path: str):
    """Save the generated responses to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(responses, f, indent=2)
    logger.info(f"Saved {len(responses)} responses to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic pilot data.")
    parser.add_argument("--manifest", type=str, default="data/interim/stimuli_manifest.json")
    parser.add_argument("--output", type=str, default="data/interim/raw_pilot_responses.json")
    parser.add_argument("--participants", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    
    logger.info(f"Generating synthetic data for {args.participants} participants...")
    
    manifest = load_manifest(args.manifest)
    stimuli = list(manifest.values())
    
    if not stimuli:
        logger.error("No stimuli found in manifest.")
        sys.exit(1)
        
    responses = generate_synthetic_responses(stimuli, args.participants, args.seed)
    save_responses(responses, args.output)
    print(f"Generated {len(responses)} trials.")

if __name__ == "__main__":
    main()