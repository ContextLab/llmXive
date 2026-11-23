"""
code/config.py: Configuration loader for parameter grids and CI constraints.
"""
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

@dataclass
class CIConstraints:
    """CI runtime and memory constraints."""
    max_memory_gb: float = 4.0
    max_runtime_seconds: int = 7200  # 120 minutes
    timeout_seconds: int = 300  # 5 minutes for quick tests

@dataclass
class GridConfig:
    """Configuration for parameter grids."""
    y_values: List[int] = field(default_factory=lambda: [100, 1000, 10000])
    x_values: List[int] = field(default_factory=lambda: [10**6, 10**7, 10**8, 10**9])
    # Spec-defined grid: h = x^alpha
    alpha_values: List[float] = field(default_factory=lambda: [0.1, 0.3, 0.5, 0.7, 0.9])
    # Plan-defined grid: fixed h
    fixed_h_values: List[int] = field(default_factory=lambda: [10**3, 10**4, 10**5, 10**6])

@dataclass
class ProjectConfig:
    """Main project configuration."""
    limit: int = 10**9
    segment_size: int = 10**6
    output_dir: str = "data"
    state_dir: str = "state"
    log_dir: str = "logs"
    ci_constraints: CIConstraints = field(default_factory=CIConstraints)
    grid_config: GridConfig = field(default_factory=GridConfig)

def load_config(config_path: Optional[str] = None) -> ProjectConfig:
    """
    Load configuration from file or return defaults.
    Currently returns defaults; can be extended to load from YAML/JSON.
    """
    # For now, return default config
    return ProjectConfig()

def main():
    """CLI entry point for config (for debugging)."""
    import argparse
    parser = argparse.ArgumentParser(description="Load project configuration")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Project Config: {config}")
    print(f"CI Constraints: {config.ci_constraints}")
    print(f"Grid Config: {config.grid_config}")

if __name__ == "__main__":
    main()
