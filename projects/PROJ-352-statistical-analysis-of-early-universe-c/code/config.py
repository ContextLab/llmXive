"""
Configuration management for the Statistical Analysis of Early Universe CMB Fluctuations.

This module provides centralized configuration for:
- File paths (raw, processed, output directories)
- Random seeds for reproducibility
- Planck mission parameters (Nside, beam FWHM, noise levels)
- Analysis thresholds and parameters
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default directory structure
DEFAULT_DIRS = {
    "raw": "data/raw",
    "processed": "data/processed",
    "output": "output",
    "figures": "output/figures",
    "logs": "output/logs"
}

# Planck 2018 Legacy Archive parameters
PLANCK_PARAMS = {
    "default_nside": 128,
    "beam_fwhm_arcmin": 5.0,
    "noise_sigma_uK": 1.1,
    "pixel_area_steradians": 4 * 3.141592653589793 / (12 * 128**2),
    # SMICA map filename for Nside=128
    "smica_filename": "COM_CMB_ILM-NR1-000_R2.01.fits",
    # Known checksums (MD5) for validation - these should be updated with actual values from Planck
    "smica_checksums": {
        "R2.01": "d41d8cd98f00b204e9800998ecf8427e"  # Placeholder - replace with real MD5
    },
    # URL template for Planck Legacy Archive
    "pla_url_template": "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID={filename}"
}

# Analysis parameters
ANALYSIS_PARAMS = {
    "mask_buffer_pixels": 2,
    "minkowski_thresholds_sigma": [-1.0, -0.5, 0.0, 0.5, 1.0],
    "genus_curve_sampling_points": 100,
    "cosmic_string_gmu_range": (1e-7, 1e-5),
    "cosmic_string_samples": 50,
}

# Simulation parameters
SIMULATION_PARAMS = {
    "n_gaussian_realizations": 500,
    "n_string_realizations": 500,
    "random_seed": 42,
    "max_runtime_hours": 6,
    "batch_size": 50,  # Process in batches to manage memory
}

# Statistical test parameters
STAT_PARAMS = {
    "ledoit_wolf_shrinkage": True,
    "pca_components": 10,
    "chi2_significance": 0.05,
    "covariance_regularization": 1e-6,
}

@dataclass
class Config:
    """Central configuration container."""
    
    # Paths
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    raw_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DIRS["raw"])
    processed_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DIRS["processed"])
    output_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DIRS["output"])
    figures_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DIRS["figures"])
    logs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / DEFAULT_DIRS["logs"])
    
    # Planck parameters
    nside: int = PLANCK_PARAMS["default_nside"]
    beam_fwhm_arcmin: float = PLANCK_PARAMS["beam_fwhm_arcmin"]
    noise_sigma_uK: float = PLANCK_PARAMS["noise_sigma_uK"]
    smica_filename: str = PLANCK_PARAMS["smica_filename"]
    pla_url_template: str = PLANCK_PARAMS["pla_url_template"]
    
    # Analysis parameters
    mask_buffer_pixels: int = ANALYSIS_PARAMS["mask_buffer_pixels"]
    minkowski_thresholds: List[float] = field(default_factory=lambda: ANALYSIS_PARAMS["minkowski_thresholds_sigma"])
    
    # Simulation parameters
    n_gaussian: int = SIMULATION_PARAMS["n_gaussian_realizations"]
    n_string: int = SIMULATION_PARAMS["n_string_realizations"]
    random_seed: int = SIMULATION_PARAMS["random_seed"]
    max_runtime_hours: float = SIMULATION_PARAMS["max_runtime_hours"]
    batch_size: int = SIMULATION_PARAMS["batch_size"]
    
    # Statistical parameters
    use_ledoit_wolf: bool = STAT_PARAMS["ledoit_wolf_shrinkage"]
    pca_components: int = STAT_PARAMS["pca_components"]
    chi2_significance: float = STAT_PARAMS["chi2_significance"]
    
    def __post_init__(self):
        """Ensure all paths are absolute and exist."""
        self.project_root = self.project_root.resolve()
        self.raw_data_dir = self.raw_data_dir.resolve()
        self.processed_data_dir = self.processed_data_dir.resolve()
        self.output_dir = self.output_dir.resolve()
        self.figures_dir = self.figures_dir.resolve()
        self.logs_dir = self.logs_dir.resolve()
        
        # Create directories if they don't exist
        for dir_path in [self.raw_data_dir, self.processed_data_dir, 
                        self.output_dir, self.figures_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_smica_url(self) -> str:
        """Get the full URL for the SMICA map download."""
        return self.pla_url_template.format(filename=self.smica_filename)
    
    def get_processed_path(self, filename: str) -> Path:
        """Get the full path for a processed data file."""
        return self.processed_data_dir / filename
    
    def get_output_path(self, filename: str) -> Path:
        """Get the full path for an output file."""
        return self.output_dir / filename
    
    def get_figure_path(self, filename: str) -> Path:
        """Get the full path for a figure file."""
        return self.figures_dir / filename
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "project_root": str(self.project_root),
            "nside": self.nside,
            "beam_fwhm_arcmin": self.beam_fwhm_arcmin,
            "noise_sigma_uK": self.noise_sigma_uK,
            "smica_filename": self.smica_filename,
            "mask_buffer_pixels": self.mask_buffer_pixels,
            "minkowski_thresholds": self.minkowski_thresholds,
            "n_gaussian": self.n_gaussian,
            "n_string": self.n_string,
            "random_seed": self.random_seed,
            "max_runtime_hours": self.max_runtime_hours,
            "batch_size": self.batch_size,
            "use_ledoit_wolf": self.use_ledoit_wolf,
            "pca_components": self.pca_components,
            "chi2_significance": self.chi2_significance,
        }
    
    def save_to_json(self, filepath: Optional[Path] = None) -> Path:
        """Save configuration to a JSON file."""
        if filepath is None:
            filepath = self.get_output_path("config.json")
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return filepath
    
    @classmethod
    def from_json(cls, filepath: Path) -> 'Config':
        """Load configuration from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        # Check Nside is valid (power of 2)
        if self.nside & (self.nside - 1) != 0 or self.nside < 4:
            raise ValueError(f"Invalid Nside: {self.nside}. Must be a power of 2 >= 4.")
        
        # Check beam FWHM is positive
        if self.beam_fwhm_arcmin <= 0:
            raise ValueError(f"Invalid beam FWHM: {self.beam_fwhm_arcmin}. Must be positive.")
        
        # Check noise sigma is positive
        if self.noise_sigma_uK <= 0:
            raise ValueError(f"Invalid noise sigma: {self.noise_sigma_uK}. Must be positive.")
        
        # Check simulation counts are positive
        if self.n_gaussian <= 0 or self.n_string <= 0:
            raise ValueError("Simulation counts must be positive.")
        
        # Check batch size is positive and <= total simulations
        if self.batch_size <= 0 or self.batch_size > (self.n_gaussian + self.n_string):
            raise ValueError("Invalid batch size.")
        
        return True

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def update_config(**kwargs) -> Config:
    """Update global configuration with provided parameters."""
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise AttributeError(f"Unknown configuration parameter: {key}")
    return config

if __name__ == "__main__":
    # Example usage: print configuration and save to file
    cfg = get_config()
    print("Current Configuration:")
    print(json.dumps(cfg.to_dict(), indent=2))
    
    # Save configuration to file
    cfg_path = cfg.save_to_json()
    print(f"\nConfiguration saved to: {cfg_path}")
    
    # Validate configuration
    if cfg.validate():
        print("Configuration validation: PASSED")
    else:
        print("Configuration validation: FAILED")