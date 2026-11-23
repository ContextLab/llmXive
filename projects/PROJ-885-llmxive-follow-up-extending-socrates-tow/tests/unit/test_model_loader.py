"""
Unit tests for the model memory estimation and exclusion logic (T009 requirement).
"""
import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from experiments.model_loader import ModelMemoryEstimate, estimate_model_memory, check_and_load_model, get_available_models, filter_models_by_memory
from config import ensure_directories


class TestModelMemoryEstimate:
    """Tests for the ModelMemoryEstimate dataclass."""

    def test_creation(self):
        """Test creating a ModelMemoryEstimate instance."""
        estimate = ModelMemoryEstimate(
            model_name="test_model",
            estimated_ram_gb=5.0,
            reason="Normal operation"
        )
        assert estimate.model_name == "test_model"
        assert estimate.estimated_ram_gb == 5.0
        assert estimate.reason == "Normal operation"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        estimate = ModelMemoryEstimate(
            model_name="test_model",
            estimated_ram_gb=5.0,
            reason="Normal operation"
        )
        estimate_dict = estimate.to_dict()
        assert isinstance(estimate_dict, dict)
        assert estimate_dict["model_name"] == "test_model"
        assert estimate_dict["estimated_ram_gb"] == 5.0
        assert estimate_dict["reason"] == "Normal operation"


class TestEstimateModelMemory:
    """Tests for the estimate_model_memory function."""

    def test_function_exists_and_callable(self):
        """Test that the function exists and is callable."""
        assert callable(estimate_model_memory)

    def test_estimation_returns_positive_value(self):
        """Test that memory estimation returns a positive value."""
        # Mock the internal logic to return a fixed value
        with patch('experiments.model_loader.ModelMemoryEstimate') as MockEstimate:
            mock_instance = MockEstimate.return_value
            mock_instance.estimated_ram_gb = 3.5
            
            result = estimate_model_memory("test_model")
            
            # The function should return a ModelMemoryEstimate object
            assert result is not None
            assert result.estimated_ram_gb > 0

    def test_large_model_estimation(self):
        """Test estimation for a model that exceeds memory limits."""
        # Mock a large model
        with patch('experiments.model_loader.ModelMemoryEstimate') as MockEstimate:
            mock_instance = MockEstimate.return_value
            mock_instance.estimated_ram_gb = 10.0  # > 7GB limit
            
            result = estimate_model_memory("large_model")
            
            assert result.estimated_ram_gb == 10.0
            assert "large" in result.model_name.lower() or "large_model" == result.model_name


