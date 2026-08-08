"""
Stimulus Generator for Text Message Tone Research.

Generates a factorial design of text message stimuli varying in:
- Relationship type (Partner, Friend, Colleague, Family)
- Cue type (Emoji, Punctuation, Both)
- Intensity (Low, Medium, High)

Output: data/raw/stimuli.csv
"""
import csv
import os
import random
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re
import json

# Import project config
from config import get_raw_data_dir, get_project_root, get_data_dir
from logging_config import setup_logging, get_logger

# Constants
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Setup logging
logger = get_logger(__name__)

# Templates for stimuli generation
RELATIONSHIPS = ["Partner", "Friend", "Colleague", "Family"]
CUE_TYPES = ["Emoji", "Punctuation", "Both"]
INTENSITIES = ["Low", "Medium", "High"]

# Base message templates per relationship
MESSAGE_TEMPLATES = {
    "Partner": [
        "I'm running a bit late, {cue}",
        "Can we meet at the usual spot? {cue}",
        "I missed you today, {cue}",
        "Let's watch a movie tonight, {cue}",
        "Thanks for being there for me, {cue}"
    ],
    "Friend": [
        "Hey, what's up? {cue}",
        "Are we still on for later? {cue}",
        "That was so funny, {cue}",
        "Need a hand with anything? {cue}",
        "Long time no see, {cue}"
    ],
    "Colleague": [
        "Could you send me the file? {cue}",
        "Meeting is at 3pm, {cue}",
        "Great work on the presentation, {cue}",
        "Let's sync up tomorrow, {cue}",
        "Thanks for the quick reply, {cue}"
    ],
    "Family": [
        "Call me when you can, {cue}",
        "Love you all, {cue}",
        "Dinner is ready, {cue}",
        "How was your day? {cue}",
        "See you this weekend, {cue}"
    ]
}

# Cue replacements
EMOJIS = {
    "Low": ["🙂"],
    "Medium": ["😊", "😄"],
    "High": ["😍", "🥰", "❤️"]
}

PUNCTUATION = {
    "Low": [".", " "],
    "Medium": ["!.", "!!"],
    "High": ["!!!", "?!"]
}

def count_emojis(text: str) -> int:
    """Count the number of emojis in a text string."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return len(emoji_pattern.findall(text))

def get_punctuation_marker(text: str) -> str:
    """Identify the type of punctuation used in the text."""
    if "!!!" in text or "?!?" in text:
        return "High"
    elif "!!" in text or "??" in text or "!!." in text:
        return "Medium"
    elif "!" in text or "?" in text:
        return "Low"
    elif "." in text:
        return "Minimal"
    return "None"

def categorize_length(text: str) -> str:
    """Categorize text length into Short, Medium, or Long."""
    length = len(text)
    if length < 30:
        return "Short"
    elif length < 60:
        return "Medium"
    else:
        return "Long"

def generate_message(template: str, cue_type: str, intensity: str) -> str:
    """Generate a message by applying the specified cue and intensity to a template."""
    if cue_type == "Emoji" or cue_type == "Both":
        emoji = random.choice(EMOJIS[intensity])
        # Replace {cue} with emoji
        if "{cue}" in template:
            message = template.replace("{cue}", emoji)
        else:
            message = template + " " + emoji
    else:
        punct = random.choice(PUNCTUATION[intensity])
        # Replace {cue} with punctuation or append
        if "{cue}" in template:
            message = template.replace("{cue}", punct)
        else:
            message = template.rstrip(".") + punct
    
    # Clean up double spaces or punctuation
    message = re.sub(r'\s+', ' ', message)
    message = re.sub(r'([.,!?])\s*([.,!?])', r'\1', message)
    
    return message

def generate_stimuli() -> List[Dict[str, Any]]:
    """Generate the full factorial design of stimuli."""
    stimuli = []
    stimulus_id = 1
    
    for relationship in RELATIONSHIPS:
        for cue_type in CUE_TYPES:
            for intensity in INTENSITIES:
                templates = MESSAGE_TEMPLATES[relationship]
                template = random.choice(templates)
                
                text = generate_message(template, cue_type, intensity)
                
                emoji_count = count_emojis(text)
                punctuation_marker = get_punctuation_marker(text)
                length_category = categorize_length(text)
                
                # Create scenario ID for factorial tracking
                scenario_id = f"{relationship}_{cue_type}_{intensity}_{stimulus_id}"
                
                # Calculate cue intensity score (normalized 0-1)
                # Based on the number of cues and their intensity
                cue_score = 0.0
                if cue_type in ["Emoji", "Both"]:
                    cue_score += (intensity == "High") * 0.4 + (intensity == "Medium") * 0.3 + (intensity == "Low") * 0.2
                if cue_type in ["Punctuation", "Both"]:
                    cue_score += (intensity == "High") * 0.4 + (intensity == "Medium") * 0.3 + (intensity == "Low") * 0.2
                
                # Normalize to 0-1 range
                cue_intensity = min(1.0, cue_score)
                
                stimuli.append({
                    "id": f"STI_{stimulus_id:04d}",
                    "text": text,
                    "emoji_count": emoji_count,
                    "punctuation_type": punctuation_marker,
                    "length_category": length_category,
                    "scenario_id": scenario_id,
                    "cue_intensity": round(cue_intensity, 2)
                })
                
                stimulus_id += 1
    
    return stimuli

def save_stimuli(stimuli: List[Dict[str, Any]], output_path: Path = None) -> Path:
    """Save stimuli to CSV file."""
    if output_path is None:
        output_path = get_raw_data_dir() / "stimuli.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["id", "text", "emoji_count", "punctuation_type", 
                 "length_category", "scenario_id", "cue_intensity"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)
    
    logger.info(f"Saved {len(stimuli)} stimuli to {output_path}")
    return output_path

def verify_stimuli(stimuli: List[Dict[str, Any]]) -> bool:
    """Verify that stimuli contain all 12 factorial combinations."""
    combinations = set()
    for s in stimuli:
        parts = s["scenario_id"].split("_")
        if len(parts) >= 4:
            rel = parts[0]
            cue = parts[1]
            intensity = parts[2]
            combinations.add((rel, cue, intensity))
    
    expected = set()
    for r in RELATIONSHIPS:
        for c in CUE_TYPES:
            for i in INTENSITIES:
                expected.add((r, c, i))
    
    if combinations != expected:
        logger.error(f"Missing combinations: {expected - combinations}")
        return False
    
    logger.info("All 12 factorial combinations verified")
    return True

def main():
    """Main entry point for stimulus generation."""
    parser = argparse.ArgumentParser(description="Generate factorial stimuli for tone research")
    parser.add_argument("--verify", action="store_true", help="Verify factorial combinations after generation")
    args = parser.parse_args()
    
    setup_logging()
    
    logger.info("Starting stimulus generation...")
    
    stimuli = generate_stimuli()
    output_path = save_stimuli(stimuli)
    
    if args.verify:
        if verify_stimuli(stimuli):
            logger.info("Verification passed")
        else:
            logger.error("Verification failed")
            sys.exit(1)
    else:
        logger.info(f"Generated {len(stimuli)} stimuli")

if __name__ == "__main__":
    main()
