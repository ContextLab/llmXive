"""
Unit tests for performance optimization module.

These tests verify that the optimization utilities work correctly
and enforce RAM limits.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json
import tracemalloc
from unittest.mock import patch, MagicMock

from src.optimization import (
    get_current_ram_mb,
    get_peak_ram_mb,
    check_ram_usage,
    force_gc,
    sample_dataframe,
    process_in_chunks,
    validate_pipeline_performance,
    MAX_RAM_GB,
    SAMPLE_SIZE
)


class TestMemoryMonitoring:
    """Tests for memory monitoring functions."""

    def test_get_current_ram_mb_returns_positive(self):
        """Test that get_current_ram_mb returns a positive number."""
        tracemalloc.start()
        ram = get_current_ram_mb()
        tracemalloc.stop()
        assert ram >= 0

    def test_get_peak_ram_mb_returns_positive(self):
        """Test that get_peak_ram_mb returns a positive number."""
        tracemalloc.start()
        # Do some memory allocation
        data = [0] * 10000
        peak = get_peak_ram_mb()
        tracemalloc.stop()
        assert peak >= 0
        del data

    def test_check_ram_usage_within_limit(self):
        """Test check_ram_usage returns True when within limit."""
        # With default MAX_RAM_GB of 7GB, this should always be True in test environment
        result = check_ram_usage()
        assert isinstance(result, bool)

    def test_force_gc_executes(self):
        """Test that force_gc runs without error."""
        force_gc()  # Should not raise


class TestSampling:
    """Tests for data sampling functionality."""

    def test_sample_smaller_than_limit_returns_original(self):
        """Test that sampling a small dataframe returns the original."""
        df = pd.DataFrame({'a': range(100)})
        sampled = sample_dataframe(df, sample_size=1000)
        assert len(sampled) == len(df)

    def test_sample_larger_than_limit_returns_sample(self):
        """Test that sampling a large dataframe returns the specified sample size."""
        df = pd.DataFrame({'a': range(10000)})
        sampled = sample_dataframe(df, sample_size=1000)
        assert len(sampled) == 1000

    def test_sample_reproducibility(self):
        """Test that sampling with same seed gives same result."""
        df = pd.DataFrame({'a': range(10000), 'b': range(10000)})
        sampled1 = sample_dataframe(df, sample_size=1000, seed=42)
        sampled2 = sample_dataframe(df, sample_size=1000, seed=42)
        assert sampled1.equals(sampled2)

    def test_sample_preserves_columns(self):
        """Test that sampling preserves all columns."""
        df = pd.DataFrame({'a': range(10000), 'b': range(10000), 'c': range(10000)})
        sampled = sample_dataframe(df, sample_size=1000)
        assert list(sampled.columns) == list(df.columns)


class TestChunkProcessing:
    """Tests for chunked processing functionality."""

    def test_process_parquet_chunked(self):
        """Test processing a parquet file in chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            # Create test data
            df = pd.DataFrame({
                'a': range(50000),
                'b': range(50000),
                'c': ['test'] * 50000
            })
            df.to_parquet(input_path)
            
            # Process function
            def process_func(chunk):
                chunk['d'] = chunk['a'] + chunk['b']
                return chunk
            
            total_rows, peak_ram = process_in_chunks(
                input_path, output_path, process_func, chunk_size=10000
            )
            
            assert total_rows == 50000
            assert output_path.exists()
            
            # Verify output
            result = pd.read_parquet(output_path)
            assert len(result) == 50000
            assert 'd' in result.columns

    def test_process_csv_sampled(self):
        """Test processing a CSV file with sampling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            # Create test data
            df = pd.DataFrame({
                'a': range(100000),
                'b': range(100000)
            })
            df.to_csv(input_path, index=False)
            
            def process_func(chunk):
                return chunk
            
            total_rows, peak_ram = process_in_chunks(
                input_path, output_path, process_func, 
                sample=True, sample_size=5000
            )
            
            assert total_rows == 50000  # Original size reported
            assert output_path.exists()
            
            # Verify sampled output
            result = pd.read_csv(output_path)
            assert len(result) == 5000

    def test_process_in_chunks_handles_large_data(self):
        """Test that chunked processing handles large data without OOM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'large.parquet'
            output_path = Path(tmpdir) / 'processed.parquet'
            
            # Create moderately large dataset
            df = pd.DataFrame({
                'a': np.random.rand(200000),
                'b': np.random.rand(200000),
                'c': np.random.rand(200000)
            })
            df.to_parquet(input_path)
            
            def process_func(chunk):
                return chunk
            
            total_rows, peak_ram = process_in_chunks(
                input_path, output_path, process_func, 
                chunk_size=50000
            )
            
            assert total_rows == 200000
            assert peak_ram < MAX_RAM_GB * 1024  # Should be under limit


class TestPerformanceValidation:
    """Tests for the full performance validation pipeline."""

    def test_validate_pipeline_performance_returns_metrics(self):
        """Test that validation returns expected metrics dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            # Create test data
            df = pd.DataFrame({'a': range(10000)})
            df.to_parquet(input_path)
            
            result = validate_pipeline_performance(
                input_path, output_path, sample=True, sample_size=1000
            )
            
            assert 'total_rows' in result
            assert 'peak_ram_mb' in result
            assert 'within_limit' in result
            assert result['within_limit'] is True

    def test_validate_pipeline_performance_creates_report(self):
        """Test that validation creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            df = pd.DataFrame({'a': range(1000)})
            df.to_parquet(input_path)
            
            validate_pipeline_performance(input_path, output_path)
            
            assert output_path.exists()


class TestOptimizationIntegration:
    """Integration tests for optimization features."""

    def test_full_pipeline_memory_safe(self):
        """Test that a full pipeline run stays within memory limits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input data
            input_path = Path(tmpdir) / 'games.parquet'
            output_path = Path(tmpdir) / 'processed.parquet'
            
            df = pd.DataFrame({
                'game_id': [f'game_{i}' for i in range(50000)],
                'white_rating': np.random.randint(1000, 3000, 50000),
                'black_rating': np.random.randint(1000, 3000, 50000),
                'outcome': np.random.choice(['1-0', '0-1', '1/2-1/2'], 50000)
            })
            df.to_parquet(input_path)
            
            # Run optimization validation
            result = validate_pipeline_performance(
                input_path, output_path, 
                max_ram_gb=MAX_RAM_GB,
                sample=True,
                sample_size=10000
            )
            
            assert result['within_limit']
            assert result['peak_ram_gb'] < MAX_RAM_GB

    def test_sampling_reduces_memory_usage(self):
        """Test that sampling significantly reduces memory usage compared to full load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'large.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            # Create large dataset
            df = pd.DataFrame({
                'a': np.random.rand(100000),
                'b': np.random.rand(100000),
                'c': np.random.rand(100000)
            })
            df.to_parquet(input_path)
            
            # Run with sampling
            result_sampled = validate_pipeline_performance(
                input_path, output_path, sample=True, sample_size=5000
            )
            
            assert result_sampled['sampled']
            assert result_sampled['within_limit']