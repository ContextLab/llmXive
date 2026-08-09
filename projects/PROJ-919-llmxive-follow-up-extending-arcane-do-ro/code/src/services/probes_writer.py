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
    logger.info(f"Ensured derived directory exists: {derived_path}")
    return derived_path

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_probes_to_jsonl(probes: List[Dict[str, Any]], output_file: Optional[Path] = None) -> Path:
    """
    Write a list of probe dictionaries to a JSONL file.
    
    Args:
        probes: List of probe dictionaries.
        output_file: Optional specific output path. If None, uses default config path.
        
    Returns:
        Path to the written file.
    """
    if output_file is None:
        ensure_derived_directory()
        config = get_config()
        output_file = Path(config["data"]["derived"]) / "probes.jsonl"
    else:
        output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(probes)} probes to {output_file}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for probe in probes:
            # Ensure consistent JSON formatting for reproducibility
            json_line = json.dumps(probe, ensure_ascii=False, sort_keys=True)
            f.write(json_line + "\n")
    
    checksum = compute_file_checksum(output_file)
    logger.info(f"Probes written successfully. File checksum: {checksum}")
    
    return output_file

def read_probes_from_jsonl(input_file: Path) -> List[Dict[str, Any]]:
    """
    Read probes from a JSONL file.
    
    Args:
        input_file: Path to the JSONL file.
        
    Returns:
        List of probe dictionaries.
    """
    if not input_file.exists():
        logger.error(f"Probes file not found: {input_file}")
        return []
    
    probes = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                probe = json.loads(line)
                probes.append(probe)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
    
    logger.info(f"Read {len(probes)} probes from {input_file}")
    return probes

def verify_probes_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of a probes file.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

def get_probes_summary(file_path: Path) -> Dict[str, Any]:
    """
    Generate a summary of the probes in a file.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        Dictionary with summary statistics.
    """
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    probes = read_probes_from_jsonl(file_path)
    
    if not probes:
        return {"count": 0, "error": "No probes found"}
    
    # Calculate basic statistics
    total_count = len(probes)
    valid_count = sum(1 for p in probes if p.get("valid", False))
    invalid_count = total_count - valid_count
    
    # Count by character
    character_counts = {}
    for probe in probes:
        char_name = probe.get("character", "unknown")
        character_counts[char_name] = character_counts.get(char_name, 0) + 1
    
    # Count by status
    status_counts = {}
    for probe in probes:
        status = probe.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total_count": total_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "character_counts": character_counts,
        "status_counts": status_counts,
        "file_path": str(file_path),
        "checksum": compute_file_checksum(file_path)
    }

def main():
    """
    Main function to demonstrate probes writer functionality.
    Creates sample probes and writes them to the derived directory.
    """
    logger.info("Starting probes writer demonstration")
    
    # Ensure directory exists
    output_dir = ensure_derived_directory()
    output_file = output_dir / "probes.jsonl"
    
    # Create sample probes for demonstration
    sample_probes = [
        {
            "id": "probe_001",
            "character": "Alice",
            "scenario": "Alice finds herself in a completely alien environment with no gravity.",
            "coarse_axes": ["Curiosity", "Resilience"],
            "fine_axes": ["Detailed observation of surroundings", "Adaptation to physical constraints"],
            "valid": True,
            "status": "generated",
            "similarity_score": 0.15,
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "probe_002",
            "character": "Bob",
            "scenario": "Bob must negotiate a peace treaty with an advanced AI civilization.",
            "coarse_axes": ["Diplomacy", "Logic"],
            "fine_axes": ["Structured argumentation", "Empathy for non-human perspectives"],
            "valid": True,
            "status": "generated",
            "similarity_score": 0.22,
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "probe_003",
            "character": "Charlie",
            "scenario": "Charlie discovers a hidden library containing the history of a lost civilization.",
            "coarse_axes": ["Curiosity", "Preservation"],
            "fine_axes": ["Systematic cataloging", "Respect for ancient knowledge"],
            "valid": True,
            "status": "generated",
            "similarity_score": 0.18,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Write probes to file
    written_file = write_probes_to_jsonl(sample_probes, output_file)
    
    # Verify the file was written correctly
    summary = get_probes_summary(written_file)
    logger.info(f"Probes summary: {json.dumps(summary, indent=2)}")
    
    # Read back and verify
    read_probes = read_probes_from_jsonl(written_file)
    logger.info(f"Successfully read back {len(read_probes)} probes")
    
    logger.info("Probes writer demonstration completed successfully")
    return written_file

if __name__ == "__main__":
    main()