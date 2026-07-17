import numpy as np
import torch
from typing import Callable, Union, Tuple, List, Optional
from config import get_path_str
from scipy.stats import entropy

class QuantizationEmulator:
    """
    Emulates NVFP4 (and other bit-widths) quantization using stochastic rounding.
    Supports dynamic switching of bit-width via re-initialization of rounding logic.
    """
    def __init__(self, bit_width: int = 4):
        self.bit_width = bit_width
        self._rounding_func: Callable[[torch.Tensor], torch.Tensor] = self._create_rounding_func(bit_width)
        self._noise_samples: Optional[np.ndarray] = None

    def _create_rounding_func(self, bit_width: int) -> Callable[[torch.Tensor], torch.Tensor]:
        """Factory function to create the stochastic rounding closure for a specific bit width."""
        if bit_width not in [2, 4, 8]:
            raise ValueError(f"Unsupported bit_width: {bit_width}. Must be 2, 4, or 8.")
        
        max_int = (2 ** bit_width) - 1
        scale = max_int

        def stochastic_round(tensor: torch.Tensor) -> torch.Tensor:
            # Scale to integer range
            scaled = tensor * scale
            # Floor and Ceiling
            floor_val = torch.floor(scaled)
            ceil_val = torch.ceil(scaled)
            # Probability of rounding up
            prob = scaled - floor_val
            # Random mask for stochastic decision
            rand_mask = torch.rand_like(prob) < prob
            # Stochastic result
            result = torch.where(rand_mask, ceil_val, floor_val)
            # Scale back to float
            return result / scale

        return stochastic_round

    def set_bit_width(self, new_bit_width: int) -> None:
        """
        Dynamically switch the bit-width by re-initializing the rounding logic.
        This allows changing precision without restarting the training loop.
        """
        if new_bit_width not in [2, 4, 8]:
            raise ValueError(f"Unsupported bit_width: {new_bit_width}. Must be 2, 4, or 8.")
        self.bit_width = new_bit_width
        self._rounding_func = self._create_rounding_func(new_bit_width)
        self._noise_samples = None  # Invalidate cached samples

    def emulate(self, x: torch.Tensor) -> torch.Tensor:
        """Apply the current stochastic rounding logic to tensor x."""
        return self._rounding_func(x)

    def validate_noise_distribution(self, sample_size: int = 10000, tolerance: float = 0.05) -> Tuple[float, bool]:
        """
        Validates that the stochastic rounding noise distribution matches theoretical uniform.
        Returns (KL_divergence, is_valid).
        """
        if self._noise_samples is None or len(self._noise_samples) < sample_size:
            # Generate fresh samples
            # We sample uniformly in [0, 1] and check the noise introduced
            # Noise = StochasticRound(x) - x. For uniform x, noise should be uniform in [-0.5/scale, 0.5/scale]
            # Actually, for stochastic rounding, the error is uniformly distributed in [-0.5, 0.5] in the scaled domain.
            # Let's sample x in [0, 1]
            x_samples = torch.rand(sample_size)
            q_samples = self.emulate(x_samples)
            errors = (q_samples - x_samples).detach().cpu().numpy()
            
            # Normalize errors to [0, 1] for histogram comparison against uniform
            # Theoretical noise range is [-0.5/scale, 0.5/scale]
            max_err = 0.5 / ((2 ** self.bit_width) - 1)
            # Shift and scale to [0, 1]
            normalized_errors = (errors + max_err) / (2 * max_err)
            normalized_errors = np.clip(normalized_errors, 0, 1)
            
            # Histogram
            hist, bin_edges = np.histogram(normalized_errors, bins=20, range=(0, 1), density=True)
            
            # Theoretical uniform PDF is 1.0 everywhere
            theoretical_pdf = np.ones_like(hist)
            
            # KL Divergence: sum(p * log(p/q))
            # Avoid log(0)
            epsilon = 1e-10
            kl = entropy(hist, theoretical_pdf + epsilon)
            self._noise_samples = errors
        else:
            errors = self._noise_samples[:sample_size]
            max_err = 0.5 / ((2 ** self.bit_width) - 1)
            normalized_errors = (errors + max_err) / (2 * max_err)
            normalized_errors = np.clip(normalized_errors, 0, 1)
            hist, _ = np.histogram(normalized_errors, bins=20, range=(0, 1), density=True)
            theoretical_pdf = np.ones_like(hist)
            epsilon = 1e-10
            kl = entropy(hist, theoretical_pdf + epsilon)

        is_valid = kl <= tolerance
        return kl, is_valid

def create_quantization_emulator(bit_width: int = 4) -> QuantizationEmulator:
    """Factory to create a QuantizationEmulator instance."""
    return QuantizationEmulator(bit_width)

def get_rounding_function(bit_width: int) -> Callable[[torch.Tensor], torch.Tensor]:
    """Helper to get just the rounding function for a specific bit width."""
    emu = QuantizationEmulator(bit_width)
    return emu._rounding_func

def switch_emulator_bit_width(emulator: QuantizationEmulator, new_bit_width: int) -> QuantizationEmulator:
    """
    Switches the bit width of an existing emulator instance.
    Returns the same instance for chaining convenience.
    """
    emulator.set_bit_width(new_bit_width)
    return emulator

def main():
    """Test dynamic switching and noise validation."""
    import sys
    
    print("Testing dynamic bit-width switching...")
    emulator = create_quantization_emulator(4)
    
    # Test initial state
    x = torch.tensor([0.1, 0.5, 0.9])
    print(f"Input: {x}")
    print(f"Bit Width 4 Output: {emulator.emulate(x)}")
    
    # Switch to 2-bit
    switch_emulator_bit_width(emulator, 2)
    print(f"Switched to 2-bit. Output: {emulator.emulate(x)}")
    
    # Switch to 8-bit
    switch_emulator_bit_width(emulator, 8)
    print(f"Switched to 8-bit. Output: {emulator.emulate(x)}")
    
    # Validate noise distribution for 4-bit
    switch_emulator_bit_width(emulator, 4)
    kl, valid = emulator.validate_noise_distribution()
    print(f"KL Divergence (4-bit): {kl:.4f}, Valid: {valid}")
    
    if not valid:
        print("Error: Noise distribution validation failed.")
        sys.exit(1)
    else:
        print("All tests passed.")

if __name__ == "__main__":
    main()