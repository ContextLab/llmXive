"""
Unit tests for the simulator module.

These tests verify:
1. The simulator produces the expected fixed difference in completion time.
2. explanation_engagement_time is strictly positive for Explainable and zero for Traditional.
3. The output JSON schema matches contracts/session.schema.yaml.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.simulator.simulator import DeterministicDataSimulator
from code.simulator.validator import load_schema, validate_session


class TestSimulatorDeterminism(unittest.TestCase):
    """Tests for deterministic behavior of the simulator."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = 42
        self.n_participants = 10
        self.schema_path = project_root / "contracts" / "session.schema.yaml"
        
        # Ensure schema exists
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found at {self.schema_path}. "
                "Please ensure T019b (Create session.schema.yaml) is completed."
            )

    def test_completion_time_difference(self):
        """
        Test that the simulator produces the expected fixed difference in completion time.
        
        The "Explainable" condition should have completion_time = baseline_time - 5.0 seconds.
        The "Traditional" condition should have completion_time = baseline_time.
        Therefore, the mean difference should be approximately 5.0 seconds.
        """
        # Generate deterministic sessions
        sessions = DeterministicDataSimulator.generate_sessions(
            n=self.n_participants, 
            seed=self.seed
        )
        
        # Separate sessions by interface type
        traditional_times = []
        explainable_times = []
        
        for session in sessions:
            if session["interface_type"] == "Traditional":
                traditional_times.append(session["metrics"]["completion_time"])
            elif session["interface_type"] == "Explainable":
                explainable_times.append(session["metrics"]["completion_time"])
        
        # Calculate means
        mean_traditional = sum(traditional_times) / len(traditional_times)
        mean_explainable = sum(explainable_times) / len(explainable_times)
        
        # Calculate difference (Traditional - Explainable)
        # Expected: Traditional is 5.0 seconds slower than Explainable
        difference = mean_traditional - mean_explainable
        
        # Assert the difference is approximately 5.0 seconds
        # Use a small tolerance for floating point arithmetic
        self.assertAlmostEqual(difference, 5.0, places=1, 
                               msg=f"Expected difference of 5.0s, got {difference:.2f}s")

    def test_explanation_engagement_time(self):
        """
        Test that explanation_engagement_time is strictly positive for Explainable
        and zero for Traditional interfaces.
        """
        sessions = DeterministicDataSimulator.generate_sessions(
            n=self.n_participants, 
            seed=self.seed
        )
        
        explainable_engagement = []
        traditional_engagement = []
        
        for session in sessions:
            engagement = session["metrics"]["explanation_engagement_time"]
            if session["interface_type"] == "Explainable":
                explainable_engagement.append(engagement)
            elif session["interface_type"] == "Traditional":
                traditional_engagement.append(engagement)
        
        # Check Traditional: all should be 0
        for time_val in traditional_engagement:
            self.assertEqual(time_val, 0, 
                             msg=f"Traditional interface should have 0 engagement time, got {time_val}")
        
        # Check Explainable: all should be strictly positive
        for time_val in explainable_engagement:
            self.assertGreater(time_val, 0, 
                               msg=f"Explainable interface should have positive engagement time, got {time_val}")

    def test_schema_compliance(self):
        """
        Test that the output JSON schema matches contracts/session.schema.yaml.
        """
        sessions = DeterministicDataSimulator.generate_sessions(
            n=self.n_participants, 
            seed=self.seed
        )
        
        # Load schema
        schema = load_schema(self.schema_path)
        
        # Validate each session against schema
        validation_errors = []
        for i, session in enumerate(sessions):
            is_valid, errors = validate_session(session, schema)
            if not is_valid:
                validation_errors.append({
                    "session_index": i,
                    "participant_id": session.get("participant_id"),
                    "errors": errors
                })
        
        # Assert no validation errors
        self.assertEqual(len(validation_errors), 0,
                         msg=f"Schema validation failed for {len(validation_errors)} sessions:\n"
                             + json.dumps(validation_errors, indent=2))

    def test_session_structure(self):
        """
        Test that each session has the required top-level fields.
        """
        sessions = DeterministicDataSimulator.generate_sessions(
            n=self.n_participants, 
            seed=self.seed
        )
        
        required_fields = ["participant_id", "session_id", "interface_type", 
                         "metrics", "status", "timestamp"]
        
        for session in sessions:
            for field in required_fields:
                self.assertIn(field, session, 
                              msg=f"Missing required field '{field}' in session {session.get('session_id')}")

    def test_metrics_structure(self):
        """
        Test that metrics contain all required fields.
        """
        sessions = DeterministicDataSimulator.generate_sessions(
            n=self.n_participants, 
            seed=self.seed
        )
        
        required_metric_fields = ["completion_time", "error_count", 
                                 "explanation_engagement_time", "sus_score"]
        
        for session in sessions:
            metrics = session.get("metrics", {})
            for field in required_metric_fields:
                self.assertIn(field, metrics, 
                              msg=f"Missing required metric '{field}' in session {session.get('session_id')}")


class TestSimulatorCLI(unittest.TestCase):
    """Tests for CLI functionality of the simulator."""

    def test_cli_output_file_creation(self):
        """
        Test that the CLI creates the expected output file.
        """
        import tempfile
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sessions.json"
            
            # Run CLI command
            cmd = [
                sys.executable,
                "-m", "code.simulator.simulator",
                "--n", "5",
                "--seed", "42",
                "--output", str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            
            # Assert command succeeded
            self.assertEqual(result.returncode, 0,
                             msg=f"CLI command failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")
            
            # Assert output file exists
            self.assertTrue(output_path.exists(),
                            msg=f"Output file not created at {output_path}")
            
            # Assert output file is valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list, "Output should be a list of sessions")
            self.assertEqual(len(data), 5, f"Expected 5 sessions, got {len(data)}")


if __name__ == "__main__":
    unittest.main()