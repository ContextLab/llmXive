"""
Configuration management for the Phase Transitions in Amorphous Solids pipeline.

This module handles environment variables, path resolution, and simulation parameters
required for the research pipeline.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file if it exists in the project root
load_dotenv()

@dataclass
class PathConfig:
    """Configuration for all project directory paths."""
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    code_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent)
    data_raw: Path = None
    data_processed: Path = None
    data_logs: Path = None
    artifacts_dir: Path = None
    models_dir: Path = None
    docs_reports: Path = None
    figures_dir: Path = None

    def __post_init__(self):
        """Initialize derived paths based on project_root."""
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.data_logs = self.project_root / "data" / "logs"
        self.artifacts_dir = self.project_root / "artifacts"
        self.models_dir = self.project_root / "models"
        self.docs_reports = self.project_root / "docs" / "reports"
        self.figures_dir = self.project_root / "figures"

        # Ensure directories exist
        for path in [
            self.data_raw,
            self.data_processed,
            self.data_logs,
            self.artifacts_dir,
            self.models_dir,
            self.docs_reports,
            self.figures_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)

@dataclass
class SimulationConfig:
    """Configuration for MD simulation parameters."""
    cooling_rate: float = 1.0e10  # K/s - default fast cooling
    time_step: float = 1.0e-15    # seconds (1 fs)
    total_steps: int = 100000
    cutoff_distance: float = 10.0  # Angstroms
    temperature_start: float = 3000.0  # K
    temperature_end: float = 100.0   # K
    pressure: float = 1.0  # atm
    
    # CPU time cap per composition (seconds)
    cpu_time_cap: int = 3600  # 1 hour default
    
    # OpenKIM potential identifiers
    kim_potential_oxide: str = "MO_9876543210"  # Placeholder, to be replaced with real KIM ID
    kim_potential_sulfide: str = "MO_1234567890"
    kim_potential_organic: str = "MO_5555555555"

@dataclass
class ModelConfig:
    """Configuration for ML model training parameters."""
    # Random Forest parameters
    rf_n_estimators: int = 100
    rf_max_depth: int = 10
    rf_min_samples_split: int = 2
    rf_min_samples_leaf: int = 1
    
    # Cross-validation
    cv_folds: int = 5
    
    # Hyperparameter grid search limits (to ensure completion within time budget)
    grid_search_max_iter: int = 50
    
    # Performance targets
    target_rmse: float = 15.0  # K
    target_roc_auc: float = 0.7
    
    # Crystallization threshold (K)
    crystallization_threshold: float = 50.0

@dataclass
class DataConfig:
    """Configuration for data processing parameters."""
    # Pilot study sample size
    pilot_sample_size: int = 24
    
    # Stratification by chemical family
    chemical_families: list = field(default_factory=lambda: ["oxide", "sulfide", "organic"])
    
    # Missing data handling
    exclude_missing_labels: bool = True
    
    # File formats
    input_csv: str = "literature_subset.csv"
    output_parquet: str = "merged_dataset.parquet"
    
    # Validation thresholds
    nan_tolerance: float = 0.0  # Fail if any NaN in required columns
    physical_bound_tolerance: float = 1e-6

class Config:
    """Main configuration container."""
    
    def __init__(self):
        self.paths = PathConfig()
        self.simulation = SimulationConfig()
        self.model = ModelConfig()
        self.data = DataConfig()
        
        # Override with environment variables if present
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        # Simulation overrides
        if os.getenv("COOLING_RATE"):
            self.simulation.cooling_rate = float(os.getenv("COOLING_RATE"))
        if os.getenv("TIME_STEP"):
            self.simulation.time_step = float(os.getenv("TIME_STEP"))
        if os.getenv("CPU_TIME_CAP"):
            self.simulation.cpu_time_cap = int(os.getenv("CPU_TIME_CAP"))
        
        # Model overrides
        if os.getenv("RF_N_ESTIMATORS"):
            self.model.rf_n_estimators = int(os.getenv("RF_N_ESTIMATORS"))
        if os.getenv("TARGET_RMSE"):
            self.model.target_rmse = float(os.getenv("TARGET_RMSE"))
        
        # Data overrides
        if os.getenv("PILOT_SAMPLE_SIZE"):
            self.data.pilot_sample_size = int(os.getenv("PILOT_SAMPLE_SIZE"))
        
        # Path overrides
        if os.getenv("PROJECT_ROOT"):
            self.paths.project_root = Path(os.getenv("PROJECT_ROOT"))
            # Re-initialize derived paths
            self.paths.__post_init__()

    def get_simulation_params(self) -> Dict[str, Any]:
        """Get simulation parameters as a dictionary."""
        return {
            "cooling_rate": self.simulation.cooling_rate,
            "time_step": self.simulation.time_step,
            "total_steps": self.simulation.total_steps,
            "cutoff_distance": self.simulation.cutoff_distance,
            "temperature_start": self.simulation.temperature_start,
            "temperature_end": self.simulation.temperature_end,
            "pressure": self.simulation.pressure,
            "cpu_time_cap": self.simulation.cpu_time_cap
        }

    def get_model_params(self) -> Dict[str, Any]:
        """Get model training parameters as a dictionary."""
        return {
            "n_estimators": self.model.rf_n_estimators,
            "max_depth": self.model.rf_max_depth,
            "min_samples_split": self.model.rf_min_samples_split,
            "min_samples_leaf": self.model.rf_min_samples_leaf,
            "cv_folds": self.model.cv_folds,
            "target_rmse": self.model.target_rmse,
            "target_roc_auc": self.model.target_roc_auc
        }

    def get_data_paths(self) -> Dict[str, Path]:
        """Get all data-related paths."""
        return {
            "raw": self.paths.data_raw,
            "processed": self.paths.data_processed,
            "logs": self.paths.data_logs,
            "artifacts": self.paths.artifacts_dir,
            "models": self.paths.models_dir,
            "reports": self.paths.docs_reports,
            "figures": self.paths.figures_dir
        }

    def validate_paths(self) -> bool:
        """Validate that all required directories exist."""
        paths = self.get_data_paths()
        for name, path in paths.items():
            if not path.exists():
                raise FileNotFoundError(f"Required directory missing: {name} -> {path}")
        return True

# Global configuration instance
config = Config()

# Convenience functions for accessing configuration
def get_config() -> Config:
    """Return the global configuration instance."""
    return config

def get_simulation_config() -> SimulationConfig:
    """Return simulation configuration."""
    return config.simulation

def get_model_config() -> ModelConfig:
    """Return model configuration."""
    return config.model

def get_data_config() -> DataConfig:
    """Return data configuration."""
    return config.data

def get_paths() -> PathConfig:
    """Return path configuration."""
    return config.paths