"""
Seed Manager Module for llmXive.

Handles deterministic seed generation and management for the image generation pipeline.
Ensures reproducibility by generating identical seeds for Baseline and Experimental groups
per scene, and distinct consistent seeds for the Control group.
"""

import os
import json
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from generation.prompt_engine import load_scene_descriptions


class SeedManager:
    """
    Manages seed generation and manifest creation for the diffusion pipeline.

    Attributes:
        base_seed (int): The global base seed for the experiment.
        scene_seeds (Dict[str, Dict[str, int]]): Mapping of scene_id to group seeds.
    """

    def __init__(self, base_seed: int = 42):
        """
        Initialize the SeedManager.

        Args:
            base_seed (int): The global base seed to derive specific seeds from.
        """
        self.base_seed = base_seed
        self.scene_seeds: Dict[str, Dict[str, int]] = {}

    def _derive_seed(self, scene_id: str, group: str, salt: str = "") -> int:
        """
        Derive a deterministic seed for a specific scene and group.

        Args:
            scene_id (str): Unique identifier for the scene.
            group (str): Group name ('baseline', 'experimental', 'control').
            salt (str): Optional additional salt for uniqueness.

        Returns:
            int: A deterministic seed integer.
        """
        # Create a deterministic string for hashing
        seed_string = f"{self.base_seed}:{scene_id}:{group}:{salt}"
        # Hash to get a consistent integer
        hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
        hash_int = int(hash_obj.hexdigest(), 16)
        # Modulo to fit within standard random seed range (0 to 2^32 - 1)
        return hash_int % (2**32)

    def generate_seeds_for_scene(self, scene_id: str) -> Dict[str, int]:
        """
        Generate seeds for all groups for a specific scene.

        Args:
            scene_id (str): The scene identifier.

        Returns:
            Dict[str, int]: Dictionary mapping group names to seeds.
        """
        seeds = {
            "baseline": self._derive_seed(scene_id, "baseline"),
            "experimental": self._derive_seed(scene_id, "experimental"),
            "control": self._derive_seed(scene_id, "control")
        }

        # Ensure Baseline and Experimental have IDENTICAL seeds for the same scene
        # as per FR-007 requirement for strict comparison.
        # Note: The prompt implies "identical seeds for Baseline and Experimental groups
        # for each scene ID". This usually means the seed used for generation is the same
        # for both prompts to isolate the prompt effect.
        seeds["experimental"] = seeds["baseline"]

        self.scene_seeds[scene_id] = seeds
        return seeds

    def generate_all_seeds(self, scene_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """
        Generate seeds for a list of scene IDs.

        Args:
            scene_ids (List[str]): List of scene identifiers.

        Returns:
            Dict[str, Dict[str, int]]: Complete seed manifest.
        """
        for scene_id in scene_ids:
            self.generate_seeds_for_scene(scene_id)
        return self.scene_seeds

    def save_manifest(self, output_path: Path) -> None:
        """
        Save the generated seed manifest to a JSON file.

        Args:
            output_path (Path): Path to the output JSON file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "base_seed": self.base_seed,
            "seeds": self.scene_seeds
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)


def get_generation_seed(scene_id: str, group: str, base_seed: int = 42) -> int:
    """
    Utility function to get a seed for a specific scene and group.

    Args:
        scene_id (str): Scene identifier.
        group (str): Group name ('baseline', 'experimental', 'control').
        base_seed (int): Global base seed.

    Returns:
        int: The calculated seed.
    """
    manager = SeedManager(base_seed=base_seed)
    return manager._derive_seed(scene_id, group)


def get_baseline_experimental_seeds(scene_id: str, base_seed: int = 42) -> Tuple[int, int]:
    """
    Get seeds for Baseline and Experimental groups.

    Note: Returns the SAME seed for both as per FR-007.

    Args:
        scene_id (str): Scene identifier.
        base_seed (int): Global base seed.

    Returns:
        Tuple[int, int]: (baseline_seed, experimental_seed) - identical values.
    """
    manager = SeedManager(base_seed=base_seed)
    seed = manager._derive_seed(scene_id, "baseline")
    return seed, seed


def run_seed_generation(
    input_csv_path: str,
    output_manifest_path: str,
    base_seed: int = 42
) -> None:
    """
    Main entry point to generate the seed manifest from scene descriptions.

    Args:
        input_csv_path (str): Path to the scene descriptions CSV.
        output_manifest_path (str): Path for the output seed manifest JSON.
        base_seed (int): Global base seed.
    """
    # Load scene IDs from the CSV
    # We expect the CSV to have a 'scene_id' column or similar.
    # Based on T011, we generated 'data/raw/scene_descriptions.csv'.
    # We need to extract the scene IDs.
    
    scene_ids = []
    try:
        # Re-using logic from prompt_engine to ensure consistency in loading
        # Although prompt_engine loads descriptions, we just need the IDs here.
        # Let's assume the CSV has a header.
        import csv
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'scene_id' in row:
                    scene_ids.append(row['scene_id'])
                elif 'id' in row:
                    scene_ids.append(row['id'])
                else:
                    # Fallback if column name is unknown, assume first column or index
                    # But T011 likely uses standard format.
                    pass
    except FileNotFoundError:
        raise FileNotFoundError(f"Scene descriptions file not found: {input_csv_path}")

    if not scene_ids:
        raise ValueError(f"No scene IDs found in {input_csv_path}")

    manager = SeedManager(base_seed=base_seed)
    manager.generate_all_seeds(scene_ids)
    
    output_path = Path(output_manifest_path)
    manager.save_manifest(output_path)
    print(f"Seed manifest generated: {output_path}")


def main():
    """Command line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate seed manifest for image generation.")
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
        help="Path for the output seed manifest JSON."
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=42,
        help="Global base seed for the experiment."
    )

    args = parser.parse_args()

    run_seed_generation(
        input_csv_path=args.input_csv,
        output_manifest_path=args.output_manifest,
        base_seed=args.base_seed
    )


if __name__ == "__main__":
    main()
