"""
Factorial Stimulus Generator for Text Message Tone Study.

Generates a controlled set of text message variants based on:
- Scenario (Base message context)
- Emoji Count (0, 1, 2)
- Punctuation Type (None, Exclamation, Ellipsis, Question)
- Length Category (Short, Medium, Long)

Output: data/raw/stimuli.csv
"""

import csv
import os
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import config for paths
try:
    from config import get_project_root, get_raw_data_dir
except ImportError:
    # Fallback for direct execution without package import
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_raw_data_dir


# --- Configuration Constants ---

# Base scenarios representing different emotional support contexts
BASE_SCENARIOS = [
    {
        "id": "scenario_01",
        "template": "I had a really rough day at work today.",
        "context": "Work stress"
    },
    {
        "id": "scenario_02",
        "template": "I just got some news about my project.",
        "context": "Project update"
    },
    {
        "id": "scenario_03",
        "template": "I'm feeling a bit overwhelmed with everything going on.",
        "context": "General stress"
    },
    {
        "id": "scenario_04",
        "template": "I found a solution to the problem we discussed.",
        "context": "Problem solving"
    },
    {
        "id": "scenario_05",
        "template": "I'm not sure how to handle this situation with my family.",
        "context": "Family issue"
    }
]

# Emoji options to inject
EMOJI_SETS = {
    0: [],
    1: ["🙂", "👍", "❤️", "😔", "😢", "🎉", "🤔", "💪"],
    2: ["🙂👍", "❤️😔", "😢🤔", "🎉💪", "👍🙂", "❤️❤️", "😔😢", "🤔👍"]
}

# Punctuation types
PUNCTUATION_TYPES = {
    "none": "",
    "exclamation": "!",
    "ellipsis": "...",
    "question": "?"
}

# Length modifiers
LENGTH_MODIFIERS = {
    "short": "",
    "medium": " It's been tough.",
    "long": " I've been trying to stay positive, but it's really hard right now."
}

# Random seed for reproducibility
RANDOM_SEED = 42


def count_emojis(text: str) -> int:
    """
    Count the number of emoji characters in a string.
    Simple heuristic: counts characters in the common emoji range.
    """
    # Basic count of known emoji characters used in this generator
    count = 0
    for char in text:
        # Check if char is in our known emoji sets
        for emoji_list in EMOJI_SETS.values():
            if char in emoji_list:
                count += 1
                break
        # Also check for common emoji unicode ranges if needed
        # For this generator, we strictly use the predefined sets
    return count


def generate_message(
    scenario_id: str,
    base_text: str,
    emoji_count: int,
    punctuation_type: str,
    length_category: str
) -> str:
    """
    Construct a single stimulus message by combining scenario, length, emojis, and punctuation.
    """
    # Apply length modifier
    text = base_text + LENGTH_MODIFIERS[length_category]

    # Append punctuation
    punct = PUNCTUATION_TYPES[punctuation_type]
    if punct:
        # If punctuation is question mark or exclamation, ensure it's at the end
        # If ellipsis, ensure it's at the end
        text = text.rstrip() + punct

    # Insert emojis
    # Strategy: Append emojis at the end for consistency in this study design
    if emoji_count > 0:
        emojis = EMOJI_SETS[emoji_count]
        # Select a specific pair/single based on a hash of the scenario and parameters
        # to ensure deterministic generation for the same factorial combination
        # but varied across combinations.
        # Since we are iterating all combinations, we just pick one deterministically.
        # We'll use the index of the emoji set to pick one if multiple exist, 
        # but our sets are lists. Let's pick the first one for simplicity 
        # or cycle through if we had more scenarios.
        # To ensure variety, we pick based on the hash of the scenario id.
        emoji_str = emojis[0] # Simplified: pick first available for this count
        
        # Better: pick based on scenario index to vary across scenarios
        scenario_idx = int(scenario_id.split('_')[1])
        emoji_str = emojis[scenario_idx % len(emojis)]
        
        text = text + " " + emoji_str

    return text


