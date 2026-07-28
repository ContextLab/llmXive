"""
Data writing logic for generated training datasets.
Saves datasets to data/ and records checksums in data/checksums.json.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add project root to path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.checksums import (
    compute_file_sha256,
    load_checksums,
    save_checksums,
    update_checksum_for_file
)
from src.utils.config import load_config, Config
from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.generators.test_generator import TestInstanceGenerator


class DataWriteError(Exception):
    """Custom exception for data writing errors."""
    pass


def write_dataset(data: List[Dict[str, Any]], output_path: Path) -> Path:
    """
    Write a list of dataset items to a JSON file.

    Args:
        data: List of dictionaries representing dataset items
        output_path: Path where the JSON file will be written

    Returns:
        Path to the written file

    Raises:
        DataWriteError: If writing fails
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path
    except Exception as e:
        raise DataWriteError(f"Failed to write dataset to {output_path}: {e}")


def register_checksum(file_path: Path, dataset_name: str, config: Config) -> None:
    """
    Compute SHA-256 checksum for a file and register it in data/checksums.json.

    Args:
        file_path: Path to the file to checksum
        dataset_name: Name identifier for the dataset
        config: Configuration object containing output paths
    """
    checksums_path = config.data_dir / "checksums.json"

    # Load existing checksums
    existing_checksums = load_checksums(checksums_path)

    # Compute new checksum
    checksum = compute_file_sha256(file_path)

    # Update checksums dictionary
    existing_checksums[dataset_name] = {
        "file": str(file_path.relative_to(config.data_dir)),
        "sha256": checksum,
        "size_bytes": file_path.stat().st_size
    }

    # Save updated checksums
    save_checksums(existing_checksums, checksums_path)


def generate_and_save_training_data(config: Config) -> Dict[str, str]:
    """
    Generate training datasets for both logic proofs and grid worlds,
    save them to data/, and register their checksums.

    Args:
        config: Configuration object with generation parameters

    Returns:
        Dictionary mapping dataset names to their file paths
    """
    generated_files = {}

    # Initialize generators
    logic_generator = LogicProofGenerator(config)
    grid_generator = GridWorldGenerator(config)

    # Generate logic proofs dataset
    print(f"Generating {config.num_logic_proofs} logic proofs...")
    logic_data = logic_generator.generate_proofs(config.num_logic_proofs)

    if not logic_data:
        raise DataWriteError("Failed to generate any logic proofs")

    logic_output_path = config.data_dir / "logic_proofs_train.json"
    write_dataset(logic_data, logic_output_path)
    register_checksum(logic_output_path, "logic_proofs_train", config)
    generated_files["logic_proofs_train"] = str(logic_output_path)
    print(f"Saved logic proofs to {logic_output_path}")

    # Generate grid worlds dataset
    print(f"Generating {config.num_grid_worlds} grid worlds...")
    grid_data = grid_generator.generate_grids(config.num_grid_worlds)

    if not grid_data:
        raise DataWriteError("Failed to generate any grid worlds")

    grid_output_path = config.data_dir / "grid_worlds_train.json"
    write_dataset(grid_data, grid_output_path)
    register_checksum(grid_output_path, "grid_worlds_train", config)
    generated_files["grid_worlds_train"] = str(grid_output_path)
    print(f"Saved grid worlds to {grid_output_path}")

    return generated_files


def main():
    """Main entry point for data generation and writing."""
    try:
        # Load configuration
        config_path = Path("config.json")
        if not config_path.exists():
            print("No config.json found, using defaults")
            config = load_config()
        else:
            config = load_config(config_path)

        # Ensure data directory exists
        config.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate and save training data
        generated_files = generate_and_save_training_data(config)

        print("\nData generation complete!")
        print("Generated files:")
        for name, path in generated_files.items():
            print(f"  - {name}: {path}")

        # Verify checksums file was created
        checksums_path = config.data_dir / "checksums.json"
        if checksums_path.exists():
            print(f"\nChecksums recorded in: {checksums_path}")
        else:
            raise DataWriteError("Checksums file was not created")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
