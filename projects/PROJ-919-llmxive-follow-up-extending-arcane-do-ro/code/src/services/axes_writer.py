import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.lib.config import get_config
from src.lib.utils import get_logger

logger = get_logger(__name__)

def ensure_derived_directory() -> Path:
    """Ensure the data/derived directory exists."""
    config = get_config()
    derived_path = Path(config["data"]["derived"])
    derived_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured derived directory exists at {derived_path}")
    return derived_path

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_axes_to_jsonl(axes: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write a list of axis definitions to a JSONL file.
    
    Args:
        axes: List of dictionaries containing axis definitions.
            Each dict should have structure matching the spec (Coarse/Fine objects).
        output_path: Optional path to write the file. If None, uses default path.
    
    Returns:
        Path to the written file.
    """
    if output_path is None:
        derived_dir = ensure_derived_directory()
        output_path = derived_dir / "axes.jsonl"
    else:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(axes)} axes to {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        for axis in axes:
            # Validate structure before writing
            if not isinstance(axis, dict):
                raise ValueError(f"Invalid axis format: expected dict, got {type(axis)}")
            
            # Ensure required fields exist if it's a Coarse or Fine definition
            if "character" not in axis or "axis_name" not in axis or "description" not in axis:
                logger.warning(f"Axis missing required fields: {axis.keys()}")
            
            # Add metadata for tracking
            axis_record = {
                "timestamp": datetime.now().isoformat(),
                "data": axis
            }
            f.write(json.dumps(axis_record) + "\n")

    logger.info(f"Successfully wrote axes to {output_path}")
    
    # Compute and log checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")
    
    return output_path

def read_axes_from_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Read axes from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file.
    
    Returns:
        List of axis dictionaries.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Axes file not found: {file_path}")
    
    axes = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Extract the actual axis data from the record
                if "data" in record:
                    axes.append(record["data"])
                else:
                    # Fallback: treat whole line as axis if no "data" key
                    axes.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON on line {line_num}: {e}")
                raise
    
    logger.info(f"Read {len(axes)} axes from {file_path}")
    return axes

def verify_axes_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of an axes file.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 checksum.
    
    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = compute_file_checksum(file_path)
    match = actual_checksum == expected_checksum
    
    if match:
        logger.info(f"Checksum verified for {file_path}")
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
    
    return match

def get_axes_summary(file_path: Path) -> Dict[str, Any]:
    """
    Generate a summary of axes in a file.
    
    Args:
        file_path: Path to the JSONL file.
    
    Returns:
        Dictionary with summary statistics.
    """
    axes = read_axes_from_jsonl(file_path)
    
    coarse_count = 0
    fine_count = 0
    characters = set()
    
    for axis in axes:
        if "type" in axis:
            if axis["type"] == "coarse":
                coarse_count += 1
            elif axis["type"] == "fine":
                fine_count += 1
        
        if "character" in axis:
            characters.add(axis["character"])
    
    return {
        "total_axes": len(axes),
        "coarse_count": coarse_count,
        "fine_count": fine_count,
        "unique_characters": list(characters),
        "file_path": str(file_path),
        "checksum": compute_file_checksum(file_path)
    }

def main():
    """
    CLI entry point for writing axes to JSONL.
    This function is designed to be called by T011 (axis_generator) after validation.
    """
    config = get_config()
    logger.info("Starting axes writer service")
    
    # Example usage: This would typically be called with data from axis_generator
    # For demonstration, we create a minimal valid structure
    sample_axes = [
        {
            "character": "Scrooge",
            "type": "coarse",
            "axis_name": "Greed vs Generosity",
            "description": "The spectrum from selfish accumulation to selfless giving"
        },
        {
            "character": "Scrooge",
            "type": "fine",
            "axis_name": "Isolation vs Connection",
            "description": "The tendency to withdraw from social bonds versus seek them",
            "source_observation": "Observed in his rejection of Fred's invitation"
        }
    ]
    
    output_path = write_axes_to_jsonl(sample_axes)
    
    summary = get_axes_summary(output_path)
    logger.info(f"Axes summary: {json.dumps(summary, indent=2)}")
    
    return output_path

if __name__ == "__main__":
    main()
