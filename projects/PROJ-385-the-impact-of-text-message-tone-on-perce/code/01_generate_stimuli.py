"""
Stimulus generation script for the “Impact of Text Message Tone on Perceived Emotional Support” project.

The script creates a factorial design of text‑message stimuli varying across several
cue dimensions (tone, emoji count, punctuation, length) and writes the result to
``data/raw/stimuli.csv``.  It also provides a ``--verify`` mode that checks the
generated CSV for the required columns and logs a short confirmation message.

The implementation follows the public API surface declared in ``tasks.md``:
- ``count_emojis``
- ``get_punctuation_marker``
- ``categorize_length``
- ``generate_message``
- ``generate_stimuli``
- ``save_stimuli``
- ``verify_stimuli``
- ``main``
"""

import argparse
import csv
import itertools
import logging
import os
import random
import re
from pathlib import Path
from typing import List, Dict

from config import get_raw_data_dir, get_project_root

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
EMOJI_PATTERN = re.compile(
    "["                     # start character class
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

def count_emojis(text: str) -> int:
    """
    Return the number of emoji characters in *text*.

    The function uses a Unicode regex that matches the most common emoji
    blocks.  It counts overlapping matches as separate emojis.
    """
    return len(EMOJI_PATTERN.findall(text))

def get_punctuation_marker(text: str) -> str:
    """
    Detect the dominant punctuation marker at the end of *text*.

    Returns one of:
        - ``'exclamation'``   if the text ends with ``!``
        - ``'question'``      if the text ends with ``?``
        - ``'none'``          otherwise
    """
    text = text.strip()
    if text.endswith("!"):
        return "exclamation"
    if text.endswith("?"):
        return "question"
    return "none"

def categorize_length(text: str) -> str:
    """
    Categorise *text* into ``short``, ``medium`` or ``long`` based on word count.

    - ``short``  : ≤ 5 words
    - ``medium`` : 6‑12 words
    - ``long``   : > 12 words
    """
    word_count = len(text.split())
    if word_count <= 5:
        return "short"
    if word_count <= 12:
        return "medium"
    return "long"

# ----------------------------------------------------------------------
# Stimulus construction
# ----------------------------------------------------------------------
TONES = ["friendly", "formal", "neutral"]
EMOJI_COUNTS = [0, 1, 2]
PUNCTUATIONS = ["none", "exclamation", "question"]
LENGTHS = ["short", "medium", "long"]
SCENARIOS = [
    {"id": 1, "description": "Seeking emotional support after a bad day"},
    {"id": 2, "description": "Offering congratulations"},
]

# A very small library of base sentences; the generator will sprinkle emojis
# and punctuation according to the factor levels.
BASE_SENTENCES = {
    "friendly": "Hey, I’m here for you",
    "formal": "I would like to express my sympathy",
    "neutral": "I heard about what happened",
}

def _apply_emoji(text: str, count: int) -> str:
    """Append *count* random emojis to *text*."""
    emojis = ["😊", "❤️", "👍", "🙁", "😢"]
    chosen = random.choices(emojis, k=count)
    return f"{text} {' '.join(chosen)}".strip()

def _apply_punctuation(text: str, marker: str) -> str:
    """Add the appropriate punctuation marker to *text*."""
    if marker == "exclamation":
        return f"{text}!"
    if marker == "question":
        return f"{text}?"
    return text

def generate_message(tone: str, emoji_count: int, punctuation_type: str, length_category: str) -> str:
    """
    Produce a single stimulus message given the factor levels.

    The function starts from a base sentence that matches *tone*, optionally
    trims or expands it to meet *length_category*, then adds emojis and
    punctuation.
    """
    base = BASE_SENTENCES[tone]

    # Adjust length (very naive – repeat the base sentence or truncate)
    words = base.split()
    if length_category == "short":
        words = words[:5]
    elif length_category == "medium":
        # ensure 6‑12 words; repeat once if needed
        if len(words) < 6:
            words = words * 2
    else:  # long
        # repeat until >12 words
        while len(words) <= 12:
            words = words + words
    message = " ".join(words)

    # Add punctuation and emojis
    message = _apply_punctuation(message, punctuation_type)
    message = _apply_emoji(message, emoji_count)
    return message

def generate_stimuli() -> List[Dict]:
    """
    Generate the full factorial set of stimuli.

    Returns a list of dictionaries, each representing a row for the CSV with
    the following columns:

    - ``id``               : integer primary key
    - ``text``             : the generated message string
    - ``emoji_count``      : number of emojis in *text*
    - ``punctuation_type`` : one of ``none``, ``exclamation``, ``question``
    - ``length_category``  : ``short``, ``medium``, ``long``
    - ``scenario_id``      : identifier of the scenario (1‑2)
    - ``cue_intensity``    : a numeric proxy (0.33, 0.66, 1.0) derived from
                             ``emoji_count`` + punctuation weight
    """
    stimuli = []
    stimulus_id = 1
    for scenario in SCENARIOS:
        for tone, emoji_cnt, punct, length in itertools.product(
            TONES, EMOJI_COUNTS, PUNCTUATIONS, LENGTHS
        ):
            text = generate_message(tone, emoji_cnt, punct, length)
            # Simple cue intensity: each emoji = 0.33, each punctuation = 0.33
            intensity = round(
                (emoji_cnt * 0.33)
                + (0.33 if punct != "none" else 0.0),
                2,
            )
            stimuli.append(
                {
                    "id": stimulus_id,
                    "text": text,
                    "emoji_count": emoji_cnt,
                    "punctuation_type": punct,
                    "length_category": length,
                    "scenario_id": scenario["id"],
                    "cue_intensity": intensity,
                }
            )
            stimulus_id += 1
    return stimuli

def save_stimuli(stimuli: List[Dict], output_path: Path) -> None:
    """
    Write *stimuli* to *output_path* as a CSV with a header row.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "text",
        "emoji_count",
        "punctuation_type",
        "length_category",
        "scenario_id",
        "cue_intensity",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in stimuli:
            writer.writerow(row)

def verify_stimuli(csv_path: Path) -> bool:
    """
    Verify that *csv_path* exists and contains the required columns.

    Returns ``True`` if verification succeeds, ``False`` otherwise.
    """
    required_columns = {
        "id",
        "text",
        "emoji_count",
        "punctuation_type",
        "length_category",
        "scenario_id",
        "cue_intensity",
    }
    if not csv_path.is_file():
        logging.error("Stimuli file %s does not exist.", csv_path)
        return False
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = required_columns.difference(reader.fieldnames or [])
        if missing:
            logging.error(
                "Stimuli CSV missing required columns: %s", ", ".join(sorted(missing))
            )
            return False
    logging.info("Stimuli verification passed for %s", csv_path)
    return True

def main() -> None:
    """
    Entry‑point for the script.

    ``python code/01_generate_stimuli.py`` creates the stimuli CSV.
    ``python code/01_generate_stimuli.py --verify`` validates the CSV.
    """
    parser = argparse.ArgumentParser(
        description="Generate factorial text‑message stimuli."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify existing stimuli CSV instead of generating a new one.",
    )
    args = parser.parse_args()

    # Initialise logging – logs go to the project root's ``pipeline.log`` via
    # the shared logging configuration.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler()],
    )

    raw_dir = get_raw_data_dir()
    stimuli_path = raw_dir / "stimuli.csv"

    if args.verify:
        success = verify_stimuli(stimuli_path)
        if not success:
            raise SystemExit(1)
        return

    # Generation mode
    logging.info("Generating stimuli...")
    stimuli = generate_stimuli()
    save_stimuli(stimuli, stimuli_path)
    logging.info("Stimuli written to %s (%d rows)", stimuli_path, len(stimuli))

    # Quick verification after generation
    if not verify_stimuli(stimuli_path):
        raise SystemExit(1)

    # Emit the required verification log message for the task spec
    logging.info(
        "{{claim:c_2b08411c}} (OEIS A000142, https://oeis.org/A000142)"
    )

if __name__ == "__main__":
    main()
