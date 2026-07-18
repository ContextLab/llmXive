import argparse
import json
import os
import sys
import uuid
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
import jsonschema.exceptions

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.seed import set_seed

logger = get_logger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "session.schema.yaml"

class SessionData:
    def __init__(self, participant_id: str, disability_type: str, interface_type: str, sequence: List[str],
                 start_time: str, end_time: str, error_count: int, explanation_engagement_time_seconds: float,
                 sus_score: int, status: str, dropout_reason: Optional[str] = None):
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
            "dropout_reason": self.dropout_reason
        }

def load_schema(schema_path: Path) -> Dict[str, Any]:
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_session_against_schema(session_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    try:
        jsonschema.validate(instance=session_data, schema=schema)
        logger.info("Session data validated successfully against schema.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        raise ValueError(f"Session data does not match schema: {e.message}")

class DeterministicDataSimulator:
    def __init__(self, n_participants: int, seed: int, output_path: str):
        self.n_participants = n_participants
        self.seed = seed
        self.output_path = output_path
        self.schema = None
        set_seed(seed)
        import random
        self.random = random.Random(seed)
        import numpy as np
        self.np = np
        self.np.random.seed(seed)

    def load_schema(self):
        if not SCHEMA_PATH.exists():
            logger.error(f"CRITICAL: Schema file missing at {SCHEMA_PATH}. Cannot validate simulator output.")
            sys.exit(1)
        self.schema = load_schema(SCHEMA_PATH)
        logger.info(f"Loaded schema from {SCHEMA_PATH}")

    def generate_session(self, participant_idx: int) -> SessionData:
        # Deterministic parameters for effect size
        baseline_time = 120.0  # seconds
        fixed_offset = 15.0    # Explainable is faster by 15s
        noise_scale = 5.0

        # Determine interface type for this session (simplified: alternating or random)
        # For deterministic testing, we assume one session per participant for the "Explainable" condition
        # In a full study, we'd use the counterbalancer. Here we generate one record per participant for the "Explainable" condition
        # to verify the pipeline.
        interface_type = "explainable"
        sequence = ["traditional", "explainable"] # Assuming standard sequence for simulation

        # Calculate metrics
        # Traditional: baseline + noise
        # Explainable: baseline - offset + noise
        if interface_type == "explainable":
            completion_time = max(0.1, baseline_time - fixed_offset + self.random.gauss(0, noise_scale))
            # Explanation engagement must be positive for explainable
            engagement_time = max(1.0, self.random.uniform(5.0, 30.0))
            sus_score = int(max(0, min(100, 75 + self.random.gauss(0, 5))))
        else:
            completion_time = max(0.1, baseline_time + self.random.gauss(0, noise_scale))
            engagement_time = 0.0
            sus_score = int(max(0, min(100, 65 + self.random.gauss(0, 5))))

        error_count = max(0, int(self.random.gauss(2, 1)))
        sus_score = max(0, min(100, sus_score))

        from datetime import datetime, timedelta
        start = datetime(2023, 1, 1, 10, 0, 0) + timedelta(minutes=participant_idx * 15)
        end = start + timedelta(seconds=completion_time)

        return SessionData(
            participant_id=f"P{participant_idx:03d}",
            disability_type="motor", # Fixed for simulation
            interface_type=interface_type,
            sequence=sequence,
            start_time=start.isoformat(),
            end_time=end.isoformat(),
            error_count=error_count,
            explanation_engagement_time_seconds=engagement_time,
            sus_score=sus_score,
            status="complete",
            dropout_reason=None
        )

    def run(self):
        self.load_schema()
        sessions = []
        
        logger.info(f"Generating {self.n_participants} simulated sessions with seed {self.seed}...")
        
        for i in range(self.n_participants):
            session = self.generate_session(i)
            session_dict = session.to_dict()
            
            # CRITICAL: Validate against schema before adding
            if not validate_session_against_schema(session_dict, self.schema):
                logger.error("Validation failed for session. Aborting simulation.")
                sys.exit(1)
            
            sessions.append(session_dict)

        # Ensure output directory exists
        output_dir = os.path.dirname(self.output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(self.output_path, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        logger.info(f"Successfully wrote {len(sessions)} sessions to {self.output_path}")
        return sessions

def main():
    parser = argparse.ArgumentParser(description="Deterministic Data Simulator for US1")
    parser.add_argument("--n", type=int, default=50, help="Number of participants to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/raw/simulated_sessions.json", help="Output JSON path")
    
    args = parser.parse_args()
    
    simulator = DeterministicDataSimulator(n_participants=args.n, seed=args.seed, output_path=args.output)
    simulator.run()

if __name__ == "__main__":
    main()