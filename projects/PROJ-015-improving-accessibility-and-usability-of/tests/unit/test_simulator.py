"""
Unit tests for the DeterministicDataSimulator (T031).

This module verifies that:
1. The simulator produces the expected fixed_offset in the mean difference of completion times.
2. The explanation_engagement_time is strictly positive for Explainable and zero for Traditional.
3. The output JSON schema matches contracts/session.schema.yaml.

These tests MUST run against the deterministic simulator output, not synthetic random data.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from simulator.simulator import DeterministicDataSimulator, SessionData
from simulator.validator import load_schema, validate_session

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "session.schema.yaml"

class TestDeterministicDataSimulator(unittest.TestCase):
    """Tests for the DeterministicDataSimulator."""

    def setUp(self):
        """Set up test fixtures."""
        self.n_participants = 10
        self.seed = 42
        self.fixed_offset = 2.0  # Seconds faster for Explainable
        self.baseline_time = 30.0
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "test_sessions.json")

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_fixed_offset_in_completion_time(self):
        """
        Test that the simulator produces the expected fixed_offset in the mean difference.
        
        The "Explainable" condition MUST have completion_time = baseline_time - fixed_offset.
        The "Traditional" condition MUST have completion_time = baseline_time.
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        # Separate by interface type
        traditional_times = [s['completion_time_seconds'] for s in sessions if s['interface_type'] == 'traditional']
        explainable_times = [s['completion_time_seconds'] for s in sessions if s['interface_type'] == 'explainable']

        # Calculate means
        mean_traditional = sum(traditional_times) / len(traditional_times)
        mean_explainable = sum(explainable_times) / len(explainable_times)

        # Verify the offset (allowing for small floating point noise from Gaussian noise)
        # The noise is added but the BASE should be offset by fixed_offset
        # Since we use a fixed seed and deterministic noise, the mean difference should be very close to fixed_offset
        mean_diff = mean_traditional - mean_explainable

        # We expect the difference to be approximately the fixed_offset
        # Using a tolerance of 0.1 to account for any minor noise accumulation
        self.assertAlmostEqual(mean_diff, self.fixed_offset, delta=0.1,
                               msg=f"Mean difference ({mean_diff}) does not match fixed_offset ({self.fixed_offset})")

    def test_explanation_engagement_time_values(self):
        """
        Test that explanation_engagement_time is strictly positive for Explainable and zero for Traditional.
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        for session in sessions:
            interface_type = session['interface_type']
            engagement_time = session['explanation_engagement_time_seconds']

            if interface_type == 'traditional':
                self.assertEqual(engagement_time, 0,
                                 msg=f"Traditional interface should have 0 engagement time, got {engagement_time}")
            elif interface_type == 'explainable':
                self.assertGreater(engagement_time, 0,
                                   msg=f"Explainable interface should have positive engagement time, got {engagement_time}")
            else:
                self.fail(f"Unknown interface type: {interface_type}")

    def test_schema_compliance(self):
        """
        Test that the output JSON schema matches contracts/session.schema.yaml.
        """
        # Check if schema file exists
        if not SCHEMA_PATH.exists():
            self.fail(f"Schema file not found at {SCHEMA_PATH}")

        # Load the schema
        schema = load_schema(str(SCHEMA_PATH))
        self.assertIsNotNone(schema, "Failed to load schema")

        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        # Validate each session against the schema
        for i, session in enumerate(sessions):
            is_valid = validate_session(session, schema)
            self.assertTrue(is_valid,
                            msg=f"Session {i} failed schema validation: {session}")

        # Verify required fields are present in at least one session
        if len(sessions) > 0:
            required_fields = ['participant_id', 'disability_type', 'interface_type', 'sequence',
                               'start_time', 'end_time', 'error_count', 'explanation_engagement_time_seconds',
                               'sus_score', 'status']
            sample_session = sessions[0]
            for field in required_fields:
                self.assertIn(field, sample_session,
                              msg=f"Required field '{field}' missing from session")

    def test_determinism_with_seed(self):
        """
        Test that running the simulator twice with the same seed produces identical output.
        """
        output_file_1 = os.path.join(self.temp_dir, "test_sessions_1.json")
        output_file_2 = os.path.join(self.temp_dir, "test_sessions_2.json")

        # Run simulator twice with same seed
        simulator1 = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=output_file_1
        )
        simulator1.run()

        simulator2 = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=output_file_2
        )
        simulator2.run()

        # Compare outputs
        with open(output_file_1, 'r') as f1, open(output_file_2, 'r') as f2:
            sessions1 = json.load(f1)
            sessions2 = json.load(f2)

        self.assertEqual(len(sessions1), len(sessions2), "Number of sessions differs")

        for s1, s2 in zip(sessions1, sessions2):
            self.assertEqual(s1['completion_time_seconds'], s2['completion_time_seconds'],
                             msg="Completion time differs between runs")
            self.assertEqual(s1['error_count'], s2['error_count'],
                             msg="Error count differs between runs")
            self.assertEqual(s1['sus_score'], s2['sus_score'],
                             msg="SUS score differs between runs")
            self.assertEqual(s1['explanation_engagement_time_seconds'], s2['explanation_engagement_time_seconds'],
                             msg="Engagement time differs between runs")

    def test_interface_type_enum(self):
        """
        Test that interface_type is strictly 'traditional' or 'explainable'.
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        valid_types = {'traditional', 'explainable'}
        for session in sessions:
            self.assertIn(session['interface_type'], valid_types,
                          msg=f"Invalid interface_type: {session['interface_type']}")

    def test_sequence_enum(self):
        """
        Test that sequence is strictly 'traditional_explainable' or 'explainable_traditional'.
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        valid_sequences = {'traditional_explainable', 'explainable_traditional'}
        for session in sessions:
            self.assertIn(session['sequence'], valid_sequences,
                          msg=f"Invalid sequence: {session['sequence']}")

    def test_status_enum(self):
        """
        Test that status is strictly 'complete' or 'incomplete'.
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        valid_statuses = {'complete', 'incomplete'}
        for session in sessions:
            self.assertIn(session['status'], valid_statuses,
                          msg=f"Invalid status: {session['status']}")

    def test_numeric_constraints(self):
        """
        Test that numeric fields meet their constraints (e.g., non-negative).
        """
        # Run the simulator
        simulator = DeterministicDataSimulator(
            n_participants=self.n_participants,
            seed=self.seed,
            baseline_time=self.baseline_time,
            fixed_offset=self.fixed_offset,
            output_path=self.output_file
        )
        simulator.run()

        # Load the output
        with open(self.output_file, 'r') as f:
            sessions = json.load(f)

        for session in sessions:
            # completion_time_seconds must be >= 0
            self.assertGreaterEqual(session['completion_time_seconds'], 0,
                                    msg=f"Negative completion time: {session['completion_time_seconds']}")

            # error_count must be >= 0
            self.assertGreaterEqual(session['error_count'], 0,
                                    msg=f"Negative error count: {session['error_count']}")

            # sus_score must be between 0 and 100
            self.assertGreaterEqual(session['sus_score'], 0,
                                    msg=f"SUS score below 0: {session['sus_score']}")
            self.assertLessEqual(session['sus_score'], 100,
                                 msg=f"SUS score above 100: {session['sus_score']}")

            # explanation_engagement_time_seconds must be >= 0
            self.assertGreaterEqual(session['explanation_engagement_time_seconds'], 0,
                                    msg=f"Negative engagement time: {session['explanation_engagement_time_seconds']}")

if __name__ == '__main__':
    unittest.main()