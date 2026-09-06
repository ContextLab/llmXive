"""
Performance optimization utilities for the Dream-State Learning pipeline.

Implements batching strategies, efficient data loading, and memory-aware
processing to ensure the pipeline runs within resource constraints.
"""
import torch
from torch.utils.data import DataLoader, Dataset
from typing import Dict, Any, Optional, List, Tuple, Iterator
import numpy as np
from collections import deque
import gc
import time
from config import Config
from utils.logger import get_logger
from utils.memory_monitor import MemoryMonitor, enforce_memory_limit

logger = get_logger(__name__)

class BatchingStrategy:
    """
    Implements adaptive batching based on available memory.
    
    Features:
    - Dynamic batch size adjustment based on memory monitoring
    - Gradient accumulation for effective larger batches on limited memory
    - Padding optimization to reduce wasted computation
    """
    
    def __init__(self, config: Config, initial_batch_size: int = 8):
        self.config = config
        self.initial_batch_size = initial_batch_size
        self.current_batch_size = initial_batch_size
        self.memory_monitor = MemoryMonitor()
        self.min_batch_size = 1
        self.max_batch_size = config.max_batch_size
        self.gradient_accumulation_steps = 1
        self._last_memory_check = 0
        self._check_interval = 10  # Check every N steps
        
        logger.info(f"Initialized BatchingStrategy with initial batch size: {initial_batch_size}")
    
    def adjust_batch_size(self, step: int, peak_memory_kb: Optional[int] = None) -> Tuple[int, int]:
        """
        Dynamically adjust batch size and gradient accumulation based on memory usage.
        
        Args:
            step: Current training step
            peak_memory_kb: Peak memory usage in KB from memory monitor
            
        Returns:
            Tuple of (effective_batch_size, gradient_accumulation_steps)
        """
        if step - self._last_memory_check < self._check_interval:
            return self.current_batch_size, self.gradient_accumulation_steps
        
        self._last_memory_check = step
        
        if peak_memory_kb is None:
            peak_memory_kb = self.memory_monitor.get_peak_rss_kb()
        
        # Memory threshold in KB (e.g., 6GB limit)
        memory_threshold_kb = int(self.config.max_memory_gb * 1024 * 1024 * 0.8)
        
        if peak_memory_kb > memory_threshold_kb:
            # Reduce batch size if memory is too high
            if self.current_batch_size > self.min_batch_size:
                new_batch_size = max(self.min_batch_size, self.current_batch_size // 2)
                self.current_batch_size = new_batch_size
                self.gradient_accumulation_steps = max(1, self.gradient_accumulation_steps * 2)
                logger.warning(
                    f"Memory pressure detected ({peak_memory_kb / 1024 / 1024:.2f}GB). "
                    f"Reducing batch size to {self.current_batch_size}, "
                    f"increasing gradient accumulation to {self.gradient_accumulation_steps}"
                )
        elif peak_memory_kb < memory_threshold_kb * 0.5:
            # Can potentially increase batch size if memory is low
            if self.current_batch_size < self.max_batch_size:
                new_batch_size = min(self.max_batch_size, self.current_batch_size * 2)
                self.current_batch_size = new_batch_size
                self.gradient_accumulation_steps = max(1, self.gradient_accumulation_steps // 2)
                logger.info(
                    f"Memory headroom available. Increasing batch size to {self.current_batch_size}, "
                    f"reducing gradient accumulation to {self.gradient_accumulation_steps}"
                )
        
        return self.current_batch_size, self.gradient_accumulation_steps
    
    def get_effective_batch_size(self) -> int:
        """Return the effective batch size (batch_size * gradient_accumulation_steps)."""
        return self.current_batch_size * self.gradient_accumulation_steps


class OptimizedDataset(Dataset):
    """
    Memory-efficient dataset wrapper that supports on-the-fly tokenization
    and caching strategies.
    """
    
    def __init__(
        self,
        data: List[Dict[str, Any]],
        tokenizer,
        max_length: int = 512,
        use_cache: bool = True,
        cache_size: int = 1000
    ):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.use_cache = use_cache
        self.cache_size = cache_size
        
        # LRU cache for tokenized samples
        self._cache: deque = deque(maxlen=cache_size)
        self._cache_keys: Dict[int, Any] = {}
        
        logger.info(f"Initialized OptimizedDataset with {len(data)} samples, cache size: {cache_size}")
    
    def __len__(self) -> int:
        return len(self.data)
    
    def _tokenize_sample(self, sample: Dict[str, Any]) -> Dict[str, torch.Tensor]:
        """Tokenize a single sample with truncation and padding."""
        text = sample.get('text', '')
        labels = sample.get('labels', -100)
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Flatten attention mask and input_ids for single sample
        encoding['input_ids'] = encoding['input_ids'].squeeze(0)
        encoding['attention_mask'] = encoding['attention_mask'].squeeze(0)
        
        if labels != -100:
            encoding['labels'] = torch.tensor(labels)
        
        return encoding
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.data[idx]
        
        if self.use_cache:
            cache_key = id(sample)
            if cache_key in self._cache_keys:
                # Move to end of deque (most recently used)
                cached_item = self._cache[self._cache_keys[cache_key]]
                self._cache.remove(cached_item)
                self._cache.append(cached_item)
                return cached_item
        
        result = self._tokenize_sample(sample)
        
        if self.use_cache:
            cache_key = id(sample)
            if len(self._cache) >= self.cache_size:
                # Remove oldest item from cache
                old_item = self._cache[0]
                old_key = None
                for k, v in self._cache_keys.items():
                    if v == 0:
                        old_key = k
                        break
                if old_key:
                    del self._cache_keys[old_key]
            
            self._cache.append(result)
            self._cache_keys[cache_key] = len(self._cache) - 1
        
        return result


class PrefetchDataLoader:
    """
    DataLoader with prefetching and background loading for improved throughput.
    
    Uses multiple worker processes and prefetching to overlap data loading
    with model computation.
    """
    
    def __init__(
        self,
        dataset: OptimizedDataset,
        batch_size: int,
        num_workers: int = 2,
        pin_memory: bool = True,
        prefetch_factor: int = 2,
        persistent_workers: bool = True
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.num_workers = min(num_workers, 2)  # Limit workers for CPU-only CI
        self.pin_memory = pin_memory
        self.prefetch_factor = prefetch_factor
        self.persistent_workers = persistent_workers
        
        self.dataloader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=pin_memory,
            prefetch_factor=prefetch_factor if num_workers > 0 else None,
            persistent_workers=persistent_workers if num_workers > 0 else False,
            drop_last=True,
            generator=torch.Generator().manual_seed(42)
        )
        
        logger.info(
            f"Initialized PrefetchDataLoader with batch_size={batch_size}, "
            f"num_workers={self.num_workers}, prefetch_factor={prefetch_factor}"
        )
    
    def __iter__(self) -> Iterator[Dict[str, torch.Tensor]]:
        return iter(self.dataloader)
    
    def __len__(self) -> int:
        return len(self.dataloader)
    
    def get_batch_size(self) -> int:
        return self.batch_size


def optimize_memory_for_training(model: torch.nn.Module, config: Config) -> None:
    """
    Apply memory optimization techniques for the model.
    
    - Enable gradient checkpointing if available
    - Set appropriate dtype
    - Clear CUDA cache (if applicable)
    """
    if hasattr(model, 'gradient_checkpointing_enable'):
        try:
            model.gradient_checkpointing_enable()
            logger.info("Enabled gradient checkpointing for memory optimization")
        except Exception as e:
            logger.warning(f"Could not enable gradient checkpointing: {e}")
    
    # Ensure model is in appropriate precision
    if config.dtype == torch.float16 and torch.cuda.is_available():
        model.half()
    elif config.dtype == torch.bfloat16 and torch.cuda.is_available():
        model.to(torch.bfloat16)
    
    # Clear any cached memory
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    logger.info("Memory optimization applied to model")


def efficient_batch_training(
    model: torch.nn.Module,
    dataloader: PrefetchDataLoader,
    optimizer: torch.optim.Optimizer,
    config: Config,
    batching_strategy: BatchingStrategy,
    step: int = 0
) -> Tuple[float, int]:
    """
    Perform training with efficient batching and gradient accumulation.
    
    Args:
        model: The model to train
        dataloader: The data loader
        optimizer: The optimizer
        config: Configuration object
        batching_strategy: The batching strategy to use
        step: Current training step
        
    Returns:
        Tuple of (average_loss, updated_step)
    """
    model.train()
    total_loss = 0.0
    batch_count = 0
    
    current_batch_size, grad_accum_steps = batching_strategy.adjust_batch_size(step)
    
    # Update dataloader batch size if needed
    if current_batch_size != dataloader.get_batch_size():
        logger.info(f"Updating dataloader batch size to {current_batch_size}")
        dataloader.batch_size = current_batch_size
        dataloader.dataloader = DataLoader(
            dataloader.dataset,
            batch_size=current_batch_size,
            shuffle=True,
            num_workers=dataloader.num_workers,
            pin_memory=dataloader.pin_memory,
            prefetch_factor=dataloader.prefetch_factor if dataloader.num_workers > 0 else None,
            persistent_workers=dataloader.persistent_workers if dataloader.num_workers > 0 else False,
            drop_last=True,
            generator=dataloader.dataloader.generator
        )
    
    for batch_idx, batch in enumerate(dataloader):
        batch = {k: v.to(config.device) if isinstance(v, torch.Tensor) else v 
                for k, v in batch.items()}
        
        # Forward pass
        outputs = model(
            input_ids=batch['input_ids'],
            attention_mask=batch['attention_mask'],
            labels=batch.get('labels', None)
        )
        
        loss = outputs.loss / grad_accum_steps
        loss.backward()
        
        total_loss += loss.item() * grad_accum_steps
        batch_count += 1
        
        # Gradient accumulation step
        if (batch_idx + 1) % grad_accum_steps == 0:
            # Clip gradients to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()
            step += 1
            
            # Monitor memory after each accumulation step
            peak_memory = batching_strategy.memory_monitor.get_peak_rss_kb()
            enforce_memory_limit(config.max_memory_gb * 1024 * 1024, peak_memory)
            
            # Clear cache periodically
            if batch_idx % 10 == 0:
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
    
    avg_loss = total_loss / max(batch_count, 1)
    return avg_loss, step


def get_optimization_report(config: Config, batching_strategy: BatchingStrategy) -> Dict[str, Any]:
    """
    Generate a report of the current optimization settings.
    
    Returns:
        Dictionary containing optimization configuration and current state
    """
    return {
        'initial_batch_size': batching_strategy.initial_batch_size,
        'current_batch_size': batching_strategy.current_batch_size,
        'gradient_accumulation_steps': batching_strategy.gradient_accumulation_steps,
        'effective_batch_size': batching_strategy.get_effective_batch_size(),
        'max_memory_gb': config.max_memory_gb,
        'max_batch_size': config.max_batch_size,
        'dtype': str(config.dtype),
        'device': str(config.device),
        'num_workers': 2  # Fixed for CPU-only CI
    }
