import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.model_selector import get_compatible_models, select_model, select_model_with_seed, main
from src.utils.config import get_config, set_seed, get_data_logs_path

class TestModelSelector:
    
    def test_get_compatible_models_empty_list(self):
        """Test behavior when no models are configured."""
        with patch('src.utils.model_selector.get_candidate_models', return_value=[]):
            compatible = get_compatible_models()
            assert compatible == []

    def test_select_model_raises_on_empty(self):
        """Test that select_model raises error if no compatible models found."""
        with patch('src.utils.model_selector.get_compatible_models', return_value=[]):
            with pytest.raises(RuntimeError, match="No compatible models found"):
                select_model()

    def test_select_model_deterministic(self):
        """Test that selection is always the first compatible model."""
        mock_models = [
            {"model_name": "model_A", "capability": True},
            {"model_name": "model_B", "capability": True}
        ]
        with patch('src.utils.model_selector.get_compatible_models', return_value=mock_models):
            selected = select_model()
            assert selected["model_name"] == "model_A"

    def test_main_creates_log_file(self):
        """Test that main() creates the model_selection.json file."""
        mock_model = {"model_name": "test-model", "type": "llm"}
        
        with patch('src.utils.model_selector.select_model', return_value=mock_model):
            with patch('src.utils.model_selector.get_data_logs_path') as mock_path:
                temp_dir = tempfile.mkdtemp()
                mock_path.return_value = Path(temp_dir)
                
                main()
                
                log_file = Path(temp_dir) / "model_selection.json"
                assert log_file.exists()
                
                with open(log_file, "r") as f:
                    data = json.load(f)
                
                assert "selected_model" in data
                assert data["selected_model"]["model_name"] == "test-model"
                assert data["deterministic"] is True
                assert data["task_id"] == "T004a"

    def test_main_with_transformers_mock(self):
        """Test model selection logic with mocked transformers."""
        mock_model = {"model_name": "mock-model"}
        
        with patch('src.utils.model_selector.get_candidate_models', return_value=[mock_model]):
            with patch('src.utils.model_selector.AutoTokenizer') as mock_tokenizer_class:
                mock_tokenizer = MagicMock()
                mock_tokenizer.return_value = mock_tokenizer
                mock_tokenizer.return_value.return_value = MagicMock(input_ids=MagicMock(numel=MagicMock(return_value=1)))
                mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                
                # This should not raise and should return the model
                compatible = get_compatible_models()
                assert len(compatible) == 1
                assert compatible[0]["model_name"] == "mock-model"
