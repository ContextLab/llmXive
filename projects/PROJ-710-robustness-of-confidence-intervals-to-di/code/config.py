"""
Configuration for the Robustness of CI to DP Noise pipeline.
Stores hyperparameters, random seeds, artifact paths, and ground truth parameters.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    def __init__(self):
        # Simulation parameters
        self.n_sim = 1000
        self.n_bootstrap = 1000
        self.confidence_level = 0.95
        self.random_seed = 42
        
        # Dataset parameters
        self.datasets = ["adult", "iris", "wine"]
        self.statistic_types = ["mean", "regression"]
        self.epsilons = [0.1, 0.5, 1.0, 2.0, 5.0]
        self.noise_types = ["laplace", "gaussian"]
        
        # Sample sizes
        self.sample_size = 1000
        self.min_sample_size = 10
        
        # Population sizes
        self.population_size_adult = 1000000
        self.population_size_iris = 1000000
        self.population_size_wine = 1000000
        
        # Noise scales (base)
        self.noise_scales = {
            "laplace": 1.0,
            "gaussian": 1.0
        }
        
        # Regression features
        self.regression_features = ["age", "education"] # For adult
        self.regression_target = "income"
        
        # Mean target columns
        self.mean_target_columns = {
            "adult": "income",
            "iris": "sepal_length",
            "wine": "alcohol"
        }
        
        # Ground truth parameters (for validation)
        # These are approximate and should be computed from the population if needed
        # But for the simulation, we compute them from the population sample
        self.ground_truth = {}

    def get_artifact_path(self, filename: str) -> Path:
        return PROJECT_ROOT / "artifacts" / filename

    def get_data_path(self, filename: str) -> Path:
        return PROJECT_ROOT / "data" / filename

    def get_figure_path(self, filename: str) -> Path:
        return PROJECT_ROOT / "figures" / filename

def get_artifact_path(filename: str) -> Path:
    config = Config()
    return config.get_artifact_path(filename)

def get_data_path(filename: str) -> Path:
    config = Config()
    return config.get_data_path(filename)

def get_figure_path(filename: str) -> Path:
    config = Config()
    return config.get_figure_path(filename)
