"""
CPU-only Euler Integrator for DanceOPD field distillation.

This module implements the Euler integration step to generate images from
velocity vectors and noise levels using specific expert field logic.
"""

import torch
import numpy as np
from typing import Dict, Any, List, Union, Optional
from pathlib import Path

# Import the expert loader to access expert field logic
# We assume the expert_loader module provides a way to get the expert model
try:
    from models.expert_loader import get_expert_field
except ImportError:
    # Fallback for standalone execution if expert_loader is not yet available
    # In a real run, this should be provided by T029b
    get_expert_field = None

from utils.config import get_config


class EulerIntegrator:
    """
    CPU-only Euler Integrator for generating images from velocity vectors.
    """

    def __init__(self, expert_type: str, step_size: float = 0.1, n_steps: int = 10):
        """
        Initialize the Euler Integrator.

        Args:
            expert_type: The type of expert field to use (e.g., 'style', 'structure').
            step_size: The step size for Euler integration.
            n_steps: The number of integration steps.
        """
        self.expert_type = expert_type
        self.step_size = step_size
        self.n_steps = n_steps
        self.config = get_config()
        self.device = torch.device("cpu")

        # Load the expert field logic
        if get_expert_field is not None:
            self.expert_model = get_expert_field(expert_type)
            if self.expert_model is None:
                raise RuntimeError(f"Failed to load expert field for type: {expert_type}")
        else:
            raise RuntimeError("Expert loader not available. Ensure T029b is completed.")

    def integrate(self, velocity_vector: Union[List[float], np.ndarray], noise_level: float) -> torch.Tensor:
        """
        Perform Euler integration to generate an image.

        Args:
            velocity_vector: The velocity vector from the teacher model or tree prediction.
            noise_level: The noise level for the integration process.
            expert_type: The expert type to use for generation.

        Returns:
            A torch.Tensor representing the generated image (C, H, W).
        """
        # Convert inputs to tensors
        if isinstance(velocity_vector, list):
            velocity_vector = np.array(velocity_vector)
        
        velocity_tensor = torch.tensor(velocity_vector, dtype=torch.float32, device=self.device)
        
        # Initialize the latent state based on noise level
        # Assuming a standard latent dimension, e.g., 64x64x3 or similar
        # The exact initialization depends on the expert field's expected input
        # For now, we assume a generic initialization based on noise
        latent_dim = int(np.sqrt(velocity_tensor.shape[0])) if velocity_tensor.ndim == 1 else 64
        # Adjust latent_dim based on the actual velocity vector dimension if needed
        # This is a placeholder; the real implementation should match the expert's expected input
        if velocity_tensor.shape[0] == 64 * 64 * 3: # 12288
            h, w, c = 64, 64, 3
        elif velocity_tensor.shape[0] == 64 * 64: # 4096
            h, w, c = 64, 64, 1
        else:
            # Fallback or error if dimension doesn't match expected
            # In a real scenario, this should be handled by the expert model's config
            raise ValueError(f"Unexpected velocity vector dimension: {velocity_tensor.shape[0]}")

        # Initialize latent state with noise
        latent_state = torch.randn(h, w, c, device=self.device) * noise_level

        # Ensure latent_state is 4D for the model (B, C, H, W)
        latent_state = latent_state.permute(2, 0, 1).unsqueeze(0) # (1, C, H, W)

        # Euler integration loop
        for step in range(self.n_steps):
            # Get the current velocity from the expert model
            # The expert model should take the current latent state and return a velocity update
            with torch.no_grad():
                # Ensure the expert model is in eval mode
                self.expert_model.eval()
                
                # The expert model might expect a specific input format
                # This is a placeholder call; the actual call depends on the expert's implementation
                # We assume the expert model takes (latent_state, velocity_vector, noise_level)
                # and returns a velocity update or directly updates the latent state
                
                # For this implementation, we assume the expert model returns a velocity update
                # based on the current latent state and the provided velocity vector
                # This is a simplified version; the real implementation should match the expert's API
                velocity_update = self.expert_model(latent_state, velocity_tensor, noise_level)
                
                # Apply Euler step: z_{t+1} = z_t + step_size * velocity_update
                latent_state = latent_state + self.step_size * velocity_update

        # Clamp values to valid range if necessary (e.g., [0, 1] or [-1, 1])
        latent_state = torch.clamp(latent_state, -1.0, 1.0)

        return latent_state.squeeze(0) # Return (C, H, W)


def integrate(
    velocity_vector: Union[List[float], np.ndarray],
    noise_level: float,
    expert_type: str,
    step_size: float = 0.1,
    n_steps: int = 10
) -> torch.Tensor:
    """
    Generate an image using Euler integration with a specific expert field.

    Args:
        velocity_vector: The velocity vector from the teacher model or tree prediction.
        noise_level: The noise level for the integration process.
        expert_type: The expert type to use for generation (e.g., 'style', 'structure').
        step_size: The step size for Euler integration.
        n_steps: The number of integration steps.

    Returns:
        A torch.Tensor representing the generated image (C, H, W).
    """
    integrator = EulerIntegrator(expert_type, step_size, n_steps)
    return integrator.integrate(velocity_vector, noise_level)


def generate_image_from_velocity(
    velocity_vector: Union[List[float], np.ndarray],
    noise_level: float,
    expert_type: str,
    seed: Optional[int] = None
) -> torch.Tensor:
    """
    Generate an image from a velocity vector using the Euler integrator.
    This is a convenience wrapper that sets the random seed.

    Args:
        velocity_vector: The velocity vector.
        noise_level: The noise level.
        expert_type: The expert type.
        seed: Optional random seed for reproducibility.

    Returns:
        A torch.Tensor representing the generated image.
    """
    if seed is not None:
        torch.manual_seed(seed)
        np.random.seed(seed)
    
    return integrate(velocity_vector, noise_level, expert_type)


def run_integrator(
    velocity_vectors: List[Union[List[float], np.ndarray]],
    noise_levels: List[float],
    expert_types: List[str],
    output_dir: Path,
    step_size: float = 0.1,
    n_steps: int = 10
) -> Dict[str, str]:
    """
    Run the Euler integrator on a batch of samples and save the results.

    Args:
        velocity_vectors: List of velocity vectors.
        noise_levels: List of noise levels.
        expert_types: List of expert types corresponding to each sample.
        output_dir: Directory to save the generated images.
        step_size: Step size for Euler integration.
        n_steps: Number of integration steps.

    Returns:
        A dictionary mapping sample index to the path of the generated image.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for i, (vel, noise, expert_type) in enumerate(zip(velocity_vectors, noise_levels, expert_types)):
        try:
            image = integrate(vel, noise, expert_type, step_size, n_steps)
            # Save the image
            output_path = output_dir / f"sample_{i}.png"
            # Convert tensor to PIL Image and save
            from PIL import Image
            import torchvision.transforms as transforms
            
            # Normalize and convert to uint8
            image = image.permute(1, 2, 0).cpu().numpy()
            image = (image + 1) / 2 * 255 # Scale from [-1, 1] to [0, 255]
            image = np.clip(image, 0, 255).astype(np.uint8)
            
            # Handle grayscale if C=1
            if image.shape[2] == 1:
                image = image.squeeze(2)
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image, mode='RGB')
            
            pil_image.save(output_path)
            results[str(i)] = str(output_path)
        except Exception as e:
            # Log error but continue with other samples
            print(f"Error processing sample {i}: {e}")
            results[str(i)] = None
    
    return results