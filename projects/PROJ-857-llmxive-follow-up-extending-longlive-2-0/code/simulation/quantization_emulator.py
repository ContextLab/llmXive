import numpy as np
import torch
from typing import Callable, Union, Tuple, List, Optional
from config import get_path_str
from scipy.stats import entropy
import json

class QuantizationEmulator:
    """Emulates quantization by applying noise or true integer quantization."""

    def __init__(self, bit_width: int, mode: str = "stochastic"):
        """Initializes the emulator with specified bit width and mode."""
        if not 2 <= bit_width <= 6:
            raise ValueError("Bit width must be between 2 and 6.")
        self.bit_width = bit_width
        self.mode = mode

    def emulate(self, x: torch.Tensor) -> torch.Tensor:
        """Applies quantization emulation to the input tensor."""
        if self.mode == "stochastic":
            return self._stochastic_rounding(x)
        elif self.mode == "integer":
            return self._true_integer_quantization(x)
        else:
            raise ValueError("Invalid mode. Choose 'stochastic' or 'integer'.")

    def _stochastic_rounding(self, x: torch.Tensor) -> torch.Tensor:
        """Applies stochastic rounding to the input tensor."""
        noise = torch.uniform(-0.5, 0.5, x.shape).to(x.device)
        quantized = torch.floor(x + noise)
        return quantized

    def _true_integer_quantization(self, x: torch.Tensor) -> torch.Tensor:
        """Applies true integer quantization to the input tensor."""
        scale = (2 ** (self.bit_width - 1)) - 1
        quantized = torch.round(x * scale) / scale
        return quantized

def create_quantization_emulator(bit_width: int, mode: str = "stochastic") -> QuantizationEmulator:
    """Creates a quantization emulator with the specified parameters."""
    return QuantizationEmulator(bit_width, mode)

def get_rounding_function(bit_width: int, mode: str = "stochastic") -> Callable[[torch.Tensor], torch.Tensor]:
    """Returns the rounding function for the given bit width and mode."""
    emulator = create_quantization_emulator(bit_width, mode)
    return emulator.emulate

def switch_emulator_bit_width(emulator: QuantizationEmulator, new_bit_width: int):
  """Switches the bit width of an existing emulator instance."""
  if not 2 <= new_bit_width <= 6:
      raise ValueError("Bit width must be between 2 and 6.")
  emulator.bit_width = new_bit_width

def calculate_kl_divergence(p, q):
    """Calculates the Kullback-Leibler divergence between two probability distributions."""
    p = np.asarray(p, dtype=np.float64)
    q = np.asarray(q, dtype=np.float64)

    # Ensure probabilities sum to 1 (normalize if necessary).  Handle potential zero values.
    if np.sum(p) > 0:
        p = p / np.sum(p)
    else:
        p = np.ones_like(p) / len(p)  # Uniform distribution if all zeros

    if np.sum(q) > 0:
        q = q / np.sum(q)
    else:
        q = np.ones_like(q) # Uniform distribution if all zeros


    return entropy(p, qk=q)

def perform_power_analysis(bit_width: int, seed: int) -> float:
    """Performs a power analysis to determine the minimum sample size."""
    # Placeholder for actual power analysis.  In a real implementation, this would involve
    # calculating the required sample size based on effect size, alpha level, and desired power.
    return 1000 # Return a fixed sample size for demonstration purposes

def main():
      """Main function (for testing/demonstration)"""
      bit_widths = [2, 3, 4, 5, 6]
      seed = 42
      np.random.seed(seed)  # For reproducibility

      results = {}
      for bit_width in bit_widths:
          emulator = create_quantization_emulator(bit_width)
          noise = np.random.rand(1000)
          quantized_noise = emulator.emulate(torch.tensor(noise))
          # Calculate KL divergence between the original noise and quantized noise (example metric).
          kl_divergence = calculate_kl_divergence(noise, quantized_noise.numpy())
          results[bit_width] = {"kl_divergence": kl_divergence}
      print(json.dumps(results))

if __name__ == "__main__":
    main()