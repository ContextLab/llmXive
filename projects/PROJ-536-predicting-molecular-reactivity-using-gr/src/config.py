"""
Configuration Manager for the Molecular Reactivity Prediction Pipeline.

This module centralizes all project paths, random seeds, and hyperparameters.
It ensures consistent configuration across the entire codebase.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch


@dataclass
class Config:
    """
    Central configuration container for the project.

    Attributes:
        project_root: Absolute path to the project root directory.
        data_dir: Path to the raw data directory.
        processed_data_dir: Path to the processed data directory.
        results_dir: Path to the results directory.
        models_dir: Path to the models directory.
        contracts_dir: Path to the contracts directory.
        seed: Random seed for reproducibility.
        device: Device to run computations on ('cpu' or 'cuda').
        
        # Hyperparameters for Data Processing
        max_smiles_length: Maximum allowed length for SMILES strings.
        min_atoms: Minimum number of atoms in a molecule to be included.
        
        # Hyperparameters for Model Training
        learning_rate: Initial learning rate.
        batch_size: Training batch size.
        num_epochs: Maximum number of training epochs.
        early_stopping_patience: Epochs to wait before stopping if no improvement.
        hidden_dim: Hidden dimension size for GNN layers.
        num_layers: Number of message passing layers.
        dropout: Dropout probability.
        
        # Hyperparameters for Baseline
        n_estimators: Number of trees for Random Forest.
        fingerprint_radius: Radius for Morgan fingerprints.
        fingerprint_bits: Number of bits for Morgan fingerprints.
        
        # Cross-validation
        n_folds: Number of folds for cross-validation.
    """
    
    # --- Paths ---
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    processed_data_dir: Path = field(init=False)
    results_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    contracts_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)
    
    # --- Seeds ---
    seed: int = 42
    
    # --- Device ---
    device: str = "cpu"
    
    # --- Data Hyperparameters ---
    max_smiles_length: int = 512
    min_atoms: int = 2
    
    # --- Model Hyperparameters ---
    learning_rate: float = 1e-3
    batch_size: int = 32
    num_epochs: int = 100
    early_stopping_patience: int = 10
    hidden_dim: int = 128
    num_layers: int = 3
    dropout: float = 0.1
    
    # --- Baseline Hyperparameters ---
    n_estimators: int = 100
    fingerprint_radius: int = 2
    fingerprint_bits: int = 2048
    
    # --- Validation Hyperparameters ---
    n_folds: int = 5
    
    # --- Conformal Prediction ---
    conformal_alpha: float = 0.1  # 1 - alpha is the target coverage
    conformal_calib_size: int = 1000

    def __post_init__(self):
        """Initialize derived paths based on project_root."""
        self.data_dir = self.project_root / "data" / "raw"
        self.processed_data_dir = self.project_root / "data" / "processed"
        self.results_dir = self.project_root / "results"
        self.models_dir = self.project_root / "models"
        self.contracts_dir = self.project_root / "contracts"
        self.figures_dir = self.project_root / "figures"
        
        # Ensure directories exist
        for p in [
            self.data_dir,
            self.processed_data_dir,
            self.results_dir,
            self.models_dir,
            self.contracts_dir,
            self.figures_dir
        ]:
            p.mkdir(parents=True, exist_ok=True)

    def set_device(self) -> torch.device:
        """
        Configures and returns the torch device.
        Forces CPU as per project constraints.
        """
        # Explicitly enforce CPU as per project constraints (PROJ-536)
        # even if CUDA is available, to ensure reproducibility and compliance.
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        self.device = "cpu"
        return torch.device(self.device)

    def seed_all(self):
        """
        Sets random seeds for Python, NumPy, and PyTorch for reproducibility.
        """
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def to_dict(self) -> Dict[str, Any]:
        """Converts the configuration to a dictionary."""
        # Exclude non-serializable Path objects by converting to string
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Returns the global configuration instance."""
    return config


if __name__ == "__main__":
    # Simple validation script to ensure config initializes correctly
    cfg = get_config()
    print(f"Project Root: {cfg.project_root}")
    print(f"Data Dir: {cfg.data_dir}")
    print(f"Device: {cfg.set_device()}")
    cfg.seed_all()
    print("Configuration initialized and seeds set.")
    print(f"Total Hyperparameters: {len(cfg.to_dict())}")
