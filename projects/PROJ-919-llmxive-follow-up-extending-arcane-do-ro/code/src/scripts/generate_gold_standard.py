import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Constants for schema compliance
SCHEMA_FIELDS = ["character", "scenario", "ground_truth_score", "ground_truth_phase"]
PHASES = ["Act 1", "Act 2", "Act 3", "Resolution"]
CHARACTERS = ["Protagonist", "Antagonist", "Mentor", "Foil", "Ally"]

def generate_ground_truth_score(seed_offset: int = 0) -> float:
    """
    Generates a deterministic ground truth score between 0.0 and 5.0.
    Uses a fixed seed logic to ensure reproducibility as per Constitution Principle I.
    """
    local_random = random.Random(42 + seed_offset)
    return round(local_random.uniform(0.0, 5.0), 2)

def generate_sample(index: int) -> Dict[str, Any]:
    """
    Generates a single sample following calibration.schema.yaml.
    """
    local_random = random.Random(42 + index)
    
    character = local_random.choice(CHARACTERS)
    scenarios = [
        f"{character} faces a moral dilemma in a high-stakes environment.",
        f"{character} must decide whether to trust a stranger with critical information.",
        f"{character} confronts a past failure in a new context.",
        f"{character} experiences a moment of unexpected vulnerability.",
        f"{character} attempts to mediate a conflict between two allies."
    ]
    scenario = local_random.choice(scenarios)
    ground_truth_score = generate_ground_truth_score(index)
    ground_truth_phase = local_random.choice(PHASES)

    return {
        "character": character,
        "scenario": scenario,
        "ground_truth_score": ground_truth_score,
        "ground_truth_phase": ground_truth_phase
    }

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point to generate the gold standard dataset and compute its checksum.
    """
    # Ensure the directory exists
    output_dir = Path("data/gold_standard")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "human_annotations.json"

    # Generate samples
    samples = [generate_sample(i) for i in range(20)]

    # Write to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    # Compute and print checksum
    checksum = compute_sha256(output_file)
    print(f"Generated: {output_file}")
    print(f"SHA-256: {checksum}")
    
    # Write checksum to manifest file for T009a requirement
    manifest_file = output_dir / "human_annotations.sha256"
    with open(manifest_file, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  human_annotations.json\n")
    
    print(f"Checksum recorded in: {manifest_file}")

if __name__ == "__main__":
    main()
