"""
Deterministic Data Simulator for CI Validation.

This module implements a rule-based simulator to generate synthetic session data
for pipeline testing (CI/CD, local dev). It is STRICTLY FOR VALIDATION PURPOSES
and MUST NOT be used for final research claims or human participant data collection.

The simulator enforces a deterministic effect size:
- Explainable interface completion_time = baseline_time - fixed_offset
- Traditional interface completion_time = baseline_time

It validates output against the session schema before writing.
"""

import argparse
import json
import os
import sys
import uuid
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import random
import numpy as np

# Import schema validation logic from existing modules
# Note: T031b ensures this validation is strict
from simulator.validator import load_schema, validate_session as validate_session_func
from utils.seed import set_seed
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for deterministic simulation
BASELINE_COMPLETION_TIME = 120.0  # seconds
FIXED_OFFSET = 15.0  # Explainable is faster by 15 seconds
NOISE_SCALE = 5.0  # Gaussian noise standard deviation
BASELINE_ERROR_COUNT = 2.0
ERROR_NOISE_SCALE = 1.0
BASELINE_SUS = 75.0
SUS_NOISE_SCALE = 3.0
EXPLAINABLE_ENGAGEMENT_BASE = 5.0  # seconds
EXPLAINABLE_ENGAGEMENT_NOISE = 1.0

class SessionData:
    """Dataclass-like structure for a simulated session."""
    def __init__(
        self,
        participant_id: str,
        disability_type: str,
        interface_type: str,
        sequence: str,
        start_time: str,
        end_time: str,
        error_count: int,
        explanation_engagement_time_seconds: float,
        sus_score: int,
        status: str,
        completion_time_seconds: float,
        dropout_reason: Optional[str] = None
    ):
        self.participant_id = participant_id
        self.disability_type = disability_type
        self.interface_type = interface_type
        self.sequence = sequence
        self.start_time = start_time
        self.end_time = end_time
        self.error_count = error_count
        self.explanation_engagement_time_seconds = explanation_engagement_time_seconds
        self.sus_score = sus_score
        self.status = status
        self.completion_time_seconds = completion_time_seconds
        self.dropout_reason = dropout_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "disability_type": self.disability_type,
            "interface_type": self.interface_type,
            "sequence": self.sequence,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_count": self.error_count,
            "explanation_engagement_time_seconds": self.explanation_engagement_time_seconds,
            "sus_score": self.sus_score,
            "status": self.status,
            "dropout_reason": self.dropout_reason,
            "completion_time_seconds": self.completion_time_seconds
        }

