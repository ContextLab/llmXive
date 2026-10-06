"""
Unit tests for the Router Inference Pipeline (T029).
Tests the orchestration logic without requiring full model execution.
"""
import pytest
import json
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from config import Config
from run_router_inference import RouterInferencePipeline


@pytest.fixture
def temp_config():
    """Create a temporary config for testing."""
    config = Config()
    config.device = "cpu"  # Force CPU for tests
    config.default_entropy_fallback = 0.5
    config.output_dir = Path(tempfile.mkdtemp())
    config.prompts_test_path = None
    config.clustering_report_path = None
    config.router_inference_output_path = None
    return config


@pytest.fixture
def sample_prompts_csv():
    """Create a temporary CSV file with sample prompts."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'caption'])
        writer.writeheader()
        writer.writerow({'id': 'prompt_1', 'caption': 'A red car'})
        writer.writerow({'id': 'prompt_2', 'caption': 'A blue sky'})
        writer.writerow({'id': 'prompt_3', 'caption': 'A green forest'})
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def sample_matrices_json():
    """Create a temporary JSON file with sample rotation matrices."""
    # Create 16 dummy matrices of shape (D,) where D=64
    matrices = []
    for i in range(16):
        matrix = np.random.randn(64).astype(np.float32)
        # Normalize to unit norm
        matrix = matrix / np.linalg.norm(matrix)
        matrices.append(matrix.tolist())
    
    data = {
        'layers': ['layer_1', 'layer_2'],
        'matrices': matrices,
        'boundaries': [0.1, 0.3, 0.5, 0.7, 0.9]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


class TestRouterInferencePipeline:
    """Tests for the RouterInferencePipeline class."""

    def test_load_test_prompts(self, temp_config, sample_prompts_csv):
        """Test loading prompts from CSV."""
        pipeline = RouterInferencePipeline(temp_config)
        prompts = pipeline.load_test_prompts(sample_prompts_csv)
        
        assert len(prompts) == 3
        assert prompts[0]['id'] == 'prompt_1'
        assert prompts[0]['caption'] == 'A red car'
        assert prompts[1]['id'] == 'prompt_2'
        assert prompts[2]['id'] == 'prompt_3'

    def test_load_test_prompts_file_not_found(self, temp_config):
        """Test that loading from a non-existent file raises FileNotFoundError."""
        pipeline = RouterInferencePipeline(temp_config)
        with pytest.raises(FileNotFoundError):
            pipeline.load_test_prompts("non_existent_file.csv")

    def test_load_rotation_matrices(self, temp_config, sample_matrices_json):
        """Test loading rotation matrices from JSON."""
        pipeline = RouterInferencePipeline(temp_config)
        matrices = pipeline.load_rotation_matrices(sample_matrices_json)
        
        assert len(matrices) == 16
        assert matrices[0].shape == (64,)
        # Check unit norm
        assert np.allclose(np.linalg.norm(matrices[0]), 1.0)

    def test_load_rotation_matrices_file_not_found(self, temp_config):
        """Test that loading from a non-existent file raises FileNotFoundError."""
        pipeline = RouterInferencePipeline(temp_config)
        with pytest.raises(FileNotFoundError):
            pipeline.load_rotation_matrices("non_existent_file.json")

    @patch('run_router_inference.EntropyProxy')
    def test_compute_entropy_scores(self, mock_entropy_proxy_class, temp_config, sample_prompts_csv):
        """Test entropy computation."""
        # Mock the entropy proxy
        mock_proxy_instance = Mock()
        mock_proxy_instance.compute_entropy.side_effect = [0.2, 0.5, 0.8]
        mock_entropy_proxy_class.return_value = mock_proxy_instance
        
        pipeline = RouterInferencePipeline(temp_config)
        prompts = pipeline.load_test_prompts(sample_prompts_csv)
        entropy_scores = pipeline.compute_entropy_scores(prompts)
        
        assert len(entropy_scores) == 3
        assert entropy_scores['prompt_1'] == 0.2
        assert entropy_scores['prompt_2'] == 0.5
        assert entropy_scores['prompt_3'] == 0.8

    @patch('run_router_inference.EntropyProxy')
    def test_compute_entropy_scores_with_fallback(self, mock_entropy_proxy_class, temp_config, sample_prompts_csv):
        """Test entropy computation with proxy failure fallback."""
        # Mock the entropy proxy to fail on one prompt
        mock_proxy_instance = Mock()
        mock_proxy_instance.compute_entropy.side_effect = [0.2, Exception("API Error"), 0.8]
        mock_entropy_proxy_class.return_value = mock_proxy_instance
        
        pipeline = RouterInferencePipeline(temp_config)
        prompts = pipeline.load_test_prompts(sample_prompts_csv)
        entropy_scores = pipeline.compute_entropy_scores(prompts)
        
        assert len(entropy_scores) == 3
        assert entropy_scores['prompt_1'] == 0.2
        assert entropy_scores['prompt_2'] == temp_config.default_entropy_fallback
        assert entropy_scores['prompt_3'] == 0.8

    @patch('run_router_inference.ModelLoader')
    @patch('run_router_inference.W2A4Engine')
    @patch('run_router_inference.EntropyRouter')
    def test_generate_images_with_router(self, mock_router_class, mock_w2a4_class, mock_loader_class, 
                                         temp_config, sample_prompts_csv, sample_matrices_json):
        """Test image generation with dynamic routing."""
        # Setup mocks
        mock_router_instance = Mock()
        mock_router_instance.select_matrix.side_effect = [0, 1, 2]
        mock_router_class.return_value = mock_router_instance
        
        mock_w2a4_instance = Mock()
        mock_w2a4_class.return_value = mock_w2a4_instance
        
        mock_loader_instance = Mock()
        mock_model = Mock()
        mock_model.generate.return_value = torch.randn(3, 64, 64)  # Dummy image
        mock_loader_instance.load_model.return_value = mock_model
        mock_loader_class.return_value = mock_loader_instance
        
        pipeline = RouterInferencePipeline(temp_config)
        prompts = pipeline.load_test_prompts(sample_prompts_csv)
        entropy_scores = {'prompt_1': 0.2, 'prompt_2': 0.5, 'prompt_3': 0.8}
        matrices = pipeline.load_rotation_matrices(sample_matrices_json)
        
        pipeline.initialize_router(matrices)
        pipeline.initialize_dit_and_engine()
        
        results = pipeline.generate_images_with_router(prompts, entropy_scores)
        
        assert len(results) == 3
        assert results[0]['status'] == 'success'
        assert results[0]['selected_matrix_index'] == 0
        assert results[1]['selected_matrix_index'] == 1
        assert results[2]['selected_matrix_index'] == 2
        assert results[0]['generation_time_sec'] > 0

    def test_save_results(self, temp_config):
        """Test saving results to JSON."""
        pipeline = RouterInferencePipeline(temp_config)
        results = [
            {'prompt_id': '1', 'status': 'success', 'entropy': 0.5},
            {'prompt_id': '2', 'status': 'failed', 'error': 'Test error'}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            pipeline.save_results(results, output_path)
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 2
            assert saved_data[0]['prompt_id'] == '1'
            assert saved_data[1]['status'] == 'failed'
        finally:
            os.unlink(output_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
