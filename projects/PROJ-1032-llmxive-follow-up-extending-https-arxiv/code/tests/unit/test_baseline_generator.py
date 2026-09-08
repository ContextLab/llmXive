import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.llmxive.baseline_generator import (
    compute_baseline_statistics,
    generate_baseline_manifest,
    verify_seed_stability,
    get_valid_seed_for_model
)
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR

class TestBaselineGenerator:
    @patch('src.llmxive.baseline_generator.load_model')
    @patch('src.llmxive.baseline_generator.GSM8KDataLoader')
    def test_compute_baseline_statistics(self, mock_loader, mock_load_model):
        # Setup mocks
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load_model.return_value = (mock_model, mock_tokenizer)
        
        mock_stream = MagicMock()
        mock_stream.__next__ = MagicMock(side_effect=[
            {"question": "Test", "answer": "1"},
            {"question": "Test2", "answer": "2"}
        ])
        mock_loader.return_value.get_train_stream.return_value = mock_stream
        
        # Mock model forward pass
        mock_outputs = MagicMock()
        mock_outputs.logits.mean.return_value = 0.5
        mock_model.__call__ = MagicMock(return_value=mock_outputs)
        mock_model.parameters.return_value = []
        
        # Run
        reward, grad_norm = compute_baseline_statistics("test_model", 42, steps=2)
        
        # Assert
        assert isinstance(reward, float)
        assert isinstance(grad_norm, float)
        assert reward > 0
        assert grad_norm >= 0

    def test_verify_seed_stability_valid(self):
        assert verify_seed_stability(1.0, 0.5) is True
        assert verify_seed_stability(10.5, 0.01) is True

    def test_verify_seed_stability_invalid(self):
        assert verify_seed_stability(float('inf'), 0.5) is False
        assert verify_seed_stability(1.0, float('nan')) is False
        assert verify_seed_stability(0.0, 0.5) is False

    @patch('src.llmxive.baseline_generator.generate_baseline_manifest')
    def test_get_valid_seed_for_model(self, mock_gen):
        mock_gen.return_value = {"status": "STABLE", "seed_id": 42}
        result = get_valid_seed_for_model("test", "/tmp", [42, 43])
        assert result["seed_id"] == 42

    @patch('src.llmxive.baseline_generator.generate_baseline_manifest')
    def test_get_valid_seed_for_model_retry(self, mock_gen):
        mock_gen.side_effect = [DATA_INTEGRITY_ERROR("Unstable"), {"status": "STABLE", "seed_id": 43}]
        result = get_valid_seed_for_model("test", "/tmp", [42, 43], max_attempts=3)
        assert result["seed_id"] == 43
        assert mock_gen.call_count == 2
