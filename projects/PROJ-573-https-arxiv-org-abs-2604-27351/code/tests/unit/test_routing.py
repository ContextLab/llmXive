"""
Unit tests for the ModalityRouter (T038).

Tests the heterogeneous routing layer to ensure:
1. Correct model instantiation per modality.
2. Proper routing of inputs to native models.
3. Unified predict interface works for multi-modal inputs.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.routing import ModalityRouter, MODALITY_MODEL_REGISTRY
from src.models.timeseries_model import TimeSeriesModel
from src.models.tabular_model import TabularModel
from src.models.text_model import TextModel


class TestModalityRouter:
    """Test suite for ModalityRouter."""
    
    def test_registry_contains_expected_modalities(self):
        """Verify that the registry includes timeseries, tabular, and text."""
        assert "timeseries" in MODALITY_MODEL_REGISTRY
        assert "tabular" in MODALITY_MODEL_REGISTRY
        assert "text" in MODALITY_MODEL_REGISTRY
    
    def test_init_creates_empty_models_dict(self):
        """Router should start with no loaded models."""
        router = ModalityRouter()
        assert router.models == {}
    
    def test_get_model_lazy_loads_timeseries(self):
        """get_model should instantiate TimeSeriesModel on first call."""
        router = ModalityRouter()
        with patch.object(TimeSeriesModel, '__init__', return_value=None) as mock_init:
            model = router.get_model("timeseries")
            assert isinstance(model, TimeSeriesModel)
            mock_init.assert_called_once()
    
    def test_get_model_caches_instance(self):
        """get_model should return the same instance on subsequent calls."""
        router = ModalityRouter()
        with patch.object(TimeSeriesModel, '__init__', return_value=None):
            model1 = router.get_model("timeseries")
            model2 = router.get_model("timeseries")
            assert model1 is model2
    
    def test_get_model_raises_on_invalid_modality(self):
        """get_model should raise ValueError for unsupported modalities."""
        router = ModalityRouter()
        with pytest.raises(ValueError, match="Unsupported modality"):
            router.get_model("image")
    
    def test_route_calls_predict_on_model(self):
        """route should call model.predict with input data."""
        router = ModalityRouter()
        mock_model = MagicMock(spec=TimeSeriesModel)
        mock_model.predict.return_value = {"prediction": 0.5}
        router.models["timeseries"] = mock_model
        
        input_data = {"values": [1, 2, 3]}
        result = router.route("timeseries", input_data)
        
        mock_model.predict.assert_called_once_with(input_data)
        assert result == {"prediction": 0.5}
    
    def test_route_fallback_to_get_embedding(self):
        """route should call get_embedding if predict is missing."""
        router = ModalityRouter()
        mock_model = MagicMock(spec=object)
        mock_model.get_embedding.return_value = np.array([1.0, 2.0])
        # Ensure predict is not present
        del mock_model.predict
        router.models["timeseries"] = mock_model
        
        input_data = {"values": [1, 2, 3]}
        result = router.route("timeseries", input_data)
        
        mock_model.get_embedding.assert_called_once_with(input_data)
        assert np.array_equal(result, np.array([1.0, 2.0]))
    
    def test_predict_handles_multiple_modalities(self):
        """predict should process all modalities in the input dict."""
        router = ModalityRouter()
        
        # Mock models for all modalities
        mock_ts = MagicMock(spec=TimeSeriesModel)
        mock_ts.predict.return_value = {"pred": "ts_result"}
        
        mock_tab = MagicMock(spec=TabularModel)
        mock_tab.predict.return_value = {"pred": "tab_result"}
        
        mock_txt = MagicMock(spec=TextModel)
        mock_txt.predict.return_value = {"pred": "txt_result"}
        
        router.models = {
            "timeseries": mock_ts,
            "tabular": mock_tab,
            "text": mock_txt
        }
        
        input_data = {
            "timeseries": {"values": [1, 2]},
            "tabular": {"f1": 10},
            "text": "hello"
        }
        
        results = router.predict(input_data)
        
        assert "timeseries" in results
        assert "tabular" in results
        assert "text" in results
        assert results["timeseries"]["pred"] == "ts_result"
    
    def test_predict_handles_missing_modality_gracefully(self):
        """predict should log error and return error dict if modality fails."""
        router = ModalityRouter()
        mock_model = MagicMock(spec=TimeSeriesModel)
        mock_model.predict.side_effect = Exception("Simulated failure")
        router.models["timeseries"] = mock_model
        
        results = router.predict({"timeseries": {"values": [1, 2]}})
        
        assert "timeseries" in results
        assert "error" in results["timeseries"]
        assert results["timeseries"]["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])