"""
T003b: Generate Mock Trajectories (DEV ONLY)

This script generates a deterministic, small JSONL file of mock trajectories
matching the schema defined in contracts/trajectory.schema.yaml.

CONSTRAINT: This task runs ONLY if DEV_MODE=true.
OUTPUT: data/fixtures/mock_trajectories.jsonl
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dev_mode():
    """Check if DEV_MODE environment variable is set to 'true'."""
    dev_mode = os.environ.get('DEV_MODE', '').lower()
    if dev_mode != 'true':
        raise RuntimeError(
            "DEV_MODE is not set to 'true'. Mock data generation is restricted to development environments. "
            "Set DEV_MODE=true to proceed."
        )
    logger.info("DEV_MODE is active. Proceeding with mock data generation.")
    return True

def load_schema_fields():
    """
    Load the schema definition from the contracts directory to ensure
    the mock data matches the expected fields.
    """
    schema_path = Path("contracts/trajectory.schema.yaml")
    if not schema_path.exists():
        # Fallback to a hardcoded schema if the file is missing,
        # but log a warning. This ensures the script can run even if T003a
        # hasn't physically written the file yet in a test environment,
        # though the spec says it depends on T003a.
        logger.warning(f"Schema file {schema_path} not found. Using default schema definition.")
        return [
            "trajectory_id", "turn", "legal_moves", "win", "loss",
            "initial_state_hash", "layer_utility", "context_tokens"
        ]

    try:
        # Simple YAML parsing without external dependency if possible,
        # but since T002 installs pyyaml, we can use it.
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Extract field names based on common schema structures
        # Assuming the schema has a 'properties' or 'fields' key
        if 'properties' in schema:
            return list(schema['properties'].keys())
        elif 'fields' in schema:
            return [f['name'] for f in schema['fields']]
        else:
            logger.warning("Could not parse schema fields. Using defaults.")
            return [
                "trajectory_id", "turn", "legal_moves", "win", "loss",
                "initial_state_hash", "layer_utility", "context_tokens"
            ]
    except Exception as e:
        logger.warning(f"Error reading schema: {e}. Using defaults.")
        return [
            "trajectory_id", "turn", "legal_moves", "win", "loss",
            "initial_state_hash", "layer_utility", "context_tokens"
        ]

def generate_hash(seed_data: str) -> str:
    """Generate a deterministic SHA256 hash for a given string."""
    return hashlib.sha256(seed_data.encode('utf-8')).hexdigest()

def create_mock_trajectories():
    """
    Create a small, deterministic set of mock trajectories.
    These are designed to match the schema and allow for pipeline testing
    without requiring real data.
    """
    schema_fields = load_schema_fields()
    
    # Define a small set of deterministic mock data
    # We create 5 trajectories with varying characteristics
    mock_data = []
    
    base_id = "mock_traj"
    
    for i in range(5):
        trajectory_id = f"{base_id}_{i:03d}"
        initial_state = f"state_seed_{i}"
        initial_state_hash = generate_hash(initial_state)
        
        # Generate a few turns per trajectory
        for turn in range(3):
            # Deterministic legal moves based on turn and trajectory id
            legal_moves = [f"move_{turn}_{j}" for j in range(2 + (i % 3))]
            
            # Determine win/loss based on trajectory id (deterministic)
            # Trajectories 0, 2 are wins; 1, 3, 4 are losses
            is_win = (i % 2 == 0)
            is_loss = not is_win
            
            # Context tokens estimation (deterministic)
            context_tokens = 256 + (turn * 64)
            
            # Layer utility (mock value)
            layer_utility = 0.5 + (turn * 0.1)
            
            record = {
                "trajectory_id": trajectory_id,
                "turn": turn,
                "legal_moves": legal_moves,
                "win": is_win,
                "loss": is_loss,
                "initial_state_hash": initial_state_hash,
                "layer_utility": round(layer_utility, 4),
                "context_tokens": context_tokens,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Ensure we only include fields present in the schema if possible,
            # but keep the core ones required by the task description.
            filtered_record = {k: v for k, v in record.items() if k in schema_fields}
            # Always ensure core task fields are present
            for core_field in ["trajectory_id", "turn", "legal_moves", "win", "loss", "initial_state_hash"]:
                if core_field not in filtered_record:
                    filtered_record[core_field] = record[core_field]
            
            mock_data.append(filtered_record)

    return mock_data

def main():
    """Main entry point for T003b."""
    logger.info("Starting T003b: Generate Mock Trajectories")
    
    # Check DEV_MODE
    try:
        check_dev_mode()
    except RuntimeError as e:
        logger.error(str(e))
        return 1

    # Ensure output directory exists
    output_dir = Path("data/fixtures")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "mock_trajectories.jsonl"

    logger.info(f"Generating mock trajectories to {output_file}")
    
    mock_trajectories = create_mock_trajectories()
    
    with open(output_file, 'w') as f:
        for record in mock_trajectories:
            f.write(json.dumps(record) + '\n')
    
    logger.info(f"Successfully generated {len(mock_trajectories)} mock trajectory records.")
    logger.info(f"Output written to: {output_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())
