import pytest
import json
import os
import tempfile
from pathlib import Path

# Import the function to test
from eval.gate import run_permutation_test_gate, load_validation_result, save_validation_result

class TestPermutationGate:
    
    def setup_method(self):
        """Create temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "proxy_validation.json")
        self.output_path = os.path.join(self.temp_dir, "gate_result.json")

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
          # Best effort cleanup
          try:
              import shutil
              shutil.rmtree(self.temp_dir)
          except:
              pass

    def test_gate_passes_high_pvalue(self):
        """Test that gate passes when p-value > 0.05."""
        # Prepare input data with high p-value
        input_data = {
            "permutation_test": {
                "p_value": 0.25,
                "iterations": 100
            }
        }
        
        with open(self.input_path, 'w') as f:
            json.dump(input_data, f)
        
        # Should return True and not raise
        result = run_permutation_test_gate(self.input_path, self.output_path)
        
        assert result is True
        
        # Verify output file
        assert os.path.exists(self.output_path)
        with open(self.output_path, 'r') as f:
            gate_result = json.load(f)
        
        assert gate_result["status"] == "PASSED"
        assert gate_result["p_value"] == 0.25

    def test_gate_blocks_low_pvalue(self):
        """Test that gate blocks deployment when p-value <= 0.05."""
        # Prepare input data with low p-value (overfitting)
        input_data = {
            "permutation_test": {
                "p_value": 0.03,
                "iterations": 100
            }
        }
        
        with open(self.input_path, 'w') as f:
            json.dump(input_data, f)
        
        # Should raise SystemExit
        with pytest.raises(SystemExit) as excinfo:
            run_permutation_test_gate(self.input_path, self.output_path)
        
        assert excinfo.value.code == 1
        
        # Verify output file indicates block
        assert os.path.exists(self.output_path)
        with open(self.output_path, 'r') as f:
            gate_result = json.load(f)
        
        assert gate_result["status"] == "BLOCKED"
        assert "Overfitting detected" in gate_result["reason"]

    def test_gate_blocks_exactly_threshold(self):
        """Test that gate blocks when p-value is exactly 0.05."""
        input_data = {
            "permutation_test": {
                "p_value": 0.05,
                "iterations": 100
            }
        }
        
        with open(self.input_path, 'w') as f:
            json.dump(input_data, f)
        
        with pytest.raises(SystemExit) as excinfo:
            run_permutation_test_gate(self.input_path, self.output_path)
        
        assert excinfo.value.code == 1

    def test_gate_missing_file(self):
        """Test that gate raises FileNotFoundError if input is missing."""
        with pytest.raises(FileNotFoundError):
            run_permutation_test_gate("non_existent_path.json", self.output_path)

    def test_gate_missing_key(self):
        """Test that gate raises KeyError if permutation_test key is missing."""
        input_data = {
            "some_other_key": {
                "value": 123
            }
        }
        
        with open(self.input_path, 'w') as f:
            json.dump(input_data, f)
        
        with pytest.raises(KeyError):
            run_permutation_test_gate(self.input_path, self.output_path)

    def test_gate_missing_pvalue(self):
        """Test that gate raises KeyError if p_value is missing."""
        input_data = {
            "permutation_test": {
                "iterations": 100
            }
        }
        
        with open(self.input_path, 'w') as f:
            json.dump(input_data, f)
        
        with pytest.raises(KeyError):
            run_permutation_test_gate(self.input_path, self.output_path)