class DeterministicDataSimulator:
    """
    Generates deterministic synthetic session data for CI validation.

    CRITICAL WARNING:
    This tool is ONLY for CI/pilot testing and NOT a replacement for the
    web-based simulator required by FR-007 for human participants.
    Do NOT use this for human participant data collection.
    """

    def __init__(self, n_participants: int, seed: int, schema_path: str):
        self.n_participants = n_participants
        self.seed = seed
        self.schema_path = schema_path
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        
        # Load schema for validation
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}. "
                                  "Ensure T019b (contracts/session.schema.yaml) is complete.")
        self.schema = load_schema(schema_path)

    def _generate_base_time(self, interface_type: str) -> float:
        """Generate completion time based on interface type with fixed offset."""
        noise = self.np_rng.normal(0, NOISE_SCALE)
        if interface_type == "explainable":
            return max(10.0, BASELINE_COMPLETION_TIME - FIXED_OFFSET + noise)
        else:
            return max(10.0, BASELINE_COMPLETION_TIME + noise)

    def _generate_error_count(self, interface_type: str) -> int:
        """Generate error count with slight variance."""
        noise = self.np_rng.normal(0, ERROR_NOISE_SCALE)
        if interface_type == "explainable":
            # Slightly fewer errors for explainable
            val = BASELINE_ERROR_COUNT - 0.5 + noise
        else:
            val = BASELINE_ERROR_COUNT + noise
        return max(0, int(round(val)))

    def _generate_sus_score(self, interface_type: str) -> int:
        """Generate SUS score."""
        noise = self.np_rng.normal(0, SUS_NOISE_SCALE)
        if interface_type == "explainable":
            val = BASELINE_SUS + 2.0 + noise # Slightly higher SUS
        else:
            val = BASELINE_SUS + noise
        return max(0, min(100, int(round(val))))

    def _generate_engagement_time(self, interface_type: str) -> float:
        """Generate explanation engagement time."""
        if interface_type == "explainable":
            return max(0.1, self.np_rng.normal(EXPLAINABLE_ENGAGEMENT_BASE, EXPLAINABLE_ENGAGEMENT_NOISE))
        else:
            return 0.0

    def generate_sessions(self) -> List[Dict[str, Any]]:
        """
        Generate N sessions (2 per participant: Traditional + Explainable).
        Returns a list of validated session dictionaries.
        """
        sessions = []
        disability_types = ["visual", "motor", "cognitive"]
        
        # Counterbalancing: 50% start with Traditional, 50% with Explainable
        # For simplicity in this deterministic sim, we alternate
        
        start_base = datetime(2023, 1, 1, 10, 0, 0)

        for i in range(self.n_participants):
            participant_id = f"P{str(i+1).zfill(3)}"
            disability = self.rng.choice(disability_types)
            
            # Determine sequence
            if i % 2 == 0:
                sequence = "traditional_explainable"
                order = ["traditional", "explainable"]
            else:
                sequence = "explainable_traditional"
                order = ["explainable", "traditional"]

            current_time = start_base + timedelta(minutes=i*30)

            for idx, iface_type in enumerate(order):
                # Generate metrics
                completion_time = self._generate_base_time(iface_type)
                error_count = self._generate_error_count(iface_type)
                sus_score = self._generate_sus_score(iface_type)
                engagement = self._generate_engagement_time(iface_type)
                
                # Simulate duration (completion_time + some overhead)
                duration = timedelta(seconds=completion_time + 10) 
                end_time = current_time + duration

                session_data = SessionData(
                    participant_id=participant_id,
                    disability_type=disability,
                    interface_type=iface_type,
                    sequence=sequence,
                    start_time=current_time.isoformat(),
                    end_time=end_time.isoformat(),
                    error_count=error_count,
                    explanation_engagement_time_seconds=engagement,
                    sus_score=sus_score,
                    status="complete",
                    completion_time_seconds=completion_time,
                    dropout_reason=None
                )

                session_dict = session_data.to_dict()

                # T031b: Strict Schema Validation
                if not validate_session_func(session_dict, self.schema):
                    logger.error(f"Generated session for {participant_id} ({iface_type}) failed schema validation.")
                    raise ValueError(f"Schema validation failed for session: {session_dict}")

                sessions.append(session_dict)
                current_time = end_time

        return sessions

def main():
    parser = argparse.ArgumentParser(description="Deterministic Data Simulator for CI Validation")
    parser.add_argument("--n", type=int, default=50, help="Number of participants to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/raw/simulated_sessions.json",
                      help="Output JSON file path")
    parser.add_argument("--schema", type=str, default="contracts/session.schema.yaml",
                      help="Path to the JSON schema for validation")
    
    args = parser.parse_args()

    logger.info(f"Starting simulation: N={args.n}, Seed={args.seed}")
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        simulator = DeterministicDataSimulator(
            n_participants=args.n,
            seed=args.seed,
            schema_path=args.schema
        )
        
        sessions = simulator.generate_sessions()
        
        with open(output_path, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        logger.info(f"Successfully generated {len(sessions)} sessions to {args.output}")
        logger.info(f"Expected effect: Explainable completion time ~{BASELINE_COMPLETION_TIME - FIXED_OFFSET}s, "
                    f"Traditional ~{BASELINE_COMPLETION_TIME}s")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()