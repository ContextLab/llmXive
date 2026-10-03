import pytest
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code_02_randomization import run_randomization, validate_balance, generate_participant_id, assign_condition

# Import the main function logic to test the save functionality indirectly
# We will mock the save function or test the logic directly
from code_02_randomization import save_randomization_log

class TestRandomizationLogic:
    def test_generate_unique_ids(self):
        """Ensure generated IDs are unique."""
        ids = [generate_participant_id() for _ in range(100)]
        assert len(ids) == len(set(ids)), "Generated IDs must be unique."

    def test_assign_condition_binary(self):
        """Ensure assign_condition only returns 'Partner' or 'Tool'."""
        for _ in range(1000):
            cond = assign_condition()
            assert cond in ['Partner', 'Tool'], f"Invalid condition: {cond}"

    def test_run_randomization_structure(self):
        """Test that run_randomization returns correct structure."""
        result = run_randomization(5, seed=42)
        assert len(result) == 5
        for item in result:
            assert 'participant_id' in item
            assert 'condition' in item
            assert item['condition'] in ['Partner', 'Tool']

    def test_validate_balance_tolerance(self):
        """Test balance validation logic."""
        # Perfect balance
        balanced = [{'condition': 'Partner' if i % 2 == 0 else 'Tool'} for i in range(100)]
        assert validate_balance(balanced) is True

        # Slightly off but within tolerance (45/55)
        slightly_off = [{'condition': 'Partner' if i < 45 else 'Tool'} for i in range(100)]
        assert validate_balance(slightly_off) is True

        # Outside tolerance (30/70)
        unbalanced = [{'condition': 'Partner' if i < 30 else 'Tool'} for i in range(100)]
        assert validate_balance(unbalanced) is False

    def test_save_randomization_log(self):
        """Test that save_randomization_log writes valid JSON with required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            assignments = run_randomization(10, seed=123)
            
            save_randomization_log(assignments, str(output_path), seed=123)
            
            assert output_path.exists(), "Log file was not created."
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert 'seed' in data
            assert 'total_participants' in data
            assert 'assignments' in data
            assert 'summary' in data
            
            assert data['total_participants'] == 10
            assert len(data['assignments']) == 10
            assert data['summary']['partner_count'] + data['summary']['tool_count'] == 10

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
