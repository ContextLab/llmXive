"""
Unit tests for the batch processing optimization module.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from batch_processor import (
    initialize_batch_processing,
    process_subject_batch,
    run_optimized_pipeline,
    BATCH_SIZE,
    MAX_WORKERS
)
from performance_optimizer import (
    PerformanceProfiler,
    estimate_runtime,
    optimize_memory_usage,
    configure_parallel_processing,
    get_performance_summary
)

class TestBatchProcessor:
    """Tests for batch processing functions."""
    
    @patch('batch_processor.initialize_runtime_monitor')
    @patch('batch_processor.check_runtime_status')
    def test_initialize_batch_processing_success(self, mock_check_runtime, mock_init_monitor):
        """Test successful initialization of batch processing."""
        mock_check_runtime.return_value = True
        
        result = initialize_batch_processing()
        
        assert result is True
        mock_init_monitor.assert_called_once()
        mock_check_runtime.assert_called_once()
    
    @patch('batch_processor.check_runtime_status')
    def test_initialize_batch_processing_runtime_exceeded(self, mock_check_runtime):
        """Test initialization when runtime limit is exceeded."""
        mock_check_runtime.return_value = False
        
        result = initialize_batch_processing()
        
        assert result is False
    
    @patch('batch_processor.run_preprocessing_pipeline')
    @patch('batch_processor.process_connectivity_matrices')
    @patch('batch_processor.get_current_ram_gb')
    @patch('batch_processor.check_runtime_status')
    def test_process_subject_batch_success(
        self,
        mock_check_runtime,
        mock_get_ram,
        mock_process_metrics,
        mock_preprocess
    ):
        """Test successful processing of a subject batch."""
        mock_check_runtime.return_value = True
        mock_get_ram.return_value = 2.0
        mock_preprocess.return_value = {'success': True}
        mock_process_metrics.return_value = {'success': True}
        
        result = process_subject_batch(
            subject_ids=['sub-001', 'sub-002'],
            data_dir=Path('data/raw'),
            results_dir=Path('data/results'),
            config={}
        )
        
        assert result['status'] == 'success'
        assert len(result['subjects_processed']) == 2
        assert len(result['subjects_failed']) == 0
        assert result['runtime_seconds'] > 0
    
    @patch('batch_processor.run_preprocessing_pipeline')
    @patch('batch_processor.get_current_ram_gb')
    @patch('batch_processor.check_runtime_status')
    def test_process_subject_batch_memory_limit(
        self,
        mock_check_runtime,
        mock_get_ram,
        mock_preprocess
    ):
        """Test batch processing when memory limit is exceeded."""
        mock_check_runtime.return_value = True
        mock_get_ram.return_value = 7.0  # Above 6GB limit
        
        result = process_subject_batch(
            subject_ids=['sub-001'],
            data_dir=Path('data/raw'),
            results_dir=Path('data/results'),
            config={}
        )
        
        assert 'sub-001' in result['subjects_failed']
        assert len(result['subjects_processed']) == 0
    
    @patch('batch_processor.run_preprocessing_pipeline')
    @patch('batch_processor.get_current_ram_gb')
    @patch('batch_processor.check_runtime_status')
    def test_process_subject_batch_runtime_exceeded(
        self,
        mock_check_runtime,
        mock_get_ram,
        mock_preprocess
    ):
        """Test batch processing when runtime limit is exceeded."""
        mock_check_runtime.return_value = False
        mock_get_ram.return_value = 2.0
        
        result = process_subject_batch(
            subject_ids=['sub-001'],
            data_dir=Path('data/raw'),
            results_dir=Path('data/results'),
            config={}
        )
        
        assert result['status'] == 'runtime_limit_exceeded'
        assert len(result['subjects_processed']) == 0

class TestPerformanceOptimizer:
    """Tests for performance optimization functions."""
    
    def test_estimate_runtime_within_limit(self):
        """Test runtime estimation for workload within limits."""
        estimate = estimate_runtime(num_subjects=10, avg_time_per_subject=180)
        
        assert estimate['num_subjects'] == 10
        assert estimate['estimated_total_hours'] < 1
        assert estimate['within_limit'] is True
    
    def test_estimate_runtime_exceeds_limit(self):
        """Test runtime estimation for workload exceeding limits."""
        estimate = estimate_runtime(num_subjects=100, avg_time_per_subject=300)
        
        assert estimate['num_subjects'] == 100
        assert estimate['estimated_total_hours'] > 5
        assert estimate['within_limit'] is False
    
    def test_configure_parallel_processing_auto(self):
        """Test automatic parallel processing configuration."""
        workers = configure_parallel_processing(max_workers=None)
        
        assert workers >= 1
        assert workers <= 75  # Reasonable upper bound
    
    def test_get_performance_summary(self):
        """Test performance summary generation."""
        summary = get_performance_summary()
        
        assert 'current_ram_gb' in summary
        assert 'elapsed_hours' in summary
        assert 'memory_limit_gb' in summary
        assert 'runtime_limit_hours' in summary
        assert 'cpu_count' in summary
    
    def test_performance_profiler_context_manager(self):
        """Test performance profiler as context manager."""
        with PerformanceProfiler("test_section") as profiler:
            time.sleep(0.1)  # Simulate some work
        
        assert profiler.start_time is not None
        assert profiler.end_time is not None
        assert profiler.end_time >= profiler.start_time

class TestBatchConstants:
    """Tests for batch processing constants."""
    
    def test_batch_size_positive(self):
        """Test that batch size is positive."""
        assert BATCH_SIZE > 0
    
    def test_max_workers_positive(self):
        """Test that max workers is positive."""
        assert MAX_WORKERS > 0
    
    def test_batch_size_reasonable(self):
        """Test that batch size is reasonable for memory constraints."""
        assert BATCH_SIZE <= 20  # Should be small enough for memory limits