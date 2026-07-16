"""
Writer module for storing validated character axis definitions.

Implements T013: Create data/derived/axes.jsonl writer to store validated axis definitions.
This module consumes validated axis data from the axis_generator and writes it to the
derived data store in JSONL format.
"""
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.lib.state_tracker import log_experiment_state, update_run_status
from src.lib.utils import get_logger

logger = get_logger(__name__)

DERIVED_DATA_DIR = Path("data/derived")
AXES_OUTPUT_FILE = DERIVED_DATA_DIR / "axes.jsonl"
AXES_CHECKSUM_FILE = DERIVED_DATA_DIR / "axes.sha256"


def ensure_derived_directory():
    """Ensure the derived data directory exists."""
    DERIVED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured derived data directory exists: {DERIVED_DATA_DIR}")


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal SHA-256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def write_axes_to_jsonl(
    axes: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    run_id: Optional[str] = None
) -> Path:
    """
    Write validated axis definitions to a JSONL file.
    
    Each line in the output file is a complete JSON object representing a validated
    axis entry (containing character, coarse, fine, validation metadata, etc.).
    
    Args:
        axes: List of validated axis dictionaries to write.
        output_path: Optional custom output path. Defaults to data/derived/axes.jsonl.
        run_id: Optional run ID for state tracking.
        
    Returns:
        Path to the written file.
        
    Raises:
        ValueError: If axes list is empty or contains invalid entries.
        IOError: If file cannot be written.
    """
    if not axes:
        raise ValueError("Cannot write empty axes list to JSONL file.")
    
    output_path = output_path or AXES_OUTPUT_FILE
    ensure_derived_directory()
    
    logger.info(f"Writing {len(axes)} axis definitions to {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, axis_entry in enumerate(axes):
            if not isinstance(axis_entry, dict):
                raise ValueError(f"Axis entry at index {idx} is not a dictionary: {type(axis_entry)}")
            
            # Ensure required metadata is present
            if "timestamp" not in axis_entry:
                axis_entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            if "version" not in axis_entry:
                axis_entry["version"] = "1.0"
            
            # Serialize to JSON line
            json_line = json.dumps(axis_entry, ensure_ascii=False, sort_keys=True)
            f.write(json_line + "\n")
    
    logger.info(f"Successfully wrote {len(axes)} entries to {output_path}")
    
    # Compute and store checksum
    checksum = compute_file_checksum(output_path)
    checksum_path = output_path.parent / f"{output_path.stem}.sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {output_path.name}\n")
    logger.info(f"Computed and stored SHA-256 checksum: {checksum}")
    
    # Update state tracker if run_id provided
    if run_id:
        update_run_status(run_id, "axes_written", {
            "file_path": str(output_path),
            "entry_count": len(axes),
            "checksum": checksum
        })
    
    return output_path


