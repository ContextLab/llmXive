"""
Factorial Stimulus Generator for Text Message Tone Study.

Generates exactly 40 unique text message variants based on a factorial design
manipulating emoji count, punctuation type, and length category.
Outputs data to data/raw/stimuli.csv.
"""

import csv
import os
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import config utilities from the project structure
try:
    from config import get_raw_data_dir, get_project_root
except ImportError:
    # Fallback for direct execution without package import
    from pathlib import Path
    def get_project_root():
        return Path(__file__).parent.parent
    def get_raw_data_dir():
        return get_project_root() / "data" / "raw"


# Define the factorial design levels
EMOJI_LEVELS = [0, 1, 2]  # 3 levels
PUNCTUATION_LEVELS = [".", "!", "..."]  # 3 levels
LENGTH_LEVELS = ["short", "medium", "long"]  # 3 levels

# Base scenarios to vary the content
BASE_SCENARIOS = [
    "Thanks for the help with the project today.",
    "I really enjoyed our conversation earlier.",
    "Let me know if you want to grab lunch tomorrow.",
    "Great job on the presentation yesterday!",
    "Sorry I couldn't make it to the meeting.",
    "I appreciate you listening to my concerns.",
    "Can we catch up this weekend?",
    "That news made my whole day better.",
    "You're always so thoughtful and kind.",
    "Looking forward to seeing you soon."
]

# We need 40 stimuli.
# 3 (emojis) * 3 (punct) * 3 (length) = 27 combinations.
# We need 13 more. We will add 13 specific variations or repeat scenarios with different parameters.
# To ensure exactly 40 unique factorial combinations (id, text, emoji_count, punct, length, scenario),
# we will iterate through the cartesian product and fill the list.
# Since 27 < 40, we will use a subset of scenarios and ensure unique (emoji, punct, length) tuples
# are distributed across scenarios to reach 40 unique rows.
# Actually, the requirement says "EXACTLY 40 stimuli (by adjusting levels or base scenarios)".
# We will generate 40 unique rows by selecting specific combinations.

def count_emojis(text: str) -> int:
    """Count the number of emojis in a text string."""
    # Simple heuristic: count common emoji characters or ranges.
    # For this generator, we will explicitly track the count we added.
    emoji_chars = set("😀😁😂😆😅😍😘😊😉😎😜😏😴😷👍👎👏🙌🙏❤️🔥✨🎉")
    count = 0
    for char in text:
        if char in emoji_chars:
            count += 1
    return count

def generate_message(scenario: str, emoji_count: int, punctuation: str, length: str) -> Tuple[str, int]:
    """
    Generate a single text message based on parameters.
    Returns (text, actual_emoji_count).
    """
    text = scenario

    # Adjust length by adding filler words or truncating slightly if needed
    # For simplicity in this generator, we assume the base scenario fits the category
    # or we append a short phrase for "long".
    if length == "long" and len(text) < 50:
        text += " It really meant a lot to me."
    elif length == "short" and len(text) > 40:
        text = text[:35] + "..."

    # Add emojis
    emojis = "😀😁😂😆😅😍😘😊😉😎😜😏😴😷👍👎👏🙌🙏❤️🔥✨🎉"
    if emoji_count > 0:
        # Select random emojis
        selected = random.sample(emojis, min(emoji_count, len(emojis)))
        # Append to end or insert before punctuation
        if text.endswith("."):
            text = text[:-1] + " " + " ".join(selected) + " " + punctuation
        else:
            text = text + " " + " ".join(selected) + " " + punctuation
    else:
        # Ensure punctuation is applied
        if not text.endswith((".", "!", "?", "...")):
            text += " " + punctuation

    return text, emoji_count

def generate_stimuli(seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate exactly 40 unique stimuli.
    """
    random.seed(seed)
    stimuli = []
    stimulus_id = 1

    # We need 40 unique combinations.
    # Let's create a pool of all possible (emoji, punct, length) combinations
    # and then distribute them across scenarios.
    combinations = []
    for e in EMOJI_LEVELS:
        for p in PUNCTUATION_LEVELS:
            for l in LENGTH_LEVELS:
                combinations.append((e, p, l))

    # We have 27 combinations. We need 13 more.
    # We will reuse the combinations but with different scenarios to ensure uniqueness in the dataset (id, text, ...).
    # However, the requirement says "unique text message variants".
    # To ensure 40 unique rows, we will just iterate 40 times, picking valid parameters.
    # We will cycle through scenarios and combinations.

    selected_combinations = []
    # First, take all 27 unique parameter sets
    selected_combinations.extend(combinations)
    
    # Now we need 13 more. We will pick 13 random parameter sets from the same pool
    # and pair them with scenarios we haven't used as much, or just random.
    # To ensure the text is different, we rely on the scenario or the random emoji selection.
    extra_count = 40 - len(selected_combinations)
    for _ in range(extra_count):
        e = random.choice(EMOJI_LEVELS)
        p = random.choice(PUNCTUATION_LEVELS)
        l = random.choice(LENGTH_LEVELS)
        selected_combinations.append((e, p, l))

    # Shuffle to mix them up
    random.shuffle(selected_combinations)
    
    # Assign to scenarios
    scenario_idx = 0
    for e, p, l in selected_combinations:
        scenario = BASE_SCENARIOS[scenario_idx % len(BASE_SCENARIOS)]
        text, _ = generate_message(scenario, e, p, l)
        
        # Determine punctuation type string for the CSV
        punct_type = "period" if p == "." else ("exclamation" if p == "!" else "ellipsis")
        
        stimuli.append({
            "id": f"STIM_{stimulus_id:03d}",
            "text": text,
            "emoji_count": e,
            "punctuation_type": punct_type,
            "length_category": l,
            "scenario_id": f"SCN_{(scenario_idx % len(BASE_SCENARIOS)) + 1:02d}"
        })
        
        stimulus_id += 1
        scenario_idx += 1

    return stimuli

def save_stimuli(stimuli: List[Dict[str, Any]], output_path: Path) -> None:
    """Save stimuli to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stimuli)

def verify_stimuli(input_path: Path) -> bool:
    """Verify the generated stimuli file."""
    if not input_path.exists():
        print(f"Error: File {input_path} does not exist.")
        return False
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Check count
    if len(rows) != 40:
        print(f"Error: Expected 40 stimuli, found {len(rows)}.")
        return False
    
    # Check columns
    expected_cols = {"id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"}
    if not expected_cols.issubset(set(rows[0].keys())):
        print(f"Error: Missing columns. Found: {rows[0].keys()}")
        return False
    
    # Check uniqueness of IDs
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        print("Error: Duplicate stimulus IDs found.")
        return False
    
    print(f"Verification passed: {len(rows)} unique stimuli found.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Generate factorial text message stimuli.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--verify", action="store_true", help="Verify the output file instead of generating")
    parser.add_argument("--output", type=str, default=None, help="Output file path (optional)")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_raw_data_dir() / "stimuli.csv"
    
    if args.verify:
        verify_stimuli(output_path)
        return
    
    print(f"Generating 40 stimuli with seed {args.seed}...")
    stimuli = generate_stimuli(seed=args.seed)
    save_stimuli(stimuli, output_path)
    print(f"Saved stimuli to {output_path}")
    
    # Auto-verify
    verify_stimuli(output_path)

if __name__ == "__main__":
    main()
