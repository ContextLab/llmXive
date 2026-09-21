import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import logging
import time

from utils.mesh_utils import create_placeholder_mesh, export_mesh

logger = logging.getLogger(__name__)

class DifferentiableRaySurfaceLayer(nn.Module):
    """
    Differentiable ray-surface intersection layer using local triangle connectivity
    and depth gradients.
    """
    def __init__(self, num_faces: int = 1024):
        super().__init__()
        # Initialize with random vertices and faces for demonstration
        # In a real scenario, this would be initialized from a coarse mesh or point cloud
        self.vertices = nn.Parameter(torch.randn(num_faces * 3, 3) * 0.1)
        self.faces = torch.arange(num_faces * 3).reshape(num_faces, 3)
        
        self.num_faces = num_faces
        self.gradient_variance_threshold = 1e-4

    def forward(self, rays_o: torch.Tensor, rays_d: torch.Tensor, 
                depth_map: torch.Tensor, view_matrix: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute ray-surface intersections.
        
        Args:
            rays_o: Ray origins (B, N, 3)
            rays_d: Ray directions (B, N, 3)
            depth_map: Depth values (B, H, W)
            view_matrix: Camera view matrix (B, 4, 4)
        
        Returns:
            intersection_points: (B, N, 3)
            normals: (B, N, 3)
        """
        # Placeholder implementation for the differentiable layer
        # In a real implementation, this would compute actual intersections
        batch_size, num_rays, _ = rays_o.shape
        
        # Simple approximation: project rays onto depth map
        # This is a simplified version; real implementation would use actual geometry
        t_values = depth_map.view(batch_size, -1, 1).expand_as(rays_o)
        intersection_points = rays_o + t_values * rays_d
        
        # Compute normals (simplified)
        normals = torch.zeros_like(intersection_points)
        normals[:, :, 2] = 1.0  # Assume flat surface facing camera
        
        return intersection_points, normals

    def compute_gradient_variance(self, depth_map: torch.Tensor) -> float:
        """
        Compute gradient variance of the depth map to detect low-texture regions.
        
        Args:
            depth_map: Depth values (B, H, W)
        
        Returns:
            variance: float
        """
        # Compute gradients
        grad_x = depth_map[:, :, 1:] - depth_map[:, :, :-1]
        grad_y = depth_map[:, 1:, :] - depth_map[:, :-1, :]
        
        # Flatten and compute variance
        all_grads = torch.cat([grad_x.flatten(), grad_y.flatten()], dim=0)
        variance = all_grads.var().item()
        
        return variance

class GeometryOnlyModel(nn.Module):
    """
    Geometry-only reconstruction model without learned refinement head.
    """
    def __init__(self, num_faces: int = 1024):
        super().__init__()
        self.ray_surface_layer = DifferentiableRaySurfaceLayer(num_faces)
        self.num_faces = num_faces

    def forward(self, rays_o: torch.Tensor, rays_d: torch.Tensor,
                depth_map: torch.Tensor, view_matrix: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Run geometry-only reconstruction.
        
        Args:
            rays_o: Ray origins
            rays_d: Ray directions
            depth_map: Depth values
            view_matrix: Camera view matrix
        
        Returns:
            result: Dictionary with intersection points, normals, and mesh data
        """
        points, normals = self.ray_surface_layer(rays_o, rays_d, depth_map, view_matrix)
        
        return {
            'points': points,
            'normals': normals,
            'vertices': self.ray_surface_layer.vertices,
            'faces': self.ray_surface_layer.faces
        }

def create_geometry_only_model(num_faces: int = 1024) -> GeometryOnlyModel:
    """
    Create a geometry-only model instance.
    
    Args:
        num_faces: Number of faces in the mesh
    
    Returns:
        model: GeometryOnlyModel instance
    """
    return GeometryOnlyModel(num_faces)

def run_geometry_optimization(model: GeometryOnlyModel, 
                              rays_o: torch.Tensor, 
                              rays_d: torch.Tensor,
                              depth_map: torch.Tensor,
                              view_matrix: torch.Tensor,
                              max_iterations: int = 100,
                              lr: float = 0.01,
                              grad_var_threshold: float = 1e-4) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run geometry optimization with convergence detection.
    
    Args:
        model: GeometryOnlyModel instance
        rays_o: Ray origins
        rays_d: Ray directions
        depth_map: Depth values
        view_matrix: Camera view matrix
        max_iterations: Maximum number of iterations (default: 100)
        lr: Learning rate
        grad_var_threshold: Gradient variance threshold for low-texture detection
    
    Returns:
        result: Dictionary with optimization results
        status: Dictionary with status information
    """
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    converged = False
    iteration = 0
    low_texture_detected = False
    gradient_variances = []
    
    for iteration in range(1, max_iterations + 1):
        optimizer.zero_grad()
        
        # Forward pass
        output = model(rays_o, rays_d, depth_map, view_matrix)
        
        # Compute loss (simplified - in real scenario would use actual loss function)
        points = output['points']
        loss = points.mean()  # Placeholder loss
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Check for low-texture regions
        grad_var = model.ray_surface_layer.compute_gradient_variance(depth_map)
        gradient_variances.append(grad_var)
        
        if grad_var < grad_var_threshold:
            low_texture_detected = True
            logger.warning(f"Low-texture region detected at iteration {iteration} with gradient variance {grad_var}")
        
        # Check for convergence (simplified - in real scenario would use actual convergence criteria)
        if iteration > 10:
            recent_vars = gradient_variances[-10:]
            if max(recent_vars) - min(recent_vars) < 1e-6:
                converged = True
                logger.info(f"Convergence detected at iteration {iteration}")
                break
        
        if iteration % 10 == 0:
            logger.debug(f"Iteration {iteration}: loss={loss.item():.6f}, grad_var={grad_var:.6f}")
    
    result = {
        'final_output': output,
        'iterations': iteration,
        'final_loss': loss.item(),
        'converged': converged,
        'low_texture_detected': low_texture_detected,
        'gradient_variances': gradient_variances
    }
    
    status = {
        'success': converged,
        'converged': converged,
        'low_texture': low_texture_detected,
        'reason': 'Converged' if converged else 'Max iterations reached'
    }
    
    return result, status

def generate_placeholder_mesh_from_failure(output_dir: Path, 
                                           scene_id: str, 
                                           error_flag: str,
                                           points: Optional[np.ndarray] = None,
                                           num_points: int = 100) -> Path:
    """
    Generate a placeholder mesh when optimization fails.
    
    Args:
        output_dir: Directory to save the mesh
        scene_id: Scene identifier
        error_flag: Error flag (e.g., 'TIMEOUT_CONVERGENCE_FAILED', 'LOW_TEXTURE_CONVERGENCE_FAILED')
        points: Optional array of points (if available)
        num_points: Number of points for placeholder mesh
    
    Returns:
        mesh_path: Path to the generated placeholder mesh
    """
    logger.warning(f"Generating placeholder mesh due to {error_flag}")
    
    # Create placeholder mesh
    if points is not None and len(points) > 0:
        mesh = create_placeholder_mesh(points)
    else:
        # Generate random points if none provided
        random_points = np.random.randn(num_points, 3) * 0.1
        mesh = create_placeholder_mesh(random_points)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save mesh
    mesh_path = output_dir / f"{scene_id}_placeholder_{error_flag}.obj"
    export_mesh(mesh, mesh_path)
    
    logger.info(f"Placeholder mesh saved to {mesh_path}")
    
    return mesh_path

def run_geometry_optimization_with_fallback(model: GeometryOnlyModel,
                                            rays_o: torch.Tensor,
                                            rays_d: torch.Tensor,
                                            depth_map: torch.Tensor,
                                            view_matrix: torch.Tensor,
                                            output_dir: Path,
                                            scene_id: str,
                                            max_iterations: int = 100,
                                            lr: float = 0.01) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[Path]]:
    """
    Run geometry optimization with fallback to placeholder mesh on failure.
    
    This function implements the general non-convergence handling required by FR-007.
    If the 100-iteration limit is hit for ANY reason (not just low-texture), it generates
    a placeholder mesh and logs the error flag "TIMEOUT_CONVERGENCE_FAILED".
    
    Args:
        model: GeometryOnlyModel instance
        rays_o: Ray origins
        rays_d: Ray directions
        depth_map: Depth values
        view_matrix: Camera view matrix
        output_dir: Directory to save results
        scene_id: Scene identifier
        max_iterations: Maximum number of iterations (default: 100)
        lr: Learning rate
    
    Returns:
        result: Dictionary with optimization results
        status: Dictionary with status information
        mesh_path: Path to the generated mesh (None if optimization succeeded)
    """
    logger.info(f"Starting geometry optimization for scene {scene_id}")
    
    # Run optimization
    result, status = run_geometry_optimization(
        model, rays_o, rays_d, depth_map, view_matrix,
        max_iterations=max_iterations, lr=lr
    )
    
    mesh_path = None
    
    # Handle non-convergence
    if not status['success']:
        if status.get('low_texture', False):
            error_flag = "LOW_TEXTURE_CONVERGENCE_FAILED"
        else:
            # General non-convergence (timeout) - this is the main focus of T043
            error_flag = "TIMEOUT_CONVERGENCE_FAILED"
            logger.warning(f"General non-convergence detected for scene {scene_id}: {status['reason']}")
            logger.warning(f"Generating placeholder mesh with error flag: {error_flag}")
        
        # Generate placeholder mesh
        points = None
        if 'final_output' in result and 'points' in result['final_output']:
            points = result['final_output']['points'].detach().cpu().numpy().reshape(-1, 3)
        
        mesh_path = generate_placeholder_mesh_from_failure(
            output_dir, scene_id, error_flag, points
        )
        
        # Update status to indicate failure handling
        status['handled'] = True
        status['error_flag'] = error_flag
        status['mesh_path'] = str(mesh_path)
    
    return result, status, mesh_path