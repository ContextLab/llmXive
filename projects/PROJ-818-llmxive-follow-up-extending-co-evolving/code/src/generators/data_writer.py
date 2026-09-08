"""
Data writing logic for generated training datasets.

Implements writing of generated datasets to disk and management of checksums
for data integrity verification.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import existing checksum utilities
from src.utils.checksums import (
    compute_file_sha256,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    ChecksumError
)
from src.utils.config import load_config, Config


class DataWriteError(Exception):
    """Exception raised for errors during data writing operations."""
    pass


def write_dataset(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write a dataset to a JSON file.
    
    Args:
        data: List of dataset records to write
        output_path: Path where the JSON file should be written
        
    Raises:
        DataWriteError: If writing fails
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write data with proper formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            
    except IOError as e:
        raise DataWriteError(f"Failed to write dataset to {output_path}: {e}")
    except TypeError as e:
        raise DataWriteError(f"Data contains non-serializable types: {e}")


def register_checksum(file_path: Path, checksums_path: Path) -> None:
    """
    Compute and register a checksum for a file in the checksums registry.
    
    Args:
        file_path: Path to the file to checksum
        checksums_path: Path to the checksums.json registry
        
    Raises:
        DataWriteError: If checksum registration fails
    """
    try:
        # Compute the checksum
        checksum = compute_file_sha256(file_path)
        
        # Load existing checksums
        checksums = load_checksums(checksums_path)
        
        # Update with new checksum
        relative_path = str(file_path.relative_to(checksums_path.parent.parent))
        checksums[relative_path] = {
            "hash": checksum,
            "timestamp": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size
        }
        
        # Save updated checksums
        save_checksums(checksums, checksums_path)
        
    except ChecksumError as e:
        raise DataWriteError(f"Failed to register checksum for {file_path}: {e}")
    except Exception as e:
        raise DataWriteError(f"Unexpected error registering checksum: {e}")


def generate_and_save_training_data(
    logic_data: List[Dict[str, Any]],
    grid_data: List[Dict[str, Any]],
    test_data: List[Dict[str, Any]],
    config: Config
) -> Dict[str, str]:
    """
    Generate and save all training datasets with checksums.
    
    This function:
    1. Writes logic proof dataset to data/logic_proofs.json
    2. Writes grid world dataset to data/grid_worlds.json
    3. Writes test instances to data/test_instances.json (if not already present)
    4. Registers checksums for all files in data/checksums.json
    
    Args:
        logic_data: List of logic proof records
        grid_data: List of grid world records
        test_data: List of test instance records
        config: Configuration object with output paths
        
    Returns:
        Dictionary mapping dataset names to their file paths
        
    Raises:
        DataWriteError: If any writing or checksum operation fails
    """
    data_dir = Path("data")
    checksums_path = data_dir / "checksums.json"
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = {}
    
    # Write logic proofs dataset
    logic_path = data_dir / "logic_proofs.json"
    write_dataset(logic_data, logic_path)
    register_checksum(logic_path, checksums_path)
    saved_paths["logic_proofs"] = str(logic_path)
    
    # Write grid worlds dataset
    grid_path = data_dir / "grid_worlds.json"
    write_dataset(grid_data, grid_path)
    register_checksum(grid_path, checksums_path)
    saved_paths["grid_worlds"] = str(grid_path)
    
    # Write test instances
    test_path = data_dir / "test_instances.json"
    write_dataset(test_data, test_path)
    register_checksum(test_path, checksums_path)
    saved_paths["test_instances"] = str(test_path)
    
    return saved_paths


def main() -> int:
    """
    Main entry point for data writing script.
    
    Loads configuration, generates training data from generators,
    and saves all datasets with checksums.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        # Load configuration
        config = load_config()
        
        # Import generators
        from src.generators.logic_generator import LogicProofGenerator
        from src.generators.grid_generator import GridWorldGenerator
        from src.generators.test_generator import TestInstanceGenerator
        
        # Initialize generators
        logic_gen = LogicProofGenerator(seed=config.get("seed", 42))
        grid_gen = GridWorldGenerator(seed=config.get("seed", 42) + 1)
        test_gen = TestInstanceGenerator(seed=config.get("seed", 42) + 2)
        
        # Generate datasets
        print("Generating logic proofs...")
        logic_data = logic_gen.generate_proofs(
            num_proofs=config.get("num_logic_proofs", 100)
        )
        
        print("Generating grid worlds...")
        grid_data = grid_gen.generate_grids(
            num_grids=config.get("num_grid_worlds", 100)
        )
        
        print("Generating test instances...")
        test_data = test_gen.generate_test_instances(
            num_instances=config.get("num_test_instances", 50)
        )
        
        # Save all datasets with checksums
        print("Saving datasets...")
        saved_paths = generate_and_save_training_data(
            logic_data=logic_data,
            grid_data=grid_data,
            test_data=test_data,
            config=config
        )
        
        print("Data writing completed successfully:")
        for name, path in saved_paths.items():
            print(f"  {name}: {path}")
        
        return 0
        
    except DataWriteError as e:
        print(f"Data write error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
