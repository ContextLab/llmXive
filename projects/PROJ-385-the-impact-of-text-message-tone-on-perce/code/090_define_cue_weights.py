"""
Define cue‑intensity weighting schemes for the sensitivity analysis.

This script creates a JSON file ``cue_intensity_weights.json`` in the
``data/processed`` directory containing four predefined weighting schemes:

1. Primary:          {"emoji": 0.4, "punctuation": 0.3, "length": 0.3}
2. Equal:            {"emoji": 0.33, "punctuation": 0.33, "length": 0.33}
3. Emoji‑Dominant:   {"emoji": 0.6, "punctuation": 0.2, "length": 0.2}
4. Punctuation‑Dominant: {"emoji": 0.2, "punctuation": 0.6, "length": 0.2}

The JSON file is written when the module is executed as a script
(``python code/090_define_cue_weights.py``) or when :func:`main` is called
programmatically.
"""

import json
from pathlib import Path
from typing import Dict, Any

from config import get_processed_data_dir

__all__ = [
    "get_cue_intensity_schemes",
    "save_schemes",
    "main",
]


def get_cue_intensity_schemes() -> Dict[str, Dict[str, float]]:
    """
    Return a dictionary containing the four cue‑intensity weighting schemes.

    Returns
    -------
    Dict[str, Dict[str, float]]
        Mapping from scheme name to a mapping of cue names to numeric weights.
    """
    # The numeric values are defined exactly as required by the specification.
    schemes: Dict[str, Dict[str, float]] = {
        "Primary": {
            "emoji": 0.4,
            "punctuation": 0.3,
            "length": 0.3,
        },
        "Equal": {
            "emoji": 0.33,
            "punctuation": 0.33,
            "length": 0.33,
        },
        "Emoji-Dominant": {
            "emoji": 0.6,
            "punctuation": 0.2,
            "length": 0.2,
        },
        "Punctuation-Dominant": {
            "emoji": 0.2,
            "punctuation": 0.6,
            "length": 0.2,
        },
    }
    return schemes


def save_schemes(
    schemes: Dict[str, Dict[str, float]],
    filename: Path | None = None,
) -> Path:
    """
    Serialize the weighting schemes to a JSON file.

    Parameters
    ----------
    schemes : Dict[str, Dict[str, float]]
        The cue‑intensity schemes to write.
    filename : Path | None, optional
        Destination file.  If ``None`` the default location
        ``data/processed/cue_intensity_weights.json`` is used.

    Returns
    -------
    Path
        The path to the file that was written.
    """
    if filename is None:
        processed_dir = get_processed_data_dir()
        filename = processed_dir / "cue_intensity_weights.json"

    # Ensure the target directory exists.
    filename.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with a stable ordering for reproducibility.
    with filename.open("w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, sort_keys=True)

    return filename


def main() -> None:
    """
    Entry‑point for the module.

    Generates the cue‑intensity weighting schemes and writes them to the
    canonical JSON file under ``data/processed``.
    """
    schemes = get_cue_intensity_schemes()
    output_path = save_schemes(schemes)
    print(f"Cue‑intensity weighting schemes saved to: {output_path}")


if __name__ == "__main__":
    main()