"""
Eco-Director: Core Cellular Automata (CA) update loop.

Implements the CA engine for the 'Infinite Worlds' simulation,
focusing on locality, memory, and non-linearity as defined in the schema.
"""
import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

def step(state: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Perform one update step of the Cellular Automata.
    
    Args:
        state: 2D numpy array representing the current grid state.
               Expected shape: (H, W). Values typically float in [0, 1].
        params: Dictionary containing CA configuration parameters.
                Expected keys:
                  - 'locality_radius': int, radius for neighborhood (default 1)
                  - 'memory_decay': float, factor for memory retention (default 0.9)
                  - 'non_linearity_strength': float, exponent for activation (default 2.0)
                  - 'threshold': float, cutoff for state change (default 0.5)
    
    Returns:
        new_state: 2D numpy array of the updated grid state.
    
    Raises:
        ValueError: If state dimensions are invalid or params are missing required keys.
    """
    if state.ndim != 2:
        raise ValueError(f"State must be a 2D array, got {state.ndim}D")
    
    if state.size == 0:
        return state

    # Extract parameters with defaults
    r = int(params.get('locality_radius', 1))
    memory_decay = float(params.get('memory_decay', 0.9))
    non_linearity = float(params.get('non_linearity_strength', 2.0))
    threshold = float(params.get('threshold', 0.5))

    H, W = state.shape
    
    # Pad state to handle boundaries (reflect mode for continuity)
    # np.pad with 'reflect' avoids introducing artificial zero boundaries
    if r > 0:
        padded_state = np.pad(state, r, mode='reflect')
    else:
        padded_state = state

    # Initialize new state
    new_state = np.zeros_like(state)

    # Vectorized neighborhood sum calculation
    # We iterate over offsets to sum neighbors within radius r
    # This is more memory efficient than creating a full convolution kernel for large r
    
    # Pre-calculate offsets
    offsets = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy == 0 and dx == 0:
                continue
            offsets.append((dy, dx))
    
    # Accumulate neighbor values
    # Using a loop over offsets is efficient for small r (typical CA radius)
    # For very large r, a 2D convolution (scipy.signal.convolve2d) would be better
    neighbor_sum = np.zeros_like(state)
    for dy, dx in offsets:
        # Extract shifted view from padded state
        # Original state [0:H, 0:W] corresponds to padded [r:r+H, r:r+W]
        # Shifted by (dy, dx) in original coords -> (r+dy, r+dx) in padded
        neighbor_sum += padded_state[r+dy : r+dy+H, r+dx : r+dx+W]

    # Calculate local density (mean of neighbors)
    # Normalize by number of neighbors
    num_neighbors = len(offsets)
    local_density = neighbor_sum / num_neighbors if num_neighbors > 0 else np.zeros_like(state)

    # Apply non-linearity (activation function)
    # Example: (local_density ^ non_linearity) to emphasize high-density clusters
    activated = np.power(local_density, non_linearity)

    # Apply threshold logic for state transition
    # If activated value > threshold, state moves towards 1, else towards 0
    # We use a simple logistic-like update for smoothness
    delta = activated - threshold
    
    # Update rule: new_state = (1 - memory_decay) * current_state + memory_decay * target
    # Target is determined by the delta. If delta > 0, target is 1, else 0 (or smooth interpolation)
    # Here we use a smooth step: target = sigmoid(delta * strength)
    # But to keep it strictly CA-like, let's use:
    # target_state = 1.0 if activated > threshold else 0.0
    # Then interpolate with memory.
    
    target_state = np.where(activated > threshold, 1.0, 0.0)
    
    # Apply memory decay: new_state = current_state * (1 - memory_decay) + target * memory_decay
    # Wait, the prompt implies 'memory' as a property. 
    # Let's interpret 'memory_decay' as how much the *current* state persists vs the new input.
    # If memory_decay is high (0.9), the state changes slowly.
    # Formula: new_state = state * (1 - alpha) + target * alpha
    # Where alpha is the update strength. Let's map memory_decay to alpha.
    # If memory_decay=0.9, we keep 90% of old state? Or 90% of new?
    # Usually "memory decay" means old information fades.
    # Let's interpret: new_state = state * memory_decay + target * (1 - memory_decay)
    # This means if memory_decay is 0.9, 90% is old, 10% is new.
    
    new_state = state * memory_decay + target_state * (1.0 - memory_decay)

    # Ensure bounds [0, 1]
    new_state = np.clip(new_state, 0.0, 1.0)

    return new_state
