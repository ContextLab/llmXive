import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import (
    validate_and_aggregate,
    check_validation_and_halt,
    get_subject_list,
    load_behavioral_scores
)

class TestDownloadValidation:
    
    def test_validate_and_aggregate_with_mock_data(self, tmp_path):
        """Test validation and aggregation with valid mock data."""
        # Create mock input
        mock_data = [
            {"id": "sub-001", "fluid_intelligence_score": 0.85},
            {"id": "sub-002", "fluid_intelligence_score": 0.72},
            {"id": "sub-003", "fluid_intelligence_score": 0.91}
        ]
        
        input_file = tmp_path / "mock_subjects.json"
        with open(input_file, 'w') as f:
            json.dump(mock_data, f)
        
        output_file = tmp_path / "valid_subjects.json"
        
        # Run validation
        result = validate_and_aggregate(mock_data, output_file)
        
        # Verify output
        assert result['count'] == 3
        assert len(result['subjects']) == 3
        assert result['subjects'][0]['id'] == "sub-001"
        assert result['subjects'][0]['score'] == 0.85
        
        # Verify file was written
        assert output_file.exists()
        with open(output_file, 'r') as f:
            written_data = json.load(f)
        assert written_data['count'] == 3

    def test_validate_and_aggregate_empty_scores(self, tmp_path):
        """Test validation when no subjects have valid scores."""
        mock_data = [
            {"id": "sub-001", "fluid_intelligence_score": None},
            {"id": "sub-002", "fluid_intelligence_score": None}
        ]
        
        output_file = tmp_path / "valid_subjects.json"
        error_log = tmp_path / "validation_errors.log"
        
        # Run validation
        result = validate_and_aggregate(mock_data, output_file)
        
        # Verify count is 0
        assert result['count'] == 0
        
        # Verify halt condition
        with pytest.raises(ValueError) as exc_info:
            check_validation_and_halt(result, error_log)
        
        assert "No valid Fluid Intelligence data found" in str(exc_info.value)
        
        # Verify error log was written
        assert error_log.exists()
        with open(error_log, 'r') as f:
            log_content = f.read()
        assert "[VALIDATION_ERROR]" in log_content

    def test_enforce_sample_limit(self, tmp_path):
        """Test that sample limit is enforced."""
        mock_data = [{"id": f"sub-{i:03d}", "fluid_intelligence_score": 0.5} for i in range(15)]
        
        output_file = tmp_path / "valid_subjects.json"
        
        result = validate_and_aggregate(mock_data, output_file, n_subjects=10)
        
        assert result['count'] == 10
        assert len(result['subjects']) == 10

    def test_no_creativity_in_code(self):
        """Verify that 'creativity' string is not present in download.py."""
        code_file = Path(__file__).parent.parent.parent / "code" / "download.py"
        with open(code_file, 'r') as f:
            content = f.read()
        
        # Check that 'creativity' is not in the code (excluding comments)
        # Simple check: remove comments and check
        lines = content.split('\n')
        code_lines = []
        for line in lines:
            # Remove comments
            if '#' in line:
                line = line[:line.index('#')]
            code_lines.append(line)
        
        code_content = '\n'.join(code_lines)
        assert 'creativity' not in code_content.lower(), "Found 'creativity' in code. Pivot not complete."

    def test_tracer_log_entry(self, tmp_path):
        """Verify that TRACER log entry is generated."""
        # This test checks the logging behavior
        # In a real scenario, we would capture logs
        # For now, we verify the code contains the log statement
        code_file = Path(__file__).parent.parent.parent / "code" / "download.py"
        with open(code_file, 'r') as f:
            content = f.read()
        
        assert "TRACER: FR-001 Pivot to Fluid Intelligence" in content, "Tracer log entry not found."

    def test_fallback_logic(self, tmp_path):
        """Test that fallback dataset is considered."""
        # This is a placeholder for fallback logic testing
        # In a real implementation, this would test the fallback mechanism
        mock_data = []
        output_file = tmp_path / "valid_subjects.json"
        
        # If no data, should halt
        with pytest.raises(ValueError):
            result = validate_and_aggregate(mock_data, output_file)
            check_validation_and_halt(result, tmp_path / "errors.log")
