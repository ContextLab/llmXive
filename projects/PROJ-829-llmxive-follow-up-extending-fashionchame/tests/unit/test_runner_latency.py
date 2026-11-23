import pytest
import time
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.runner import (
    measure_component_latency,
    analyze_bottleneck,
    process_single_sample_with_bottleneck_analysis,
    run_text_adapter_pipeline_with_bottleneck_analysis
)

class TestLatencyBottleneckAnalysis:
    
    def test_measure_component_latency(self):
        """Test that timing function returns correct duration"""
        def slow_func():
            time.sleep(0.1)
            return "result"
        
        result, duration = measure_component_latency("test", slow_func)
        
        assert result == "result"
        assert duration >= 0.1
        assert duration < 0.2  # Allow small overhead

    def test_analyze_bottleneck_identifies_max(self):
        """Test that bottleneck analysis correctly identifies the slowest component"""
        profile = {
            "text_encoder.encode": 0.01,
            "adapter.forward": 0.05,
            "backbone.generate": 0.03
        }
        
        analysis = analyze_bottleneck(profile)
        
        assert analysis["bottleneck"] == "adapter.forward"
        assert analysis["max_latency_ms"] == 50.0
        assert "profile_ms" in analysis

    def test_analyze_bottleneck_empty(self):
        """Test handling of empty profile"""
        analysis = analyze_bottleneck({})
        assert analysis["status"] == "NO_DATA"
        assert analysis["bottleneck"] is None

    def test_process_single_sample_with_bottleneck_analysis(self):
        """Test the full single sample analysis logic"""
        # Mock components
        mock_adapter = MagicMock()
        mock_text_encoder = MagicMock()
        mock_backbone = MagicMock()
        
        # Setup return values
        mock_text_encoder.encode.return_value = "embedding"
        mock_adapter.forward.return_value = "adapter_out"
        mock_backbone.generate.return_value = "final_out"
        
        sample = {
            "id": "sample_1",
            "prompt": "a red dress",
            "image_latents": None
        }
        
        config = {
            "latency_threshold_ms": 50.0
        }
        
        result = process_single_sample_with_bottleneck_analysis(
            sample, mock_adapter, mock_text_encoder, mock_backbone, config
        )
        
        assert result["sample_id"] == "sample_1"
        assert "latency_profile_ms" in result
        assert "bottleneck" in result
        assert "total_latency_ms" in result
        assert "exceeds_threshold" in result
        
        # Verify components were called
        mock_text_encoder.encode.assert_called_once()
        mock_adapter.forward.assert_called_once()
        mock_backbone.generate.assert_called_once()

    def test_exceeds_threshold_flagging(self):
        """Test that frames exceeding threshold are flagged"""
        # Create a mock that simulates a slow process
        def slow_encode(text):
            time.sleep(0.06) # 60ms
            return "embedding"
        
        mock_adapter = MagicMock()
        mock_text_encoder = MagicMock()
        mock_text_encoder.encode = slow_encode
        mock_backbone = MagicMock()
        mock_backbone.generate.return_value = "out"
        
        sample = {"id": "slow_sample", "prompt": "test", "image_latents": None}
        config = {"latency_threshold_ms": 50.0}
        
        result = process_single_sample_with_bottleneck_analysis(
            sample, mock_adapter, mock_text_encoder, mock_backbone, config
        )
        
        assert result["exceeds_threshold"] is True
        assert result["total_latency_ms"] > 50.0
        
        # Verify bottleneck is text_encoder
        assert result["bottleneck"] == "text_encoder.encode"

    @patch('src.pipeline.runner.should_trigger_batch_processing')
    @patch('src.pipeline.runner.trigger_memory_cleanup')
    def test_pipeline_memory_trigger(self, mock_cleanup, mock_should_trigger):
        """Test that memory trigger is checked during pipeline"""
        mock_should_trigger.return_value = True
        
        mock_stream = [
            {"id": "1", "prompt": "test", "image_latents": None},
            {"id": "2", "prompt": "test", "image_latents": None}
        ]
        
        mock_adapter = MagicMock()
        mock_text_encoder = MagicMock()
        mock_text_encoder.encode.return_value = "emb"
        mock_backbone = MagicMock()
        mock_backbone.generate.return_value = "out"
        
        config = {
            "latency_threshold_ms": 1000.0, # High threshold to avoid flagging
            "memory_trigger_gb": 6.5
        }
        
        output_path = Path("/tmp/test_bottleneck.json")
        
        # Run pipeline (mocked data stream)
        run_text_adapter_pipeline_with_bottleneck_analysis(
            mock_stream, mock_adapter, mock_text_encoder, mock_backbone, config, output_path
        )
        
        # Verify cleanup was called if trigger hit
        # Note: In real code, trigger depends on memory, here we mock the check
        # The logic ensures the check is performed
        assert mock_should_trigger.called

    def test_report_generation(self):
        """Test that the pipeline writes a valid JSON report"""
        mock_stream = [
            {"id": "1", "prompt": "test", "image_latents": None}
        ]
        
        mock_adapter = MagicMock()
        mock_text_encoder = MagicMock()
        mock_text_encoder.encode.return_value = "emb"
        mock_backbone = MagicMock()
        mock_backbone.generate.return_value = "out"
        
        config = {"latency_threshold_ms": 1000.0}
        output_path = Path("/tmp/test_report_output.json")
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        run_text_adapter_pipeline_with_bottleneck_analysis(
            mock_stream, mock_adapter, mock_text_encoder, mock_backbone, config, output_path
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert "config" in report
        assert "summary" in report
        assert "frame_details" in report
        assert report["config"]["threshold_ms"] == 1000.0
        assert report["summary"]["total_samples_processed"] == 1
        
        # Cleanup
        output_path.unlink()