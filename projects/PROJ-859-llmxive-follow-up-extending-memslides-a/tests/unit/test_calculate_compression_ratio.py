"""
Unit tests for compression ratio calculation.

Tests verify that compression ratios and fidelity losses are calculated correctly
for per-trace analysis.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the module under test
from evaluation.calculate_compression_ratio import (
    CompressionRatioCalculator,
    calculate_compression_ratios,
    main
)
from config import Config


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock config with temporary directories."""
    config = Mock(spec=Config)
    config.data_raw_dir = str(tmp_path / "raw")
    config.data_processed_dir = str(tmp_path / "processed")
    
    # Create directories
    (tmp_path / "raw").mkdir()
    (tmp_path / "processed" / "rules").mkdir(parents=True)
    
    return config


@pytest.fixture
def sample_trace_data():
    """Sample trace data for testing."""
    return {
        "trace_id": "test-123",
        "exact_tool_sequence": [
            {"tool": "create_slide", "args": {"title": "Test"}},
            {"tool": "add_text", "args": {"content": "Hello"}},
            {"tool": "add_image", "args": {"path": "img.png"}},
            {"tool": "format_text", "args": {"bold": True}},
            {"tool": "save", "args": {}}
        ],
        "final_state": {"slides": 1, "elements": 4}
    }

@pytest.fixture
def sample_rule_set():
    """Sample rule set for testing."""
    return {
        "trace_id": "test-123",
        "rules": [
            {"rule_id": 1, "pattern": "create_slide + add_text", "action": "template_1"},
            {"rule_id": 2, "pattern": "add_image + format", "action": "template_2"}
        ],
        "fidelity": 0.95,
        "accuracy": 0.95
    }

@pytest.fixture
def calculator(mock_config):
    """Create a calculator instance with mock config."""
    return CompressionRatioCalculator(mock_config)

class TestCompressionRatioCalculator:
    """Tests for CompressionRatioCalculator class."""

    def test_calculate_compression_ratio_basic(self, calculator, sample_trace_data, sample_rule_set):
        """Test basic compression ratio calculation."""
        # 5 steps in trace, 2 rules -> ratio = 2/5 = 0.4
        ratio = calculator.calculate_compression_ratio(sample_trace_data, sample_rule_set)
        assert ratio == 0.4
    
    def test_calculate_compression_ratio_no_rules(self, calculator, sample_trace_data):
        """Test compression ratio when rule set is empty."""
        empty_rule_set = {"rules": []}
        ratio = calculator.calculate_compression_ratio(sample_trace_data, empty_rule_set)
        assert ratio == 0.0
    
    def test_calculate_compression_ratio_missing_data(self, calculator):
        """Test compression ratio with missing data."""
        ratio = calculator.calculate_compression_ratio(None, sample_rule_set)
        assert ratio == 1.0  # No compression if missing data
        
        ratio = calculator.calculate_compression_ratio(sample_trace_data, None)
        assert ratio == 1.0
    
    def test_calculate_compression_ratio_empty_trace(self, calculator, sample_rule_set):
        """Test compression ratio with empty trace sequence."""
        empty_trace = {"exact_tool_sequence": []}
        ratio = calculator.calculate_compression_ratio(empty_trace, sample_rule_set)
        assert ratio == 1.0
    
    def test_calculate_fidelity_loss_basic(self, calculator, sample_trace_data, sample_rule_set):
        """Test basic fidelity loss calculation."""
        # Fidelity = 0.95, so loss = 1 - 0.95 = 0.05
        loss = calculator.calculate_fidelity_loss(sample_trace_data, sample_rule_set)
        assert loss == 0.05
    
    def test_calculate_fidelity_loss_perfect_fidelity(self, calculator, sample_trace_data, sample_rule_set):
        """Test fidelity loss with perfect fidelity."""
        perfect_rule_set = {**sample_rule_set, "fidelity": 1.0}
        loss = calculator.calculate_fidelity_loss(sample_trace_data, perfect_rule_set)
        assert loss == 0.0
    
    def test_calculate_fidelity_loss_zero_fidelity(self, calculator, sample_trace_data, sample_rule_set):
        """Test fidelity loss with zero fidelity."""
        zero_rule_set = {**sample_rule_set, "fidelity": 0.0}
        loss = calculator.calculate_fidelity_loss(sample_trace_data, zero_rule_set)
        assert loss == 1.0
    
    def test_calculate_fidelity_loss_missing_data(self, calculator):
        """Test fidelity loss with missing data."""
        loss = calculator.calculate_fidelity_loss(None, sample_rule_set)
        assert loss == 1.0
        
        loss = calculator.calculate_fidelity_loss(sample_trace_data, None)
        assert loss == 1.0
    
    def test_load_trace_data(self, calculator, mock_config, sample_trace_data):
        """Test loading trace data from file."""
        # Create trace file
        trace_file = Path(mock_config.data_raw_dir) / "session_test-456.json"
        with open(trace_file, 'w') as f:
            json.dump(sample_trace_data, f)
        
        # Load and verify
        loaded = calculator.load_trace_data("test-456")
        assert loaded is not None
        assert loaded["trace_id"] == sample_trace_data["trace_id"]
    
    def test_load_trace_data_not_found(self, calculator):
        """Test loading non-existent trace file."""
        result = calculator.load_trace_data("non-existent")
        assert result is None
    
    def test_load_rule_set(self, calculator, mock_config, sample_rule_set):
        """Test loading rule set from file."""
        # Create rule file
        rule_file = Path(mock_config.data_processed_dir) / "rules" / "rules_test-789.json"
        with open(rule_file, 'w') as f:
            json.dump(sample_rule_set, f)
        
        # Load and verify
        loaded = calculator.load_rule_set("test-789")
        assert loaded is not None
        assert loaded["fidelity"] == sample_rule_set["fidelity"]
    
    def test_load_rule_set_not_found(self, calculator):
        """Test loading non-existent rule file."""
        result = calculator.load_rule_set("non-existent")
        assert result is None

