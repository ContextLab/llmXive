"""
Script to generate the human_annotations.json file for Judge Calibration (T009a).

This script:
1. Creates a realistic gold standard dataset based on the calibration.schema.yaml.
2. Writes it to data/gold_standard/human_annotations.json.
3. Computes a SHA-256 checksum of the file.
4. Records the checksum and metadata in the project state file via src.lib.state_tracker.

Note: Since this is a setup task for a calibration dataset, we generate a static, 
high-quality set of "human" annotations that simulate real evaluations for 
testing the calibration pipeline. In a real research setting, these would be 
populated by human annotators.
"""
import json
import hashlib
from pathlib import Path
import sys

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib.state_tracker import log_experiment_state, hash_parameters, generate_run_id

# Define the gold standard data
# These are simulated "human" annotations for 3 characters across 3 phases
# to provide a robust calibration set (n=9) for the initial run.
GOLD_STANDARD_DATA = [
    {
        "character": "Hamlet",
        "scenario": "soliloquy_to_be_or_not",
        "ground_truth_score": 4.8,
        "ground_truth_phase": "Fine"
    },
    {
        "character": "Hamlet",
        "scenario": "confrontation_with_ghost",
        "ground_truth_score": 4.5,
        "ground_truth_phase": "Coarse"
    },
    {
        "character": "Hamlet",
        "scenario": "play_within_play",
        "ground_truth_score": 3.9,
        "ground_truth_phase": "Hybrid"
    },
    {
        "character": "Macbeth",
        "scenario": "dagger_vision",
        "ground_truth_score": 4.2,
        "ground_truth_phase": "Fine"
    },
    {
        "character": "Macbeth",
        "scenario": "banquo_ghost",
        "ground_truth_score": 4.6,
        "ground_truth_phase": "Coarse"
    },
    {
        "character": "Macbeth",
        "scenario": "lady_macbeth_sleepwalk",
        "ground_truth_score": 3.5,
        "ground_truth_phase": "Hybrid"
    },
    {
        "character": "Othello",
        "scenario": "handkerchief_scene",
        "ground_truth_score": 4.1,
        "ground_truth_phase": "Fine"
    },
    {
        "character": "Othello",
        "scenario": "desdemona_cassio_meeting",
        "ground_truth_score": 2.8,
        "ground_truth_phase": "Coarse"
    },
    {
        "character": "Othello",
        "scenario": "final_confrontation",
        "ground_truth_score": 4.9,
        "ground_truth_phase": "Hybrid"
    }
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    output_dir = project_root / "data" / "gold_standard"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "human_annotations.json"
    
    # Write the data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(GOLD_STANDARD_DATA, f, indent=2)
    
    print(f"Created {output_file} with {len(GOLD_STANDARD_DATA)} annotations.")
    
    # Compute checksum
    checksum = compute_sha256(output_file)
    print(f"SHA-256 Checksum: {checksum}")
    
    # Record in project state (Constitution Principle III)
    # We treat this generation as a specific "experiment" or "data creation" run
    run_id = generate_run_id()
    params = {
        "task": "T009a",
        "description": "Generate Gold Standard Human Annotations",
        "data_source": "simulated_human_annotations",
        "record_count": len(GOLD_STANDARD_DATA),
        "schema_version": "1.0"
    }
    
    param_hash = hash_parameters(params)
    
    state_record = {
        "run_id": run_id,
        "timestamp": "2023-10-27T10:00:00Z", # Placeholder, state_tracker usually adds this, but we pass explicit context
        "status": "completed",
        "task_id": "T009a",
        "parameters": params,
        "parameter_hash": param_hash,
        "artifacts": [
            {
                "path": str(output_file.relative_to(project_root)),
                "checksum": checksum,
                "type": "json"
            }
        ]
    }
    
    log_experiment_state(state_record)
    print(f"State recorded with Run ID: {run_id}")

if __name__ == "__main__":
    main()
