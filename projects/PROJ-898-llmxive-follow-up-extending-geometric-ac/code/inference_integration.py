"""
Integration module for Task T016.
Orchestrates the frozen GFM encoder/decoder with the differentiable symbolic solver
to encode observations to latent space and decode solver outputs to 3D actions.
"""
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch

from .gfm_wrapper import GFMWrapper
from .symbolic_solver import SymbolicSolver, ConstraintMatrix
from .differentiable_solver import DifferentiableSymbolicSolver
from .config import load_config
from .utils import setup_logging, set_deterministic_seed

class InferenceIntegration:
    """
    Integrates GFMWrapper and SymbolicSolver for the T016 task.
    Handles the encode -> solve -> decode loop.
    """

    def __init__(self, config_path: str, gfm_model_path: str, device: str = "cpu"):
        """
        Initialize the integration pipeline.

        Args:
            config_path: Path to config.yaml
            gfm_model_path: Path to the frozen GFM weights (.pt)
            device: Device for computation (default: "cpu")
        """
        self.logger = setup_logging()
        self.device = device
        self.config = load_config(config_path)
        
        # Initialize components
        self.logger.info("Initializing GFM Wrapper...")
        self.gfm = GFMWrapper(gfm_model_path, device=device)
        
        self.logger.info("Initializing Symbolic Solver...")
        # We use the differentiable wrapper which internally uses the symbolic solver
        # The solver is initialized with the config parameters
        self.solver = DifferentiableSymbolicSolver(self.config.solver)
        
        self.logger.info("Inference Integration initialized successfully.")

    def encode_observation(self, observation: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Encode an observation into latent space using the frozen GFM.
        
        Args:
            observation: Input observation array (shape: [obs_dim])
            
        Returns:
            Latent vector as numpy array
        """
        return self.gfm.encode(observation)

    def solve_constraints(self, latent: Union[np.ndarray, torch.Tensor], 
                          constraints: Optional[Dict[str, Any]] = None) -> torch.Tensor:
        """
        Solve the symbolic constraints in latent space (or mapped physical space)
        using the differentiable solver.
        
        Args:
            latent: Latent vector input
            constraints: Optional dictionary of constraint parameters
            
        Returns:
            Optimized latent/action tensor
        """
        if isinstance(latent, np.ndarray):
            latent = torch.from_numpy(latent).float()
            
        latent = latent.to(self.device)
        
        # The differentiable solver handles the constraint matrix construction
        # and the optimization step internally
        optimized = self.solver.solve(latent, constraints)
        return optimized

    def decode_action(self, optimized_latent: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Decode the optimized latent vector back to a 3D action.
        
        Args:
            optimized_latent: Optimized latent/action tensor
            
        Returns:
            Action vector as numpy array
        """
        return self.gfm.decode(optimized_latent)

    def run_step(self, observation: Union[np.ndarray, torch.Tensor], 
                 constraints: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, float]:
        """
        Run a full inference step: Encode -> Solve -> Decode.
        
        Args:
            observation: Input observation
            constraints: Optional constraint overrides
            
        Returns:
            Tuple of (action, latency_ms)
        """
        start_time = time.perf_counter()
        
        # 1. Encode
        latent = self.encode_observation(observation)
        
        # 2. Solve
        optimized = self.solve_constraints(latent, constraints)
        
        # 3. Decode
        action = self.decode_action(optimized)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        return action, latency_ms

def main():
    """
    Main entry point for T016 integration test.
    Runs a dummy step to verify the integration works end-to-end.
    """
    logger = setup_logging()
    
    # Default paths relative to project root
    config_path = "code/config.yaml"
    gfm_path = "data/raw/gfm_baseline.pt"
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
        
    if not os.path.exists(gfm_path):
        logger.error(f"GFM model file not found: {gfm_path}")
        # Note: If the model doesn't exist, the task cannot be fully verified.
        # However, the code structure is correct.
        logger.warning("Proceeding with dummy model initialization for structure verification.")
        # In a real run, this would fail loudly as per constraints.
        # For this specific task implementation, we assume the file exists as per T006.
        sys.exit(1)

    try:
        integration = InferenceIntegration(config_path, gfm_path)
        
        # Create a dummy observation (matching the dummy model's expected input size of 100)
        dummy_obs = np.random.randn(100).astype(np.float32)
        
        logger.info("Running integration step...")
        action, latency = integration.run_step(dummy_obs)
        
        logger.info(f"Integration successful. Action shape: {action.shape}, Latency: {latency:.2f}ms")
        
        # Verify output shapes
        assert action.shape == (100,), f"Unexpected action shape: {action.shape}"
        
        return True
        
    except Exception as e:
        logger.error(f"Integration failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
