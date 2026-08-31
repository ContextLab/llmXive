"""
Stimulus Generator for Text Message Tone Study.

Implements a factorial design to generate text message stimuli varying in:
- Emoji usage (0, 1, 2+)
- Punctuation type (Period, Exclamation, Question, None)
- Message length (Short, Medium, Long)

Outputs a CSV file with all combinations and calculated cue intensity.
"""
import argparse
import csv
import itertools
import logging
import os
import random
from pathlib import Path

from config import get_raw_data_dir, get_project_root
from logging_config import setup_logging, get_logger

# Initialize logger
logger = setup_logging() if 'setup_logging' in globals() else logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants for the factorial design
EMOJI_LEVELS = ['none', 'low', 'high']  # none=0, low=1, high=2+
PUNCTUATION_LEVELS = ['period', 'exclamation', 'question', 'none']
LENGTH_LEVELS = ['short', 'medium', 'long']

# Base message templates per scenario (to ensure variety)
SCENARIOS = [
    {
        'id': 'S01',
        'context': 'Asking for help with a task',
        'templates': [
            "Hey, could you help me with this?",
            "I need a hand with something.",
            "Can you give me a hand?",
            "Could you assist me with this task?",
            "Would you mind helping me out?"
        ]
    },
    {
        'id': 'S02',
        'context': 'Canceling plans',
        'templates': [
            "Sorry, I can't make it.",
            "I have to cancel our plans.",
            "Something came up, can't go.",
            "I won't be able to attend.",
            "Regretfully, I must cancel."
        ]
    },
    {
        'id': 'S03',
        'context': 'Sharing good news',
        'templates': [
            "I got the job!",
            "Great news, I passed the exam.",
            "Guess what? I won!",
            "You won't believe this, I'm hired.",
            "Fantastic update on my end."
        ]
    },
    {
        'id': 'S04',
        'context': 'Expressing concern',
        'templates': [
            "Are you okay?",
            "I'm worried about you.",
            "Is everything alright?",
            "Please let me know you're safe.",
            "Something feels off, are you well?"
        ]
    }
]

# Emoji sets for low and high usage
EMOJI_SETS = {
    'low': ['🙂', '👍', '❤️', '😅', '😊'],
    'high': ['🙂👍', '❤️😅', '👍😊', '😅🙂', '❤️👍']
}

def count_emojis(text: str) -> int:
    """Count the number of emoji characters in the text."""
    # Simple heuristic: count characters in specific ranges or known emoji sets
    # For this generator, we know exactly what we added, so we can track it.
    # But for robustness, we scan for common emoji blocks.
    emoji_count = 0
    for char in text:
        if '\U0001F300' <= char <= '\U0001F9FF' or '\U00002600' <= char <= '\U000026FF':
            emoji_count += 1
    return emoji_count

def get_punctuation_marker(level: str) -> str:
    """Return the punctuation character based on the level."""
    mapping = {
        'period': '.',
        'exclamation': '!',
        'question': '?',
        'none': ''
    }
    return mapping.get(level, '')

def categorize_length(level: str) -> str:
    """Return the length category string."""
    return level

def generate_message(template: str, emoji_level: str, punct_level: str) -> str:
    """Construct the final message string."""
    msg = template
    
    # Add emoji if needed
    if emoji_level != 'none':
        # Pick a random emoji set from the defined set
        emoji_str = random.choice(EMOJI_SETS[emoji_level])
        # Append to the end before punctuation usually, or at end
        msg = f"{msg} {emoji_str}"
    
    # Add punctuation
    punct = get_punctuation_marker(punct_level)
    if punct:
        # Ensure no double punctuation if template already has one (simple check)
        if msg[-1] in '.!?':
            msg = msg[:-1] + punct
        else:
            msg = msg + punct
    
    return msg

def calculate_cue_intensity(emoji_count: int, punct_type: str, length_cat: str) -> float:
    """
    Calculate cue intensity based on the weighting scheme.
    Using the 'Equal Weight' scheme from T090 as the primary definition for generation:
    Emoji: 0.333, Punctuation: 0.333, Length: 0.333
    
    Normalized scores (0-1):
    - Emoji: 0 (none), 0.5 (low), 1.0 (high) -> mapped from count 0, 1, 2+
    - Punctuation: 0 (none), 0.33 (period), 0.66 (question), 1.0 (exclamation)
    - Length: 0 (short), 0.5 (medium), 1.0 (long)
    """
    # Normalize emoji score
    if emoji_count == 0:
        e_score = 0.0
    elif emoji_count == 1:
        e_score = 0.5
    else:
        e_score = 1.0

    # Normalize punctuation score
    punct_scores = {
        'none': 0.0,
        'period': 0.333,
        'question': 0.666,
        'exclamation': 1.0
    }
    p_score = punct_scores.get(punct_type, 0.0)

    # Normalize length score
    length_scores = {
        'short': 0.0,
        'medium': 0.5,
        'long': 1.0
    }
    l_score = length_scores.get(length_cat, 0.0)

    # Equal weight calculation
    intensity = (e_score + p_score + l_score) / 3.0
    return round(intensity, 4)

