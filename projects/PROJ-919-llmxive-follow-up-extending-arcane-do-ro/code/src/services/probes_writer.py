import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.lib.config import get_config
from src.lib.utils import get_logger

logger = get_logger(__name__)

def ensure_derived_directory() -> Path:
    """Ensure the data/derived directory exists."""
    config = get_config()
    derived_dir = Path(config.data_dir) / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured derived directory exists at {derived_dir}")
    return derived_dir

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_probes_to_jsonl(probes: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write a list of validated probe dictionaries to a JSONL file.
    
    Args:
        probes: List of probe records (each a dict).
        output_path: Optional specific path. If None, uses default derived/probes.jsonl.
        
    Returns:
        Path to the written file.
    """
    if output_path is None:
        derived_dir = ensure_derived_directory()
        output_path = derived_dir / "probes.jsonl"
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {len(probes)} probes to {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, probe in enumerate(probes):
            # Ensure probe has required metadata
            if "timestamp" not in probe:
                probe["timestamp"] = datetime.utcnow().isoformat()
            if "index" not in probe:
                probe["index"] = idx
            
            f.write(json.dumps(probe, ensure_ascii=False) + "\n")
    
    # Compute and log checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Written {len(probes)} probes to {output_path} (SHA-256: {checksum[:16]}...)")
    
    return output_path

def read_probes_from_jsonl(input_path: Path) -> List[Dict[str, Any]]:
    """
    Read probes from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file.
        
    Returns:
        List of probe dictionaries.
    """
    if not input_path.exists():
        logger.warning(f"Probes file not found: {input_path}")
        return []
    
    probes = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                probes.append(json.loads(line))
    
    logger.info(f"Read {len(probes)} probes from {input_path}")
    return probes

def verify_probes_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the checksum of a probes file against an expected value.
    
    Args:
        file_path: Path to the probes file.
        expected_checksum: Expected SHA-256 hex string.
        
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
        logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False

def get_probes_summary(probes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of the probes list.
    
    Args:
        probes: List of probe dictionaries.
        
    Returns:
        Dictionary with summary statistics.
    """
    if not probes:
        return {
            "count": 0,
            "characters": [],
            "valid_count": 0,
            "invalid_count": 0
        }
    
    characters = set()
    valid_count = 0
    invalid_count = 0
    
    for probe in probes:
        char = probe.get("character", "unknown")
        characters.add(char)
        
        status = probe.get("character_status", "unknown")
        if status == "valid":
            valid_count += 1
        elif status == "invalid":
            invalid_count += 1
    
    return {
        "count": len(probes),
        "characters": sorted(list(characters)),
        "valid_count": valid_count,
        "invalid_count": invalid_count
    }

def main():
    """
    Main entry point for the probes writer script.
    Demonstrates writing probes to data/derived/probes.jsonl.
    """
    # Example usage: This would typically be called by the probe generation pipeline
    # For now, we demonstrate the writer functionality with a sample structure
    # In a real run, this would be populated by generate_probes_batch()
    
    sample_probes = [
        {
            "character": "Sherlock Holmes",
            "probe_text": "You are in a silent library where books whisper secrets. What do you do?",
            "source_axes": {"coarse": "deductive_reasoning", "fine": "observational_detail"},
            "semantic_distance": 0.85,
            "character_status": "valid"
        },
        {
            "character": "Sherlock Holmes",
            "probe_text": "A mysterious fog rolls in, carrying voices of the past. How do you react?",
            "source_axes": {"coarse": "deductive_reasoning", "fine": "observational_detail"},
            "semantic_distance": 0.78,
            "character_status": "valid"
        }
    ]
    
    logger.info("Running probes writer demonstration...")
    output_path = write_probes_to_jsonl(sample_probes)
    
    summary = get_probes_summary(read_probes_from_jsonl(output_path))
    logger.info(f"Probes summary: {summary}")
    
    return output_path

if __name__ == "__main__":
    main()
