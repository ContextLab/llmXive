"""
Configuration loader for parameter grids and CI constraints.

This module provides a centralized way to manage the experimental parameters
for the smooth number distribution study, including:
- Parameter grids for x, y, and h
- CI constraints (RAM limits, timeouts)
- Output paths and logging settings
"""

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = os.path.join(DEFAULT_PROJECT_ROOT, "data")
DEFAULT_STATE_DIR = os.path.join(DEFAULT_PROJECT_ROOT, "state")
DEFAULT_OUTPUT_CSV = os.path.join(DEFAULT_DATA_DIR, "density_measurements.csv")
DEFAULT_MODEL_FITS_JSON = os.path.join(DEFAULT_DATA_DIR, "model_fits.json")
DEFAULT_PRIMES_CSV = os.path.join(DEFAULT_DATA_DIR, "primes_1e9.csv")

# Default CI constraints
DEFAULT_RAM_LIMIT_GB = 14.0  # ~14 GB disk/RAM budget
DEFAULT_TIMEOUT_SECONDS = 7200  # 120 minutes max runtime
DEFAULT_DICKMAN_TOLERANCE = 1e-6

@dataclass
class CIConstraints:
    """Constraints for CI execution environment."""
    ram_limit_gb: float = DEFAULT_RAM_LIMIT_GB
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    dickman_tolerance: float = DEFAULT_DICKMAN_TOLERANCE
    max_interval_length: int = 10**6  # Safety cap on h

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to a dictionary."""
        return {
            "ram_limit_gb": self.ram_limit_gb,
            "timeout_seconds": self.timeout_seconds,
            "dickman_tolerance": self.dickman_tolerance,
            "max_interval_length": self.max_interval_length,
        }

@dataclass
class GridConfig:
    """Configuration for parameter grids."""
    # Primary Plan-defined grid
    y_values: List[int] = field(default_factory=lambda: [100, 1000, 10000])
    x_values: List[int] = field(default_factory=lambda: [10**6, 10**7, 10**8, 10**9])
    h_values: List[int] = field(default_factory=lambda: [10**3, 10**4, 10**5, 10**6])

    # Secondary Spec-defined grid (for validation)
    h_spec_powers: List[float] = field(default_factory=lambda: [0.1, 0.3, 0.5, 0.7, 0.9])

    def get_plan_grid(self) -> List[Tuple[int, int, int]]:
        """Generate the primary Plan-defined grid (x, y, h)."""
        grid = []
        for x in self.x_values:
            for y in self.y_values:
                for h in self.h_values:
                    # Skip configurations where x + h exceeds our prime limit (10^9)
                    if x + h > 10**9:
                        continue
                    grid.append((x, y, h))
        return grid

    def get_spec_validation_grid(self, base_x: int, base_y: int) -> List[Tuple[int, int, int]]:
        """Generate the secondary Spec-defined grid for a given base (x, y)."""
        grid = []
        for power in self.h_spec_powers:
            h = int(base_x ** power)
            # Ensure h is at least 1 and doesn't exceed base_x
            h = max(1, min(h, base_x))
            if base_x + h <= 10**9:
                grid.append((base_x, base_y, h))
        return grid

    def to_dict(self) -> Dict[str, Any]:
        """Convert grid config to a dictionary."""
        return {
            "y_values": self.y_values,
            "x_values": self.x_values,
            "h_values": self.h_values,
            "h_spec_powers": self.h_spec_powers,
        }

@dataclass
class ProjectConfig:
    """Main configuration container."""
    project_root: str = DEFAULT_PROJECT_ROOT
    data_dir: str = DEFAULT_DATA_DIR
    state_dir: str = DEFAULT_STATE_DIR
    output_csv: str = DEFAULT_OUTPUT_CSV
    model_fits_json: str = DEFAULT_MODEL_FITS_JSON
    primes_csv: str = DEFAULT_PRIMES_CSV
    
    ci: CIConstraints = field(default_factory=CIConstraints)
    grid: GridConfig = field(default_factory=GridConfig)
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def validate(self) -> None:
        """Validate configuration and create necessary directories."""
        # Ensure directories exist
        for directory in [self.data_dir, self.state_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Validate constraints
        if self.ci.ram_limit_gb <= 0:
            raise ValueError("RAM limit must be positive")
        if self.ci.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        # Validate grid
        if not self.grid.y_values or not self.grid.x_values or not self.grid.h_values:
            raise ValueError("Grid values cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "project_root": self.project_root,
            "data_dir": self.data_dir,
            "state_dir": self.state_dir,
            "output_csv": self.output_csv,
            "model_fits_json": self.model_fits_json,
            "primes_csv": self.primes_csv,
            "ci": self.ci.to_dict(),
            "grid": self.grid.to_dict(),
            "log_level": self.log_level,
            "log_file": self.log_file,
        }

def load_config(
    project_root: Optional[str] = None,
    data_dir: Optional[str] = None,
    state_dir: Optional[str] = None,
    output_csv: Optional[str] = None,
    model_fits_json: Optional[str] = None,
    primes_csv: Optional[str] = None,
    ram_limit_gb: Optional[float] = None,
    timeout_seconds: Optional[int] = None,
    dickman_tolerance: Optional[float] = None,
    y_values: Optional[List[int]] = None,
    x_values: Optional[List[int]] = None,
    h_values: Optional[List[int]] = None,
    log_level: Optional[str] = None,
) -> ProjectConfig:
    """
    Load configuration with optional overrides.

    Args:
        project_root: Base directory for the project
        data_dir: Directory for data files
        state_dir: Directory for state files
        output_csv: Path for density measurements output
        model_fits_json: Path for model fits output
        primes_csv: Path for primes input file
        ram_limit_gb: RAM limit in GB
        timeout_seconds: Maximum runtime in seconds
        dickman_tolerance: Tolerance for Dickman function comparisons
        y_values: List of y values for the grid
        x_values: List of x values for the grid
        h_values: List of h values for the grid
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        ProjectConfig instance with applied overrides
    """
    config = ProjectConfig()

    # Apply overrides
    if project_root is not None:
        config.project_root = project_root
        config.data_dir = data_dir or os.path.join(project_root, "data")
        config.state_dir = state_dir or os.path.join(project_root, "state")
    
    if data_dir is not None:
        config.data_dir = data_dir
    if state_dir is not None:
        config.state_dir = state_dir
    if output_csv is not None:
        config.output_csv = output_csv
    if model_fits_json is not None:
        config.model_fits_json = model_fits_json
    if primes_csv is not None:
        config.primes_csv = primes_csv
    
    if log_level is not None:
        config.log_level = log_level

    # Override CI constraints
    if ram_limit_gb is not None:
        config.ci.ram_limit_gb = ram_limit_gb
    if timeout_seconds is not None:
        config.ci.timeout_seconds = timeout_seconds
    if dickman_tolerance is not None:
        config.ci.dickman_tolerance = dickman_tolerance

    # Override grid values
    if y_values is not None:
        config.grid.y_values = y_values
    if x_values is not None:
        config.grid.x_values = x_values
    if h_values is not None:
        config.grid.h_values = h_values

    return config

def main():
    """Demonstrate configuration loading."""
    config = load_config()
    config.validate()
    
    print("Configuration loaded successfully:")
    print(f"  Project Root: {config.project_root}")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  RAM Limit: {config.ci.ram_limit_gb} GB")
    print(f"  Timeout: {config.ci.timeout_seconds} seconds")
    print(f"  Grid (Plan): {len(config.grid.get_plan_grid())} configurations")
    print(f"  Output CSV: {config.output_csv}")

if __name__ == "__main__":
    main()