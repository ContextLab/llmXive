"""
Unit tests for the DeterministicDataSimulator (T031-gen, T031-cli, T031b, T031c).

This test suite verifies:
1. The simulator produces the expected FIXED_OFFSET in mean completion time.
2. explanation_engagement_time is strictly positive for Explainable and zero for Traditional.
3. The output JSON schema matches contracts/session.schema.yaml.
4. Dropouts are generated correctly when --dropout-rate is set.

IMPORTANT: These tests use the deterministic simulator for CI validation ONLY.
They do NOT generate synthetic data for final research claims (per T012a).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from simulator.simulator import DeterministicDataSimulator, SessionData
from simulator.validator import load_schema, validate_session

# Constants from T031-gen
FIXED_OFFSET = 5.0
BASELINE_TIME = 60.0  # Base completion time in seconds

class TestDeterministicDataSimulator(unittest.TestCase):
    """Tests for the deterministic session data simulator."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / "contracts" / "session.schema.yaml"
        self.simulator = DeterministicDataSimulator()

    def _load_schema(self):
        """Load the session schema for validation."""
        if not self.schema_path.exists():
            self.fail(f"Schema file not found: {self.schema_path}")
        return load_schema(str(self.schema_path))

    def test_fixed_offset_completion_time(self):
        """
        Verify that the simulator produces the expected FIXED_OFFSET in mean completion time.
        
        Per T031-gen:
        - "Explainable" condition MUST have completion_time = baseline_time - FIXED_OFFSET
        - "Traditional" condition MUST have completion_time = baseline_time
        - Random noise must be added (Gaussian) but seeds must be pinned.
        """
        # Generate a small sample with pinned seed
        n_participants = 10
        seed = 42
        
        sessions = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0  # No dropouts for this test
        )
        
        # Separate by interface type
        traditional_times = []
        explainable_times = []
        
        for session in sessions:
            if session.interface_type == "traditional":
                traditional_times.append(session.completion_time_seconds)
            elif session.interface_type == "explainable":
                explainable_times.append(session.completion_time_seconds)
        
        # Verify we have data for both conditions
        self.assertEqual(len(traditional_times), n_participants,
                        "Should have one Traditional session per participant")
        self.assertEqual(len(explainable_times), n_participants,
                        "Should have one Explainable session per participant")
        
        # Calculate means
        mean_traditional = sum(traditional_times) / len(traditional_times)
        mean_explainable = sum(explainable_times) / len(explainable_times)
        
        # The difference should be approximately FIXED_OFFSET
        # Allow small tolerance for Gaussian noise
        observed_diff = mean_traditional - mean_explainable
        tolerance = 0.5  # Small tolerance for noise with N=10
        
        self.assertAlmostEqual(
            observed_diff, 
            FIXED_OFFSET, 
            delta=tolerance,
            msg=f"Mean difference ({observed_diff:.2f}) should be close to FIXED_OFFSET ({FIXED_OFFSET})"
        )

    def test_explanation_engagement_time(self):
        """
        Verify that explanation_engagement_time is strictly positive for Explainable
        and zero for Traditional.
        """
        n_participants = 5
        seed = 123
        
        sessions = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0
        )
        
        for session in sessions:
            if session.interface_type == "traditional":
                self.assertEqual(
                    session.explanation_engagement_time_seconds, 0.0,
                    f"Traditional interface should have 0 explanation engagement time, got {session.explanation_engagement_time_seconds}"
                )
            elif session.interface_type == "explainable":
                self.assertGreater(
                    session.explanation_engagement_time_seconds, 0.0,
                    f"Explainable interface should have positive explanation engagement time, got {session.explanation_engagement_time_seconds}"
                )

    def test_schema_compliance(self):
        """
        Verify that the output JSON schema matches contracts/session.schema.yaml.
        """
        schema = self._load_schema()
        
        n_participants = 3
        seed = 456
        
        sessions = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0
        )
        
        # Convert to dict format for validation
        for session in sessions:
            session_dict = session.to_dict()
            
            # Validate against schema
            is_valid, errors = validate_session(session_dict)
            
            self.assertTrue(
                is_valid,
                f"Session data should conform to schema. Errors: {errors}"
            )

    def test_dropout_generation(self):
        """
        Verify that dropouts are generated correctly when --dropout-rate is set.
        """
        n_participants = 20
        seed = 789
        dropout_rate = 0.5  # 50% dropout rate for testing
        
        sessions = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=dropout_rate
        )
        
        # Count dropouts
        incomplete_sessions = [s for s in sessions if s.status == "incomplete"]
        complete_sessions = [s for s in sessions if s.status == "complete"]
        
        # With 50% dropout rate and 20 participants (40 total sessions),
        # we expect roughly 20 incomplete sessions (allowing for randomness)
        total_sessions = len(sessions)
        expected_dropouts = int(total_sessions * dropout_rate)
        
        # Allow some variance due to randomness
        self.assertGreater(
            len(incomplete_sessions), 0,
            "Should have at least some incomplete sessions with 50% dropout rate"
        )
        
        # Verify that incomplete sessions have dropout_reason populated
        for session in incomplete_sessions:
            self.assertIsNotNone(
                session.dropout_reason,
                f"Incomplete session {session.session_id} should have dropout_reason"
            )
            self.assertNotEqual(
                session.dropout_reason, "",
                f"Incomplete session {session.session_id} should have non-empty dropout_reason"
            )
        
        # Verify that complete sessions do NOT have dropout_reason
        for session in complete_sessions:
            self.assertIsNone(
                session.dropout_reason,
                f"Complete session {session.session_id} should not have dropout_reason"
            )

    def test_counterbalancing_sequence(self):
        """
        Verify that the counterbalancing logic assigns correct sequences.
        """
        n_participants = 4
        seed = 999
        
        sessions = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0
        )
        
        # Group by participant
        participant_sessions = {}
        for session in sessions:
            pid = session.participant_id
            if pid not in participant_sessions:
                participant_sessions[pid] = []
            participant_sessions[pid].append(session)
        
        # Verify each participant has exactly 2 sessions
        for pid, participant_sess in participant_sessions.items():
            self.assertEqual(
                len(participant_sess), 2,
                f"Participant {pid} should have exactly 2 sessions"
            )
            
            # Verify sequences are different (one Traditional->Explainable, one Explainable->Traditional)
            sequences = [s.sequence for s in participant_sess]
            self.assertIn("Traditional->Explainable", sequences)
            self.assertIn("Explainable->Traditional", sequences)

    def test_determinism(self):
        """
        Verify that the simulator produces deterministic results with the same seed.
        """
        n_participants = 5
        seed = 111
        
        # Generate twice with same seed
        sessions_1 = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0
        )
        
        sessions_2 = self.simulator.generate_sessions(
            n=n_participants,
            seed=seed,
            dropout_rate=0.0
        )
        
        # Compare
        self.assertEqual(len(sessions_1), len(sessions_2))
        
        for s1, s2 in zip(sessions_1, sessions_2):
            self.assertEqual(s1.session_id, s2.session_id)
            self.assertEqual(s1.participant_id, s2.participant_id)
            self.assertEqual(s1.interface_type, s2.interface_type)
            self.assertEqual(s1.completion_time_seconds, s2.completion_time_seconds)
            self.assertEqual(s1.error_count, s2.error_count)
            self.assertEqual(s1.sus_score, s2.sus_score)
            self.assertEqual(s1.explanation_engagement_time_seconds, s2.explanation_engagement_time_seconds)

    def test_output_file_creation(self):
        """
        Verify that the CLI wrapper can write output to a file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_sessions.json")
            
            # Run simulator with CLI-like parameters
            self.simulator.generate_sessions_and_save(
                n=5,
                seed=42,
                dropout_rate=0.0,
                output_path=output_path
            )
            
            # Verify file exists
            self.assertTrue(os.path.exists(output_path), f"Output file should exist: {output_path}")
            
            # Verify file is valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 10)  # 5 participants * 2 sessions each

if __name__ == "__main__":
    unittest.main()