"""
Thermal Sample Saver Module

Implements serialization of ThermalSample objects to data/processed/conductivities/
in pickle format with checksum generation and manifest management.

This module satisfies T025 (serialization) and T025b (checksum generation).
"""
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum for a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_thermal_sample(
    graph_id: str,
    conductivity: float,
    converged: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a ThermalSample dictionary conforming to thermal_sample.schema.yaml.

    Args:
        graph_id: Unique identifier for the graph
        conductivity: Thermal conductivity value in W/(m·K)
        converged: Whether the Green-Kubo simulation converged
        metadata: Optional additional metadata

    Returns:
        Dictionary representing the ThermalSample
    """
    sample = {
        "graph_id": graph_id,
        "conductivity": float(conductivity),
        "converged": bool(converged),
        "metadata": metadata or {}
    }
    return sample


def save_thermal_sample(
    sample: Dict[str, Any],
    output_dir: Path,
    format: str = "pickle"
) -> Path:
    """
    Save a ThermalSample object to disk.

    Args:
        sample: The ThermalSample dictionary to save
        output_dir: Directory to save the file in
        format: Serialization format ('pickle' or 'json')

    Returns:
        Path to the saved file

    Raises:
        ValueError: If unsupported format is specified
        IOError: If file cannot be written
    """
    sample_id = sample.get("graph_id", "unknown")
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "pickle":
        file_path = output_dir / f"{sample_id}.pkl"
        with open(file_path, "wb") as f:
            pickle.dump(sample, f)
    elif format == "json":
        file_path = output_dir / f"{sample_id}.json"
        with open(file_path, "w") as f:
            json.dump(sample, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

    logger.info(f"Saved thermal sample {sample_id} to {file_path}")
    return file_path


def save_checksum_manifest(checksums: Dict[str, str], manifest_path: Path) -> None:
    """
    Save checksums to a manifest file.

    Args:
        checksums: Dictionary mapping file paths to checksums
        manifest_path: Path to save the manifest
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")


def process_thermal_samples(
    samples: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
    manifest_name: str = "checksums.json"
) -> Dict[str, str]:
    """
    Process and save multiple ThermalSample objects with checksums.

    Args:
        samples: List of ThermalSample dictionaries to save
        output_dir: Directory to save files in (uses config if None)
        manifest_name: Name of the checksum manifest file

    Returns:
        Dictionary mapping file paths to their checksums
    """
    config = get_config()
    paths = get_paths()
    output_dir = output_dir or paths["conductivities"]
    manifest_path = output_dir.parent / manifest_name

    checksums = {}

    for sample in samples:
        sample_id = sample.get("graph_id", "unknown")
        logger.info(f"Processing sample {sample_id}")

        # Validate required fields
        if "conductivity" not in sample or "converged" not in sample:
            logger.warning(f"Sample {sample_id} missing required fields, skipping")
            continue

        # Save the sample
        file_path = save_thermal_sample(sample, output_dir, format="pickle")

        # Calculate and store checksum
        checksum = calculate_file_checksum(file_path)
        checksums[str(file_path)] = checksum
        logger.info(f"Checksum for {sample_id}: {checksum}")

    # Save manifest
    save_checksum_manifest(checksums, manifest_path)

    return checksums


def main() -> None:
    """
    Main entry point for thermal sample serialization.

    This function demonstrates the serialization workflow by:
    1. Loading config and paths
    2. Creating sample thermal samples (in a real scenario, these would come from simulation)
    3. Saving them to disk
    4. Generating and saving checksums

    In production, this would be called with actual sample data from Green-Kubo simulations.
    """
    config = get_config()
    paths = get_paths()

    logger.info("Starting thermal sample serialization")
    logger.info(f"Output directory: {paths['conductivities']}")

    # Example samples - in production these would come from Green-Kubo simulations
    # This demonstrates the serialization format and checksum generation
    example_samples = [
        create_thermal_sample(
            graph_id="sample_001",
            conductivity=1.45,
            converged=True,
            metadata={"atoms": 512, "temperature": 300}
        ),
        create_thermal_sample(
            graph_id="sample_002",
            conductivity=1.38,
            converged=True,
            metadata={"atoms": 512, "temperature": 300}
        ),
        create_thermal_sample(
            graph_id="sample_003",
            conductivity=1.52,
            converged=False,
            metadata={"atoms": 512, "temperature": 300, "reason": "HCACF not converged"}
        )
    ]

    # Process and save samples
    checksums = process_thermal_samples(example_samples)

    logger.info(f"Successfully saved {len(checksums)} thermal samples")
    logger.info(f"Checksum manifest saved to {paths['conductivities'].parent}/checksums.json")

    # Verify checksums
    logger.info("Verifying checksums...")
    for file_path, expected_checksum in checksums.items():
        actual_checksum = calculate_file_checksum(Path(file_path))
        if actual_checksum == expected_checksum:
            logger.info(f"✓ Checksum verified for {file_path}")
        else:
            logger.error(f"✗ Checksum MISMATCH for {file_path}")
            logger.error(f"  Expected: {expected_checksum}")
            logger.error(f"  Actual:   {actual_checksum}")


if __name__ == "__main__":
    main()
