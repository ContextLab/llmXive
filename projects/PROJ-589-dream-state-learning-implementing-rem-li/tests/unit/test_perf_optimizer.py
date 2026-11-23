"""
Unit tests for performance optimization utilities.
"""
import pytest
import torch
from torch.utils.data import Dataset
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from config import Config
from utils.perf_optimizer import (
    BatchingStrategy,
    OptimizedDataset,
    PrefetchDataLoader,
    optimize_memory_for_training,
    efficient_batch_training,
    get_optimization_report
)
from utils.memory_monitor import MemoryMonitor


class MockTokenizer:
    """Mock tokenizer for testing."""
    
    def __call__(self, text, max_length=512, padding='max_length', truncation=True, return_tensors='pt'):
        # Create mock tokenized output
        input_ids = torch.randint(0, 1000, (1, max_length))
        attention_mask = torch.ones(1, max_length)
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask
        }


class TestBatchingStrategy:
    """Tests for BatchingStrategy class."""
    
    def test_initialization(self):
        config = Config()
        strategy = BatchingStrategy(config, initial_batch_size=8)
        
        assert strategy.current_batch_size == 8
        assert strategy.initial_batch_size == 8
        assert strategy.min_batch_size == 1
        assert strategy.max_batch_size == config.max_batch_size
    
    def test_adjust_batch_size_no_memory_pressure(self):
        config = Config()
        strategy = BatchingStrategy(config, initial_batch_size=8)
        
        # Simulate low memory usage
        batch_size, grad_accum = strategy.adjust_batch_size(10, peak_memory_kb=1000000)
        
        assert batch_size == 8
        assert grad_accum == 1
    
    def test_adjust_batch_size_memory_pressure(self):
        config = Config()
        strategy = BatchingStrategy(config, initial_batch_size=8)
        
        # Simulate high memory usage (above threshold)
        high_memory_kb = int(config.max_memory_gb * 1024 * 1024 * 0.9)
        batch_size, grad_accum = strategy.adjust_batch_size(10, peak_memory_kb=high_memory_kb)
        
        assert batch_size < 8
        assert grad_accum > 1
    
    def test_get_effective_batch_size(self):
        config = Config()
        strategy = BatchingStrategy(config, initial_batch_size=8)
        
        effective = strategy.get_effective_batch_size()
        assert effective == 8
        
        # Simulate gradient accumulation
        strategy.current_batch_size = 4
        strategy.gradient_accumulation_steps = 2
        effective = strategy.get_effective_batch_size()
        assert effective == 8


class TestOptimizedDataset:
    """Tests for OptimizedDataset class."""
    
    def test_initialization(self):
        mock_tokenizer = MockTokenizer()
        data = [{'text': 'test'} for _ in range(10)]
        
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128, use_cache=True)
        
        assert len(dataset) == 10
        assert dataset.max_length == 128
        assert dataset.use_cache is True
    
    def test_getitem(self):
        mock_tokenizer = MockTokenizer()
        data = [{'text': 'test sample'}]
        
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128)
        item = dataset[0]
        
        assert 'input_ids' in item
        assert 'attention_mask' in item
        assert item['input_ids'].shape[0] == 128
    
    def test_cache_behavior(self):
        mock_tokenizer = MockTokenizer()
        data = [{'text': f'sample_{i}'} for i in range(5)]
        
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128, use_cache=True, cache_size=2)
        
        # Access items to populate cache
        _ = dataset[0]
        _ = dataset[1]
        _ = dataset[0]  # Should be cached
        
        assert len(dataset._cache) <= 2


class TestPrefetchDataLoader:
    """Tests for PrefetchDataLoader class."""
    
    def test_initialization(self):
        mock_tokenizer = MockTokenizer()
        data = [{'text': 'test'} for _ in range(20)]
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128)
        
        dataloader = PrefetchDataLoader(dataset, batch_size=4, num_workers=0)
        
        assert dataloader.batch_size == 4
        assert len(dataloader) > 0
    
    def test_iteration(self):
        mock_tokenizer = MockTokenizer()
        data = [{'text': 'test'} for _ in range(20)]
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128)
        
        dataloader = PrefetchDataLoader(dataset, batch_size=4, num_workers=0)
        
        batches = list(dataloader)
        assert len(batches) > 0
        assert 'input_ids' in batches[0]
        assert 'attention_mask' in batches[0]


class TestOptimizeMemoryForTraining:
    """Tests for optimize_memory_for_training function."""
    
    def test_gradient_checkpointing(self):
        config = Config()
        model = torch.nn.Transformer(d_model=16, nhead=2, num_encoder_layers=1, num_decoder_layers=1)
        
        # Mock gradient_checkpointing_enable
        model.gradient_checkpointing_enable = Mock()
        
        optimize_memory_for_training(model, config)
        
        # Should attempt to enable gradient checkpointing
        model.gradient_checkpointing_enable.assert_called_once()
    
    def test_dtype_conversion(self):
        config = Config()
        config.dtype = torch.float16
        model = torch.nn.Linear(10, 10)
        
        optimize_memory_for_training(model, config)
        
        # On CPU, dtype conversion might not happen, but function should not crash
        assert model is not None


class TestEfficientBatchTraining:
    """Tests for efficient_batch_training function."""
    
    def test_training_step(self):
        config = Config()
        config.max_grad_norm = 1.0
        
        # Create simple model
        model = torch.nn.Transformer(d_model=16, nhead=2, num_encoder_layers=1, num_decoder_layers=1)
        
        # Create mock data
        mock_tokenizer = MockTokenizer()
        data = [{'text': 'test'} for _ in range(8)]
        dataset = OptimizedDataset(data, mock_tokenizer, max_length=128)
        dataloader = PrefetchDataLoader(dataset, batch_size=4, num_workers=0)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        batching_strategy = BatchingStrategy(config, initial_batch_size=4)
        
        loss, step = efficient_batch_training(
            model, dataloader, optimizer, config, batching_strategy, step=0
        )
        
        assert loss >= 0
        assert step > 0


class TestGetOptimizationReport:
    """Tests for get_optimization_report function."""
    
    def test_report_structure(self):
        config = Config()
        batching_strategy = BatchingStrategy(config, initial_batch_size=8)
        
        report = get_optimization_report(config, batching_strategy)
        
        assert 'initial_batch_size' in report
        assert 'current_batch_size' in report
        assert 'gradient_accumulation_steps' in report
        assert 'effective_batch_size' in report
        assert 'max_memory_gb' in report
        assert 'max_batch_size' in report
        assert 'dtype' in report
        assert 'device' in report
        assert report['initial_batch_size'] == 8
        assert report['effective_batch_size'] == 8
