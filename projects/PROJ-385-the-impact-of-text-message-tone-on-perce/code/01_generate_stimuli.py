"""
Stimulus Generation Module for Text Message Tone Study.

This module implements the factorial generator for creating text message stimuli
based on base scenarios, varying emoji count, punctuation type, and message length.
It calculates cue intensity based on defined weighting schemes and outputs a
CSV file with all required metadata.
"""

import argparse
import csv
import itertools
import logging
import os
import random
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from config import get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants for factorial design
EMOJI_CATEGORIES = [0, 1, 2]  # 0 emojis, 1 emoji, >1 emojis (2 for factorial simplicity)
PUNCTUATION_TYPES = ["standard", "excessive"]
LENGTH_CATEGORIES = ["short", "long"]  # <10 words, >=10 words

# Base scenarios will be loaded from a JSON file
BASE_SCENARIOS_PATH = Path(get_raw_data_dir()) / "base_scenarios.json"

def load_base_scenarios() -> List[str]:
    """Load base scenarios from the JSON file."""
    if not BASE_SCENARIOS_PATH.exists():
        logger.error(f"Base scenarios file not found at {BASE_SCENARIOS_PATH}")
        raise FileNotFoundError(f"Base scenarios file not found at {BASE_SCENARIOS_PATH}")
    
    with open(BASE_SCENARIOS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'scenarios' not in data:
        logger.error("JSON file must contain a 'scenarios' key with a list of strings.")
        raise ValueError("JSON file must contain a 'scenarios' key with a list of strings.")
    
    return data['scenarios']

def load_weights() -> Dict[str, float]:
    """Load the primary cue intensity weighting scheme from the JSON file."""
    weights_path = Path(get_processed_data_dir()) / "cue_intensity_weights.json"
    if not weights_path.exists():
        logger.error(f"Weights file not found at {weights_path}")
        raise FileNotFoundError(f"Weights file not found at {weights_path}")
    
    with open(weights_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # We expect the "equal" scheme to be the primary one, or we take the first one
    # The file structure is a dict of scheme_name -> weights
    if "equal" in data:
        return data["equal"]
    elif len(data) > 0:
        # Fallback to first scheme if "equal" not found
        first_key = list(data.keys())[0]
        logger.warning(f"Scheme 'equal' not found, using first available scheme: {first_key}")
        return data[first_key]
    else:
        logger.error("No weighting schemes found in the file.")
        raise ValueError("No weighting schemes found in the file.")

def count_emojis(text: str) -> int:
    """Count the number of emojis in the text."""
    # Basic emoji regex for common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    matches = emoji_pattern.findall(text)
    return len(matches)

def get_punctuation_marker(text: str) -> str:
    """Determine if punctuation is standard or excessive."""
    # Count punctuation marks
    punct_count = len(re.findall(r'[.!?;:]', text))
    word_count = len(text.split())
    
    # Excessive if more than 1.5 punctuation marks per sentence (approx)
    # Or if there are more than 3 punctuation marks in a short message
    if word_count < 10:
        return "excessive" if punct_count > 2 else "standard"
    else:
        return "excessive" if punct_count > 5 else "standard"

def categorize_length(text: str) -> str:
    """Categorize text length as short (<10 words) or long (>=10 words)."""
    words = text.split()
    return "long" if len(words) >= 10 else "short"

def generate_message(base_text: str, emoji_count: int, punct_type: str) -> str:
    """
    Generate a stimulus message by applying emoji and punctuation variations
    to a base scenario.
    """
    # Start with base text
    message = base_text.strip()
    
    # Apply punctuation variation
    if punct_type == "excessive":
        # Add extra punctuation
        if not message.endswith(('.', '!', '?')):
            message += "!"
        message += "!!"  # Excessive punctuation
    else:
        # Ensure standard punctuation
        if not message.endswith(('.', '!', '?')):
            message += "."
    
    # Apply emoji variation
    emojis = ["😊", "😢", "😠", "😍", "😡", "😔", "🙏", "💪", "❤️", "👍"]
    selected_emojis = []
    
    if emoji_count > 0:
        # Select random emojis
        num_to_add = min(emoji_count, len(emojis))
        selected_emojis = random.sample(emojis, num_to_add)
        # Append emojis to the end of the message
        message += " " + " ".join(selected_emojis)
    
    return message

def calculate_cue_intensity(emoji_count: int, punct_type: str, length: str, weights: Dict[str, float]) -> float:
    """
    Calculate cue intensity based on weighted combination of features.
    Normalized to [0, 1] range.
    """
    # Normalize each feature to [0, 1]
    emoji_score = min(emoji_count / 2.0, 1.0)  # Max 2 emojis = 1.0
    
    punct_score = 1.0 if punct_type == "excessive" else 0.0
    
    length_score = 1.0 if length == "long" else 0.0
    
    # Weighted sum
    intensity = (
        weights.get("emoji", 0.33) * emoji_score +
        weights.get("punctuation", 0.33) * punct_score +
        weights.get("length", 0.34) * length_score
    )
    
    return round(intensity, 4)

def generate_stimuli() -> List[Dict[str, Any]]:
    """
    Generate all factorial combinations of stimuli based on base scenarios.
    Returns a list of dictionaries with stimulus metadata.
    """
    scenarios = load_base_scenarios()
    weights = load_weights()
    
    stimuli = []
    stimulus_id_counter = 1
    
    for scenario_id, base_text in enumerate(scenarios, 1):
        # Generate all factorial combinations
        for emoji_count, punct_type, length_cat in itertools.product(
            EMOJI_CATEGORIES, PUNCTUATION_TYPES, LENGTH_CATEGORIES
        ):
            # Generate the message
            message = generate_message(base_text, emoji_count, punct_type)
            
            # Recalculate actual features from generated message
            actual_emoji_count = count_emojis(message)
            actual_punct_type = get_punctuation_marker(message)
            actual_length_cat = categorize_length(message)
            
            # Calculate cue intensity
            cue_intensity = calculate_cue_intensity(
                actual_emoji_count, actual_punct_type, actual_length_cat, weights
            )
            
            stimulus = {
                "stimulus_id": f"STIM_{stimulus_id_counter:04d}",
                "text": message,
                "emoji_count": actual_emoji_count,
                "punctuation_type": actual_punct_type,
                "length_category": actual_length_cat,
                "scenario_id": f"SCEN_{scenario_id:03d}",
                "cue_intensity": cue_intensity
            }
            
            stimuli.append(stimulus)
            stimulus_id_counter += 1
    
    logger.info(f"Generated {len(stimuli)} stimuli from {len(scenarios)} scenarios.")
    return stimuli

def save_stimuli(stimuli: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Save stimuli to a CSV file."""
    if output_path is None:
        output_path = Path(get_raw_data_dir()) / "stimuli.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "stimulus_id", "text", "emoji_count", "punctuation_type", 
        "length_category", "scenario_id", "cue_intensity"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)
    
    logger.info(f"Saved {len(stimuli)} stimuli to {output_path}")
    return output_path

def verify_stimuli(stimuli: List[Dict[str, Any]]) -> bool:
    """
    Verify that all feature combinations are unique.
    Returns True if all combinations are unique, False otherwise.
    """
    seen_combinations = set()
    duplicates = []
    
    for stim in stimuli:
        combo = (
            stim["emoji_count"],
            stim["punctuation_type"],
            stim["length_category"],
            stim["scenario_id"]
        )
        
        if combo in seen_combinations:
            duplicates.append(stim["stimulus_id"])
        else:
            seen_combinations.add(combo)
    
    if duplicates:
        logger.warning(f"Found duplicate feature combinations for stimuli: {duplicates}")
        return False
    
    logger.info("All feature combinations are unique.")
    return True

def main():
    """Main entry point for the stimulus generation script."""
    parser = argparse.ArgumentParser(description="Generate text message stimuli for the tone study.")
    parser.add_argument(
        "--verify", 
        action="store_true", 
        help="Verify that all feature combinations are unique after generation."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output path for the stimuli CSV file."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        # Generate stimuli
        stimuli = generate_stimuli()
        
        # Save to CSV
        output_path = Path(args.output) if args.output else None
        save_stimuli(stimuli, output_path)
        
        # Verify if requested
        if args.verify:
            is_unique = verify_stimuli(stimuli)
            if not is_unique:
                logger.error("Verification failed: duplicate feature combinations found.")
                exit(1)
            else:
                logger.info("Verification passed: all feature combinations are unique.")
        
        logger.info("Stimulus generation completed successfully.")
        exit(0)
        
    except Exception as e:
        logger.error(f"Error during stimulus generation: {e}")
        exit(1)

if __name__ == "__main__":
    main()
