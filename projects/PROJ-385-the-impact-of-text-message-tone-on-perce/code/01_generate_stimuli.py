"""
Stimulus Generation Module for Text Tone Analysis.
Generates a factorial set of text message stimuli based on defined scenarios and linguistic cues.
"""
import csv
import os
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import config utilities to ensure path consistency
try:
    from config import get_raw_data_dir, get_project_root
except ImportError:
    # Fallback if running as script directly in code/ or root
    from pathlib import Path
    import sys
    # Attempt to add parent to path if needed
    if 'code' in str(Path.cwd()):
        sys.path.insert(0, str(Path.cwd().parent))
    else:
        sys.path.insert(0, str(Path.cwd()))
    from config import get_project_root, get_raw_data_dir


# --- Constants and Configuration ---
RANDOM_SEED = 42
TOTAL_STIMULI_TARGET = 40

# Base Scenarios (Context for the message)
SCENARIOS = [
    "Support after a bad day",
    "Congratulating on a success",
    "Apologizing for a mistake",
    "Checking in on a friend",
    "Offering help with a task",
    "Expressing gratitude for support",
    "Inviting to a casual gathering",
    "Sharing good news"
]

# Linguistic Cue Levels
EMOJI_LEVELS = [0, 1, 2, 3]  # Count of emojis
PUNCTUATION_LEVELS = [
    "standard",      # Single period or none
    "exclamation",   # Exclamation mark(s)
    "multiple_excl", # Multiple exclamation marks
    "ellipsis"       # Ellipsis (...)
]
LENGTH_CATEGORIES = [
    "short",         # < 20 chars
    "medium",        # 20-50 chars
    "long"           # > 50 chars
]

# Template parts for generating text
# Format: {scenario} + {cue_modifier}
BASE_TEMPLATES = {
    "Support after a bad day": [
        "I'm so sorry you had a rough day.",
        "That sounds really tough, I'm here for you.",
        "Sending you a big hug, things will get better.",
        "I know today was hard. Take your time."
    ],
    "Congratulating on a success": [
        "Huge congrats on the new job!",
        "You absolutely crushed it today!",
        "So proud of your achievement!",
        "Amazing news! You worked so hard for this."
    ],
    "Apologizing for a mistake": [
        "I'm really sorry for what I said.",
        "I messed up, please forgive me.",
        "I didn't mean to hurt your feelings.",
        "My bad, I'll make it up to you."
    ],
    "Checking in on a friend": [
        "Hey, just thinking of you.",
        "How have you been lately?",
        "Miss you! We should catch up soon.",
        "Just wanted to say hi and see how you are."
    ],
    "Offering help with a task": [
        "Let me know if you need a hand with that.",
        "I can help you move this weekend if you want.",
        "Need any help with the project? I'm free.",
        "Happy to lend a hand whenever you need it."
    ],
    "Expressing gratitude for support": [
        "Thanks so much for listening to me.",
        "I really appreciate your help today.",
        "You're the best, thank you for being there.",
        "Your support means the world to me."
    ],
    "Inviting to a casual gathering": [
        "We're having a small get-together tonight.",
        "You should come over for coffee sometime.",
        "Thinking of grabbing dinner later, want to join?",
        "Some of us are hanging out, come by if you're free."
    ],
    "Sharing good news": [
        "I finally got the promotion!",
        "Guess what? I passed the exam!",
        "Just got some amazing news I wanted to share.",
        "You won't believe what happened today!"
    ]
}

# Emoji Sets per context (to ensure relevance)
EMOJI_MAP = {
    "Support after a bad day": ["🥺", "🤗", "💔", "☁️"],
    "Congratulating on a success": ["🎉", "👏", "🏆", "✨"],
    "Apologizing for a mistake": ["😔", "🙏", "😞", "💔"],
    "Checking in on a friend": ["👋", "😊", "💬", "❤️"],
    "Offering help with a task": ["🤝", "💪", "🛠️", "📦"],
    "Expressing gratitude for support": ["🙏", "❤️", "🌟", "🙌"],
    "Inviting to a casual gathering": ["🍕", "☕", "🎈", "🏠"],
    "Sharing good news": ["🎉", "🥳", "✨", "🚀"]
}

def count_emojis(text: str) -> int:
    """Count the number of emoji characters in a string."""
    # Simple heuristic: count characters in common emoji ranges or specific set
    # For this simulation, we will explicitly insert emojis and count them.
    return text.count('😀') + text.count('😢') + text.count('🎉') + text.count('🤝') + \
           text.count('🥺') + text.count('🤗') + text.count('💔') + text.count('☁️') + \
           text.count('👏') + text.count('🏆') + text.count('✨') + text.count('🙏') + \
           text.count('😞') + text.count('👋') + text.count('😊') + text.count('💬') + \
           text.count('❤️') + text.count('💪') + text.count('🛠️') + text.count('📦') + \
           text.count('🌟') + text.count('🙌') + text.count('🍕') + text.count('☕') + \
           text.count('🎈') + text.count('🏠') + text.count('🥳') + text.count('🚀')

def get_punctuation_marker(punct_type: str) -> str:
    """Return the punctuation string based on the type."""
    mapping = {
        "standard": "",
        "exclamation": "!",
        "multiple_excl": "!!!",
        "ellipsis": "..."
    }
    return mapping.get(punct_type, "")

