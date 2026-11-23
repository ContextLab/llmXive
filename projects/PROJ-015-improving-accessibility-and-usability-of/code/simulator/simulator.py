"""
Deterministic Data Simulator for Gene Regulation Usability Study.

This module generates deterministic session data for CI validation and local debugging.
It does NOT generate synthetic data for final research claims.
"""
import argparse
import json
import os
import sys
import uuid
import math
import random
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import existing utilities from the project API surface
from utils.seed import set_seed, seeded_generator
from utils.logger import get_logger
from simulator.validator import load_schema, validate_session
from simulator.counterbalance import LatinSquareCounterbalancer

logger = get_logger(__name__)

@dataclass
class SessionData:
    participant_id: str
    session_id: str
    interface_type: str
    completion_time: float
    error_count: int
    explanation_engagement_time: float
    sus_score: float
    status: str
    dropout_reason: Optional[str] = None
    sequence_order: List[int] = field(default_factory=list)
    disability_type: Optional[str] = None
    timestamp: str = field(default_factory=lambda: "2023-10-27T10:00:00")

class DeterministicDataSimulator:
    """
    Generates deterministic session data for CI validation.
    CRITICAL: This data is FORBIDDEN for final research claims.
    """

    DROPOUT_REASONS = [
        "Technical difficulty",
        "Task too complex",
        "Time constraints",
        "Interface confusion",
        "Fatigue",
        "Unexpected error",
        "Lack of interest",
        "Accessibility barrier"
    ]

    def __init__(self, seed: int = 42, dropout_rate: float = 0.0):
        self.seed = seed
        self.dropout_rate = max(0.0, min(1.0, dropout_rate))
        set_seed(seed)
        self.rng = seeded_generator(seed)

    def _generate_baseline_time(self) -> float:
        """Generate baseline completion time from normal distribution."""
        # Mean=60, std=10
        return self.rng.normal(60.0, 10.0)

    def _generate_noise(self) -> float:
        """Generate random noise (Gaussian, mean=0, std=2)."""
        return self.rng.normal(0.0, 2.0)

    def _determine_status_and_reason(self) -> tuple[str, Optional[str]]:
        """Determine if session is complete or incomplete based on dropout rate."""
        if self.rng.random() < self.dropout_rate:
            reason = self.rng.choice(self.DROPOUT_REASONS)
            return "incomplete", reason
        return "complete", None

    def generate_sessions(self, n: int) -> List[Dict[str, Any]]:
        """
        Generate N synthetic sessions.

        Logic:
        - "Explainable" condition: completion_time = baseline_time - 5.0
        - "Traditional" condition: completion_time = baseline_time
        - Random noise added to all.
        - Dropout sessions marked with status='incomplete' and reason.
        """
        sessions = []
        counterbalancer = LatinSquareCounterbalancer(self.seed)

        for i in range(n):
            participant_id = f"p{i+1:03d}"
            session_id = str(uuid.uuid4())

            # Determine interface type (alternating for simplicity in simulation)
            # In real app, this is determined by counterbalancer
            interface_type = "Explainable" if i % 2 == 0 else "Traditional"

            # Generate base metrics
            baseline = self._generate_baseline_time()
            noise = self._generate_noise()

            if interface_type == "Explainable":
                completion_time = max(1.0, baseline - 5.0 + noise)
                explanation_engagement_time = max(0.1, abs(noise) * 2.0)
            else:
                completion_time = max(1.0, baseline + noise)
                explanation_engagement_time = 0.0

            error_count = max(0, int(abs(noise) * 2))

            # SUS score (simplified deterministic generation)
            # Range 0-100, centered around 70 for Explainable, 60 for Traditional
            base_sus = 70.0 if interface_type == "Explainable" else 60.0
            sus_score = max(0.0, min(100.0, base_sus + self.rng.normal(0, 10)))

            # Handle dropout
            status, dropout_reason = self._determine_status_and_reason()

            # Get sequence order from counterbalancer
            sequence_order = counterbalancer.get_sequence(participant_id)

            session = SessionData(
                participant_id=participant_id,
                session_id=session_id,
                interface_type=interface_type,
                completion_time=round(completion_time, 2),
                error_count=error_count,
                explanation_engagement_time=round(explanation_engagement_time, 2),
                sus_score=round(sus_score, 2),
                status=status,
                dropout_reason=dropout_reason,
                sequence_order=sequence_order,
                disability_type="visual" if i % 3 == 0 else "motor" if i % 3 == 1 else "cognitive"
            )

            sessions.append(asdict(session))

        return sessions

    def validate_and_save(self, sessions: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Validate sessions against schema and save to JSON.
        Returns True if successful, False otherwise.
        """
        # Load schema
        schema_path = Path("contracts/session.schema.yaml")
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False

        schema = load_schema(schema_path)

        # Validate each session
        for session in sessions:
            if not validate_session(session, schema):
                logger.error(f"Session validation failed for {session['session_id']}")
                return False

        # Save to JSON
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(sessions, f, indent=2)

        logger.info(f"Saved {len(sessions)} sessions to {output_path}")
        return True

def main():
    parser = argparse.ArgumentParser(description="Deterministic Data Simulator")
    parser.add_argument("--n", type=int, default=10, help="Number of sessions to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/simulated_sessions.json",
                        help="Output file path")
    parser.add_argument("--dropout-rate", type=float, default=0.0,
                        help="Percentage of sessions to mark as incomplete (0.0 to 1.0)")

    args = parser.parse_args()

    if args.dropout_rate < 0.0 or args.dropout_rate > 1.0:
        logger.error("Dropout rate must be between 0.0 and 1.0")
        sys.exit(1)

    logger.info(f"Generating {args.n} sessions with seed {args.seed} and dropout rate {args.dropout_rate}")

    simulator = DeterministicDataSimulator(seed=args.seed, dropout_rate=args.dropout_rate)
    sessions = simulator.generate_sessions(args.n)

    if not simulator.validate_and_save(sessions, args.output):
        logger.error("Failed to validate or save sessions")
        sys.exit(1)

    logger.info("Simulation completed successfully")

if __name__ == "__main__":
    main()