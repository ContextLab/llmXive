"""
Base module for quantization strategies.
Defines the abstract interface for all quantizers used in the KVarN pipeline.
"""
from abc import ABC, abstractmethod
from typing import Union

import torch
import torch.nn as nn


class Quantizer(ABC):
    """
    Abstract base class for all quantization strategies.

    Subclasses must implement `quantize` and `dequantize` methods to handle
    the conversion between full-precision tensors and quantized representations.
    """

    def __init__(self, bits: int = 8, **kwargs):
        """
        Initialize the quantizer.

        Args:
            bits: Number of bits for quantization (default: 8).
            **kwargs: Additional configuration parameters specific to the strategy.
        """
        self.bits = bits
        self.config = kwargs

    @abstractmethod
    def quantize(self, tensor: torch.Tensor) -> Union[torch.Tensor, dict]:
        """
        Quantize a full-precision tensor.

        Args:
            tensor: The input tensor to be quantized (typically float16 or float32).

        Returns:
            Either a quantized tensor (e.g., int8) or a dictionary containing
            the quantized data and necessary scaling parameters (scale, zero_point)
            for dequantization.
        """
        pass

    @abstractmethod
    def dequantize(self, data: Union[torch.Tensor, dict]) -> torch.Tensor:
        """
        Dequantize a quantized tensor or data structure back to full precision.

        Args:
            data: The quantized tensor or dictionary containing quantized data
                  and scaling parameters.

        Returns:
            A tensor approximating the original full-precision input.
        """
        pass

    def get_memory_footprint(self, tensor_shape: tuple) -> int:
        """
        Estimate the memory footprint of the quantized representation.

        Args:
            tensor_shape: The shape of the original tensor.

        Returns:
            Estimated size in bytes.
        """
        total_elements = 1
        for dim in tensor_shape:
            total_elements *= dim
        # Assume quantized data takes 1 byte per element (8-bit)
        # Plus potential overhead for scale/zero_point per channel or block
        # Base calculation: 1 byte per element
        return total_elements * (self.bits // 8)

class UniformQuantizer(Quantizer):
    """
    Concrete implementation of a uniform quantizer (placeholder for T005).
    This class is provided here to satisfy the immediate need for a concrete
    subclass if T005 is not yet imported, but T005 will overwrite/replace
    this logic in `code/src/quantization/uniform.py`.
    """
    def __init__(self, bits: int = 8, **kwargs):
        super().__init__(bits, **kwargs)

    def quantize(self, tensor: torch.Tensor) -> dict:
        # Placeholder implementation to ensure the file is runnable
        # Actual implementation moved to uniform.py
        raise NotImplementedError("UniformQuantizer logic is implemented in uniform.py")

    def dequantize(self, data: dict) -> torch.Tensor:
        # Placeholder implementation
        raise NotImplementedError("UniformQuantizer logic is implemented in uniform.py")