def categorize_length(text: str) -> str:
    """Categorize text length."""
    length = len(text)
    if length < 20:
        return "short"
    elif length <= 50:
        return "medium"
    else:
        return "long"

def generate_message(scenario: str, emoji_count: int, punct_type: str) -> str:
    """
    Generate a single stimulus message based on scenario and cue levels.
    """
    # Select a base template for the scenario
    templates = BASE_TEMPLATES.get(scenario, ["Hello there."])
    base_text = random.choice(templates)

    # Add punctuation
    punct = get_punctuation_marker(punct_type)
    if base_text and base_text[-1] not in ['.', '!', '?', ',']:
        # Ensure it ends with something if not already
        if punct:
            base_text += punct
        else:
            base_text += "."
    elif punct:
        # Replace existing end punctuation if we want to force specific punctuation
        # For simplicity, just append or replace if it's a period
        if base_text.endswith('.'):
            base_text = base_text[:-1] + punct
        else:
            base_text += punct

    # Add emojis
    emojis = []
    available_emojis = EMOJI_MAP.get(scenario, ["😀"])
    for _ in range(emoji_count):
        emojis.append(random.choice(available_emojis))
    
    emoji_str = "".join(emojis)
    
    # Construct final text: Text + Emojis (common pattern)
    final_text = base_text + emoji_str
    
    # If we need to adjust length category, we might need to pad or trim, 
    # but for a factorial design, we accept the natural length resulting from the cues.
    # However, the task asks for 'length_category' as a column, which we will compute.
    
    return final_text

def generate_stimuli(seed: int = RANDOM_SEED, target_count: int = TOTAL_STIMULI_TARGET) -> List[Dict[str, Any]]:
    """
    Generate a factorial set of stimuli.
    To reach exactly 40 stimuli, we will iterate through scenarios and cue combinations
    and select a subset that ensures coverage of the main factors.
    
    Factors:
    - Scenario: 8 levels
    - Emoji: 4 levels
    - Punctuation: 4 levels
    Total combinations: 8 * 4 * 4 = 128.
    We need to select 40 unique combinations.
    
    Strategy:
    We will create a balanced subset by iterating through scenarios and picking
    specific combinations of cues to ensure 5 stimuli per scenario (8 * 5 = 40).
    """
    random.seed(seed)
    stimuli = []
    stimulus_id = 1

    # We need 40 total. 8 scenarios. 40 / 8 = 5 stimuli per scenario.
    stimuli_per_scenario = 5

    for scenario in SCENARIOS:
        # Generate 5 unique combinations for this scenario
        combinations = []
        while len(combinations) < stimuli_per_scenario:
            emoji_count = random.choice(EMOJI_LEVELS)
            punct_type = random.choice(PUNCTUATION_LEVELS)
            
            combo = (emoji_count, punct_type)
            if combo not in combinations:
                combinations.append(combo)
        
        for emoji_count, punct_type in combinations:
            text = generate_message(scenario, emoji_count, punct_type)
            length_cat = categorize_length(text)
            
            stimuli.append({
                "id": f"S{stimulus_id:03d}",
                "text": text,
                "emoji_count": emoji_count,
                "punctuation_type": punct_type,
                "length_category": length_cat,
                "scenario_id": scenario
            })
            stimulus_id += 1

    return stimuli

def save_stimuli(stimuli: List[Dict[str, Any]], output_path: str) -> None:
    """Save stimuli to a CSV file."""
    if not stimuli:
        raise ValueError("No stimuli to save.")
    
    fieldnames = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"]
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)

def verify_stimuli(stimuli: List[Dict[str, Any]], expected_count: int = TOTAL_STIMULI_TARGET) -> bool:
    """Verify that the generated stimuli meet the requirements."""
    if len(stimuli) != expected_count:
        print(f"ERROR: Expected {expected_count} stimuli, got {len(stimuli)}")
        return False
    
    # Check for unique IDs
    ids = [s["id"] for s in stimuli]
    if len(ids) != len(set(ids)):
        print("ERROR: Duplicate stimulus IDs found.")
        return False
    
    # Check required columns
    required_cols = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"]
    if not all(col in stimuli[0].keys() for col in required_cols):
        print("ERROR: Missing required columns in stimulus data.")
        return False
    
    print(f"Verification passed: {len(stimuli)} unique stimuli generated.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate text message stimuli for tone analysis.")
    parser.add_argument('--seed', type=int, default=RANDOM_SEED, help="Random seed for reproducibility")
    parser.add_argument('--count', type=int, default=TOTAL_STIMULI_TARGET, help="Target number of stimuli")
    parser.add_argument('--verify', action='store_true', help="Run verification checks after generation")
    parser.add_argument('--output', type=str, default=None, help="Output file path (optional)")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Use config to get standard path
        try:
            raw_data_dir = get_raw_data_dir()
            output_path = str(Path(raw_data_dir) / "stimuli.csv")
        except Exception:
            # Fallback if config fails
            output_path = "data/raw/stimuli.csv"
    
    print(f"Generating {args.count} stimuli with seed {args.seed}...")
    stimuli = generate_stimuli(seed=args.seed, target_count=args.count)
    
    save_stimuli(stimuli, output_path)
    print(f"Saved stimuli to {output_path}")
    
    if args.verify:
        if verify_stimuli(stimuli, args.count):
            print("Verification successful.")
        else:
            print("Verification failed.")
            exit(1)

if __name__ == "__main__":
    main()