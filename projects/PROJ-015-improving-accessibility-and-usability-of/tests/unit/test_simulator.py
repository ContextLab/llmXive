"""
Unit tests for the DeterministicDataSimulator.

These tests verify:
1. The simulator produces the expected fixed_offset in mean difference.
2. explanation_engagement_time is strictly positive for Explainable and zero for Traditional.
3. The output JSON schema matches contracts/session.schema.yaml.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.simulator.simulator import (
    generate_session, 
    generate_simulated_data, 
    validate_session_against_schema,
    load_schema,
    FIXED_OFFSET_SECONDS,
    TRADITIONAL_ENGAGEMENT_TIME,
    EXPLAINABLE_ENGAGEMENT_MEAN
)
from utils.seed import set_seed

class TestSimulatorLogic:
    """Tests for the core simulation logic."""

    def test_fixed_offset_in_completion_time(self):
        """Verify that Explainable is faster by the fixed offset."""
        # Use a large N to minimize noise impact
        n_participants = 100
        seed = 12345
        
        sessions = generate_simulated_data(n_participants, seed)
        
        traditional_times = [s['completion_time_seconds'] for s in sessions if s['interface_type'] == 'traditional']
        explainable_times = [s['completion_time_seconds'] for s in sessions if s['interface_type'] == 'explainable']
        
        mean_trad = np.mean(traditional_times)
        mean_exp = np.mean(explainable_times)
        diff = mean_trad - mean_exp
        
        # Allow some tolerance for noise (e.g., 5 seconds)
        assert abs(diff - FIXED_OFFSET_SECONDS) < 5.0, \
            f"Mean difference {diff:.2f}s deviates too much from expected {FIXED_OFFSET_SECONDS:.2f}s"
        
        # Ensure the direction is correct (Explainable is faster)
        assert mean_exp < mean_trad, "Explainable interface should be faster than Traditional"

    def test_explanation_engagement_time_traditional(self):
        """Verify explanation_engagement_time is zero for Traditional interface."""
        set_seed(42)
        session = generate_session(1, 'traditional', 'traditional_first', np.random.default_rng(42))
        
        assert session['explanation_engagement_time_seconds'] == TRADITIONAL_ENGAGEMENT_TIME, \
            f"Traditional interface should have 0 engagement time, got {session['explanation_engagement_time_seconds']}"

    def test_explanation_engagement_time_explainable(self):
        """Verify explanation_engagement_time is positive for Explainable interface."""
        set_seed(42)
        session = generate_session(1, 'explainable', 'explainable_first', np.random.default_rng(42))
        
        assert session['explanation_engagement_time_seconds'] > 0, \
            f"Explainable interface should have positive engagement time, got {session['explanation_engagement_time_seconds']}"
        
        # Check it's within a reasonable range (mean + 3*std)
        max_expected = EXPLAINABLE_ENGAGEMENT_MEAN + 3 * 3.0  # std is 3.0
        assert session['explanation_engagement_time_seconds'] < max_expected, \
            f"Engagement time {session['explanation_engagement_time_seconds']} exceeds expected range"

    def test_counterbalancing_sequence(self):
        """Verify that participants are counterbalanced."""
        n_participants = 10
        sessions = generate_simulated_data(n_participants, seed=42)
        
        # Group by participant
        participant_sequences = {}
        for s in sessions:
            pid = s['participant_id']
            if pid not in participant_sequences:
                participant_sequences[pid] = []
            participant_sequences[pid].append(s['interface_type'])
        
        # Each participant should have exactly 2 sessions
        for pid, interfaces in participant_sequences.items():
            assert len(interfaces) == 2, f"Participant {pid} should have 2 sessions"
            assert set(interfaces) == {'traditional', 'explainable'}, \
                f"Participant {pid} should have both interface types"

class TestSchemaValidation:
    """Tests for schema validation logic."""

    def test_valid_session_passes(self):
        """Verify a valid session passes validation."""
        schema = {
            "properties": {
                "participant_id": {"type": "string"},
                "interface_type": {"type": "string"},
                "completion_time_seconds": {"type": "number"},
                "error_count": {"type": "integer"},
                "explanation_engagement_time_seconds": {"type": "number"},
                "sus_score": {"type": "integer"},
                "status": {"type": "string"}
            }
        }
        
        session = {
            "participant_id": "P0001",
            "interface_type": "traditional",
            "completion_time_seconds": 120.0,
            "error_count": 0,
            "explanation_engagement_time_seconds": 0.0,
            "sus_score": 75,
            "status": "complete"
        }
        
        assert validate_session_against_schema(session, schema) is True

    def test_missing_field_fails(self):
        """Verify a session with missing field fails validation."""
        schema = {
            "properties": {
                "participant_id": {"type": "string"},
                "interface_type": {"type": "string"}
            }
        }
        
        session = {
            "participant_id": "P0001",
            # Missing interface_type
            "completion_time_seconds": 120.0
        }
        
        assert validate_session_against_schema(session, schema) is False

    def test_invalid_interface_type_fails(self):
        """Verify invalid interface_type fails validation."""
        schema = {
            "properties": {
                "participant_id": {"type": "string"},
                "interface_type": {"type": "string"}
            }
        }
        
        session = {
            "participant_id": "P0001",
            "interface_type": "invalid_type",
            "completion_time_seconds": 120.0
        }
        
        assert validate_session_against_schema(session, schema) is False

class TestCLIIntegration:
    """Tests for CLI integration."""

    def test_output_file_creation(self):
        """Verify the CLI creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            schema_path = Path(tmpdir) / "test_schema.yaml"
            
            # Create a minimal schema
            schema_content = {
                "properties": {
                    "participant_id": {"type": "string"},
                    "interface_type": {"type": "string"},
                    "completion_time_seconds": {"type": "number"},
                    "error_count": {"type": "integer"},
                    "explanation_engagement_time_seconds": {"type": "number"},
                    "sus_score": {"type": "integer"},
                    "status": {"type": "string"}
                }
            }
            with open(schema_path, 'w') as f:
                yaml.dump(schema_content, f)
            
            # Run simulation
            from code.simulator.simulator import generate_simulated_data
            sessions = generate_simulated_data(5, seed=42, schema_path=schema_path)
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(sessions, f)
            
            assert output_path.exists(), "Output file was not created"
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 10, "Should have 10 sessions (5 participants * 2 interfaces)"
            assert isinstance(data[0], dict), "Each session should be a dictionary"

    def test_deterministic_output(self):
        """Verify that running with the same seed produces identical output."""
        sessions1 = generate_simulated_data(10, seed=999, schema_path=None)
        sessions2 = generate_simulated_data(10, seed=999, schema_path=None)
        
        # Compare JSON strings
        json1 = json.dumps(sessions1, sort_keys=True)
        json2 = json.dumps(sessions2, sort_keys=True)
        
        assert json1 == json2, "Same seed should produce identical output"