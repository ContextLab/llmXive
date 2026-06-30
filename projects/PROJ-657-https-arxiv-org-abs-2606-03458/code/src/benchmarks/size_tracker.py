"""
Module to track KV-cache size reduction for quantization methods.
Implements FR-007: Measure and report KV-cache size reduction percentage.
"""
import torch
from typing import Dict, Any, Optional, List

class KVCacheSizeTracker:
    """
    Tracks the memory size of KV caches before and after quantization
    to calculate size reduction percentages.
    """

    def __init__(self):
        self.original_sizes: List[int] = []
        self.quantized_sizes: List[int] = []
        self.total_original_bytes: int = 0
        self.total_quantized_bytes: int = 0

    def record_original_cache(self, keys: torch.Tensor, values: torch.Tensor):
        """
        Record the size of the original (unquantized) KV cache.
        
        Args:
            keys: Key tensor from the model
            values: Value tensor from the model
        """
        if keys is not None and values is not None:
            # Calculate size in bytes (assuming float16 for original)
            # keys: [batch, heads, seq_len, head_dim]
            orig_bytes = keys.element_size() * keys.numel() + \
                         values.element_size() * values.numel()
            self.original_sizes.append(orig_bytes)
            self.total_original_bytes += orig_bytes

    def record_quantized_cache(self, keys: torch.Tensor, values: torch.Tensor):
        """
        Record the size of the quantized KV cache.
        
        Args:
            keys: Quantized key tensor
            values: Quantized value tensor
        """
        if keys is not None and values is not None:
            # Calculate size in bytes
            # Quantized tensors might be int8 (1 byte) or similar
            quant_bytes = keys.element_size() * keys.numel() + \
                          values.element_size() * values.numel()
            self.quantized_sizes.append(quant_bytes)
            self.total_quantized_bytes += quant_bytes

    def get_reduction_percentage(self) -> float:
        """
        Calculate the percentage reduction in KV-cache size.
        
        Returns:
            float: Percentage reduction (0.0 to 100.0)
        """
        if self.total_original_bytes == 0:
            return 0.0
        
        reduction = (self.total_original_bytes - self.total_quantized_bytes) / \
                    self.total_original_bytes * 100.0
        return max(0.0, min(100.0, reduction))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about cache size reduction.
        
        Returns:
            Dict containing size metrics and reduction percentage
        """
        return {
            "total_original_bytes": self.total_original_bytes,
            "total_quantized_bytes": self.total_quantized_bytes,
            "reduction_percentage": self.get_reduction_percentage(),
            "num_cache_steps": len(self.original_sizes),
            "avg_original_per_step": self.total_original_bytes / max(1, len(self.original_sizes)),
            "avg_quantized_per_step": self.total_quantized_bytes / max(1, len(self.quantized_sizes))
        }

    def reset(self):
        """Reset all tracking data."""
        self.original_sizes = []
        self.quantized_sizes = []
        self.total_original_bytes = 0
        self.total_quantized_bytes = 0


def create_size_tracker() -> KVCacheSizeTracker:
    """
    Factory function to create a new KVCacheSizeTracker instance.
    
    Returns:
        KVCacheSizeTracker: Fresh tracker instance
    """
    return KVCacheSizeTracker()
