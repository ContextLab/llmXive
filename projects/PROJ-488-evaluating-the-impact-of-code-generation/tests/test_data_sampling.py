import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_sampling import (
    get_sample_fraction,
    stream_and_sample_dataset,
    process_codesearchnet_stream,
    process_codegen_stream,
    run_sampling_workflow,
    MAX_TOTAL_SNIPPETS
)

class TestSampleFraction:
    def test_fraction_less_than_one(self):
        """Test that fraction is < 1 when total > target"""
        fraction = get_sample_fraction(total_available=20000, target_max=10000)
        assert fraction == 0.5

    def test_fraction_one_when_under_limit(self):
        """Test that fraction is 1 when total <= target"""
        fraction = get_sample_fraction(total_available=5000, target_max=10000)
        assert fraction == 1.0

    def test_fraction_zero_when_empty(self):
        """Test that fraction is 0 when total is 0"""
        fraction = get_sample_fraction(total_available=0, target_max=10000)
        assert fraction == 0.0

    def test_fraction_very_large_dataset(self):
        """Test fraction calculation for very large dataset"""
        fraction = get_sample_fraction(total_available=1000000, target_max=10000)
        assert fraction == 0.01

class TestStreamAndSample:
    @patch('data_sampling.load_dataset')
    def test_streaming_stops_at_target(self, mock_load):
        """Test that streaming stops after target_count items"""
        # Create mock dataset iterator
        mock_items = [{"code": f"code_{i}"} for i in range(100)]
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_items))
        mock_load.return_value = mock_ds

        count = 0
        target = 10
        for item in stream_and_sample_dataset("test", target_count=target):
            count += 1
            assert "code" in item

        assert count == target

    @patch('data_sampling.load_dataset')
    def test_streaming_mode_enabled(self, mock_load):
        """Test that streaming=True is passed to load_dataset"""
        mock_items = [{"code": "test"}]
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_items))
        mock_load.return_value = mock_ds

        list(stream_and_sample_dataset("test", target_count=1))

        mock_load.assert_called_once()
        call_kwargs = mock_load.call_args
        assert call_kwargs[1].get('streaming') == True

class TestProcessCodeSearchNet:
    @patch('data_sampling.load_dataset')
    def test_processes_valid_snippets(self, mock_load):
        """Test that process_codesearchnet_stream processes valid snippets"""
        mock_data = [
            {"code": "def foo(): pass", "repo": "test/repo", "path": "file.py"},
            {"code": "", "repo": "test/repo", "path": "empty.py"},  # Should be skipped
            {"code": "def bar(): return 1", "repo": "test/repo", "path": "file2.py"}
        ]
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_data))
        mock_load.return_value = mock_ds

        with patch('data_sampling.Path') as mock_path:
            mock_path.return_value.__truediv__ = lambda self, other: Path(f"mock/{other}")
            with patch('builtins.open', MagicMock()):
                result = process_codesearchnet_stream(target_count=10, output_file="mock/output.json")

        assert result["count"] == 2
        assert result["source"] == "code_search_net"

class TestProcessCodeGen:
    @patch('data_sampling.load_dataset')
    def test_processes_codegen_snippets(self, mock_load):
        """Test that process_codegen_stream processes CodeGen snippets"""
        mock_data = [
            {"code": "x = 1"},
            {"text": "y = 2"},  # Alternative field
            {"code": "", "text": ""},  # Should be skipped
            {"code": "def test(): pass"}
        ]
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=iter(mock_data))
        mock_load.return_value = mock_ds

        with patch('data_sampling.Path') as mock_path:
            mock_path.return_value.__truediv__ = lambda self, other: Path(f"mock/{other}")
            with patch('builtins.open', MagicMock()):
                result = process_codegen_stream(target_count=10, output_file="mock/output.json")

        assert result["count"] == 3
        assert result["source"] == "codeparrot_codegen"

class TestSamplingWorkflow:
    @patch('data_sampling.process_codesearchnet_stream')
    @patch('data_sampling.process_codegen_stream')
    @patch('data_sampling.load_verified_sources')
    def test_workflow_limits_total_count(self, mock_verify, mock_codegen, mock_csnet):
        """Test that workflow respects total count limit"""
        mock_verify.return_value = {"sources": {}}
        mock_csnet.return_value = {"count": 5000, "status": "completed", "source": "code_search_net"}
        mock_codegen.return_value = {"count": 5000, "status": "completed", "source": "codeparrot_codegen"}

        results = run_sampling_workflow()

        assert results["total_count"] == 10000
        assert results["total_count"] <= MAX_TOTAL_SNIPPETS

    @patch('data_sampling.process_codesearchnet_stream')
    @patch('data_sampling.process_codegen_stream')
    @patch('data_sampling.load_verified_sources')
    def test_workflow_handles_partial_failures(self, mock_verify, mock_codegen, mock_csnet):
        """Test workflow handles when one dataset fails"""
        mock_verify.return_value = {"sources": {}}
        mock_csnet.return_value = {"count": 5000, "status": "completed", "source": "code_search_net"}
        mock_codegen.return_value = {"status": "failed", "error": "Connection error"}

        results = run_sampling_workflow()

        assert results["total_count"] == 5000
        assert results["llm_generated"]["status"] == "failed"

    @patch('data_sampling.process_codesearchnet_stream')
    @patch('data_sampling.process_codegen_stream')
    @patch('data_sampling.load_verified_sources')
    def test_workflow_detects_exceed_limit(self, mock_verify, mock_codegen, mock_csnet):
        """Test workflow detects when limit is exceeded"""
        mock_verify.return_value = {"sources": {}}
        mock_csnet.return_value = {"count": 6000, "status": "completed", "source": "code_search_net"}
        mock_codegen.return_value = {"count": 6000, "status": "completed", "source": "codeparrot_codegen"}

        results = run_sampling_workflow()

        assert results["total_count"] == 12000
        assert results["status"] == "warning"

class TestIntegration:
    def test_sample_fraction_logic(self):
        """Integration test for fraction calculation logic"""
        # Scenario: 50k available, want 10k
        assert get_sample_fraction(50000, 10000) == 0.2
        # Scenario: 5k available, want 10k -> take all
        assert get_sample_fraction(5000, 10000) == 1.0
        # Scenario: 0 available
        assert get_sample_fraction(0, 10000) == 0.0
