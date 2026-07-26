"""
Unit tests for batch generation functionality (T018).

Tests verify:
- Correct generator instantiation for each topology class
- Retry logic behavior on disconnected networks
- Batch size adjustment logic
- Proper logging and metadata generation
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import networkx as nx

from code.src.generators.batch_runner import (
    get_generator,
    generate_single_graph,
    generate_batch,
    main
)
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.retry_logic import RetryHandler
from code.src.generators.timeout import TimeoutHandler


class TestGetGenerator:
    """Tests for the get_generator factory function."""

    def test_er_generator_instantiation(self):
        """Test that Erdős-Rényi generator is correctly instantiated."""
        config = {'er_params': {'n': 10, 'p': 0.3}}
        generator = get_generator('erdos_renyi', config)
        assert isinstance(generator, ErdosRenyiGenerator)

    def test_sw_generator_instantiation(self):
        """Test that Watts-Strogatz generator is correctly instantiated."""
        config = {'sw_params': {'n': 10, 'k': 4, 'p': 0.1}}
        generator = get_generator('watts_strogatz', config)
        assert isinstance(generator, WattsStrogatzGenerator)

    def test_sf_generator_instantiation(self):
        """Test that Barabási-Albert generator is correctly instantiated."""
        config = {'sf_params': {'n': 10, 'm': 2}}
        generator = get_generator('barabasi_albert', config)
        assert isinstance(generator, BarabasiAlbertGenerator)

    def test_unknown_topology_raises_error(self):
        """Test that unknown topology class raises ValueError."""
        config = {}
        with pytest.raises(ValueError, match="Unknown topology class"):
            get_generator('unknown_topology', config)


class TestGenerateSingleGraph:
    """Tests for single graph generation with retry and timeout handling."""

    @pytest.fixture
    def mock_generator(self):
        """Create a mock generator that returns a connected graph."""
        mock = MagicMock()
        mock.generate.return_value = nx.erdos_renyi_graph(10, 0.3, seed=42)
        mock.is_connected.return_value = True
        mock.get_params.return_value = {'n': 10, 'p': 0.3}
        mock.__class__.__name__ = 'MockGenerator'
        return mock

    @pytest.fixture
    def retry_handler(self):
        return RetryHandler(max_retries=5, timeout_factor=1.5)

    @pytest.fixture
    def timeout_handler(self):
        return TimeoutHandler(default_timeout=300)

    def test_successful_generation(self, mock_generator, retry_handler, timeout_handler):
        """Test that a graph is successfully generated."""
        graph, status = generate_single_graph(
            generator=mock_generator,
            topology_class='test',
            seed=42,
            retry_handler=retry_handler,
            timeout_handler=timeout_handler,
            run_id='test_run'
        )
        assert graph is not None
        assert status == 'SUCCESS'
        assert graph.number_of_nodes() == 10

    def test_disconnected_graph_handling(self, mock_generator, retry_handler, timeout_handler):
        """Test that disconnected graphs are handled correctly."""
        mock_generator.is_connected.return_value = False
        graph, status = generate_single_graph(
            generator=mock_generator,
            topology_class='test',
            seed=42,
            retry_handler=retry_handler,
            timeout_handler=timeout_handler,
            run_id='test_run'
        )
        assert graph is None
        assert '[DISCONNECTED_NETWORK_FAILURE]' in status


class TestGenerateBatch:
    """Tests for batch generation logic."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration dictionary."""
        return {
            'global_seed': 42,
            'er_params': {'n': 10, 'p': 0.3},
            'sw_params': {'n': 10, 'k': 4, 'p': 0.1},
            'sf_params': {'n': 10, 'm': 2},
            'retry_params': {'max_retries': 3, 'timeout_factor': 1.5},
            'timeout_params': {'default_timeout_seconds': 300},
            'stratification_params': {
                'bins': [0.1, 0.3, 0.5],
                'target_counts': {},
                'tolerance': 0.05
            },
            'rejection_threshold': 0.4,
            'rejection_adjustment_factor': 1.5
        }

    def test_batch_generation_creates_files(self, temp_output_dir, mock_config):
        """Test that batch generation creates graph files and metadata."""
        with patch('code.src.generators.batch_runner.get_generator') as mock_get_gen:
            mock_gen = MagicMock()
            mock_graph = nx.erdos_renyi_graph(10, 0.3, seed=42)
            mock_gen.generate.return_value = mock_graph
            mock_gen.is_connected.return_value = True
            mock_gen.get_params.return_value = {'n': 10, 'p': 0.3}
            mock_gen.__class__.__name__ = 'MockGenerator'
            mock_get_gen.return_value = mock_gen

            result = generate_batch(
                topology_class='erdos_renyi',
                config=mock_config,
                batch_size=3,
                output_dir=temp_output_dir,
                run_id='test_run'
            )

            # Verify result structure
            assert result['topology_class'] == 'erdos_renyi'
            assert result['actual_size'] == 3
            assert result['total_attempts'] >= 3
            assert 'generated_graphs' in result
            assert 'failed_graphs' in result

            # Verify files were created
            assert len(list(temp_output_dir.glob('*.gpickle'))) == 3
            assert len(list((temp_output_dir / 'metadata').glob('*.json'))) == 3

    def test_sample_size_adjustment_logic(self, temp_output_dir, mock_config):
        """Test that sample size adjustment is triggered when rejection rate is high."""
        mock_config['rejection_threshold'] = 0.1  # Low threshold to trigger adjustment
        mock_config['rejection_adjustment_factor'] = 2.0

        with patch('code.src.generators.batch_runner.get_generator') as mock_get_gen:
            mock_gen = MagicMock()
            # First attempt fails, second succeeds
            mock_gen.generate.side_effect = [None, nx.erdos_renyi_graph(10, 0.3, seed=42)]
            mock_gen.is_connected.return_value = True
            mock_gen.get_params.return_value = {'n': 10, 'p': 0.3}
            mock_gen.__class__.__name__ = 'MockGenerator'
            mock_get_gen.return_value = mock_gen

            with patch('code.src.generators.batch_runner.log_metric') as mock_log:
                result = generate_batch(
                    topology_class='erdos_renyi',
                    config=mock_config,
                    batch_size=2,
                    output_dir=temp_output_dir,
                    run_id='test_run'
                )

                # Verify adjustment was logged
                adjustment_logs = [
                    call for call in mock_log.call_args_list
                    if 'sample_size_adjustment' in str(call)
                ]
                assert len(adjustment_logs) > 0

    def test_stratified_sampling(self, temp_output_dir, mock_config):
        """Test that stratified sampling respects bin quotas."""
        mock_config['stratification_params']['target_counts'] = {0.1: 1, 0.3: 1, 0.5: 1}

        with patch('code.src.generators.batch_runner.get_generator') as mock_get_gen:
            mock_gen = MagicMock()
            mock_graph = nx.erdos_renyi_graph(10, 0.3, seed=42)
            mock_gen.generate.return_value = mock_graph
            mock_gen.is_connected.return_value = True
            mock_gen.get_params.return_value = {'n': 10, 'p': 0.3}
            mock_gen.__class__.__name__ = 'MockGenerator'
            mock_get_gen.return_value = mock_gen

            with patch('code.src.generators.binning.classify_graph', return_value=0.1):
                result = generate_batch(
                    topology_class='erdos_renyi',
                    config=mock_config,
                    batch_size=3,
                    output_dir=temp_output_dir,
                    run_id='test_run'
                )

                # Verify bin distribution
                assert result['bin_distribution'][0.1] == 1


