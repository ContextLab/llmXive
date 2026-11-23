"""
T003a: Generate the trajectory schema file.

This script generates the contracts/trajectory.schema.yaml file defining
the schema for AgenticSTS trajectories. The schema is used for validation
in T005b-verify and T006a.

The schema is hardcoded in this module to ensure consistency and reproducibility.
"""
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCHEMA_CONTENT = """$schema: http://json-schema.org/draft-07/schema#
title: AgenticSTS Trajectory Schema
description: |
  Schema for AgenticSTS agent trajectories. Defines the structure for
  trajectory_id, turn sequence, legal moves, state metrics, and metadata.
  Used for validation of raw JSONL inputs in T005b-verify and T006a.
type: object
required:
  - trajectory_id
  - turns
properties:
  trajectory_id:
    type: string
    description: Unique identifier for the trajectory.
    pattern: "^traj_[a-zA-Z0-9]+$"
  
  initial_state_hash:
    type: string
    description: SHA256 hash of the initial game state to ensure deterministic replay.
    pattern: "^[a-f0-9]{64}$"
  
  agent_name:
    type: string
    description: Name of the agent that generated this trajectory.
  
  environment:
    type: string
    description: Environment identifier (e.g., "gym-minesweeper").
  
  total_turns:
    type: integer
    description: Total number of turns in the trajectory.
    minimum: 1
  
  turns:
    type: array
    description: Ordered list of turns in the trajectory.
    minItems: 1
    items:
type: object
required:
  - turn
  - action
  - legal_moves
  - state_metrics
properties:
  turn:
    type: integer
    description: Turn index (0-based).
    minimum: 0
  
  action:
    type: string
    description: The action taken by the agent.
  
  legal_moves:
    type: array
    description: List of legal moves available at this turn.
    items:
      type: string
    minItems: 1
  
  state_metrics:
    type: object
    description: Metrics extracted from the game state at this turn.
    required:
      - health_ratio
      - enemy_threat
      - deck_size
    properties:
      health_ratio:
        type: number
        description: Ratio of current health to max health (0.0 to 1.0).
        minimum: 0.0
        maximum: 1.0
      
      enemy_threat:
        type: number
        description: Normalized threat level from enemies (0.0 to 1.0).
        minimum: 0.0
        maximum: 1.0
      
      deck_size:
        type: integer
        description: Number of cards/items remaining in the deck.
        minimum: 0
      
      move_entropy:
        type: number
        description: Shannon entropy of the legal move distribution.
        minimum: 0.0
        nullable: true
        description: |
          Calculated as -sum(p * log2(p)) where p is the probability
          of each legal move. May be null if calculation failed.
  
  memory_layers_used:
    type: array
    description: Names of memory layers retrieved for this turn.
    items:
      type: string
  
  tokens_used:
    type: integer
    description: Number of tokens used in the prompt for this turn.
    minimum: 0
  
outcome:
  type: object
  description: Final outcome of the trajectory.
  required:
    - win
    - final_state_hash
  properties:
    win:
type: boolean
description: Whether the agent won the game.
    
    final_state_hash:
type: string
description: SHA256 hash of the final game state.
pattern: "^[a-f0-9]{64}$"
    
    turns_played:
type: integer
description: Number of turns played until termination.
minimum: 1
"""

def main():
    """Generate the trajectory schema file."""
    project_root = Path(__file__).resolve().parent.parent
    contracts_dir = project_root / "contracts"
    schema_path = contracts_dir / "trajectory.schema.yaml"

    # Ensure contracts directory exists
    contracts_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating schema at: {schema_path}")
    
    # Write the schema content
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(SCHEMA_CONTENT)
    
    logger.info(f"Schema successfully written to {schema_path}")
    logger.info(f"Schema size: {schema_path.stat().st_size} bytes")

    # Verify the file was written
    if schema_path.exists():
        logger.info("Verification: Schema file exists.")
    else:
        logger.error("Verification failed: Schema file does not exist.")
        raise RuntimeError("Failed to write schema file")

if __name__ == "__main__":
    main()