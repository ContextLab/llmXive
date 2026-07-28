import os
import numpy as np
from typing import Optional, Dict, Any

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Centralized configuration manager for random seeds and system parameters.
    
    This class provides a single source of truth for all simulation parameters,
    ensuring reproducibility and consistent system-wide settings.
    """
    
    # Default system parameters
    DEFAULTS = {
        'seed': 42,
        'min_system_size': 4,
        'max_system_size': 40,
        'entanglement_cut_fraction': 0.5,
        'compression_bits': 16,
        'bootstrap_iterations': 1000,
        'confidence_level': 0.95,
        'numerical_tolerance': 1e-10,
        'max_memory_mb': 7000,
        'data_path': 'data',
        'output_path': 'data/processed',
        'figures_path': 'figures',
        'log_level': 'INFO',
        'log_file': 'logs/pipeline.log',
    }
    
    def __init__(self, seed: Optional[int] = None, **overrides: Dict[str, Any]):
        """
        Initialize configuration with optional seed and parameter overrides.
        
        Args:
            seed: Random seed for reproducibility. Defaults to DEFAULTS['seed'].
            **overrides: Any number of configuration parameter overrides.
        
        Raises:
            ConfigError: If an unknown parameter is provided or if a parameter
                        value is out of valid range.
        """
        # Start with defaults
        self._params = self.DEFAULTS.copy()
        
        # Apply overrides with validation
        for key, value in overrides.items():
            if key not in self._params:
                raise ConfigError(f"Unknown configuration parameter: {key}")
            self._params[key] = value
        
        # Handle seed specifically
        if seed is not None:
            self._params['seed'] = seed
        
        # Validate seed
        if not isinstance(self._params['seed'], int) or self._params['seed'] < 0:
            raise ConfigError(f"Seed must be a non-negative integer, got {self._params['seed']}")
        
        # Initialize random state
        self._random_state = np.random.RandomState(self._params['seed'])
        
        # Set global numpy seed
        np.random.seed(self._params['seed'])
        
        # Validate system size constraints
        if self._params['min_system_size'] < 2:
            raise ConfigError("min_system_size must be at least 2")
        if self._params['max_system_size'] < self._params['min_system_size']:
            raise ConfigError("max_system_size must be >= min_system_size")
        
        # Validate entanglement cut
        if not 0 < self._params['entanglement_cut_fraction'] < 1:
            raise ConfigError("entanglement_cut_fraction must be in (0, 1)")
        
        # Validate compression bits
        if self._params['compression_bits'] not in [8, 16, 32, 64]:
            raise ConfigError("compression_bits must be 8, 16, 32, or 64")
        
        # Validate bootstrap iterations
        if self._params['bootstrap_iterations'] < 100:
            raise ConfigError("bootstrap_iterations must be at least 100")
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for path_key in ['data_path', 'output_path', 'figures_path', 'log_file']:
            if path_key == 'log_file':
                dir_path = os.path.dirname(self._params['log_file'])
            else:
                dir_path = self._params[path_key]
            
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
    
    @property
    def seed(self) -> int:
        """Current random seed."""
        return self._params['seed']
    
    @property
    def random_state(self) -> np.random.RandomState:
        """Returns a numpy RandomState object for reproducible sampling."""
        return self._random_state
    
    @property
    def min_system_size(self) -> int:
        """Minimum system size (number of spins)."""
        return self._params['min_system_size']
    
    @property
    def max_system_size(self) -> int:
        """Maximum system size (number of spins)."""
        return self._params['max_system_size']
    
    @property
    def entanglement_cut_fraction(self) -> float:
        """Fraction of system to use for entanglement cut."""
        return self._params['entanglement_cut_fraction']
    
    @property
    def compression_bits(self) -> int:
        """Number of bits for wavefunction quantization."""
        return self._params['compression_bits']
    
    @property
    def bootstrap_iterations(self) -> int:
        """Number of bootstrap iterations for confidence intervals."""
        return self._params['bootstrap_iterations']
    
    @property
    def confidence_level(self) -> float:
        """Confidence level for intervals (e.g., 0.95 for 95%)."""
        return self._params['confidence_level']
    
    @property
    def numerical_tolerance(self) -> float:
        """Tolerance for numerical stability checks."""
        return self._params['numerical_tolerance']
    
    @property
    def max_memory_mb(self) -> int:
        """Maximum memory usage in MB."""
        return self._params['max_memory_mb']
    
    @property
    def data_path(self) -> str:
        """Path to raw data directory."""
        return self._params['data_path']
    
    @property
    def output_path(self) -> str:
        """Path to processed data output directory."""
        return self._params['output_path']
    
    @property
    def figures_path(self) -> str:
        """Path to figures output directory."""
        return self._params['figures_path']
    
    @property
    def log_level(self) -> str:
        """Logging level."""
        return self._params['log_level']
    
    @property
    def log_file(self) -> str:
        """Path to log file."""
        return self._params['log_file']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration parameter by key.
        
        Args:
            key: Parameter name.
            default: Default value if key not found.
        
        Returns:
            Parameter value or default.
        """
        return self._params.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration parameter.
        
        Args:
            key: Parameter name.
            value: New value.
        
        Raises:
            ConfigError: If key is unknown or value is invalid.
        """
        if key not in self._params:
            raise ConfigError(f"Unknown configuration parameter: {key}")
        
        # Special validation for seed
        if key == 'seed':
            if not isinstance(value, int) or value < 0:
                raise ConfigError(f"Seed must be a non-negative integer, got {value}")
            self._params['seed'] = value
            self._random_state = np.random.RandomState(value)
            np.random.seed(value)
            return
        
        # Special validation for system sizes
        if key == 'min_system_size':
            if value < 2:
                raise ConfigError("min_system_size must be at least 2")
            if value > self._params['max_system_size']:
                raise ConfigError("min_system_size must be <= max_system_size")
        
        if key == 'max_system_size':
            if value < self._params['min_system_size']:
                raise ConfigError("max_system_size must be >= min_system_size")
        
        # Special validation for entanglement cut
        if key == 'entanglement_cut_fraction':
            if not 0 < value < 1:
                raise ConfigError("entanglement_cut_fraction must be in (0, 1)")
        
        # Special validation for compression bits
        if key == 'compression_bits':
            if value not in [8, 16, 32, 64]:
                raise ConfigError("compression_bits must be 8, 16, 32, or 64")
        
        # Special validation for bootstrap iterations
        if key == 'bootstrap_iterations':
            if value < 100:
                raise ConfigError("bootstrap_iterations must be at least 100")
        
        self._params[key] = value
    
    def set_seed(self, seed: int) -> None:
        """
        Update the random seed and re-initialize random states.
        
        Args:
            seed: New random seed.
        
        Raises:
            ConfigError: If seed is invalid.
        """
        self.set('seed', seed)
    
    def get_random_state(self) -> np.random.RandomState:
        """
        Get a fresh RandomState for reproducible sampling.
        
        Returns:
            A numpy RandomState object initialized with the current seed.
        """
        return np.random.RandomState(self._params['seed'])
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as a dictionary.
        
        Returns:
            Dictionary of all configuration parameters.
        """
        return self._params.copy()
    
    def __repr__(self) -> str:
        return f"Config(seed={self._params['seed']}, ...)"
    
    def __str__(self) -> str:
        return (
            f"Configuration (seed={self._params['seed']}):\n"
            f"  System: N in [{self._params['min_system_size']}, {self._params['max_system_size']}]\n"
            f"  Entanglement cut: {self._params['entanglement_cut_fraction']*100:.1f}%\n"
            f"  Quantization: {self._params['compression_bits']}-bit\n"
            f"  Bootstrap: {self._params['bootstrap_iterations']} iterations\n"
            f"  Memory limit: {self._params['max_memory_mb']} MB\n"
            f"  Paths: data='{self._params['data_path']}', output='{self._params['output_path']}'"
        )