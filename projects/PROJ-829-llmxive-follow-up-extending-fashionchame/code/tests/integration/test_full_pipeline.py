"""
Integration tests for T040: Full pipeline execution.

Tests that the full pipeline (loader -> filter -> stratify -> adapter -> metrics)
can execute end-to-end with mocked components where necessary.
"""
import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.data.loader import load_config
from src.data.feasibility_filter import FeasibilityFilter, GarmentFeatureClass
from src.data.stratified_subset import stratify_samples
from src.pipeline.runner import process_single_sample_with_bottleneck_analysis
from src.metrics.fidelity import compute_fidelity_scores
from src.pipeline.reporter import aggregate_scores_by_class


class TestPipelineIntegration:
    """Integration tests for the full benchmark pipeline."""

    def test_config_loading(self):
        """Test that configuration can be loaded from settings.yaml."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
        seed: 42
        streaming_chunk_size: 100
        latency_threshold_ms: 50
        optical_flow_threshold: 0.05
        vlm_confidence_threshold: 0.8
        """)
            config_path = f.name
        
        try:
            config = load_config(Path(config_path))
            
            assert config is not None
            assert config['seed'] == 42
            assert config['latency_threshold_ms'] == 50
            assert config['vlm_confidence_threshold'] == 0.8
        finally:
            Path(config_path).unlink()

    @patch('src.data.feasibility_filter.FeasibilityFilter.verify_prompt_with_vlm')
    def test_feasibility_filter_integration(self, mock_vlm):
        """Test feasibility filter with mocked VLM."""
        # Mock VLM to return high confidence
        mock_vlm.return_value = {
            'confidence': 0.95,
            'verified': True,
            'reason': 'Prompt is clear and unambiguous'
        }
        
        # Create a mock sample
        mock_sample = {
            'image_id': 'test_001',
            'prompt': 'A red dress on a model walking',
            'attributes': {
                'garment_color': 'red',
                'garment_pattern': 'solid',
                'garment_texture': 'smooth'
            },
            'optical_flow_magnitude': 0.1
        }
        
        filter_instance = FeasibilityFilter(
            vlm_confidence_threshold=0.8,
            optical_flow_threshold=0.05
        )
        
        result = filter_instance.filter_sample(mock_sample)
        
        assert result is not None
        assert result['image_id'] == 'test_001'
        assert result['verified'] is True
        assert result['confidence'] == 0.95

    def test_stratified_sampling(self):
        """Test stratified sampling logic."""
        # Create sample data with known distribution
        samples = [
            {'id': f'00{i}', 'class': 'color'} for i in range(10)
        ] + [
            {'id': f'0{i}', 'class': 'pattern'} for i in range(10)
        ] + [
            {'id': f'1{i}', 'class': 'texture'} for i in range(10)
        ]
        
        # Stratify to get 2 samples per class
        stratified = stratify_samples(
            samples=samples,
            class_field='class',
            samples_per_class=2,
            seed=42
        )
        
        assert len(stratified) == 6  # 2 per class * 3 classes
        
        # Count per class
        class_counts = {}
        for sample in stratified:
            cls = sample['class']
            class_counts[cls] = class_counts.get(cls, 0) + 1
        
        assert class_counts['color'] == 2
        assert class_counts['pattern'] == 2
        assert class_counts['texture'] == 2

    @patch('src.pipeline.runner.TextCrossAttentionAdapter')
    @patch('src.pipeline.runner.ensure_cpu_only_execution')
    def test_single_sample_processing(self, mock_cpu, mock_adapter):
        """Test processing a single sample through the pipeline."""
        # Setup mocks
        mock_cpu.return_value = None
        
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.generate.return_value = {
            'generated_frames': [MagicMock()],
            'latency': 0.045
        }
        mock_adapter.return_value = mock_adapter_instance
        
        # Mock sample
        mock_sample = {
            'image_id': 'test_001',
            'prompt': 'Test prompt',
            'reference_image': MagicMock(),
            'attributes': {'garment_color': 'red'}
        }
        
        result = process_single_sample_with_bottleneck_analysis(
            sample=mock_sample,
            adapter=mock_adapter_instance,
            latency_threshold_ms=50
        )
        
        assert result is not None
        assert 'image_id' in result
        assert 'latency_ms' in result
        assert result['latency_ms'] >= 0

    def test_fidelity_score_computation(self):
        """Test fidelity score computation with mock images."""
        # Create mock images (we'll use random tensors)
        import torch
        mock_ref = torch.rand(3, 224, 224)
        mock_gen = torch.rand(3, 224, 224)
        
        # Compute scores
        scores = compute_fidelity_scores(
            reference_images=[mock_ref],
            generated_images=[mock_gen]
        )
        
        assert isinstance(scores, list)
        assert len(scores) == 1
        assert 'lpips' in scores[0]
        assert 'ssim' in scores[0]
        assert 0 <= scores[0]['lpips'] <= 1
        assert 0 <= scores[0]['ssim'] <= 1

    def test_reporter_aggregation(self):
        """Test that reporter correctly aggregates scores by class."""
        # Create mock raw scores
        raw_scores = [
            {'image_id': '001', 'class': 'color', 'lpips': 0.1, 'ssim': 0.9},
            {'image_id': '002', 'class': 'color', 'lpips': 0.2, 'ssim': 0.8},
            {'image_id': '003', 'class': 'pattern', 'lpips': 0.15, 'ssim': 0.85},
            {'image_id': '004', 'class': 'texture', 'lpips': 0.25, 'ssim': 0.75},
        ]
        
        # Aggregate
        aggregated = aggregate_scores_by_class(raw_scores)
        
        assert isinstance(aggregated, dict)
        assert 'color' in aggregated
        assert 'pattern' in aggregated
        assert 'texture' in aggregated
        
        assert aggregated['color']['mean_lpips'] == 0.15
        assert aggregated['color']['mean_ssim'] == 0.85
        assert aggregated['pattern']['mean_lpips'] == 0.15
        assert aggregated['texture']['mean_lpips'] == 0.25
