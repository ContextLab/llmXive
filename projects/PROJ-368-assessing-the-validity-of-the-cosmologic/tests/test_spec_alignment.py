import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from spec_alignment_check import check_spec_alignment, load_file_text

class TestCheckSpecAlignment:
    
    def test_valid_spec_and_plan(self):
        """Test when both spec and plan correctly state Maximum Statistic and no BH."""
        spec = "US3: Use Maximum Statistic approach. Benjamini-Hochberg correction is NOT used."
        plan = "Implementation uses Maximum Statistic."
        
        results = check_spec_alignment(spec, plan)
        
        assert results["spec_valid"] is True
        assert results["plan_valid"] is True
        assert results["aligned"] is True
        assert len(results["flags"]) == 0

    def test_spec_missing_max_stat(self):
        """Test when spec does not mention Maximum Statistic."""
        spec = "US3: Use some other method."
        plan = "Implementation uses Maximum Statistic."
        
        results = check_spec_alignment(spec, plan)
        
        assert results["spec_valid"] is False
        assert "Spec missing 'Maximum Statistic' statement." in results["flags"]

    def test_spec_mandates_bh(self):
        """Test when spec incorrectly mandates BH."""
        spec = "US3: Must use Benjamini-Hochberg correction."
        plan = "Implementation uses Maximum Statistic."
        
        results = check_spec_alignment(spec, plan)
        
        assert results["spec_valid"] is False
        assert "CRITICAL: Spec incorrectly mandates BH." in results["flags"]
        assert results["aligned"] is False

    def test_plan_has_documentation_error(self):
        """Test when plan has the 'Note on Spec Conflict' error claiming Spec mandates BH."""
        spec = "US3: Use Maximum Statistic approach. Benjamini-Hochberg correction is NOT used."
        plan = "Implementation uses Maximum Statistic. Note on Spec Conflict: Spec mandates BH."
        
        results = check_spec_alignment(spec, plan)
        
        assert results["spec_valid"] is True
        assert results["plan_valid"] is True
        assert results["aligned"] is True
        assert "DOCUMENTATION ERROR: Plan's 'Note on Spec Conflict' incorrectly claims Spec mandates BH." in results["flags"]

    def test_plan_missing_max_stat(self):
        """Test when plan does not mention Maximum Statistic."""
        spec = "US3: Use Maximum Statistic approach. Benjamini-Hochberg correction is NOT used."
        plan = "Implementation uses some other method."
        
        results = check_spec_alignment(spec, plan)
        
        assert results["plan_valid"] is False
        assert results["aligned"] is False

class TestLoadFileText:
    
    def test_load_existing_file(self):
        """Test loading a file that exists."""
        # Create a temporary file for testing
        test_content = "Test content"
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch.object(Path, 'exists', return_value=True):
                # We can't easily mock the full path resolution without more setup, 
                # so we test the logic directly if possible or rely on the mock
                # Here we just ensure the function doesn't crash on valid input structure
                pass
        
        # Direct test with real file creation in temp dir
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            content = load_file_text(temp_path)
            assert content == test_content
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Test loading a file that does not exist."""
        with pytest.raises(FileNotFoundError):
            load_file_text("/non/existent/path/file.txt")