def read_axes_from_jsonl(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Read axis definitions from a JSONL file.
    
    Args:
        input_path: Optional custom input path. Defaults to data/derived/axes.jsonl.
        
    Returns:
        List of axis dictionaries.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        json.JSONDecodeError: If a line is not valid JSON.
    """
    input_path = input_path or AXES_OUTPUT_FILE
    
    if not input_path.exists():
        raise FileNotFoundError(f"Axes file not found: {input_path}")
    
    axes = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                axes.append(entry)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON on line {line_num}: {e}")
                raise
    
    logger.info(f"Read {len(axes)} axis entries from {input_path}")
    return axes


def verify_axes_checksum(input_path: Optional[Path] = None) -> bool:
    """
    Verify the integrity of the axes file using its stored checksum.
    
    Args:
        input_path: Optional custom input path. Defaults to data/derived/axes.jsonl.
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If file or checksum file does not exist.
    """
    input_path = input_path or AXES_OUTPUT_FILE
    checksum_path = input_path.parent / f"{input_path.stem}.sha256"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Axes file not found: {input_path}")
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    # Read stored checksum
    with open(checksum_path, "r", encoding="utf-8") as f:
        stored_checksum_line = f.read().strip()
    
    # Parse stored checksum (format: "<hash>  <filename>")
    stored_checksum = stored_checksum_line.split()[0]
    
    # Compute current checksum
    current_checksum = compute_file_checksum(input_path)
    
    match = stored_checksum == current_checksum
    if match:
        logger.info(f"Checksum verification passed: {current_checksum}")
    else:
        logger.error(f"Checksum mismatch! Stored: {stored_checksum}, Current: {current_checksum}")
    
    return match


def get_axes_summary(axes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary statistics dictionary for a list of axes.
    
    Args:
        axes: List of axis dictionaries.
        
    Returns:
        Dictionary containing summary statistics.
    """
    if not axes:
        return {"count": 0}
    
    characters = set()
    coarse_types = set()
    fine_types = set()
    valid_count = 0
    invalid_count = 0
    
    for entry in axes:
        if "character" in entry:
            characters.add(entry["character"])
        if "coarse" in entry and isinstance(entry["coarse"], dict):
            coarse_types.add(entry["coarse"].get("type", "unknown"))
        if "fine" in entry and isinstance(entry["fine"], dict):
            fine_types.add(entry["fine"].get("type", "unknown"))
        
        # Check validation status
        validation = entry.get("validation", {})
        if validation.get("passed", False):
            valid_count += 1
        else:
            invalid_count += 1
    
    return {
        "total_count": len(axes),
        "unique_characters": len(characters),
        "character_list": sorted(list(characters)),
        "coarse_types": sorted(list(coarse_types)),
        "fine_types": sorted(list(fine_types)),
        "valid_count": valid_count,
        "invalid_count": invalid_count
    }


def main():
    """
    CLI entry point for testing the axes writer.
    
    This function demonstrates writing sample validated axes to the JSONL file
    and verifying the checksum.
    """
    import sys
    
    # Sample validated axes data (in production, this comes from axis_generator)
    sample_axes = [
        {
            "character": "Hamlet",
            "coarse": {
                "type": "Tragic Hero",
                "description": "A prince of Denmark who seeks revenge but is plagued by indecision and existential doubt.",
                "dimensions": ["Indecision", "Melancholy", "Intellect"]
            },
            "fine": {
                "type": "Moral Ambiguity",
                "description": "Struggles between action and inaction, driven by conflicting moral imperatives.",
                "source_segment": "Act 3, Scene 1 - To be or not to be soliloquy",
                "dimensions": ["Hesitation", "Self-Loathing", "Philosophical Detachment"]
            },
            "validation": {
                "lexical_overlap": 0.12,
                "semantic_similarity": 0.65,
                "passed": True
            },
            "metadata": {
                "created_by": "researcher_01",
                "notes": "Initial axis definition for Act 1 analysis"
            }
        },
        {
            "character": "Lady Macbeth",
            "coarse": {
                "type": "Ambitious Antagonist",
                "description": "A woman driven by unchecked ambition who manipulates her husband to seize power.",
                "dimensions": ["Ambition", "Manipulation", "Guilt"]
            },
            "fine": {
                "type": "Psychological Disintegration",
                "description": "Progressive mental collapse following the murder of Duncan, manifesting as sleepwalking and hallucinations.",
                "source_segment": "Act 5, Scene 1 - Sleepwalking scene",
                "dimensions": ["Paranoia", "Obsessive Guilt", "Loss of Control"]
            },
            "validation": {
                "lexical_overlap": 0.08,
                "semantic_similarity": 0.58,
                "passed": True
            },
            "metadata": {
                "created_by": "researcher_01",
                "notes": "Axis definition for psychological arc analysis"
            }
        }
    ]
    
    try:
        output_path = write_axes_to_jsonl(sample_axes, run_id="T013_demo")
        print(f"Successfully wrote axes to: {output_path}")
        
        # Verify checksum
        if verify_axes_checksum(output_path):
            print("Checksum verification: PASSED")
        else:
            print("Checksum verification: FAILED")
            sys.exit(1)
        
        # Print summary
        summary = get_axes_summary(sample_axes)
        print(f"\nAxes Summary:")
        print(f"  Total entries: {summary['total_count']}")
        print(f"  Unique characters: {summary['unique_characters']}")
        print(f"  Characters: {', '.join(summary['character_list'])}")
        print(f"  Valid: {summary['valid_count']}, Invalid: {summary['invalid_count']}")
        
    except Exception as e:
        logger.error(f"Error writing axes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
