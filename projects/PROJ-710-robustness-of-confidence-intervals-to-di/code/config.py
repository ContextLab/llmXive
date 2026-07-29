import os
from pathlib import Path

# Project root is the directory containing this file
project_root = Path(__file__).resolve().parent.parent
code_root = project_root

class Config:
    """
    Central configuration for the robustness of confidence intervals to DP noise project.
    
    Attributes:
        nominal_coverage_target: The target coverage probability (default 0.95).
        random_seed: Seed for reproducibility.
        artifacts_dir: Directory for output artifacts.
        data_dir: Directory for data files.
    """
    
    def __init__(self):
        self.nominal_coverage_target = 0.95
        self.random_seed = 42
        self.n_bootstrap = 1000
        
        # Directory paths
        self.artifacts_dir = project_root / "artifacts"
        self.data_dir = project_root / "data"
        self.figures_dir = project_root / "figures"
        
        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # DP Noise Parameters
        self.epsilon_values = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.noise_types = ['laplace', 'gaussian']
        
        # Datasets
        self.datasets = ['adult', 'iris', 'wine']
        
        # Validation thresholds
        self.min_sample_size = 30
        self.max_noise_scale_factor = 10.0
        
        # GLM settings
        self.glm_alpha = 0.05

    def get_artifact_path(self, filename: str) -> Path:
        """Get the full path for an artifact file."""
        return self.artifacts_dir / filename

    def get_data_path(self, filename: str) -> Path:
        """Get the full path for a data file."""
        return self.data_dir / filename

# Singleton instance for convenience
config = Config()