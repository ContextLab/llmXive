#!/usr/bin/env python
"""
Euler Integrator for DanceOPD Generative Field Distillation.

Implements CPU-only Euler integration to generate images from velocity vectors,
noise levels, and expert types. This module is designed to be CPU-safe and
compatible with the project's resource constraints.
"""
import torch
import numpy as np
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
import logging
import random

# Import from project utils
from utils.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set default device to CPU explicitly
torch.set_default_device('cpu')


class EulerIntegrator:
    """
    CPU-only Euler integrator for generative field distillation.
    
    Implements the Euler integration loop with noise injection:
    x_{t+1} = x_t + step_size * v_t + sqrt(step_size) * noise
    
    Parameters:
        step_size (float): Integration step size (default: 0.1)
        steps (int): Number of integration steps (default: 10)
        seed (int): Random seed for reproducibility (default: 42)
    """
    
    def __init__(self, step_size: float = 0.1, steps: int = 10, seed: int = 42):
        self.step_size = step_size
        self.steps = steps
        self.seed = seed
        self._set_seed(seed)
        
    def _set_seed(self, seed: int):
        """Set random seeds for reproducibility."""
        random.seed(seed)
        torch.manual_seed(seed)
        np.random.seed(seed)
        
    def integrate(
        self,
        velocity_vector: Union[List[float], np.ndarray, torch.Tensor],
        noise_level: float,
        expert_type: str,
        initial_state: Optional[Union[np.ndarray, torch.Tensor]] = None
    ) -> torch.Tensor:
        """
        Perform Euler integration to generate a state from velocity vector.
        
        Args:
            velocity_vector: The velocity vector (list, numpy array, or tensor)
            noise_level: The noise level for the diffusion process
            expert_type: The type of expert field (used for expert-specific logic)
            initial_state: Optional initial state. If None, starts from noise.
        
        Returns:
            torch.Tensor: The integrated state (image representation)
        """
        # Convert inputs to tensors on CPU
        if isinstance(velocity_vector, list):
            velocity_vector = torch.tensor(velocity_vector, dtype=torch.float32)
        elif isinstance(velocity_vector, np.ndarray):
            velocity_vector = torch.from_numpy(velocity_vector).float()
        
        # Ensure velocity is on CPU
        velocity_vector = velocity_vector.cpu()
        
        # Initialize state
        if initial_state is None:
            # Start from Gaussian noise scaled by noise_level
            dim = velocity_vector.shape[0]
            initial_state = torch.randn(dim, dtype=torch.float32) * noise_level
        else:
            if isinstance(initial_state, np.ndarray):
                initial_state = torch.from_numpy(initial_state).float()
            initial_state = initial_state.cpu()
        
        current_state = initial_state.clone()
        
        # Euler integration loop
        for t in range(self.steps):
            # Get noise for this step
            noise = torch.randn_like(current_state)
            
            # Euler step: x_{t+1} = x_t + step_size * v_t + sqrt(step_size) * noise
            # Note: In practice, v_t might depend on current_state and expert_type
            # For this implementation, we use the provided velocity_vector directly
            # In a real scenario, this would call expert field logic
            
            # Apply expert-specific modulation if needed
            velocity = self._apply_expert_modulation(velocity_vector, expert_type, t)
            
            # Compute update
            update = self.step_size * velocity + np.sqrt(self.step_size) * noise
            
            # Update state
            current_state = current_state + update
            
            # Clamp to valid range (e.g., [-1, 1] for normalized images)
            current_state = torch.clamp(current_state, -1.0, 1.0)
        
        return current_state
    
    def _apply_expert_modulation(
        self,
        velocity_vector: torch.Tensor,
        expert_type: str,
        step: int
    ) -> torch.Tensor:
        """
        Apply expert-specific modulation to the velocity vector.
        
        This is a placeholder for expert-specific logic that would be
        implemented in a real system. For now, it returns the velocity
        unchanged.
        
        Args:
            velocity_vector: The base velocity vector
            expert_type: The expert type identifier
            step: Current integration step
        
        Returns:
            torch.Tensor: Modulated velocity vector
        """
        # In a real implementation, this would load and apply expert-specific
        # weights or transformations from the expert field
        # For now, return the velocity unchanged
        return velocity_vector


