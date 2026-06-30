"""
Hooks for intercepting and modifying KV-cache during generation.
"""
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from src.quantization.base import Quantizer
from src.benchmarks.size_tracker import KVCacheSizeTracker
from src.inference.logging_hooks import MSELogger

class KVCacheInterceptor:
    """
    Intercepts KV-cache tensors during model forward pass to apply quantization.
    
    This hook is registered with the transformer model to capture key and value
    tensors before they are stored in the cache, allowing for on-the-fly quantization.
    """

    def __init__(
        self,
        quantizer: Quantizer,
        size_tracker: Optional[KVCacheSizeTracker] = None,
        mse_logger: Optional[MSELogger] = None
    ):
        """
        Initialize the KV-cache interceptor.
        
        Args:
            quantizer: The quantizer to apply to KV caches
            size_tracker: Optional tracker for cache size reduction (FR-007)
            mse_logger: Optional logger for reconstruction error
        """
        self.quantizer = quantizer
        self.size_tracker = size_tracker
        self.mse_logger = mse_logger
        self.handles: List[Any] = []
        self.cache_keys: List[torch.Tensor] = []
        self.cache_values: List[torch.Tensor] = []

    def _intercept_forward(
        self,
        module: nn.Module,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any]
    ) -> None:
        """
        Interceptor function called before module forward pass.
        
        Captures original KV tensors for quantization and tracking.
        """
        # Extract key and value tensors from attention layers
        # This is a simplified approach - in practice, we'd need to identify
        # the specific attention layer outputs
        
        # For now, we'll use a generic approach that works with most transformers
        # by intercepting the cache update step
        pass

    def quantize_cache(
        self,
        key: torch.Tensor,
        value: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply quantization to KV tensors and track metrics.
        
        Args:
            key: Original key tensor
            value: Original value tensor
        
        Returns:
            Tuple of (quantized_key, quantized_value)
        """
        # Track original size if size tracking is enabled (FR-007)
        if self.size_tracker is not None:
            self.size_tracker.record_original_cache(key, value)
        
        # Quantize the tensors
        quant_key, quant_value = self.quantizer.quantize(key), self.quantizer.quantize(value)
        
        # Dequantize to measure error (for MSE logging)
        if self.mse_logger is not None:
            dequant_key = self.quantizer.dequantize(quant_key)
            dequant_value = self.quantizer.dequantize(quant_value)
            
            # Calculate MSE
            key_mse = torch.nn.functional.mse_loss(dequant_key, key).item()
            value_mse = torch.nn.functional.mse_loss(dequant_value, value).item()
            avg_mse = (key_mse + value_mse) / 2.0
            
            # Log the error
            self.mse_logger.log_mse(avg_mse)
        
        # Track quantized size if size tracking is enabled (FR-007)
        if self.size_tracker is not None:
            self.size_tracker.record_quantized_cache(quant_key, quant_value)
        
        return quant_key, quant_value

    def register(self, model: nn.Module):
        """
        Register the interceptor with the model.
        
        Args:
            model: The transformer model to intercept
        """
        # Register forward hook on all linear layers that might produce KV
        # This is a simplified registration - a full implementation would
        # target specific attention layers
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # We'll use a simpler approach: intercept at the model level
                # by wrapping the generate method or using a custom attention wrapper
                pass

    def unregister(self):
        """Remove all registered hooks."""
        for handle in self.handles:
            handle.remove()
        self.handles.clear()
        self.cache_keys.clear()
        self.cache_values.clear()

    def apply_to_cache(
        self,
        past_key_values: Optional[Tuple[Tuple[torch.Tensor, torch.Tensor]]]
    ) -> Optional[Tuple[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Apply quantization to an existing past_key_values tuple.
        
        Args:
            past_key_values: Tuple of (key, value) tensors from previous steps
        
        Returns:
            Tuple of quantized (key, value) tensors
        """
        if past_key_values is None:
            return None
        
        quantized_cache = []
        for layer_idx, (key, value) in enumerate(past_key_values):
            q_key, q_value = self.quantize_cache(key, value)
            quantized_cache.append((q_key, q_value))
        
        return tuple(quantized_cache)
