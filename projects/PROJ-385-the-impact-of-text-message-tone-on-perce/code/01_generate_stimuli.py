"""
Stimulus Generation Module (T013)

Implements a factorial generator for text message stimuli based on:
- Emoji presence/count
- Punctuation type
- Message length
- Scenario context

Output: data/raw/stimuli.csv
"""
import argparse
import csv
import itertools
import logging
import os
import random
import json
from pathlib import Path

from config import get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Scenario templates (placeholders for {text})
SCENARIOS = [
    "Hey, {text}",
    "Just wanted to say {text}",
    "Are you there? {text}",
    "So about our plans: {text}",
    "I was thinking {text}",
    "Can you check {text}",
    "Oh, {text}",
    "Wait, {text}",
]

# Text fragments to vary length and emoji content
FRAGMENTS = {
    "short": [
        "ok",
        "yes",
        "no",
        "bye",
        "hi",
        "lol",
        "wow",
        "wow",
        "yep",
        "nah",
    ],
    "medium": [
        "I think that sounds good",
        "Let me know what you think",
        "I'm not sure about that",
        "That works for me",
        "Can we do it later?",
        "I'm on my way now",
        "See you in a bit",
        "Sounds like a plan",
    ],
    "long": [
        "I was wondering if we could maybe reschedule our meeting for tomorrow instead of today since I have a conflict",
        "Actually I think I might be running a bit late so sorry about that but I'll be there as soon as I can",
        "I just wanted to double check if you are still coming to the event this weekend because I need to know for sure",
        "Hey I was thinking maybe we could grab coffee sometime next week if you are free let me know what works",
        "I'm really sorry I forgot to send that file yesterday I'll send it over right now please check your email",
    ],
}

# Emoji options
EMOJIS = [
    "😀", "😂", "😍", "😎", "😢", "😡", "😱", "🤔", "👍", "👎",
    "❤️", "🔥", "✨", "🎉", "🙏", "💯", "🤝", "👀", "🚀", "💡"
]

# Punctuation types
PUNCTUATION_TYPES = ["period", "exclamation", "question", "none"]

def count_emojis(text: str) -> int:
    """Count the number of emoji characters in the text."""
    # Simple heuristic: count characters in the emoji range
    # This is a simplified check; in production, use a dedicated emoji library
    count = 0
    for char in text:
        if '\U0001F600' <= char <= '\U0001F64F' or \
           '\U0001F300' <= char <= '\U0001F5FF' or \
           '\U0001F680' <= char <= '\U0001F6FF' or \
           '\U0001F1E0' <= char <= '\U0001F1FF' or \
           '\u2600' <= char <= '\u26FF' or \
           '\u2700' <= char <= '\u27BF':
            count += 1
    return count

def get_punctuation_marker(punct_type: str) -> str:
    """Return the punctuation character based on type."""
    mapping = {
        "period": ".",
        "exclamation": "!",
        "question": "?",
        "none": ""
    }
    return mapping.get(punct_type, "")

def categorize_length(text: str) -> str:
    """Categorize text length into short, medium, or long."""
    length = len(text.split())
    if length <= 3:
        return "short"
    elif length <= 10:
        return "medium"
    else:
        return "long"

def generate_message(scenario: str, fragment: str, punct_type: str, add_emoji: bool) -> str:
    """Generate a full message from scenario, fragment, punctuation, and optional emoji."""
    punct = get_punctuation_marker(punct_type)
    text = f"{fragment}{punct}"
    
    if add_emoji:
        emoji = random.choice(EMOJIS)
        # Place emoji at the end or beginning randomly
        if random.random() > 0.5:
            text = f"{text} {emoji}"
        else:
            text = f"{emoji} {text}"
    
    return scenario.format(text=text)

def calculate_cue_intensity(emoji_count: int, punct_type: str, length_cat: str, weights: dict) -> float:
    """
    Calculate cue intensity score based on weighted features.
    
    Args:
        emoji_count: Number of emojis
        punct_type: Type of punctuation (period, exclamation, question, none)
        length_cat: Length category (short, medium, long)
        weights: Dictionary of weights for each feature from cue_intensity_weights.json
    
    Returns:
        Float score representing cue intensity
    """
    # Normalize emoji count (0-2 emojis considered, cap at 2 for normalization)
    emoji_score = min(emoji_count, 2) / 2.0 if weights.get("emoji", 0) > 0 else 0.0
    
    # Normalize punctuation intensity
    punct_scores = {"none": 0.0, "period": 0.3, "question": 0.5, "exclamation": 1.0}
    punct_score = punct_scores.get(punct_type, 0.0)
    
    # Normalize length
    length_scores = {"short": 0.3, "medium": 0.6, "long": 1.0}
    length_score = length_scores.get(length_cat, 0.5)
    
    # Calculate weighted sum
    intensity = (
        emoji_score * weights.get("emoji", 0.33) +
        punct_score * weights.get("punctuation", 0.33) +
        length_score * weights.get("length", 0.34)
    )
    
    return round(intensity, 4)