def integrate(
    velocity_vector: Union[List[float], np.ndarray, torch.Tensor],
    noise_level: float,
    expert_type: str,
    step_size: float = 0.1,
    steps: int = 10,
    seed: int = 42,
    initial_state: Optional[Union[np.ndarray, torch.Tensor]] = None
) -> torch.Tensor:
    """
    Convenience function to perform Euler integration.
    
    Args:
        velocity_vector: The velocity vector (list, numpy array, or tensor)
        noise_level: The noise level for the diffusion process
        expert_type: The type of expert field
        step_size: Integration step size (default: 0.1)
        steps: Number of integration steps (default: 10)
        seed: Random seed for reproducibility (default: 42)
        initial_state: Optional initial state
    
    Returns:
        torch.Tensor: The integrated state
    """
    integrator = EulerIntegrator(step_size=step_size, steps=steps, seed=seed)
    return integrator.integrate(
        velocity_vector=velocity_vector,
        noise_level=noise_level,
        expert_type=expert_type,
        initial_state=initial_state
    )


def generate_image_from_velocity(
    velocity_vector: Union[List[float], np.ndarray, torch.Tensor],
    noise_level: float,
    expert_type: str,
    output_path: Optional[str] = None,
    step_size: float = 0.1,
    steps: int = 10,
    seed: int = 42
) -> torch.Tensor:
    """
    Generate an image representation from velocity vector and save to disk.
    
    Args:
        velocity_vector: The velocity vector
        noise_level: The noise level
        expert_type: The expert type
        output_path: Optional path to save the generated image
        step_size: Integration step size
        steps: Number of integration steps
        seed: Random seed
    
    Returns:
        torch.Tensor: The generated image tensor
    """
    # Perform integration
    image_tensor = integrate(
        velocity_vector=velocity_vector,
        noise_level=noise_level,
        expert_type=expert_type,
        step_size=step_size,
        steps=steps,
        seed=seed
    )
    
    # Save to disk if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to numpy and save
        image_np = image_tensor.detach().cpu().numpy()
        
        # For demonstration, save as a simple text file with the tensor values
        # In a real implementation, this would be saved as an image file
        np.savetxt(output_path, image_np, fmt='%.6f')
        logger.info(f"Generated image saved to {output_path}")
    
    return image_tensor


def run_integrator(
    input_data: Dict[str, Any],
    output_dir: str,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Run the integrator on a batch of input data.
    
    Args:
        input_data: Dictionary containing:
            - velocity_vectors: List of velocity vectors
            - noise_levels: List of noise levels
            - expert_types: List of expert types
            - sample_ids: List of sample identifiers
        output_dir: Directory to save generated images
        config: Optional configuration dictionary
    
    Returns:
        List[str]: Paths to generated image files
    """
    # Get config values
    if config is None:
        config = get_config()
    
    step_size = config.get('EULER_STEP_SIZE', 0.1)
    steps = config.get('EULER_STEPS', 10)
    seed = config.get('SEED', 42)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Process each sample
    for i, sample_id in enumerate(input_data['sample_ids']):
        velocity_vector = input_data['velocity_vectors'][i]
        noise_level = input_data['noise_levels'][i]
        expert_type = input_data['expert_types'][i]
        
        # Generate image
        output_file = output_path / f"{sample_id}.txt"
        
        try:
            image_tensor = generate_image_from_velocity(
                velocity_vector=velocity_vector,
                noise_level=noise_level,
                expert_type=expert_type,
                output_path=str(output_file),
                step_size=step_size,
                steps=steps,
                seed=seed + i  # Vary seed for each sample
            )
            generated_files.append(str(output_file))
            logger.info(f"Generated image for sample {sample_id}")
        except Exception as e:
            logger.error(f"Failed to generate image for sample {sample_id}: {e}")
            raise
    
    return generated_files


def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Euler Integrator for DanceOPD")
    parser.add_argument("--velocity", type=str, required=True, help="Comma-separated velocity vector")
    parser.add_argument("--noise", type=float, default=0.5, help="Noise level")
    parser.add_argument("--expert", type=str, default="default", help="Expert type")
    parser.add_argument("--output", type=str, default="data/results/generated_image.txt", help="Output file path")
    parser.add_argument("--steps", type=int, default=10, help="Number of integration steps")
    parser.add_argument("--step-size", type=float, default=0.1, help="Step size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Parse velocity vector
    velocity_vector = [float(x) for x in args.velocity.split(',')]
    
    logger.info(f"Running Euler integrator with {len(velocity_vector)}-dim velocity vector")
    logger.info(f"Noise level: {args.noise}, Expert: {args.expert}")
    logger.info(f"Steps: {args.steps}, Step size: {args.step_size}")
    
    # Generate image
    image_tensor = generate_image_from_velocity(
        velocity_vector=velocity_vector,
        noise_level=args.noise,
        expert_type=args.expert,
        output_path=args.output,
        step_size=args.step_size,
        steps=args.steps,
        seed=args.seed
    )
    
    logger.info(f"Successfully generated image: {image_tensor.shape}")
    logger.info(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()