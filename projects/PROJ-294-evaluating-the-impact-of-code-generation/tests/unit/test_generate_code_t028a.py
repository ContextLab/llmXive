import os
import sys
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from generate_code import (
    check_local_model_availability,
    write_model_availability_status,
    ensure_state_dir,
    MODEL_AVAILABILITY_FILE,
    main
)
from utils import setup_logging, set_task_id

class TestModelAvailabilityCheck:
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup a temporary state directory for each test."""
        self.tmp_state_dir = tmp_path / "state"
        self.tmp_state_dir.mkdir()
        self.original_state_dir = "state"
        
        # Mock the STATE_DIR constant in generate_code module
        # We need to patch it to point to our temp directory
        with patch('generate_code.STATE_DIR', str(self.tmp_state_dir)):
            # Re-derive the file path based on the patched directory
            self.test_model_file = os.path.join(str(self.tmp_state_dir), "model_availability.json")
            yield

    def test_check_local_model_availability_transformers_not_installed(self):
        """Test behavior when transformers library is missing."""
        with patch.dict(sys.modules, {'transformers': None}):
            # Force import error by removing it from sys.modules temporarily if it exists
            if 'transformers' in sys.modules:
                del sys.modules['transformers']
            
            # We need to re-import or mock the import inside the function
            # Since the function does 'import transformers' inside, we mock the import mechanism
            with patch('builtins.__import__', side_effect=ImportError("No module named 'transformers'")):
                result = check_local_model_availability("test_model")
                
                assert result["available"] is False
                assert "transformers library not installed" in result["reason"]
                assert result["model_name"] == "test_model"

    def test_check_local_model_availability_success(self):
        """Test behavior when model is successfully found."""
        # Mock transformers and AutoTokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.vocab_size = 50257
        mock_tokenizer.__class__.__name__ = "CodeGenTokenizer"
        
        with patch('generate_code.AutoTokenizer') as mock_auto_tokenizer:
            mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
            
            # Also need to mock the import inside the function
            # The function does 'from transformers import ...'
            # We patch the module in sys.modules to simulate it being present
            mock_transformers = MagicMock()
            sys.modules['transformers'] = mock_transformers
            sys.modules['transformers'].AutoModelForCausalLM = MagicMock()
            sys.modules['transformers'].AutoTokenizer = mock_auto_tokenizer
            
            result = check_local_model_availability("Salesforce/codegen-mono")
            
            assert result["available"] is True
            assert "Model accessible" in result["reason"]
            assert result["details"]["vocab_size"] == 50257

    def test_check_local_model_availability_failure(self):
        """Test behavior when model cannot be loaded."""
        mock_transformers = MagicMock()
        sys.modules['transformers'] = mock_transformers
        
        # Mock AutoTokenizer to raise an error
        mock_auto_tokenizer = MagicMock()
        mock_auto_tokenizer.from_pretrained.side_effect = Exception("Model not found or network error")
        sys.modules['transformers'].AutoTokenizer = mock_auto_tokenizer
        
        result = check_local_model_availability("non_existent_model")
        
        assert result["available"] is False
        assert "Failed to access model" in result["reason"]

    def test_write_model_availability_status(self):
        """Test that the status file is written correctly."""
        status_data = {
            "model_name": "test_model",
            "available": True,
            "reason": "Test reason",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        write_model_availability_status(status_data)
        
        assert os.path.exists(self.test_model_file)
        
        with open(self.test_model_file, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == status_data

    def test_main_function(self):
        """Test the main function execution."""
        set_task_id("T028a")
        setup_logging(task_id="T028a")
        
        # Mock the check function to return a known status
        mock_status = {
            "model_name": "Salesforce/codegen-mono",
            "available": True,
            "reason": "Test mock",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        with patch('generate_code.check_local_model_availability', return_value=mock_status):
            result = main()
            
            assert result == 0
            assert os.path.exists(self.test_model_file)
            
            with open(self.test_model_file, 'r') as f:
                data = json.load(f)
            
            assert data["available"] is True
            assert data["model_name"] == "Salesforce/codegen-mono"

    def test_main_function_when_model_unavailable(self):
        """Test main function when model is unavailable."""
        set_task_id("T028a")
        setup_logging(task_id="T028a")
        
        mock_status = {
            "model_name": "Salesforce/codegen-mono",
            "available": False,
            "reason": "Model not found",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        with patch('generate_code.check_local_model_availability', return_value=mock_status):
            result = main()
            
            assert result == 0  # Should still return 0 as it's just a status check
            assert os.path.exists(self.test_model_file)
            
            with open(self.test_model_file, 'r') as f:
                data = json.load(f)
            
            assert data["available"] is False