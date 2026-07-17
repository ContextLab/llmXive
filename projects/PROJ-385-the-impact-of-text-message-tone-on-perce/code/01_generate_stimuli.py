"""
Stimulus Generator for Text Tone Study (US1)

Generates a factorial design of text message stimuli varying by:
- Emoji Level (3 levels: None, Low, High)
- Punctuation (2 levels: Standard, Exaggerated)
- Length (2 levels: Short, Long)
- Context (2 levels: Friend, Acquaintance)

Total: 3 * 2 * 2 * 2 = 24 unique variants.
Outputs: data/raw/stimuli.csv
"""

import csv
import os
import random
from pathlib import Path
from typing import List, Dict, Any

# Project root resolution (assuming code/ is the root for imports, but data/ is sibling)
# We use relative paths from the script location to ensure portability
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure output directory exists
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Seed for reproducibility (using a fixed seed for the generator itself to ensure
# the 24 variants are deterministic, even if the order is shuffled)
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# --- Factor Definitions ---

EMOJI_LEVELS = ["none", "low", "high"]
PUNCTUATION_TYPES = ["standard", "exaggerated"]
LENGTH_TYPES = ["short", "long"]
CONTEXTS = ["friend", "acquaintance"]

# --- Content Templates ---

# Base message templates for each context
# {emoji_level} will be replaced by the actual emoji string
# {punct} will be replaced by the sentence terminator
# {length} logic is handled by appending filler or not

TEMPLATES = {
    "friend": {
        "short": "Hey, just wanted to check in on you{punct} {emoji}",
        "long": "Hey, just wanted to check in on you{punct} {emoji} Hope everything is going well with you and let me know if you need anything at all.",
        "filler": " Also, thinking about you."
    },
    "acquaintance": {
        "short": "Hi, just checking in on the project status{punct} {emoji}",
        "long": "Hi, just checking in on the project status{punct} {emoji} I wanted to ensure we are on track for the deadline. Please update me when you can.",
        "filler": " Looking forward to your response."
    }
}

EMOJI_MAP = {
    "none": "",
    "low": " 🙂",
    "high": " 🙂👍✨"
}

PUNCT_MAP = {
    "standard": ".",
    "exaggerated": "!!!"
}

def generate_message(context: str, length: str, emoji_level: str, punct_type: str) -> str:
    """
    Constructs a single message string based on the factorial parameters.
    """
    template_data = TEMPLATES[context][length]
    
    # Determine emoji string
    emoji_str = EMOJI_MAP[emoji_level]
    
    # Determine punctuation
    punct_str = PUNCT_MAP[punct_type]

    # Format the base template
    # Note: The template string contains {emoji} and {punct} placeholders
    # We need to be careful with the curly braces in the template if they are part of the text,
    # but here they are our format keys.
    
    # For "long" variants, we might want to ensure the filler is included if the template logic was split,
    # but our templates above already include the full text for "long".
    
    # However, the template above for "long" already has the full text.
    # Let's just format.
    message = template_data.format(emoji=emoji_str, punct=punct_str)
    
    return message

def generate_stimuli() -> List[Dict[str, Any]]:
    """
    Generates the full factorial design of 24 stimuli.
    """
    stimuli = []
    
    # Iterate through all combinations
    for context in CONTEXTS:
        for length in LENGTH_TYPES:
            for punct in PUNCTUATION_TYPES:
                for emoji in EMOJI_LEVELS:
                    text = generate_message(context, length, emoji, punct)
                    
                    # Create a unique ID based on the factors
                    # Format: C{context[0]}_L{length[0]}_P{punct[0]}_E{emoji[0]}
                    # Context: f (friend), a (acquaintance)
                    # Length: s (short), l (long)
                    # Punct: s (standard), e (exaggerated)
                    # Emoji: n (none), l (low), h (high)
                    
                    ctx_code = context[0].upper()
                    len_code = length[0].upper()
                    punct_code = punct[0].upper()
                    emoji_code = emoji[0].upper()
                    
                    stimulus_id = f"S_{ctx_code}{len_code}{punct_code}{emoji_code}"
                    
                    stimuli.append({
                        "stimulus_id": stimulus_id,
                        "context": context,
                        "length": length,
                        "punctuation": punct,
                        "emoji_level": emoji,
                        "text": text
                    })
    
    return stimuli

def save_stimuli(stimuli: List[Dict[str, Any]], output_path: Path):
    """
    Saves the stimuli to a CSV file.
    """
    if not stimuli:
        raise ValueError("No stimuli generated to save.")
    
    fieldnames = ["stimulus_id", "context", "length", "punctuation", "emoji_level", "text"]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)

def main():
    """
    Entry point for the stimulus generation script.
    """
    print(f"Generating stimuli for project: {PROJECT_ROOT}")
    
    stimuli = generate_stimuli()
    
    output_file = DATA_RAW_DIR / "stimuli.csv"
    save_stimuli(stimuli, output_file)
    
    print(f"Successfully generated {len(stimuli)} unique stimuli.")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()