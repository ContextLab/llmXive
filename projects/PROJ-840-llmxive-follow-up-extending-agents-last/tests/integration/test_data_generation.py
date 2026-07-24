import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.generator import main, FailureType

class TestDataGeneration:
    def test_golden_subset_generation(self, tmp_path):
        """Test that the generator creates the golden subset file with correct schema."""
        output_file = tmp_path / "golden_subset.json"
        
        # Run the generator
        sys.argv = [
            "generator.py",
            "--mode", "golden",
            "--seed", "42",
            "--num-tasks", "5",
            "--output", str(output_file)
        ]
        main()
        
        # Verify file exists
        assert output_file.exists(), "Output file was not created"
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Output should be a list of traces"
        assert len(data) == 5, "Should generate exactly 5 traces"
        
        # Verify schema for each trace
        for trace in data:
            assert "trace_id" in trace, "Missing trace_id"
            assert "ground_truth_label" in trace, "Missing ground_truth_label"
            assert "step_state" in trace, "Missing step_state"
            assert "task_description" in trace, "Missing task_description"
            
            assert trace["ground_truth_label"] in [
                FailureType.STATE_PERSISTENCE, 
                FailureType.REASONING_DEFICIT
            ], f"Invalid label: {trace['ground_truth_label']}"
            
            # Check step_state structure
            step_state = trace["step_state"]
            assert "files" in step_state, "Missing files in step_state"
            assert "variables" in step_state, "Missing variables in step_state"
            
            # Check files structure
            for file_entry in step_state["files"]:
                assert "path" in file_entry
                assert "content" in file_entry
                assert "deleted" in file_entry
                
            # Check variables structure
            for var_entry in step_state["variables"]:
                assert "name" in var_entry
                assert "value" in var_entry
                assert "type" in var_entry

    def test_seed_reproducibility(self, tmp_path):
        """Test that running with the same seed produces identical output."""
        output_file_1 = tmp_path / "golden_subset_1.json"
        output_file_2 = tmp_path / "golden_subset_2.json"
        
        # Run 1
        sys.argv = [
            "generator.py",
            "--mode", "golden",
            "--seed", "123",
            "--num-tasks", "3",
            "--output", str(output_file_1)
        ]
        main()
        
        # Run 2
        sys.argv = [
            "generator.py",
            "--mode", "golden",
            "--seed", "123",
            "--num-tasks", "3",
            "--output", str(output_file_2)
        ]
        main()
        
        # Compare content
        with open(output_file_1, 'r') as f1, open(output_file_2, 'r') as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)
        
        assert data1 == data2, "Output should be identical with same seed"

    def test_state_error_mode(self, tmp_path):
        """Test that state_error mode generates only state persistence errors."""
        output_file = tmp_path / "state_error.json"
        
        sys.argv = [
            "generator.py",
            "--mode", "state_error",
            "--seed", "999",
            "--num-tasks", "5",
            "--output", str(output_file)
        ]
        main()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        for trace in data:
            assert trace["ground_truth_label"] == FailureType.STATE_PERSISTENCE

    def test_reasoning_deficit_mode(self, tmp_path):
        """Test that reasoning_deficit mode generates only reasoning deficits."""
        output_file = tmp_path / "reasoning_deficit.json"
        
        sys.argv = [
            "generator.py",
            "--mode", "reasoning_deficit",
            "--seed", "999",
            "--num-tasks", "5",
            "--output", str(output_file)
        ]
        main()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        for trace in data:
            assert trace["ground_truth_label"] == FailureType.REASONING_DEFICIT