def load_weights():
    """Load cue intensity weights from the JSON file."""
    weights_path = get_processed_data_dir() / "cue_intensity_weights.json"
    if not weights_path.exists():
        logger.error(f"Weights file not found: {weights_path}")
        raise FileNotFoundError(f"Weights file not found: {weights_path}")
    
    with open(weights_path, 'r') as f:
        data = json.load(f)
    
    # Return the primary scheme (Equal) for this generation
    # We can extend this to generate multiple versions if needed
    return data.get("Equal", {"emoji": 0.33, "punctuation": 0.33, "length": 0.34})

def generate_stimuli():
    """
    Generate all factorial combinations of stimulus features.
    
    Returns:
        List of dictionaries representing each stimulus
    """
    weights = load_weights()
    stimuli = []
    stimulus_id = 0
    
    # Factorial design:
    # - 8 scenarios
    # - 3 length categories (short, medium, long)
    # - 4 punctuation types
    # - 2 emoji conditions (with emoji, without emoji)
    # - Multiple fragments per length category to ensure variety
    
    scenarios = SCENARIOS
    lengths = ["short", "medium", "long"]
    punct_types = PUNCTUATION_TYPES
    emoji_conditions = [False, True]
    
    # Create factorial combinations
    for scenario in scenarios:
        for length_cat in lengths:
            fragments = FRAGMENTS[length_cat]
            for punct_type in punct_types:
                for add_emoji in emoji_conditions:
                    # Select a fragment (cycle through if needed)
                    # Use a deterministic selection based on indices to ensure reproducibility
                    fragment_idx = stimulus_id % len(fragments)
                    fragment = fragments[fragment_idx]
                    
                    # Generate message
                    message = generate_message(scenario, fragment, punct_type, add_emoji)
                    
                    # Calculate features
                    emoji_count = count_emojis(message)
                    length_cat_actual = categorize_length(message)
                    
                    # Calculate cue intensity
                    cue_intensity = calculate_cue_intensity(
                        emoji_count, punct_type, length_cat_actual, weights
                    )
                    
                    # Create stimulus record
                    record = {
                        "id": f"stim_{stimulus_id:04d}",
                        "text": message,
                        "emoji_count": emoji_count,
                        "punctuation_type": punct_type,
                        "length_category": length_cat_actual,
                        "scenario_id": scenarios.index(scenario),
                        "cue_intensity": cue_intensity
                    }
                    
                    stimuli.append(record)
                    stimulus_id += 1
    
    logger.info(f"Generated {len(stimuli)} unique stimuli")
    return stimuli

def save_stimuli(stimuli: list, output_path: Path):
    """Save stimuli to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id", "cue_intensity"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)
    
    logger.info(f"Saved {len(stimuli)} stimuli to {output_path}")

def verify_stimuli(stimuli: list) -> bool:
    """
    Verify that all feature combinations are unique.
    
    Args:
        stimuli: List of stimulus dictionaries
    
    Returns:
        True if verification passes, False otherwise
    """
    combinations = set()
    duplicates = []
    
    for s in stimuli:
        # Create a tuple of key features to check uniqueness
        key = (
            s["scenario_id"],
            s["length_category"],
            s["punctuation_type"],
            s["emoji_count"] > 0  # Binary: has emoji or not
        )
        
        if key in combinations:
            duplicates.append(s["id"])
        else:
            combinations.add(key)
    
    if duplicates:
        logger.warning(f"Found duplicate combinations in stimuli: {duplicates[:5]}...")
        return False
    
    logger.info("Verification passed: All feature combinations are unique")
    return True

def main():
    """Main entry point for stimulus generation."""
    parser = argparse.ArgumentParser(description="Generate factorial text message stimuli")
    parser.add_argument("--verify", action="store_true", help="Verify uniqueness of feature combinations")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        # Generate stimuli
        stimuli = generate_stimuli()
        
        # Save to CSV
        output_path = get_raw_data_dir() / "stimuli.csv"
        save_stimuli(stimuli, output_path)
        
        # Verify if requested
        if args.verify:
            if not verify_stimuli(stimuli):
                logger.error("Verification failed: Duplicate feature combinations found")
                return 1
        
        logger.info("Stimulus generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during stimulus generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
