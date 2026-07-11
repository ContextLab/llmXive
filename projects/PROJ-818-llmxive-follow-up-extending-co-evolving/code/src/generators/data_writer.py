"""
Data writer module for saving generated datasets with checksums.

This module handles the persistence of generated training datasets to disk
and maintains integrity tracking via SHA-256 checksums.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Add src to path for imports when running as script
if "code" in str(Path(__file__).parent):
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
else:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.checksums import (
    update_checksum_for_file, 
    load_checksums, 
    ChecksumError
)
from src.generators.logic_generator import LogicProofGenerator, main as logic_main
from src.generators.grid_generator import GridWorldGenerator, main as grid_main
from src.generators.test_generator import TestInstanceGenerator, main as test_main

class DataWriteError(Exception):
    """Raised when data writing operations fail."""
    pass

def write_dataset(
    data: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write dataset dictionary to a JSON file.
    
    Args:
        data: Dictionary containing dataset to write
        output_path: Path to the output JSON file
        
    Raises:
        DataWriteError: If writing fails
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        raise DataWriteError(f"Failed to write dataset to {output_path}: {e}")

def register_checksum(filepath: Path, checksum_file: Path) -> str:
    """
    Register a file's checksum in the checksums registry.
    
    Args:
        filepath: Path to the file to register
        checksum_file: Path to the checksums JSON file
        
    Returns:
        The computed SHA-256 hash
        
    Raises:
        DataWriteError: If checksum registration fails
    """
    try:
        return update_checksum_for_file(filepath, checksum_file)
    except ChecksumError as e:
        raise DataWriteError(f"Failed to register checksum for {filepath}: {e}")

def generate_and_save_training_data(
    config: Dict[str, Any],
    output_dir: Path,
    checksum_file: Path
) -> Dict[str, str]:
    """
    Generate training datasets and save them with checksums.
    
    This function orchestrates the generation of both logic proofs and grid worlds,
    saves them to disk, and registers their checksums.
    
    Args:
        config: Configuration dictionary with generation parameters
        output_dir: Directory to save generated datasets
        checksum_file: Path to the checksums JSON file
        
    Returns:
        Dictionary mapping dataset filenames to their SHA-256 checksums
        
    Raises:
        DataWriteError: If generation or saving fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = {}
    
    # Generate and save logic proofs
    logic_output = output_dir / "logic_proofs.json"
    try:
        # Prepare args for logic generator
        logic_args = [
            "--output", str(logic_output),
            "--count", str(config.get("logic_count", 100)),
            "--seed", str(config.get("seed", 42))
        ]
        logic_main(logic_args)
        
        # Register checksum
        checksum = register_checksum(logic_output, checksum_file)
        generated_files["logic_proofs.json"] = checksum
    except Exception as e:
        raise DataWriteError(f"Failed to generate logic proofs: {e}")
        
    # Generate and save grid worlds
    grid_output = output_dir / "grid_worlds.json"
    try:
        # Prepare args for grid generator
        grid_args = [
            "--output", str(grid_output),
            "--count", str(config.get("grid_count", 100)),
            "--seed", str(config.get("seed", 42) + 1000)
        ]
        grid_main(grid_args)
        
        # Register checksum
        checksum = register_checksum(grid_output, checksum_file)
        generated_files["grid_worlds.json"] = checksum
    except Exception as e:
        raise DataWriteError(f"Failed to generate grid worlds: {e}")
        
    return generated_files

def main(args: Optional[List[str]] = None) -> None:
    """
    CLI entry point for data writing.
    
    Usage:
        python -m src.generators.data_writer --config <config.json> --output <dir>
        
    Args:
        args: Command line arguments (optional, uses sys.argv if None)
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate and save training datasets with checksums"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/data/config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="code/data",
        help="Output directory for generated datasets"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Load configuration
    config_path = Path(parsed_args.config)
    if not config_path.exists():
        print(f"Warning: Config file not found at {config_path}, using defaults")
        config = {
            "logic_count": 100,
            "grid_count": 100,
            "seed": 42
        }
    else:
        with open(config_path, "r") as f:
            config = json.load(f)
            
    output_dir = Path(parsed_args.output)
    checksum_file = output_dir / "checksums.json"
    
    print(f"Generating training datasets to {output_dir}...")
    try:
        generated = generate_and_save_training_data(
            config, 
            output_dir, 
            checksum_file
        )
        print(f"Successfully generated {len(generated)} datasets:")
        for filename, checksum in generated.items():
            print(f"  - {filename}: {checksum[:16]}...")
            
        print(f"Checksums saved to {checksum_file}")
    except DataWriteError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
