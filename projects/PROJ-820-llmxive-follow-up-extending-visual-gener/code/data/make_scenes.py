"""make_scenes.py
----------------
Deterministic generator for the stimulus dataset required by task T001.

This script creates two CSV files:
  * data/raw/scene_descriptions.csv      – 500 main scene descriptions
  * data/raw/validation_scenes.csv       – 50 validation scene descriptions

The generation is fully deterministic (seed=42) and uses a small set of
object names and textual templates.  Every description is guaranteed to
match one of the predefined templates, satisfying the verification
criteria.

The script can be invoked directly:
    python code/data/make_scenes.py

No command‑line arguments are required; the seed is fixed to ensure
reproducibility across runs.
"""

import csv
import random
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SEED = 42
MAIN_COUNT = 500
VALID_COUNT = 50

# Simple object vocabulary – can be extended without affecting determinism.
OBJECTS = [
    "cup",
    "book",
    "ball",
    "box",
    "bottle",
    "plate",
    "chair",
    "table",
    "lamp",
    "vase",
]

# Templates with placeholders.  The placeholder names are kept for
# readability; they are filled with objects from the OBJECTS list.
TEMPLATES = [
    "a {obj1} on a {obj2}",
    "a {obj1} next to a {obj2}",
    "a {obj1} under a {obj2}",
    "a {obj1} inside a {obj2}",
    "a {obj1} leaning against a {obj2}",
    "a {obj1} on top of a {obj2}",
    "a {obj1} touching a {obj2}",
    "a {obj1} above a {obj2}",
    "a {obj1} below a {obj2}",
    "a {obj1} behind a {obj2}",
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _choose_objects(rng: random.Random) -> tuple[str, str]:
    """Return a deterministic pair of distinct objects."""
    obj1 = rng.choice(OBJECTS)
    obj2 = rng.choice(OBJECTS)
    # Ensure the two objects differ to keep the description meaningful.
    while obj2 == obj1:
        obj2 = rng.choice(OBJECTS)
    return obj1, obj2

def _build_description(rng: random.Random) -> str:
    """Create a single scene description using a random template."""
    template = rng.choice(TEMPLATES)
    obj1, obj2 = _choose_objects(rng)
    description = template.format(obj1=obj1, obj2=obj2)
    return description

def _generate_descriptions(count: int, rng: random.Random) -> list[dict]:
    """Generate a list of scene dictionaries with deterministic IDs."""
    scenes = []
    for i in range(1, count + 1):
        scene_id = f"scene_{i:04d}"
        description = _build_description(rng)
        scenes.append({"scene_id": scene_id, "description_text": description})
    return scenes

def _write_csv(file_path: Path, rows: list[dict]) -> None:
    """Write rows to a CSV file with a header."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["scene_id", "description_text"])
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), file_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Generate the stimulus CSV files."""
    rng = random.Random(SEED)

    # Main dataset
    main_scenes = _generate_descriptions(MAIN_COUNT, rng)
    main_path = paths.data("raw", "scene_descriptions.csv")
    _write_csv(main_path, main_scenes)

    # Validation dataset – re‑seed to guarantee a different but still
    # deterministic set of descriptions.
    rng = random.Random(SEED + 1)
    val_scenes = _generate_descriptions(VALID_COUNT, rng)
    val_path = paths.data("raw", "validation_scenes.csv")
    _write_csv(val_path, val_scenes)

    log.info("Dataset generation completed successfully.")

if __name__ == "__main__":
    main()
