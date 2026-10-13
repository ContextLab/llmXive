"""
Seed Manifest Generation Script
--------------------------------
Generates a deterministic seed manifest JSON file that maps each scene identifier
to a shared integer seed used for the baseline and experimental image generations.
The manifest is stored at ``data/derived/seed_manifest.json``.
"""

import csv
import json
from pathlib import Path
from typing import List

from generation.seed_manager import SeedManager


def _load_scene_ids(csv_path: Path) -> List[str]:
    """
    Load scene identifiers from the provided CSV file.

    The CSV is expected to have a column named ``scene_id`` (or ``id`` as a fallback).

    Args:
        csv_path: Path to the scene description CSV.

    Returns:
        List of scene identifier strings.

    Raises:
        FileNotFoundError: If the CSV does not exist.
        ValueError: If no scene IDs can be extracted.
    """
    scene_ids: List[str] = []
    with csv_path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'scene_id' in row:
                scene_ids.append(row['scene_id'])
            elif 'id' in row:
                scene_ids.append(row['id'])
            else:
                # If neither column exists, fall back to the first column value.
                first_key = next(iter(row))
                scene_ids.append(row[first_key])

    if not scene_ids:
        raise ValueError(f"No scene IDs found in {csv_path}")
    return scene_ids


def generate_seed_manifest(
    scene_csv_path: Path,
    manifest_path: Path,
    base_seed: int = 42
) -> None:
    """
    Create the seed manifest JSON file.

    The manifest format matches the expectations of ``generation.diffusion_runner``:

    .. code-block:: json
        {
            "base_seed": 42,
            "seeds": {
                "scene_001": {
                    "baseline": 123456,
                    "experimental": 123456,
                    "control": 789012
                },
                ...
            }
        }

    Args:
        scene_csv_path: Path to ``data/raw/scene_descriptions.csv``.
        manifest_path: Destination path for ``seed_manifest.json``.
        base_seed: Global deterministic seed.
    """
    scene_ids = _load_scene_ids(scene_csv_path)

    manager = SeedManager(base_seed=base_seed)
    manager.generate_all_seeds(scene_ids)
    manager.save_manifest(manifest_path)
    print(f"Seed manifest written to {manifest_path}")


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate deterministic seed manifest for image generation."
    )
    parser.add_argument(
        "--input-csv",
        type=str,
        default="data/raw/scene_descriptions.csv",
        help="Path to the scene descriptions CSV file."
    )
    parser.add_argument(
        "--output-manifest",
        type=str,
        default="data/derived/seed_manifest.json",
        help="Path where the seed manifest JSON will be saved."
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=42,
        help="Global base seed for deterministic seed derivation."
    )

    args = parser.parse_args()

    generate_seed_manifest(
        scene_csv_path=Path(args.input_csv),
        manifest_path=Path(args.output_manifest),
        base_seed=args.base_seed
    )


if __name__ == "__main__":
    main()
