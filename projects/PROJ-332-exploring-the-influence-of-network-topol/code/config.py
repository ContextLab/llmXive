"""
Configuration module for simulation parameters.

Loads environment variables for simulation parameters (N, p, d, l, seed)
and provides validation and default values.
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Configuration container for nanowire network simulation."""
    
    # Network topology parameters
    N: int  # Number of nodes
    p: float  # Connection probability
    
    # Geometry parameters
    d: float  # Wire diameter in nanometers
    l: float  # Wire length in nanometers
    
    # Random seed for reproducibility
    seed: int
    
    # Material parameter (bulk conductivity in W/(m·K))
    # Can be overridden via environment variable
    material: str = "Si"
    
    # Thermal solver parameters
    lambda_mean_free_path: float = 10.0  # Mean free path in nm
    specularity_parameter: float = 0.5  # Specularity parameter (0-1)
    
    # Simulation control
    timeout_hours: float = 6.0  # Maximum runtime in hours
    
    @classmethod
    def from_env(cls) -> "SimulationConfig":
        """
        Load configuration from environment variables.
        
        Environment variables:
        - SIM_N: Number of nodes (default: 100)
        - SIM_P: Connection probability (default: 0.1)
        - SIM_D: Wire diameter in nm (default: 50)
        - SIM_L: Wire length in nm (default: 500)
        - SIM_SEED: Random seed (default: 42)
        - SIM_MATERIAL: Material name (default: "Si")
        - SIM_LAMBDA: Mean free path in nm (default: 10)
        - SIM_SPECULARITY: Specularity parameter (default: 0.5)
        - SIM_TIMEOUT_HOURS: Timeout in hours (default: 6)
        
        Returns:
            SimulationConfig: Configuration object with loaded values
        """
        def get_int_env(key: str, default: int) -> int:
            value = os.getenv(key)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Environment variable {key} must be an integer, got: {value}")
        
        def get_float_env(key: str, default: float) -> float:
            value = os.getenv(key)
            if value is None:
                return default
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Environment variable {key} must be a float, got: {value}")
        
        def get_str_env(key: str, default: str) -> str:
            value = os.getenv(key)
            return value if value is not None else default
        
        return cls(
            N=get_int_env("SIM_N", 100),
            p=get_float_env("SIM_P", 0.1),
            d=get_float_env("SIM_D", 50.0),
            l=get_float_env("SIM_L", 500.0),
            seed=get_int_env("SIM_SEED", 42),
            material=get_str_env("SIM_MATERIAL", "Si"),
            lambda_mean_free_path=get_float_env("SIM_LAMBDA", 10.0),
            specularity_parameter=get_float_env("SIM_SPECULARITY", 0.5),
            timeout_hours=get_float_env("SIM_TIMEOUT_HOURS", 6.0),
        )
    
    def validate(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValueError: If any parameter is out of valid range
        """
        if self.N < 2:
            raise ValueError(f"Number of nodes N must be >= 2, got {self.N}")
        
        if not (0 <= self.p <= 1):
            raise ValueError(f"Connection probability p must be in [0, 1], got {self.p}")
        
        if self.d <= 0:
            raise ValueError(f"Wire diameter d must be > 0, got {self.d}")
        
        if self.l <= 0:
            raise ValueError(f"Wire length l must be > 0, got {self.l}")
        
        if self.seed < 0:
            raise ValueError(f"Random seed must be >= 0, got {self.seed}")
        
        if self.lambda_mean_free_path <= 0:
            raise ValueError(f"Mean free path must be > 0, got {self.lambda_mean_free_path}")
        
        if not (0 <= self.specularity_parameter <= 1):
            raise ValueError(f"Specularity parameter must be in [0, 1], got {self.specularity_parameter}")
        
        if self.timeout_hours <= 0:
            raise ValueError(f"Timeout must be > 0, got {self.timeout_hours}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            dict: Dictionary representation of configuration
        """
        return {
            "N": self.N,
            "p": self.p,
            "d": self.d,
            "l": self.l,
            "seed": self.seed,
            "material": self.material,
            "lambda_mean_free_path": self.lambda_mean_free_path,
            "specularity_parameter": self.specularity_parameter,
            "timeout_hours": self.timeout_hours,
        }
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"SimulationConfig(N={self.N}, p={self.p}, d={self.d}, "
            f"l={self.l}, seed={self.seed}, material='{self.material}')"
        )


def load_config() -> SimulationConfig:
    """
    Load and validate configuration from environment variables.
    
    Returns:
        SimulationConfig: Validated configuration object
        
    Raises:
        ValueError: If configuration validation fails
    """
    config = SimulationConfig.from_env()
    config.validate()
    return config


def get_simulation_parameters() -> Dict[str, Any]:
    """
    Get simulation parameters as a dictionary.
    
    This is a convenience function that loads config and returns
    the parameter dictionary.
    
    Returns:
        dict: Dictionary of simulation parameters
    """
    config = load_config()
    return config.to_dict()


if __name__ == "__main__":
    # Example usage: print current configuration
    config = load_config()
    print(f"Loaded configuration: {config}")
    print(f"Parameters: {config.to_dict()}")