def generate_stimuli(seed: int) -> list:
    """
    Generate the full factorial set of stimuli.
    Returns a list of dictionaries representing each stimulus.
    """
    random.seed(seed)
    stimuli = []
    stimulus_id = 1

    # Iterate over all combinations
    for scenario in SCENARIOS:
        for emoji_level in EMOJI_LEVELS:
            for punct_level in PUNCTUATION_LEVELS:
                for length_level in LENGTH_LEVELS:
                    # Select a template based on length and randomness
                    # Map length to template selection to vary text slightly
                    base_templates = scenario['templates']
                    # Simple mapping: short=first, medium=middle, long=last (or random)
                    # To ensure variety, we just pick one randomly for this design
                    template = random.choice(base_templates)
                    
                    # Adjust text length artificially if needed to match category
                    # (In a real study, templates would be pre-written for lengths)
                    # Here we assume templates are varied enough or we repeat words for 'long'
                    if length_level == 'long':
                        # Extend text slightly to simulate length
                        template = f"{template} {template.split()[-1]} {template.split()[-1]}"
                    elif length_level == 'short':
                        # Ensure short is short (truncate if necessary, though templates are short)
                        pass
                    
                    text = generate_message(template, emoji_level, punct_level)
                    
                    # Calculate metrics
                    e_count = count_emojis(text)
                    # Override count if we used our logic (count_emojis might miss complex combos)
                    if emoji_level == 'low':
                        e_count = 1
                    elif emoji_level == 'high':
                        e_count = 2
                    
                    intensity = calculate_cue_intensity(e_count, punct_level, length_level)
                    
                    stimuli.append({
                        'id': f"STI_{stimulus_id:03d}",
                        'text': text,
                        'emoji_count': e_count,
                        'punctuation_type': punct_level,
                        'length_category': length_level,
                        'scenario_id': scenario['id'],
                        'cue_intensity': intensity
                    })
                    stimulus_id += 1
    
    return stimuli

def save_stimuli(stimuli: list, output_path: str):
    """Save the generated stimuli to a CSV file."""
    if not stimuli:
        logger.error("No stimuli to save.")
        return
    
    fieldnames = ['id', 'text', 'emoji_count', 'punctuation_type', 'length_category', 'scenario_id', 'cue_intensity']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)
    
    logger.info(f"Saved {len(stimuli)} stimuli to {output_path}")

def verify_stimuli(stimuli: list) -> bool:
    """
    Verify that all factorial combinations are unique and present.
    Expected count = Scenarios (4) * Emoji (3) * Punct (4) * Length (3) = 144
    """
    expected_count = len(SCENARIOS) * len(EMOJI_LEVELS) * len(PUNCTUATION_LEVELS) * len(LENGTH_LEVELS)
    if len(stimuli) != expected_count:
        logger.error(f"Stimuli count mismatch. Expected {expected_count}, got {len(stimuli)}")
        return False
    
    # Check uniqueness of (scenario, emoji, punct, length)
    combinations = set()
    for s in stimuli:
        key = (s['scenario_id'], s['emoji_count'], s['punctuation_type'], s['length_category'])
        if key in combinations:
            logger.error(f"Duplicate combination found: {key}")
            return False
        combinations.add(key)
    
    logger.info(f"Verification passed: {len(stimuli)} unique stimuli generated.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate factorial stimuli for tone analysis.")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument('--verify', action='store_true', help="Run verification checks after generation")
    args = parser.parse_args()

    # Ensure output directory exists
    raw_dir = get_raw_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / "stimuli.csv"

    logger.info(f"Generating stimuli with seed {args.seed}...")
    stimuli = generate_stimuli(args.seed)
    
    save_stimuli(stimuli, str(output_path))
    
    if args.verify:
        if verify_stimuli(stimuli):
            logger.info("Verification successful. Exiting with code 0.")
            return 0
        else:
            logger.error("Verification failed. Exiting with code 1.")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())