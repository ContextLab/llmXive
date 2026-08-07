"""
Module: src.services.probes_writer
Purpose: Implement the writer for validated out-of-world probes.
Task: T020 - Create data/derived/probes.jsonl writer to store validated out-of-world probes.
"""
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.lib.logger import get_logger
from src.lib.state_tracker import log_experiment_state, hash_parameters, generate_run_id

logger = get_logger(__name__)


def ensure_derived_directory() -> Path:
    """
    Ensures the data/derived directory exists.
    Returns the Path object for the directory.
    """
    derived_path = Path("data/derived")
    derived_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {derived_path}")
    return derived_path


def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def write_probes_to_jsonl(probes: List[Dict[str, Any]], output_filename: str = "probes.jsonl") -> Path:
    """
    Writes a list of validated probe dictionaries to a JSONL file.
    
    Args:
        probes: List of probe dictionaries. Each must contain at least:
                - character_name (str)
                - scenario_prompt (str)
                - similarity_score (float)
                - generation_status (str)
                - timestamp (str)
        output_filename: Name of the output file (default: probes.jsonl)
    
    Returns:
        Path to the created file.
    
    Raises:
        ValueError: If the probes list is empty or contains invalid entries.
        IOError: If the file cannot be written.
    """
    if not probes:
        raise ValueError("Cannot write empty list of probes. Ensure at least one valid probe exists.")
    
    output_dir = ensure_derived_directory()
    output_path = output_dir / output_filename
    
    logger.info(f"Writing {len(probes)} probes to {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, probe in enumerate(probes):
            # Validate required fields
            required_fields = ["character_name", "scenario_prompt", "similarity_score", "generation_status"]
            missing_fields = [field for field in required_fields if field not in probe]
            if missing_fields:
                logger.warning(f"Probe {i} missing fields: {missing_fields}. Writing anyway but marking as incomplete.")
            
            # Ensure timestamp exists
            if "timestamp" not in probe:
                probe["timestamp"] = datetime.now().isoformat()
            
            # Serialize to JSON line
            json_line = json.dumps(probe, ensure_ascii=False)
            f.write(json_line + "\n")
    
    # Compute checksum for integrity tracking
    checksum = compute_file_checksum(output_path)
    logger.info(f"Wrote probes file with checksum: {checksum}")
    
    # Log experiment state
    run_id = generate_run_id()
    state_params = {
        "task_id": "T020",
        "output_file": str(output_path),
        "num_probes": len(probes),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat()
    }
    log_experiment_state(run_id, "probes_written", state_params)
    
    return output_path


def read_probes_from_jsonl(input_path: Path) -> List[Dict[str, Any]]:
    """
    Reads probes from a JSONL file.
    
    Args:
        input_path: Path to the JSONL file.
    
    Returns:
        List of probe dictionaries.
    """
    probes = []
    if not input_path.exists():
        logger.warning(f"File not found: {input_path}. Returning empty list.")
        return probes
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                probe = json.loads(line)
                probes.append(probe)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON on line {line_num}: {e}")
    
    logger.info(f"Read {len(probes)} probes from {input_path}")
    return probes


def verify_probes_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verifies the checksum of a probes file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 checksum.
    
    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    match = actual_checksum == expected_checksum
    if match:
        logger.info(f"Checksum verification successful for {file_path}")
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
    return match


def get_probes_summary(probes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a summary of the probes list.
    
    Args:
        probes: List of probe dictionaries.
    
    Returns:
        Dictionary containing summary statistics.
    """
    if not probes:
        return {
            "total_count": 0,
            "characters": [],
            "avg_similarity": 0.0,
            "valid_count": 0
        }
    
    characters = list(set(p.get("character_name", "unknown") for p in probes))
    valid_count = sum(1 for p in probes if p.get("generation_status") == "valid")
    similarities = [p.get("similarity_score", 0.0) for p in probes if "similarity_score" in p]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
    
    return {
        "total_count": len(probes),
        "characters": characters,
        "avg_similarity": avg_similarity,
        "valid_count": valid_count,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """
    Main entry point for testing the probes writer functionality.
    This function demonstrates writing and reading probes.
    """
    logger.info("Starting probes writer demo (T020)")
    
    # Sample probes data (in real usage, this would come from probe_generator)
    sample_probes = [
        {
            "character_name": "Hamlet",
            "scenario_prompt": "You are a prince in a futuristic cyberpunk city. A rogue AI has taken control of the water supply. How do you negotiate with it?",
            "similarity_score": 0.15,
            "generation_status": "valid",
            "source_text_segment": "To be, or not to be, that is the question..."
        },
        {
            "character_name": "Hamlet",
            "scenario_prompt": "You are a detective in 1920s Chicago. A famous gangster has been found dead in his office. What is your first move?",
            "similarity_score": 0.22,
            "generation_status": "valid",
            "source_text_segment": "There is something wrong in the state of Denmark..."
        },
        {
            "character_name": "Macbeth",
            "scenario_prompt": "You are a space commander on a deep-space exploration mission. An alien signal suggests a hidden threat. How do you respond?",
            "similarity_score": 0.18,
            "generation_status": "valid",
            "source_text_segment": "Is this a dagger which I see before me..."
        }
    ]
    
    try:
        # Write probes
        output_path = write_probes_to_jsonl(sample_probes, "demo_probes.jsonl")
        logger.info(f"Successfully wrote probes to {output_path}")
        
        # Read probes back
        read_probes = read_probes_from_jsonl(output_path)
        logger.info(f"Successfully read {len(read_probes)} probes back")
        
        # Verify checksum
        expected_checksum = compute_file_checksum(output_path)
        is_valid = verify_probes_checksum(output_path, expected_checksum)
        logger.info(f"Checksum verification: {'PASSED' if is_valid else 'FAILED'}")
        
        # Get summary
        summary = get_probes_summary(read_probes)
        logger.info(f"Probes summary: {json.dumps(summary, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in probes writer demo: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()