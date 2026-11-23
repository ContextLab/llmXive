import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from evaluation.calculate_compression_ratio import (
    CompressionRatioCalculator,
    CompressionRatioCalculatorError,
    calculate_compression_ratios,
    main
)
from config import get_config


class TestCompressionRatioCalculator:
    """Tests for the CompressionRatioCalculator class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        return {
            'base_dir': tempfile.mkdtemp(),
            'evaluation_sample_size': 10
        }

    @pytest.fixture
    def setup_test_environment(self, mock_config):
        """Set up a test environment with mock data."""
        base_dir = Path(mock_config['base_dir'])
        data_dir = base_dir / 'data'
        processed_dir = data_dir / 'processed'
        rules_dir = processed_dir / 'rules'
        sweeps_dir = rules_dir / 'sweeps'
        held_out_dir = data_dir / 'held_out'

        # Create directories
        for dir_path in [data_dir, processed_dir, rules_dir, sweeps_dir, held_out_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create mock original rules
        original_rules = {
            'rules': [
                {'id': 1, 'condition': 'A', 'action': 'B'},
                {'id': 2, 'condition': 'C', 'action': 'D'},
                {'id': 3, 'condition': 'E', 'action': 'F'},
                {'id': 4, 'condition': 'G', 'action': 'H'},
                {'id': 5, 'condition': 'I', 'action': 'J'}
            ]
        }
        with open(rules_dir / 'global_rules.json', 'w') as f:
            json.dump(original_rules, f)

        # Create mock compressed rules (simulating sweep output)
        compressed_rules_1 = {
            'rules': [
                {'id': 1, 'condition': 'A', 'action': 'B'},
                {'id': 2, 'condition': 'C', 'action': 'D'}
            ]
        }
        with open(sweeps_dir / 'rules_min_support_0.5.json', 'w') as f:
            json.dump(compressed_rules_1, f)

        compressed_rules_2 = {
            'rules': [
                {'id': 1, 'condition': 'A', 'action': 'B'}
            ]
        }
        with open(sweeps_dir / 'rules_min_support_0.8.json', 'w') as f:
            json.dump(compressed_rules_2, f)

        # Create mock traces
        trace_1 = {
            'input': {'session_id': 'test1'},
            'expected_output': {'result': 'success'}
        }
        trace_2 = {
            'input': {'session_id': 'test2'},
            'expected_output': {'result': 'success'}
        }
        with open(held_out_dir / 'session_test1.json', 'w') as f:
            json.dump(trace_1, f)
        with open(held_out_dir / 'session_test2.json', 'w') as f:
            json.dump(trace_2, f)

        yield mock_config

        # Cleanup
        import shutil
        shutil.rmtree(base_dir)

    def test_calculate_compression_ratio(self, setup_test_environment):
        """Test that compression ratio is calculated correctly."""
        config = setup_test_environment
        calculator = CompressionRatioCalculator(config)

        original_path = Path(config['base_dir']) / 'data' / 'processed' / 'rules' / 'global_rules.json'
        compressed_path = Path(config['base_dir']) / 'data' / 'processed' / 'rules' / 'sweeps' / 'rules_min_support_0.5.json'

        ratio = calculator._calculate_compression_ratio(original_path, compressed_path)

        # Original has 5 rules, compressed has 2 -> ratio = 2/5 = 0.4
        assert abs(ratio - 0.4) < 0.01

    def test_calculate_fidelity_loss(self, setup_test_environment):
        """Test that fidelity loss is calculated correctly."""
        config = setup_test_environment
        calculator = CompressionRatioCalculator(config)

        # Mock agents
        mock_baseline = MagicMock()
        mock_compressed = MagicMock()

        # Mock traces
        traces = [
            {'input': {'session_id': 'test1'}, 'expected_output': {'result': 'success'}},
            {'input': {'session_id': 'test2'}, 'expected_output': {'result': 'success'}}
        ]

        # Mock baseline to succeed on both
        mock_baseline.run.side_effect = [
            {'output': {'result': 'success'}},
            {'output': {'result': 'success'}}
        ]

        # Mock compressed to succeed on one
        mock_compressed.run.side_effect = [
            {'output': {'result': 'success'}},
            {'output': {'result': 'failure'}}
        ]

        fidelity_loss = calculator._calculate_fidelity_loss(mock_baseline, mock_compressed, traces)

        # Baseline accuracy = 2/2 = 1.0
        # Compressed accuracy = 1/2 = 0.5
        # Fidelity loss = 1 - (0.5 / 1.0) = 0.5
        assert abs(fidelity_loss - 0.5) < 0.01

    def test_calculate_trade_off_curve(self, setup_test_environment):
        """Test the full trade-off curve calculation."""
        config = setup_test_environment
        calculator = CompressionRatioCalculator(config)

        original_path = Path(config['base_dir']) / 'data' / 'processed' / 'rules' / 'global_rules.json'
        sweep_dir = Path(config['base_dir']) / 'data' / 'processed' / 'rules' / 'sweeps'

        with patch.object(calculator, '_calculate_fidelity_loss', return_value=0.2):
            trade_off_data = calculator.calculate_trade_off_curve(
                original_rules_path=original_path,
                sweep_dir=sweep_dir
            )

        assert len(trade_off_data) == 2
        assert all('threshold' in item for item in trade_off_data)
        assert all('compression_ratio' in item for item in trade_off_data)
        assert all('fidelity_loss' in item for item in trade_off_data)

    def test_save_trade_off_curve(self, setup_test_environment):
        """Test saving trade-off curve to CSV."""
        config = setup_test_environment
        calculator = CompressionRatioCalculator(config)

        trade_off_data = [
            {'threshold': 0.5, 'compression_ratio': 0.4, 'fidelity_loss': 0.1},
            {'threshold': 0.8, 'compression_ratio': 0.2, 'fidelity_loss': 0.3}
        ]

        output_path = Path(config['base_dir']) / 'data' / 'processed' / 'trade_off_curve.csv'
        calculator.save_trade_off_curve(trade_off_data, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['threshold'] == '0.5'
            assert rows[0]['compression_ratio'] == '0.4'
            assert rows[0]['fidelity_loss'] == '0.1'

    def test_missing_sweep_directory(self, mock_config):
        """Test error handling when sweep directory is missing."""
        calculator = CompressionRatioCalculator(mock_config)

        with pytest.raises(CompressionRatioCalculatorError):
            calculator.calculate_trade_off_curve(
                sweep_dir=Path(mock_config['base_dir']) / 'nonexistent'
            )

    def test_missing_original_rules(self, setup_test_environment):
        """Test error handling when original rules file is missing."""
        config = setup_test_environment
        calculator = CompressionRatioCalculator(config)

        non_existent_path = Path(config['base_dir']) / 'nonexistent' / 'rules.json'

        with pytest.raises(CompressionRatioCalculatorError):
            calculator.calculate_trade_off_curve(original_rules_path=non_existent_path)


class TestCalculateCompressionRatios:
    """Tests for the calculate_compression_ratios function."""

    def test_calculate_compression_ratios_integration(self, setup_test_environment):
        """Integration test for calculate_compression_ratios function."""
        config = setup_test_environment
        base_dir = Path(config['base_dir'])

        original_path = base_dir / 'data' / 'processed' / 'rules' / 'global_rules.json'
        sweep_dir = base_dir / 'data' / 'processed' / 'rules' / 'sweeps'
        output_path = base_dir / 'data' / 'processed' / 'trade_off_curve.csv'

        with patch('evaluation.calculate_compression_ratio.CompressionRatioCalculator._calculate_fidelity_loss', return_value=0.15):
            result = calculate_compression_ratios(
                config=config,
                original_rules_path=original_path,
                sweep_dir=sweep_dir,
                output_path=output_path
            )

        assert result.exists()
        with open(result, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0


class TestMain:
    """Tests for the main function."""

    def test_main_success(self, setup_test_environment):
        """Test main function executes successfully."""
        config = setup_test_environment
        base_dir = Path(config['base_dir'])

        # Mock get_config to return our test config
        with patch('evaluation.calculate_compression_ratio.get_config', return_value=config):
            with patch('evaluation.calculate_compression_ratio.CompressionRatioCalculator._calculate_fidelity_loss', return_value=0.1):
                # This should not raise an exception
                main()

        # Verify output file was created
        output_path = base_dir / 'data' / 'processed' / 'trade_off_curve.csv'
        assert output_path.exists()

    def test_main_error_handling(self, mock_config):
        """Test main function handles errors gracefully."""
        # Mock get_config to return a config with missing directories
        with patch('evaluation.calculate_compression_ratio.get_config', return_value=mock_config):
            with pytest.raises(SystemExit):
                main()