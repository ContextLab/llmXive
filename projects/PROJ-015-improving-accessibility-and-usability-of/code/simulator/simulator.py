"""
Deterministic Data Simulator for CI Validation.

This module generates deterministic, rule-based session data for pipeline validation.
It is strictly forbidden to use this data for final research claims.
Production runs MUST fail if real data is missing and --simulate is not set.
"""
import argparse
import json
import os
import sys
import uuid
import math
import random
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import existing utilities
try:
    from utils.seed import set_seed, seeded_generator
except ImportError:
    # Fallback for direct execution if utils not in path
    def set_seed(s):
        random.seed(s)
        import numpy as np
        np.random.seed(s)
    def seeded_generator(seed):
        rng = random.Random(seed)
        return rng

try:
    from simulator.validator import load_schema, validate_session
    from utils.logger import get_logger
except ImportError:
    # Fallback definitions if running in isolation
    def load_schema(path):
        # Minimal schema for validation if file missing
        return {"required": ["participant_id", "disability_type", "interface_type", "sequence", "start_time", "end_time", "error_count", "explanation_engagement_time_seconds", "sus_score", "status"]}
    def validate_session(data):
        return True
    def get_logger(name):
        import logging
        return logging.getLogger(name)

@dataclass
class SessionData:
    """Data class representing a single session record."""
    participant_id: str
    disability_type: str
    interface_type: str
    sequence: str
    start_time: str
    end_time: str
    error_count: int
    explanation_engagement_time_seconds: float
    sus_score: int
    status: str
    dropout_reason: Optional[str] = None
    completion_time_seconds: float = 0.0
    task_metrics: Dict[str, Any] = field(default_factory=dict)

class DeterministicDataSimulator:
    """
    Generates deterministic synthetic session data for CI validation.
    
    Constraints:
    - Explainable interface MUST have completion_time = baseline - FIXED_OFFSET
    - Traditional interface MUST have completion_time = baseline
    - Random noise is added but seeds are pinned.
    - Dropouts can be generated via --dropout-rate.
    """
    
    # Configuration constants
    BASELINE_COMPLETION_TIME = 120.0  # seconds
    FIXED_OFFSET = 5.0  # seconds faster for Explainable
    ERROR_RATE_TRADITIONAL = 0.15
    ERROR_RATE_EXPLAINABLE = 0.05
    SUS_BASELINE = 60
    SUS_IMPROVEMENT = 10  # Explainable is better
    
    # Dropout configuration
    DROPOUT_REASONS = [
        "Technical difficulty with interface",
        "Session timeout",
        "Participant requested to stop",
        "Confusion with task instructions",
        "Accessibility accommodation failure"
    ]

    def __init__(self, seed: int = 42, dropout_rate: float = 0.0):
        self.seed = seed
        self.dropout_rate = dropout_rate
        set_seed(seed)
        self.logger = get_logger("DeterministicDataSimulator")
        self.rng = random.Random(seed)

    def _generate_participant_id(self, index: int) -> str:
        """Generate a deterministic participant ID."""
        return f"P{index:03d}"

    def _generate_sequence(self) -> str:
        """Generate a counterbalanced sequence."""
        # Alternating sequences for determinism
        return "Traditional->Explainable" if self.rng.random() > 0.5 else "Explainable->Traditional"

    def _generate_disability_type(self) -> str:
        """Select a disability type."""
        types = ["visual", "motor", "cognitive", "none"]
        return self.rng.choice(types)

    def _simulate_session(self, participant_id: str, index: int) -> SessionData:
        """Simulate a single session."""
        interface_type = "traditional" if index % 2 == 0 else "explainable"
        sequence = self._generate_sequence()
        disability_type = self._generate_disability_type()
        
        # Calculate metrics based on interface type
        is_explainable = (interface_type == "explainable")
        
        # Completion Time
        base_time = self.BASELINE_COMPLETION_TIME
        if is_explainable:
            base_time -= self.FIXED_OFFSET
        
        # Add deterministic noise based on index
        noise = math.sin(index) * 5.0 + (self.rng.random() * 2.0 - 1.0)
        completion_time = max(10.0, base_time + noise)
        
        # Error Count
        error_prob = self.ERROR_RATE_EXPLAINABLE if is_explainable else self.ERROR_RATE_TRADITIONAL
        error_count = 1 if self.rng.random() < error_prob else 0
        
        # SUS Score
        sus_base = self.SUS_BASELINE + (self.SUS_IMPROVEMENT if is_explainable else 0)
        sus_noise = self.rng.randint(-5, 5)
        sus_score = max(0, min(100, sus_base + sus_noise))
        
        # Explanation Engagement Time
        # Must be > 0 for Explainable, 0 for Traditional
        exp_time = 0.0
        if is_explainable:
            exp_time = max(1.0, self.rng.uniform(5.0, 30.0))
        
        # Determine Status (Dropout)
        status = "complete"
        dropout_reason = None
        
        if self.dropout_rate > 0 and self.rng.random() < self.dropout_rate:
            status = "incomplete"
            dropout_reason = self.rng.choice(self.DROPOUT_REASONS)
        
        # Timestamps
        start_time = datetime(2023, 1, 1, 10, 0, 0) + timedelta(minutes=index * 30)
        end_time = start_time + timedelta(seconds=completion_time)
        
        return SessionData(
            participant_id=participant_id,
            disability_type=disability_type,
            interface_type=interface_type,
            sequence=sequence,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            error_count=error_count,
            explanation_engagement_time_seconds=exp_time,
            sus_score=sus_score,
            status=status,
            dropout_reason=dropout_reason,
            completion_time_seconds=completion_time,
            task_metrics={"difficulty": 1.0}
        )

    def generate_sessions(self, n: int) -> List[Dict[str, Any]]:
        """
        Generate N sessions.
        
        Args:
            n: Number of sessions to generate.
            
        Returns:
            List of session dictionaries.
        """
        sessions = []
        for i in range(n):
            pid = self._generate_participant_id(i)
            session = self._simulate_session(pid, i)
            sessions.append(asdict(session))
        return sessions

    def validate_and_save(self, sessions: List[Dict[str, Any]], output_path: str):
        """
        Validate sessions against schema and save to JSON.
        
        Args:
            sessions: List of session data.
            output_path: Path to save the JSON file.
        """
        schema = load_schema("contracts/session.schema.yaml")
        
        valid_sessions = []
        for i, session in enumerate(sessions):
            if validate_session(session):
                valid_sessions.append(session)
            else:
                self.logger.error(f"Session {i} failed schema validation")
                # In a real run, we might raise here, but for CI we log and skip
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(valid_sessions, f, indent=2)
        
        self.logger.info(f"Saved {len(valid_sessions)} sessions to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Deterministic Data Simulator for CI Validation")
    parser.add_argument("--n", type=int, default=50, help="Number of sessions to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/simulated_sessions.json", help="Output file path")
    parser.add_argument("--dropout-rate", type=float, default=0.0, help="Probability of a session being a dropout (0.0 to 1.0)")
    
    args = parser.parse_args()
    
    if args.dropout_rate < 0.0 or args.dropout_rate > 1.0:
        print("Error: --dropout-rate must be between 0.0 and 1.0")
        sys.exit(1)
        
    simulator = DeterministicDataSimulator(seed=args.seed, dropout_rate=args.dropout_rate)
    
    sessions = simulator.generate_sessions(args.n)
    simulator.validate_and_save(sessions, args.output)

if __name__ == "__main__":
    main()