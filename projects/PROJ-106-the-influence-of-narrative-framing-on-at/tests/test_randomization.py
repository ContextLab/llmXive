import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code_02_randomization import (
    generate_participant_id,
    assign_condition,
    run_randomization,
    validate_balance,
    save_randomization_log
)

class TestRandomization:
    """Tests for the randomization logic in code/02_randomization.py"""

    def test_generate_participant_id_unique(self):
        """Test that generated participant IDs are unique."""
        ids = [generate_participant_id() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Participant IDs should be unique"
        assert all(len(pid) == 8 for pid in ids), "Participant IDs should be 8 characters"

    def test_assign_condition_balanced(self):
        """Test that condition assignment is roughly 50/50 over many trials."""
        random.seed(42)  # For reproducibility in test
        conditions = [assign_condition() for _ in range(10000)]
        partner_count = conditions.count('Partner')
        tool_count = conditions.count('Tool')
        
        # Should be within 5% of 50/50 for large N
        assert 4500 <= partner_count <= 5500, f"Partner count {partner_count} not within 45-55% of 10000"
        assert 4500 <= tool_count <= 5500, f"Tool count {tool_count} not within 45-55% of 10000"

    def test_run_randomization_structure(self):
        """Test that run_randomization returns correct structure."""
        participants = run_randomization(10)
        assert len(participants) == 10
        for p in participants:
            assert 'participant_id' in p
            assert 'condition' in p
            assert p['condition'] in ['Partner', 'Tool']

    def test_validate_balance_balanced(self):
        """Test validation of a balanced distribution."""
        participants = [{'participant_id': str(i), 'condition': 'Partner' if i < 50 else 'Tool'} 
                       for i in range(100)]
        is_balanced, details = validate_balance(participants)
        assert is_balanced, "50/50 split should be considered balanced"
        assert details['partner_count'] == 50
        assert details['tool_count'] == 50
        assert details['ratio'] == 0.5

    def test_validate_balance_unbalanced(self):
        """Test validation of an unbalanced distribution."""
        participants = [{'participant_id': str(i), 'condition': 'Partner' if i < 90 else 'Tool'} 
                       for i in range(100)]
        is_balanced, details = validate_balance(participants)
        assert not is_balanced, "90/10 split should not be considered balanced"
        assert details['partner_count'] == 90
        assert details['tool_count'] == 10

    def test_save_randomization_log_creates_file(self):
        """Test that save_randomization_log creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            participants = run_randomization(5)
            
            written_path = save_randomization_log(participants, output_path)
            
            assert written_path.exists(), "Log file should be created"
            assert written_path == output_path

    def test_save_randomization_log_content(self):
        """Test that the saved log contains correct data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            participants = run_randomization(3)
            
            save_randomization_log(participants, output_path)
            
            with open(output_path, 'r') as f:
                log_data = json.load(f)
            
            assert len(log_data) == 3
            for entry in log_data:
                assert 'participant_id' in entry
                assert 'condition' in entry
                assert 'timestamp' in entry
                assert entry['condition'] in ['Partner', 'Tool']
                # Verify timestamp format (ISO 8601)
                assert 'T' in entry['timestamp'] or '+' in entry['timestamp'] or 'Z' in entry['timestamp']

    def test_save_randomization_log_immediate_write(self):
        """
        Test that the log is written immediately (before survey display).
        This is critical for Constitution III compliance.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "immediate_log.json"
            participants = run_randomization(1)
            
            # Write the log
            save_randomization_log(participants, output_path)
            
            # Verify the file exists on disk immediately
            assert output_path.exists(), "Log must be written to disk immediately"
            
            # Verify we can read it back
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['participant_id'] == participants[0]['participant_id']
            assert data[0]['condition'] == participants[0]['condition']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
