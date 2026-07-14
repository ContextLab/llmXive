"""
Sliding Window Extraction Module.

Implements sliding window extraction with normalization as per spec.
"""
import numpy as np
from typing import List, Tuple, Generator
import logging

logger = logging.getLogger(__name__)

def sliding_window(
    data: np.ndarray,
    window_size: int,
    stride: int,
    normalize: bool = True
) -> List[np.ndarray]:
    """
    Extract sliding windows from a time series.
    
    Args:
        data: 1D array of time series data.
        window_size: Size of the window.
        stride: Step size between windows.
        normalize: Whether to normalize each window (zero mean, unit variance).
        
    Returns:
        List of 1D arrays, each representing a window.
    """
    if len(data) < window_size:
        logger.warning(f"Data length ({len(data)}) is less than window size ({window_size}). Returning empty list.")
        return []
    
    windows = []
    for i in range(0, len(data) - window_size + 1, stride):
        window = data[i : i + window_size]
        
        if normalize:
            mean = np.mean(window)
            std = np.std(window)
            if std > 1e-8:
                window = (window - mean) / std
            else:
                window = window - mean # Zero mean only if std is 0
        
        windows.append(window)
    
    return windows

def main():
    """
    Test the sliding window function.
    """
    data = np.sin(np.linspace(0, 10, 100)) + 0.1 * np.random.randn(100)
    windows = sliding_window(data, window_size=10, stride=5)
    print(f"Generated {len(windows)} windows.")
    for i, w in enumerate(windows[:3]):
        print(f"Window {i}: mean={np.mean(w):.3f}, std={np.std(w):.3f}")

if __name__ == "__main__":
    main()
