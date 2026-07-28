import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure we are using the project's relative imports structure
# If this file is run directly, we need to add the parent 'code' to path
# but usually this is imported by the CLI or runner.
# The API surface indicates this file exists at code/src/services/axes_writer.py

DERIVED_DIR = Path("data/derived")
AXES_FILE = DERIVED_DIR / "axes.jsonl"

def ensure_derived_directory():
    """Creates the data/derived directory if it does not exist."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(filepath: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_axes_to_jsonl(axes_data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Writes a list of axis definitions to a JSONL file.
    
    Args:
        axes_data: List of dictionaries containing 'character', 'coarse', 'fine', 
                   and validation metadata.
        output_path: Optional path to write to. Defaults to data/derived/axes.jsonl.
    
    Returns:
        The path to the written file.
    """
    if output_path is None:
        ensure_derived_directory()
        output_path = AXES_FILE
    
    with open(output_path, "w", encoding="utf-8") as f:
        for record in axes_data:
            # Ensure the record is serializable
            json_line = json.dumps(record, ensure_ascii=False)
            f.write(json_line + "\n")
    
    return output_path

def read_axes_from_jsonl(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Reads axes definitions from a JSONL file.
    
    Args:
        input_path: Optional path to read from. Defaults to data/derived/axes.jsonl.
    
    Returns:
        List of axis dictionaries.
    """
    if input_path is None:
        input_path = AXES_FILE
    
    if not input_path.exists():
        return []
    
    axes = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                axes.append(json.loads(line))
    return axes

def verify_axes_checksum(filepath: Optional[Path] = None, expected_checksum: Optional[str] = None) -> bool:
    """
    Verifies the checksum of the axes file against an expected value.
    
    Args:
        filepath: Path to the file. Defaults to data/derived/axes.jsonl.
        expected_checksum: The expected SHA-256 hash string.
    
    Returns:
        True if checksums match, False otherwise.
    """
    if filepath is None:
        filepath = AXES_FILE
    
    if not filepath.exists():
        return False
    
    actual_checksum = compute_file_checksum(filepath)
    if expected_checksum is None:
        # If no expected checksum provided, just verify we can compute one
        return True
    
    return actual_checksum == expected_checksum

def get_axes_summary(axes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a summary of the axes data.
    
    Args:
        axes_data: List of axis dictionaries.
    
    Returns:
        Dictionary with summary statistics.
    """
    if not axes_data:
        return {
            "total_count": 0,
            "characters": [],
            "validation_pass_rate": 0.0
        }
    
    characters = set()
    passed_validation = 0
    
    for record in axes_data:
        if "character" in record:
            characters.add(record["character"])
        # Check for validation status if present
        if record.get("validation_passed", False):
            passed_validation += 1
    
    return {
        "total_count": len(axes_data),
        "unique_characters": list(characters),
        "validation_pass_rate": passed_validation / len(axes_data) if axes_data else 0.0,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """
    Entry point for testing the axes writer functionality.
    This function demonstrates writing and reading axes data.
    """
    # Sample data mimicking what would come from axis_generator
    sample_axes = [
        {
            "character": "Hamlet",
            "coarse": {
                "name": "Existential Anxiety",
                "description": "High levels of existential dread and contemplation of mortality."
            },
            "fine": {
                "name": "Indecision due to Over-analysis",
                "description": "Tendency to delay action when faced with moral ambiguity."
            },
            "validation": {
                "lexical_overlap": 0.12,
                "semantic_similarity": 0.25,
                "passed": True
            },
            "timestamp": datetime.now().isoformat()
        },
        {
            "character": "Lady Macbeth",
            "coarse": {
                "name": "Ambition",
                "description": "Intense drive for power and status, often overriding moral constraints."
            },
            "fine": {
                "name": "Guilt-induced Paranoia",
                "description": "Psychological deterioration manifesting as hallucinations and sleepwalking."
            },
            "validation": {
                "lexical_overlap": 0.05,
                "semantic_similarity": 0.18,
                "passed": True
            },
            "timestamp": datetime.now().isoformat()
        }
    ]

    print("Writing sample axes to data/derived/axes.jsonl...")
    output_path = write_axes_to_jsonl(sample_axes)
    print(f"Written to: {output_path}")

    # Verify checksum
    checksum = compute_file_checksum(output_path)
    print(f"Checksum: {checksum}")

    # Read back and verify
    read_data = read_axes_from_jsonl(output_path)
    summary = get_axes_summary(read_data)
    
    print(f"Read back {summary['total_count']} records.")
    print(f"Unique characters: {summary['unique_characters']}")
    print(f"Validation pass rate: {summary['validation_pass_rate']:.2%}")

    # Verify checksum matches
    if verify_axes_checksum(output_path, checksum):
        print("Checksum verification: PASSED")
    else:
        print("Checksum verification: FAILED")

if __name__ == "__main__":
    main()
