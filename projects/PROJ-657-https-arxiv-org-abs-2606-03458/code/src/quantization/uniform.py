"""
Uniform 8-bit Linear Quantization Implementation.

This module provides the baseline linear quantization logic (FR-002)
for the KVarN research pipeline. It implements a standard uniform
quantizer that maps FP16/FP32 tensors to 8-bit integers and back.
"""
import torch
import torch.nn as nn
from typing import Union
from .base import Quantizer


class UniformQuantizer(Quantizer):
    """
    Baseline 8-bit linear quantization.
    
    Quantizes a tensor to 8-bit integers using the min/max range
    of the input tensor (per-tensor or per-channel depending on implementation
    needs, here per-tensor for baseline simplicity) and then dequantizes
    back to the original dtype.
    
    Attributes:
        bits (int): Number of bits for quantization (fixed at 8).
        qmin (int): Minimum quantized value (0 for unsigned 8-bit).
        qmax (int): Maximum quantized value (255 for unsigned 8-bit).
    """
    
    def __init__(self, bits: int = 8):
        super().__init__()
        if bits != 8:
            raise ValueError("UniformQuantizer currently only supports 8-bit quantization.")
        self.bits = bits
        self.qmin = 0
        self.qmax = (1 << bits) - 1
        self._scale = None
        self._zero_point = None
    
    def _calculate_params(self, x: torch.Tensor) -> tuple:
        """
        Calculate scale and zero_point based on the input tensor's range.
        
        Args:
            x (torch.Tensor): Input tensor.
        
        Returns:
            tuple: (scale, zero_point)
        """
        x_min = x.min()
        x_max = x.max()
        
        # Handle degenerate case where all values are the same
        if x_min == x_max:
            scale = torch.tensor(1.0, dtype=x.dtype, device=x.device)
            zero_point = torch.tensor(self.qmin, dtype=torch.int32, device=x.device)
        else:
            scale = (x_max - x_min) / (self.qmax - self.qmin)
            # Round zero_point to nearest integer to ensure it stays within [qmin, qmax]
            zero_point = self.qmin - (x_min / scale)
            zero_point = torch.clamp(torch.round(zero_point), self.qmin, self.qmax)
        
        return scale, zero_point.to(torch.int32)
    
    def quantize(self, x: torch.Tensor) -> torch.Tensor:
        """
        Quantize input tensor to 8-bit integers.
        
        Args:
            x (torch.Tensor): Input tensor (FP16/FP32).
        
        Returns:
            torch.Tensor: Quantized tensor with dtype torch.int8 (or int32 if using unsigned mapping logic internally).
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor, got {type(x)}")
        
        scale, zero_point = self._calculate_params(x)
        
        # Quantization formula: round(x / scale + zero_point)
        # We use float math for intermediate steps to avoid overflow/underflow before rounding
        q = torch.round((x / scale) + zero_point)
        q = torch.clamp(q, self.qmin, self.qmax)
        
        # Store params for dequantization if needed (optional, but good for stateful usage)
        self._scale = scale
        self._zero_point = zero_point
        
        # Return as int8 for memory efficiency, casting from clamped range
        return q.to(torch.int8)
    
    def dequantize(self, q: torch.Tensor) -> torch.Tensor:
        """
        Dequantize 8-bit integer tensor back to floating point.
        
        Args:
            q (torch.Tensor): Quantized tensor (int8).
        
        Returns:
            torch.Tensor: Dequantized tensor in original dtype.
        """
        if not isinstance(q, torch.Tensor):
            raise TypeError(f"Expected torch.Tensor, got {type(q)}")
        
        # If params weren't stored (e.g., called on a fresh instance), re-calculate is not possible
        # without original range. We assume either:
        # 1. The user calls quantize() first to set state, OR
        # 2. We need to infer from the quantized tensor if we assume symmetric/standard range?
        # However, standard uniform quantization usually requires the scale/zero_point passed in or stored.
        # To make this robust as a standalone class method without state dependency for the test:
        # We will re-calculate params if not present, but this implies the input 'q' must be accompanied
        # by the original range info if we want perfect reconstruction.
        # 
        # CRITICAL FIX FOR STANDALONE USAGE:
        # Since `dequantize` in many libraries takes (q, scale, zp), but our base signature is just `dequantize(q)`,
        # we must rely on the state set by `quantize` OR accept that dequantize without `quantize` first 
        # is ambiguous. 
        # 
        # To satisfy the "baseline logic" requirement and allow the base class contract:
        # We will assume the user calls `quantize` first, which sets `self._scale` and `self._zero_point`.
        # If those are None, we cannot accurately dequantize without the original min/max.
        # 
        # Alternative: Re-implement to accept scale/zp as arguments? 
        # The base class signature is `dequantize(self, q)`. 
        # Let's assume the standard pattern: quantize sets state, dequantize uses it.
        
        if self._scale is None or self._zero_point is None:
            # Fallback: If state is missing, we can't do it perfectly. 
            # However, for the purpose of this research implementation, 
            # we will raise an error to force the correct usage pattern: 
            # quantize -> dequantize sequence.
            raise RuntimeError(
                "Dequantization parameters (scale, zero_point) not set. "
                "Please call quantize() first on this instance, or pass parameters if the base class allows."
            )
        
        # Dequantization formula: (q - zero_point) * scale
        x_reconstructed = (q.float() - self._zero_point.float()) * self._scale
        
        return x_reconstructed

    def quantize_and_dequantize(self, x: torch.Tensor) -> torch.Tensor:
        """
        Convenience method to quantize and immediately dequantize a tensor.
        Useful for calculating reconstruction error (MSE).
        
        Args:
            x (torch.Tensor): Input tensor.
        
        Returns:
            torch.Tensor: Reconstructed tensor.
        """
        q = self.quantize(x)
        return self.dequantize(q)

    def get_mse(self, x: torch.Tensor) -> float:
        """
        Calculate Mean Squared Error between original and reconstructed tensor.
        
        Args:
            x (torch.Tensor): Original input tensor.
        
        Returns:
            float: MSE value.
        """
        x_reconstructed = self.quantize_and_dequantize(x)
        mse = torch.nn.functional.mse_loss(x.float(), x_reconstructed.float())
        return mse.item()