class TestProcessAllTraces:
    """Tests for process_all_traces method."""

    def test_process_all_traces_success(self, calculator, mock_config, sample_trace_data, sample_rule_set):
        """Test processing multiple traces successfully."""
        # Create multiple trace and rule files
        for i in range(3):
            trace_id = f"trace-{i}"
            
            # Write trace file
            trace_file = Path(mock_config.data_raw_dir) / f"session_{trace_id}.json"
            with open(trace_file, 'w') as f:
                json.dump({**sample_trace_data, "trace_id": trace_id}, f)
            
            # Write rule file
            rule_file = Path(mock_config.data_processed_dir) / "rules" / f"rules_{trace_id}.json"
            with open(rule_file, 'w') as f:
                json.dump({**sample_rule_set, "trace_id": trace_id}, f)
        
        # Process
        results = calculator.process_all_traces()
        
        # Verify
        assert len(results) == 3
        for result in results:
            assert 'trace_id' in result
            assert 'compression_ratio' in result
            assert 'fidelity_loss' in result
            assert 0 <= result['compression_ratio'] <= 1
            assert 0 <= result['fidelity_loss'] <= 1

    def test_process_all_traces_no_files(self, calculator, mock_config):
        """Test processing when no trace files exist."""
        with pytest.raises(FileNotFoundError, match="No trace files found"):
            calculator.process_all_traces()

class TestCalculateCompressionRatiosFunction:
    """Tests for the main calculate_compression_ratios function."""

    @patch('evaluation.calculate_compression_ratio.CompressionRatioCalculator')
    def test_calculate_compression_ratios_success(self, mock_calculator_class, mock_config):
        """Test successful execution of calculate_compression_ratios."""
        mock_calculator = Mock()
        mock_calculator.process_all_traces.return_value = [
            {'trace_id': 'test', 'compression_ratio': 0.5, 'fidelity_loss': 0.1}
        ]
        mock_calculator.save_results.return_value = Path("output.csv")
        mock_calculator_class.return_value = mock_calculator
        
        results, output_path = calculate_compression_ratios(mock_config)
        
        assert len(results) == 1
        assert output_path == Path("output.csv")

class TestMain:
    """Tests for the main entry point."""

    @patch('evaluation.calculate_compression_ratio.calculate_compression_ratios')
    @patch('evaluation.calculate_compression_ratio.sys')
    def test_main_success(self, mock_sys, mock_calculate):
        """Test main function with successful execution."""
        mock_calculate.return_value = (
            [{'trace_id': 'test', 'compression_ratio': 0.5, 'fidelity_loss': 0.1}],
            Path("output.csv")
        )
        
        main()
        
        mock_calculate.assert_called_once()
        mock_sys.exit.assert_not_called()

    @patch('evaluation.calculate_compression_ratio.calculate_compression_ratios')
    @patch('evaluation.calculate_compression_ratio.sys')
    def test_main_file_not_found(self, mock_sys, mock_calculate):
        """Test main function with file not found error."""
        mock_calculate.side_effect = FileNotFoundError("No traces found")
        
        main()
        
        mock_sys.exit.assert_called_with(1)

    @patch('evaluation.calculate_compression_ratio.calculate_compression_ratios')
    @patch('evaluation.calculate_compression_ratio.sys')
    def test_main_general_error(self, mock_sys, mock_calculate):
        """Test main function with general error."""
        mock_calculate.side_effect = Exception("Unexpected error")
        
        main()
        
        mock_sys.exit.assert_called_with(1)