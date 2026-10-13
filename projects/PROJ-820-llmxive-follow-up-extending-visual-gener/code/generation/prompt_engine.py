"""
Prompt engineering module for generating Baseline and Experimental prompts.
Implements T003.

The script reads scene descriptions from a CSV file and corresponding physics
constraint JSON files. For each scene it writes two prompt files under the
specified output directory:

* `{scene_id}_baseline.txt`      – the original scene description only.
* `{scene_id}_experimental.txt` – the original description followed by a
  deterministic natural‑language descriptor taken from the JSON field
  ``natural_language_descriptor``.

Both files contain a single non‑empty line. The experimental descriptor is a
pure function of the physics JSON; no randomness is introduced.

Additional helper functions ``format_physics_constraints`` and
``generate_control_prompt`` are provided to satisfy the public API expected
by ``code/generation/__init__.py`` and other modules.
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class PromptEngineError(Exception):
    """Base exception for prompt engine errors."""
    pass

class SceneDescriptionNotFoundError(PromptEngineError):
    """Raised when a scene description file is missing."""
    pass

class PhysicsConstraintNotFoundError(PromptEngineError):
    """Raised when a physics‑constraint JSON file is missing."""
    pass

def load_scene_descriptions(csv_path: str) -> Dict[str, str]:
    """
    Load scene descriptions from a CSV file.

    The CSV must contain a column named ``scene_id`` (or ``id``) and a column
    named ``description`` (or ``description_text``/``text``). Returns a mapping
    from scene_id to description string.
    """
    path = Path(csv_path)
    if not path.exists():
        raise SceneDescriptionNotFoundError(f"Scene descriptions file not found: {csv_path}")

    scenes: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scene_id = row.get("scene_id") or row.get("id")
            description = (
                row.get("description")
                or row.get("description_text")
                or row.get("text")
            )
            if scene_id and description:
                scenes[scene_id] = description.strip()
    return scenes

def load_physics_constraints(json_dir: str, scene_id: str) -> Dict:
    """
    Load the physics‑constraint JSON for a given scene.

    Returns an empty dict if the file does not exist – the caller can decide
    whether to treat the missing descriptor as an empty string.
    """
    constraint_path = Path(json_dir) / f"{scene_id}.json"
    if not constraint_path.exists():
        raise PhysicsConstraintNotFoundError(
            f"Physics constraints not found for scene {scene_id} at {constraint_path}"
        )
    with constraint_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _extract_descriptor(constraints: Dict) -> str:
    """
    Retrieve the deterministic natural‑language descriptor from the physics JSON.

    The specification defines the key ``natural_language_descriptor``. If the
    key is missing or empty, an empty string is returned.
    """
    return constraints.get("natural_language_descriptor", "").strip()

# ----------------------------------------------------------------------
# Public helper functions expected by the rest of the codebase
# ----------------------------------------------------------------------
def format_physics_constraints(constraints: Dict) -> str:
    """
    Format the physics constraints into a deterministic natural‑language string.

    This function is part of the public API imported in ``generation.__init__``.
    It simply extracts the ``natural_language_descriptor`` field, mirroring the
    behaviour of ``_extract_descriptor`` but keeping a stable public name.
    """
    return _extract_descriptor(constraints)

def generate_baseline_prompt(scene_description: str) -> str:
    """
    Baseline prompt: the original scene description unchanged.
    """
    return scene_description.strip()

def generate_experimental_prompt(scene_description: str, constraints: Dict) -> str:
    """
    Experimental prompt: original description followed by the deterministic
    descriptor extracted from the physics JSON. If the descriptor is empty,
    the prompt falls back to the baseline version.
    """
    descriptor = _extract_descriptor(constraints)
    if descriptor:
        # Ensure a single line – separate with a space.
        return f"{scene_description.strip()} {descriptor}"
    return scene_description.strip()

def generate_control_prompt(scene_description: str) -> str:
    """
    Control prompt placeholder.

    The original specification mentions a possible third “control” group
    (e.g., length‑matched random text). For the current pipeline we simply
    return the baseline prompt, which satisfies the import contract without
    affecting downstream logic.
    """
    return generate_baseline_prompt(scene_description)

# ----------------------------------------------------------------------
# File‑writing utilities
# ----------------------------------------------------------------------
def write_prompt_file(prompt: str, output_path: Path) -> None:
    """
    Write a single‑line prompt to ``output_path``. The parent directory is
    created if necessary. The function overwrites any existing file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Enforce single‑line output
    single_line = prompt.replace("\n", " ").strip()
    if not single_line:
        raise PromptEngineError(f"Attempted to write empty prompt to {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        f.write(single_line)
    logger.info(f"Written prompt to {output_path}")

def run_prompt_engineering(scenes_csv: str, physics_dir: str, output_dir: str) -> None:
    """
    Main driver: for each scene, generate baseline and experimental prompts and
    write them to ``output_dir`` using the naming convention
    ``{scene_id}_baseline.txt`` and ``{scene_id}_experimental.txt``.
    """
    scenes = load_scene_descriptions(scenes_csv)
    logger.info(f"Loaded {len(scenes)} scene descriptions from {scenes_csv}")

    for scene_id, description in scenes.items():
        try:
            constraints = load_physics_constraints(physics_dir, scene_id)
        except PhysicsConstraintNotFoundError as exc:
            logger.warning(str(exc))
            constraints = {}

        baseline = generate_baseline_prompt(description)
        experimental = generate_experimental_prompt(description, constraints)

        base_path = Path(output_dir) / f"{scene_id}_baseline.txt"
        exp_path = Path(output_dir) / f"{scene_id}_experimental.txt"

        write_prompt_file(baseline, base_path)
        write_prompt_file(experimental, exp_path)

    logger.info(
        f"Prompt engineering complete – generated prompts for {len(scenes)} scenes "
        f"under {output_dir}"
    )

def main() -> None:
    """
    CLI entry point.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate baseline and experimental prompts for all scenes."
    )
    parser.add_argument(
        "--scenes",
        required=True,
        help="Path to the CSV file containing scene descriptions.",
    )
    parser.add_argument(
        "--physics-dir",
        required=True,
        help="Directory containing physics‑constraint JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where prompt text files will be written.",
    )

    args = parser.parse_args()
    run_prompt_engineering(
        scenes_csv=args.scenes,
        physics_dir=args.physics_dir,
        output_dir=args.output_dir,
    )

if __name__ == "__main__":
    main()