def generate_stimuli(seed: int = RANDOM_SEED) -> List[Dict[str, Any]]:
    """
    Generate all factorial combinations of stimuli.
    
    Factors:
    - Scenarios: 5
    - Emoji Counts: 3 (0, 1, 2)
    - Punctuation Types: 4 (none, exclamation, ellipsis, question)
    - Length Categories: 3 (short, medium, long)
    
    Total: 5 * 3 * 4 * 3 = 180 stimuli
    """
    random.seed(seed)
    stimuli = []
    
    scenario_ids = [s["id"] for s in BASE_SCENARIOS]
    emoji_counts = [0, 1, 2]
    punctuation_types = list(PUNCTUATION_TYPES.keys())
    length_categories = list(LENGTH_MODIFIERS.keys())
    
    stimulus_id_counter = 1
    
    for scenario in BASE_SCENARIOS:
        for emoji_count in emoji_counts:
            for punct_type in punctuation_types:
                for length_cat in length_categories:
                    text = generate_message(
                        scenario_id=scenario["id"],
                        base_text=scenario["template"],
                        emoji_count=emoji_count,
                        punctuation_type=punct_type,
                        length_category=length_cat
                    )
                    
                    stimuli.append({
                        "id": f"stim_{stimulus_id_counter:04d}",
                        "text": text,
                        "emoji_count": emoji_count,
                        "punctuation_type": punct_type,
                        "length_category": length_cat,
                        "scenario_id": scenario["id"]
                    })
                    stimulus_id_counter += 1
                    
    return stimuli


def save_stimuli(stimuli: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save stimuli to a CSV file.
    """
    if not stimuli:
        raise ValueError("No stimuli to save.")
        
    fieldnames = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"]
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)


def verify_stimuli(stimuli: List[Dict[str, Any]]) -> bool:
    """
    Verify that all factorial combinations are present and unique.
    """
    if not stimuli:
        return False
        
    seen_ids = set()
    seen_combinations = set()
    
    required_combinations = (
        len(BASE_SCENARIOS) * 
        len([0, 1, 2]) * 
        len(PUNCTUATION_TYPES) * 
        len(LENGTH_MODIFIERS)
    )
    
    for s in stimuli:
        # Check uniqueness of ID
        if s["id"] in seen_ids:
            print(f"Error: Duplicate ID {s['id']}")
            return False
        seen_ids.add(s["id"])
        
        # Check uniqueness of combination
        combo = (
            s["scenario_id"], 
            s["emoji_count"], 
            s["punctuation_type"], 
            s["length_category"]
        )
        if combo in seen_combinations:
            print(f"Error: Duplicate combination {combo}")
            return False
        seen_combinations.add(combo)
        
        # Validate counts
        if s["emoji_count"] != count_emojis(s["text"]):
            print(f"Error: Emoji count mismatch for {s['id']}: {s['emoji_count']} vs {count_emojis(s['text'])}")
            return False
            
    if len(stimuli) != required_combinations:
        print(f"Error: Expected {required_combinations} stimuli, got {len(stimuli)}")
        return False
        
    print(f"Verification passed: {len(stimuli)} unique stimuli generated.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate factorial stimuli for text message tone study.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility.")
    parser.add_argument("--verify", action="store_true", help="Run verification checks after generation.")
    parser.add_argument("--output", type=str, default=None, help="Output file path (default: data/raw/stimuli.csv).")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        raw_data_dir = get_raw_data_dir()
        output_path = str(raw_data_dir / "stimuli.csv")
        
    print(f"Generating stimuli with seed {args.seed}...")
    stimuli = generate_stimuli(seed=args.seed)
    
    print(f"Saving {len(stimuli)} stimuli to {output_path}...")
    save_stimuli(stimuli, output_path)
    
    if args.verify:
        print("Verifying stimuli...")
        if verify_stimuli(stimuli):
            print("Verification successful.")
        else:
            print("Verification failed.")
            exit(1)
    else:
        print("Generation complete. Use --verify to check integrity.")


if __name__ == "__main__":
    main()