class TestMain:
    """Tests for the main entry point."""

    def test_main_with_valid_config(self, temp_dir, mock_config):
        """Test that main() runs successfully with valid arguments."""
        # Create a temporary config file
        config_path = temp_dir / "test_config.yaml"
        # Note: In a real test, we'd write YAML, but for now we mock load_config
        with patch('code.src.generators.batch_runner.load_config', return_value=mock_config):
            with patch('code.src.generators.batch_runner.get_generator') as mock_get_gen:
                mock_gen = MagicMock()
                mock_graph = nx.erdos_renyi_graph(10, 0.3, seed=42)
                mock_gen.generate.return_value = mock_graph
                mock_gen.is_connected.return_value = True
                mock_gen.get_params.return_value = {'n': 10, 'p': 0.3}
                mock_gen.__class__.__name__ = 'MockGenerator'
                mock_get_gen.return_value = mock_gen

                # Mock sys.argv
                with patch('sys.argv', [
                    'batch_runner.py',
                    '--config', str(config_path),
                    '--output', str(temp_dir / 'output'),
                    '--batch-size', '2',
                    '--topology', 'erdos_renyi'
                ]):
                    result = main()
                    assert result == 0

    def test_main_creates_summary_file(self, temp_dir, mock_config):
        """Test that main() creates a batch_summary.json file."""
        config_path = temp_dir / "test_config.yaml"
        output_dir = temp_dir / 'output'

        with patch('code.src.generators.batch_runner.load_config', return_value=mock_config):
            with patch('code.src.generators.batch_runner.get_generator') as mock_get_gen:
                mock_gen = MagicMock()
                mock_graph = nx.erdos_renyi_graph(10, 0.3, seed=42)
                mock_gen.generate.return_value = mock_graph
                mock_gen.is_connected.return_value = True
                mock_gen.get_params.return_value = {'n': 10, 'p': 0.3}
                mock_gen.__class__.__name__ = 'MockGenerator'
                mock_get_gen.return_value = mock_gen

                with patch('sys.argv', [
                    'batch_runner.py',
                    '--config', str(config_path),
                    '--output', str(output_dir),
                    '--batch-size', '1'
                ]):
                    main()

                # Verify summary file exists
                summary_path = output_dir / "batch_summary.json"
                assert summary_path.exists()
                with open(summary_path) as f:
                    summary = json.load(f)
                assert 'run_id' in summary
                assert 'results' in summary