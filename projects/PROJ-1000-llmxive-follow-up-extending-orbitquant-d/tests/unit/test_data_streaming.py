"""
Unit tests for the optimized data streaming module.

Tests cover:
- CSV streaming loading
- Memory-mapped loading
- JSON streaming
- Caching functionality
- Batched loading
"""
import os
import json
import csv
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.data_streaming import DataLoader, ActivationLoader, MetricsLoader
from code.config import Config


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'text', 'value'])
        writer.writeheader()
        for i in range(100):
            writer.writerow({'id': i, 'text': f'prompt_{i}', 'value': i * 1.5})
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = [{'id': i, 'text': f'item_{i}', 'value': i * 2.0} for i in range(50)]
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


class TestDataLoader:
    """Tests for the DataLoader class."""
    
    def test_load_csv_streaming(self, temp_csv_file, config):
        """Test streaming CSV loading with batching."""
        loader = DataLoader(config)
        batches = list(loader.load_csv_streaming(temp_csv_file, batch_size=10))
        
        assert len(batches) == 10
        assert all(isinstance(batch, list) for batch in batches)
        assert all(len(batch) == 10 for batch in batches)
        assert all('id' in batch[0] for batch in batches)
        
    def test_load_csv_streaming_last_batch(self, temp_csv_file, config):
        """Test that the last batch handles incomplete batches correctly."""
        loader = DataLoader(config)
        batches = list(loader.load_csv_streaming(temp_csv_file, batch_size=30))
        
        assert len(batches) == 4
        assert len(batches[0]) == 30
        assert len(batches[1]) == 30
        assert len(batches[2]) == 30
        assert len(batches[3]) == 10
        
    def test_load_json_streaming(self, temp_json_file, config):
        """Test streaming JSON loading with batching."""
        loader = DataLoader(config)
        batches = list(loader.load_json_streaming(temp_json_file, batch_size=10))
        
        assert len(batches) == 5
        assert all(isinstance(batch, list) for batch in batches)
        assert all(len(batch) == 10 for batch in batches)
        
    def test_load_csv_memory_mapped(self, temp_csv_file, config):
        """Test memory-mapped CSV loading."""
        loader = DataLoader(config)
        data = loader.load_csv_memory_mapped(temp_csv_file)
        
        assert isinstance(data, np.ndarray)
        assert data.shape[0] == 100
        
    def test_cache_functionality(self, temp_csv_file, config):
        """Test data caching and retrieval."""
        loader = DataLoader(config)
        
        # First load should cache
        data1 = loader.load_and_cache_prompts(temp_csv_file)
        assert len(data1) == 100
        
        # Second load should use cache
        data2 = loader.get_cached(temp_csv_file)
        assert data1 is data2
        
    def test_cache_clear(self, temp_csv_file, config):
        """Test cache clearing functionality."""
        loader = DataLoader(config)
        loader.load_and_cache_prompts(temp_csv_file)
        assert loader.get_cached(temp_csv_file) is not None
        
        loader.clear_cache()
        assert loader.get_cached(temp_csv_file) is None
        
    def test_file_not_found(self, config):
        """Test handling of missing files."""
        loader = DataLoader(config)
        
        with pytest.raises(FileNotFoundError):
            loader.load_csv_streaming('/nonexistent/path.csv')
            
        with pytest.raises(FileNotFoundError):
            loader.load_json_streaming('/nonexistent/path.json')


class TestActivationLoader:
    """Tests for the ActivationLoader class."""
    
    def test_load_clustering_report(self, config):
        """Test loading clustering report."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report = {
                'layers': ['layer1', 'layer2'],
                'subsets': {'layer1': [0, 10], 'layer2': [10, 20]},
                'boundaries': [0, 10, 20],
                'matrices': {'layer1': [[1, 0], [0, 1]], 'layer2': [[0, 1], [1, 0]]}
            }
            json.dump(report, f)
            temp_path = f.name
        
        try:
            loader = ActivationLoader(config)
            loaded = loader.load_clustering_report(temp_path)
            
            assert loaded['layers'] == ['layer1', 'layer2']
            assert 'matrices' in loaded
        finally:
            os.unlink(temp_path)
            
    def test_load_quantized_activations(self, config):
        """Test loading quantized activations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                'layer1': [[1.0, 2.0], [3.0, 4.0]],
                'layer2': [[5.0, 6.0], [7.0, 8.0]]
            }
            json.dump(data, f)
            temp_path = f.name
        
        try:
            loader = ActivationLoader(config)
            loaded = loader.load_quantized_activations(temp_path)
            
            assert isinstance(loaded['layer1'], np.ndarray)
            assert loaded['layer1'].shape == (2, 2)
            assert loaded['layer2'].shape == (2, 2)
        finally:
            os.unlink(temp_path)
            
    def test_load_activations_batched(self, config):
        """Test batched activation loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = list(range(100))
            json.dump(data, f)
            temp_path = f.name
        
        try:
            loader = ActivationLoader(config)
            batches = list(loader.load_activations_batched(temp_path, batch_size=20))
            
            assert len(batches) == 5
            assert all(isinstance(batch, np.ndarray) for batch in batches)
        finally:
            os.unlink(temp_path)


class TestMetricsLoader:
    """Tests for the MetricsLoader class."""
    
    def test_load_metrics(self, config):
        """Test loading metrics with caching."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            metrics = {'fid': 10.5, 'clip_score': 25.3, 'mse': 0.05}
            json.dump(metrics, f)
            temp_path = f.name
        
        try:
            loader = MetricsLoader(config)
            loaded = loader.load_metrics(temp_path)
            
            assert loaded['fid'] == 10.5
            assert loaded['clip_score'] == 25.3
            
            # Test caching
            assert loader._cache[temp_path] is loaded
        finally:
            os.unlink(temp_path)
            
    def test_load_comparison_metrics(self, config):
        """Test loading baseline and dynamic metrics."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_baseline.json', delete=False) as f1:
            json.dump({'fid': 12.0, 'mse': 0.08}, f1)
            baseline_path = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='_dynamic.json', delete=False) as f2:
            json.dump({'fid': 10.5, 'mse': 0.05}, f2)
            dynamic_path = f2.name
        
        try:
            loader = MetricsLoader(config)
            baseline, dynamic = loader.load_comparison_metrics(baseline_path, dynamic_path)
            
            assert baseline['fid'] == 12.0
            assert dynamic['fid'] == 10.5
        finally:
            os.unlink(baseline_path)
            os.unlink(dynamic_path)


class TestIntegration:
    """Integration tests for the data streaming module."""
    
    def test_end_to_end_pipeline(self, config, temp_csv_file, temp_json_file):
        """Test end-to-end data loading pipeline."""
        data_loader = DataLoader(config)
        activation_loader = ActivationLoader(config)
        metrics_loader = MetricsLoader(config)
        
        # Load prompts
        prompts = data_loader.load_and_cache_prompts(temp_csv_file)
        assert len(prompts) == 100
        
        # Create and load a clustering report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'layers': ['test'], 'matrices': {'test': [[1, 0], [0, 1]]}}, f)
            report_path = f.name
        
        try:
            report = activation_loader.load_clustering_report(report_path)
            assert 'layers' in report
        finally:
            os.unlink(report_path)
            
        # Create and load metrics
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'test_metric': 1.0}, f)
            metrics_path = f.name
        
        try:
            metrics = metrics_loader.load_metrics(metrics_path)
            assert metrics['test_metric'] == 1.0
        finally:
            os.unlink(metrics_path)