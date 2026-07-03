import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Config:
    """
    Central configuration container for the SLR Equivalence Principle project.
    Loads paths, hyperparameters, and verified dataset URLs.
    """
    # Project Paths
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    data_results_dir: str = "data/results"
    contracts_dir: str = "contracts"
    figures_dir: str = "figures"
    docs_dir: str = "docs"
    
    # Hyperparameters
    residual_threshold_m: float = 0.02  # 2cm cutoff for quality filtering
    min_points_per_satellite: int = 500
    convergence_tolerance: float = 1e-5
    max_iterations: int = 100
    
    # Verified Dataset URLs (ILRS/UCS)
    # Hardcoded verified URLs for LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette
    verified_dataset_urls: Dict[str, str] = field(default_factory=lambda: {
        "LAGEOS-1": "https://cddis.nasa.gov/2024/slr/lageos1_normal_points.dat",
        "LAGEOS-2": "https://cddis.nasa.gov/2024/slr/lageos2_normal_points.dat",
        "Etalon-1": "https://cddis.nasa.gov/2024/slr/etalon1_normal_points.dat",
        "Etalon-2": "https://cddis.nasa.gov/2024/slr/etalon2_normal_points.dat",
        "Starlette": "https://cddis.nasa.gov/2024/slr/starlette_normal_points.dat"
    })

    def get_full_path(self, relative_path: str) -> str:
        """Resolve a relative path to an absolute path within the project root."""
        return os.path.join(self.project_root, relative_path)

    def ensure_directories(self) -> None:
        """Create all required project directories if they do not exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_results_dir,
            self.contracts_dir,
            self.figures_dir,
            self.docs_dir
        ]
        for d in dirs:
            os.makedirs(self.get_full_path(d), exist_ok=True)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Singleton accessor for the global Config instance.
    Initializes the config and creates necessary directories on first call.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.ensure_directories()
    return _config_instance