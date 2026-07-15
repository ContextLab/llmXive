"""
CPU-only Euler integrator for DanceOPD field distillation.

This module is the single source of truth for the integration logic.
It accepts a velocity vector, noise level, and expert type, and performs
a fixed-step Euler integration to generate an image.
"""

import torch
import numpy as np
from typing import Tuple, Optional
from pathlib import Path

# Import config to access hyperparameters and expert definitions
from utils.config import get_config


class ExpertFieldSimulator:
    """
    Simulates the expert field logic required to compute velocity updates.
    
    In the full DanceOPD setup, this would invoke the actual pre-trained
    expert networks. For this CPU-only implementation, we simulate the
    field dynamics based on the provided expert_type to ensure the
    integrator logic is correct and runnable without GPU dependencies.
    
    NOTE: In a production environment with real weights, this class would
    load the specific expert network weights and perform actual forward passes.
    """
    
    def __init__(self, expert_type: str, config: dict):
        self.expert_type = expert_type
        self.config = config
        
        # Simulated parameters for the field dynamics
        # In reality, these would be learned weights
        self.scale_factor = 0.1
        self.noise_scale = 0.01
        
    def compute_velocity(self, x: torch.Tensor, t: float) -> torch.Tensor:
        """
        Computes the velocity vector for the current state x at time t.
        
        Args:
            x: Current state tensor (latent representation)
            t: Current time step (normalized 0.0 to 1.0)
            
        Returns:
            Velocity vector tensor of the same shape as x
        """
        # Simulate a non-linear field dependent on expert type
        # This is a placeholder for the actual expert network inference
        if self.expert_type == "style":
            # Style expert: emphasizes frequency components
            velocity = torch.sin(x * 2.0 * np.pi * t) * self.scale_factor
        elif self.expert_type == "structure":
            # Structure expert: emphasizes gradients/edges
            velocity = torch.cos(x * 1.5 * np.pi * (1.0 - t)) * self.scale_factor
        elif self.expert_type == "texture":
            # Texture expert: high-frequency noise injection
            noise = torch.randn_like(x) * self.noise_scale
            velocity = (x * 0.5 + noise) * self.scale_factor
        else:
            # Default expert: linear decay
            velocity = -x * self.scale_factor
            
        return velocity


def euler_integrate(
    velocity_vector: np.ndarray,
    noise_level: float,
    expert_type: str,
    steps: int = 50,
    step_size: Optional[float] = None
) -> np.ndarray:
    """
    Performs CPU-only Euler integration to generate an image latent.
    
    This function implements the core integration logic:
    x_{t+1} = x_t + step_size * v(x_t, t)
    
    Args:
        velocity_vector: Initial velocity vector (numpy array) representing 
                         the starting point or direction in latent space.
        noise_level: Initial noise level (scalar) to modulate the starting state.
        expert_type: String identifier for the expert field (e.g., "style", "structure").
        steps: Number of integration steps (default 50).
        step_size: Size of each integration step. If None, calculated as 1.0/steps.
        
    Returns:
        Final integrated state as a numpy array (image latent).
    """
    # Get configuration for any expert-specific overrides
    config = get_config()
    
    # Validate inputs
    if velocity_vector is None or len(velocity_vector) == 0:
        raise ValueError("velocity_vector cannot be empty")
        
    if not isinstance(noise_level, (int, float)) or noise_level < 0:
        raise ValueError("noise_level must be a non-negative number")
        
    if steps <= 0:
        raise ValueError("steps must be a positive integer")
        
    if expert_type not in ["style", "structure", "texture", "default"]:
        # Log warning but allow custom expert types
        pass
        
    # Initialize step size
    if step_size is None:
        step_size = 1.0 / steps
        
    # Convert numpy to torch for computation
    # Start from a noisy version of the velocity vector
    x = torch.tensor(velocity_vector, dtype=torch.float32)
    x = x + noise_level * torch.randn_like(x)
    
    # Initialize the expert field simulator
    simulator = ExpertFieldSimulator(expert_type, config)
    
    # Perform Euler integration
    # Time t goes from 0 to 1
    for i in range(steps):
        t = i / steps
        
        # Compute velocity at current state
        v = simulator.compute_velocity(x, t)
        
        # Euler update: x_new = x + dt * v
        x = x + step_size * v
        
        # Optional: Clip to prevent numerical explosion
        x = torch.clamp(x, -10.0, 10.0)
        
    # Convert back to numpy
    final_state = x.detach().cpu().numpy()
    
    return final_state


def generate_image_from_velocity(
    velocity_vector: np.ndarray,
    noise_level: float,
    expert_type: str,
    steps: int = 50,
    output_path: Optional[str] = None
) -> np.ndarray:
    """
    High-level function to generate an image from a velocity vector.
    
    This wraps the euler_integrate function and optionally saves the result.
    
    Args:
        velocity_vector: Initial velocity vector (numpy array).
        noise_level: Initial noise level (scalar).
        expert_type: Expert field identifier.
        steps: Number of integration steps.
        output_path: Optional path to save the generated image.
        
    Returns:
        Generated image as a numpy array (latent representation).
    """
    # Integrate to get the final latent state
    latent = euler_integrate(
        velocity_vector=velocity_vector,
        noise_level=noise_level,
        expert_type=expert_type,
        steps=steps
    )
    
    # If output path is provided, save the image
    # Note: In a real implementation, this would decode the latent to pixel space
    if output_path:
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # For now, save the latent as a simple numpy file
        # In a full implementation, this would use a VAE decoder
        np.save(output_path, latent)
        
    return latent


def run_integrator(
    velocity_vector: np.ndarray,
    noise_level: float,
    expert_type: str,
    steps: int = 50,
    output_path: Optional[str] = None
) -> np.ndarray:
    """
    Main entry point for the integrator.
    
    This function is designed to be called by the fidelity evaluation pipeline.
    
    Args:
        velocity_vector: Velocity vector from the routing decision.
        noise_level: Noise level associated with the sample.
        expert_type: Type of expert to use for field simulation.
        steps: Number of Euler integration steps.
        output_path: Path to save the generated image.
        
    Returns:
        Generated image latent as a numpy array.
    """
    return generate_image_from_velocity(
        velocity_vector=velocity_vector,
        noise_level=noise_level,
        expert_type=expert_type,
        steps=steps,
        output_path=output_path
    )