class TestCheckAndLoadModel:
    """Tests for the check_and_load_model function and exclusion logic."""

    @pytest.fixture
    def temp_scope_adjustments_path(self):
        """Provide a temporary path for scope_adjustments.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "scope_adjustments.json"
            # Initialize empty list
            path.write_text(json.dumps([]))
            yield path

    def test_model_within_memory_limit(self, temp_scope_adjustments_path):
        """Test that a model within memory limits is loaded successfully."""
        # Mock a small model
        with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
            mock_estimate.return_value = ModelMemoryEstimate(
                model_name="small_model",
                estimated_ram_gb=3.0,
                reason="Fits in memory"
            )
            
            with patch('experiments.model_loader.logger') as mock_logger:
                # Mock the actual loading
                with patch('experiments.model_loader.load_model_from_hf') as mock_load:
                    mock_load.return_value = MagicMock()
                    
                    model, reason = check_and_load_model(
                        "small_model",
                        temp_scope_adjustments_path,
                        max_memory_gb=7.0
                    )
                    
                    assert model is not None
                    assert reason is None  # No reason for exclusion
                    mock_logger.info.assert_called()  # Should log success

    def test_model_exceeds_memory_limit(self, temp_scope_adjustments_path):
        """Test that a model exceeding memory limits is excluded and logged."""
        # Mock a large model
        with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
            mock_estimate.return_value = ModelMemoryEstimate(
                model_name="large_model",
                estimated_ram_gb=10.0,
                reason="Exceeds 7GB limit"
            )
            
            with patch('experiments.model_loader.logger') as mock_logger:
                model, reason = check_and_load_model(
                    "large_model",
                    temp_scope_adjustments_path,
                    max_memory_gb=7.0
                )
                
                assert model is None
                assert reason is not None
                assert "Exceeds" in reason
                
                # Verify exclusion was recorded
                assert temp_scope_adjustments_path.exists()
                content = json.loads(temp_scope_adjustments_path.read_text())
                assert isinstance(content, list)
                assert len(content) > 0
                exclusion_record = content[-1]
                assert exclusion_record["model_name"] == "large_model"
                assert exclusion_record["reason"] == "Exceeds 7GB limit"
                assert exclusion_record["estimated_ram_gb"] == 10.0

    def test_scope_adjustments_schema(self, temp_scope_adjustments_path):
        """Test that scope_adjustments.json has the correct schema."""
        # Trigger an exclusion
        with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
            mock_estimate.return_value = ModelMemoryEstimate(
                model_name="test_model",
                estimated_ram_gb=8.0,
                reason="Test exclusion"
            )
            
            check_and_load_model("test_model", temp_scope_adjustments_path, max_memory_gb=7.0)
            
            # Verify schema
            content = json.loads(temp_scope_adjustments_path.read_text())
            assert len(content) == 1
            record = content[0]
            
            # Required keys
            assert "model_name" in record
            assert "reason" in record
            assert "estimated_ram_gb" in record
            
            # Type checks
            assert isinstance(record["model_name"], str)
            assert isinstance(record["reason"], str)
            assert isinstance(record["estimated_ram_gb"], (int, float))

    def test_multiple_exclusions(self, temp_scope_adjustments_path):
        """Test that multiple model exclusions are recorded correctly."""
        models_to_exclude = [
            ("model_1", 8.0),
            ("model_2", 9.0),
            ("model_3", 10.0)
        ]
        
        for model_name, ram_gb in models_to_exclude:
            with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
                mock_estimate.return_value = ModelMemoryEstimate(
                    model_name=model_name,
                    estimated_ram_gb=ram_gb,
                    reason="Exceeds limit"
                )
                
                check_and_load_model(model_name, temp_scope_adjustments_path, max_memory_gb=7.0)
        
        # Verify all exclusions recorded
        content = json.loads(temp_scope_adjustments_path.read_text())
        assert len(content) == 3
        
        for i, (model_name, ram_gb) in enumerate(models_to_exclude):
            assert content[i]["model_name"] == model_name
            assert content[i]["estimated_ram_gb"] == ram_gb


class TestGetAvailableModels:
    """Tests for the get_available_models function."""

    def test_function_exists_and_callable(self):
        """Test that the function exists and is callable."""
        assert callable(get_available_models)

    def test_returns_list_of_models(self):
        """Test that the function returns a list of model names."""
        # Mock the internal logic
        with patch('experiments.model_loader.MODEL_LIST') as mock_list:
            mock_list = ["model_1", "model_2", "model_3"]
            
            result = get_available_models()
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert "model_1" in result

    def test_empty_model_list(self):
        """Test behavior when no models are available."""
        with patch('experiments.model_loader.MODEL_LIST') as mock_list:
            mock_list = []
            
            result = get_available_models()
            
            assert isinstance(result, list)
            assert len(result) == 0


class TestFilterModelsByMemory:
    """Tests for the filter_models_by_memory function."""

    def test_function_exists_and_callable(self):
        """Test that the function exists and is callable."""
        assert callable(filter_models_by_memory)

    def test_filter_within_limit(self):
        """Test filtering models that fit within memory limit."""
        models = ["small_model_1", "small_model_2"]
        
        with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
            mock_estimate.return_value = ModelMemoryEstimate(
                model_name="small_model",
                estimated_ram_gb=3.0,
                reason="Fits"
            )
            
            result = filter_models_by_memory(models, max_memory_gb=7.0)
            
            # All models should be included
            assert len(result) == 2

    def test_filter_exceeds_limit(self):
        """Test filtering models that exceed memory limit."""
        models = ["large_model_1", "large_model_2"]
        
        with patch('experiments.model_loader.estimate_model_memory') as mock_estimate:
            mock_estimate.return_value = ModelMemoryEstimate(
                model_name="large_model",
                estimated_ram_gb=10.0,
                reason="Exceeds"
            )
            
            result = filter_models_by_memory(models, max_memory_gb=7.0)
            
            # No models should be included
            assert len(result) == 0

    def test_mixed_model_sizes(self):
        """Test filtering with a mix of small and large models."""
        models = ["small_model", "large_model"]
        
        call_count = 0
        def mock_estimate_side_effect(model_name):
            nonlocal call_count
            call_count += 1
            if "small" in model_name:
                return ModelMemoryEstimate(model_name, 3.0, "Fits")
            else:
                return ModelMemoryEstimate(model_name, 10.0, "Exceeds")
        
        with patch('experiments.model_loader.estimate_model_memory', side_effect=mock_estimate_side_effect):
            result = filter_models_by_memory(models, max_memory_gb=7.0)
            
            # Only small model should be included
            assert len(result) == 1
            assert "small_model" in result