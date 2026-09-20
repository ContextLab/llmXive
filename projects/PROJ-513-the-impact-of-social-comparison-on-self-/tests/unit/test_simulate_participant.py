"""
Unit tests for simulate_participant.py.

These tests verify that the simulation functions work correctly
and produce data in the expected format.
"""

import pytest
import json
import tempfile
from pathlib import Path
from code.simulate_participant import (
    set_seed,
    generate_participant_id,
    simulate_incom_score,
    simulate_usage_frequency,
    simulate_biss_score,
    simulate_session,
    write_session_file
)

class TestSimulateParticipant:
    """Test suite for simulate_participant functions."""

    def test_set_seed(self):
        """Test that set_seed sets the random seed."""
        set_seed(42)
        val1 = random.random()
        set_seed(42)
        val2 = random.random()
        assert val1 == val2, "Seed should produce reproducible results"

    def test_generate_participant_id(self):
        """Test participant ID generation."""
        id1 = generate_participant_id()
        id2 = generate_participant_id()
        assert len(id1) == 8, "ID should be 8 characters"
        assert id1 != id2, "IDs should be unique"

    def test_simulate_incom_score_range(self):
        """Test INCOM score is within valid range [0, 60]."""
        for i in range(100):
            score = simulate_incom_score(seed=i)
            assert 0 <= score <= 60, f"INCOM score {score} out of range"

    def test_simulate_usage_frequency_non_negative(self):
        """Test usage frequency is non-negative."""
        for i in range(100):
            freq = simulate_usage_frequency(seed=i)
            assert freq >= 0, f"Usage frequency {freq} should be non-negative"

    def test_simulate_biss_score_ai(self):
        """Test BISS score for AI images is within [1, 7]."""
        for i in range(100):
            score = simulate_biss_score('ai', seed=i)
            assert 1 <= score <= 7, f"BISS score {score} out of range for AI"

    def test_simulate_biss_score_human(self):
        """Test BISS score for Human images is within [1, 7]."""
        for i in range(100):
            score = simulate_biss_score('human', seed=i)
            assert 1 <= score <= 7, f"BISS score {score} out of range for Human"

    def test_simulate_session_structure(self):
        """Test session structure is correct."""
        stimuli = [
            {'stimulus_id': 's1', 'origin': 'ai'},
            {'stimulus_id': 's2', 'origin': 'human'}
        ]
        session = simulate_session(
            participant_id='test123',
            stimuli_list=stimuli,
            incom_score=35,
            usage_frequency=5.0,
            seed=42
        )
        
        assert 'session_id' in session
        assert session['participant_id'] == 'test123'
        assert session['INCOM_score'] == 35
        assert session['usage_frequency'] == 5.0
        assert 'responses' in session
        assert len(session['responses']) == 2
        assert session['is_complete'] == True

    def test_write_session_file(self):
        """Test writing session to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test.jsonl'
            
            session = {
                'session_id': 's1',
                'participant_id': 'p1',
                'responses': []
            }
            
            write_session_file(session, output_path)
            
            assert output_path.exists()
            with open(output_path) as f:
                line = f.readline()
                data = json.loads(line)
                assert data['session_id'] == 's1'
                assert data['participant_id'] == 'p1'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
