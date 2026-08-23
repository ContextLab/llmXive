"""
090_define_cue_weights.py

This script defines a set of cue‑intensity weighting schemes used throughout the
analysis pipeline and stores them as a JSON file in the processed data directory.

Expected output:
    data/processed/cue_intensity_weights.json
"""
import json
from pathlib import Path

from config import get_processed_data_dir


def get_cue_intensity_schemes() -> list[dict]:
    """
    Return a list of cue‑intensity weighting scheme definitions.

    Each scheme is represented as a dictionary with a ``name`` key and a
    ``weights`` dictionary that maps the three cue types (relationship,
    emoji, punctuation) to their respective weights.

    The four schemes required by the specification are:

    1. Primary               – 0.4 / 0.3 / 0.3
    2. Equal                 – 0.33 / 0.33 / 0.33
    3. Emoji‑Dominant        – 0.2 / 0.6 / 0.2
    4. Punctuation‑Dominant – 0.2 / 0.2 / 0.6
    """
    return [
        {
            "name": "Primary",
            "weights": {
                "relationship": 0.4,
                "emoji": 0.3,
                "punctuation": 0.3,
            },
        },
        {
            "name": "Equal",
            "weights": {
                "relationship": 0.33,
                "emoji": 0.33,
                "punctuation": 0.33,
            },
        },
        {
            "name": "Emoji-Dominant",
            "weights": {
                "relationship": 0.2,
                "emoji": 0.6,
                "punctuation": 0.2,
            },
        },
        {
            "name": "Punctuation-Dominant",
            "weights": {
                "relationship": 0.2,
                "emoji": 0.2,
                "punctuation": 0.6,
            },
        },
    ]


def save_schemes(schemes: list[dict], output_path: Path) -> None:
    """
    Persist the cue‑intensity schemes to ``output_path`` as pretty‑printed JSON.

    Parameters
    ----------
    schemes: list[dict]
        The list returned by :func:`get_cue_intensity_schemes`.
    output_path: Path
        Destination file path (including filename). Parent directories are
        created if they do not already exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, sort_keys=False)
    # Ensure a trailing newline for POSIX compliance
    output_path.open("a", encoding="utf-8").write("\n")


def main() -> None:
    """
    Entry‑point for the script.

    It obtains the predefined schemes, determines the processed data directory
    via the project's configuration utilities, and writes the JSON file.
    """
    schemes = get_cue_intensity_schemes()
    processed_dir = get_processed_data_dir()
    output_file = processed_dir / "cue_intensity_weights.json"
    save_schemes(schemes, output_file)
    print(f"Cue‑intensity weighting schemes written to {output_file}")


if __name__ == "__main__":
    main()
