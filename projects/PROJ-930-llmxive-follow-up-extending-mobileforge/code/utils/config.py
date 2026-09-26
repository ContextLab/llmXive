import os
import random
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import json
import logging

# Configure logging for config operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG_PATH = DEFAULT_PROJECT_ROOT / "code" / ".env.json"

# Constitution Principle I: Centralized configuration management
# All paths and seeds must be loaded from environment or config file

@dataclass
class ProjectConfig:
    """
    Centralized configuration manager for the llmXive project.
    
    Handles:
    - Dataset paths (raw, processed, evaluation)
    - Random seeds for reproducibility
    - Model paths and hyperparameters
    - Execution constraints (CPU-only, timeouts)
    
    Constitution Principle I compliance:
    - All critical paths must be explicitly configured
    - Random seeds must be set for reproducibility
    - Configuration must be validated before use
    """
    # Paths
    project_root: Path
    data_raw_dir: Path
    data_processed_dir: Path
    data_evaluation_dir: Path
    models_dir: Path
    state_dir: Path
    results_dir: Path
    
    # Random seeds
    random_seed: int
    torch_seed: int
    numpy_seed: int
    
    # Execution constraints
    cpu_only: bool = True
    max_execution_time: int = 21600  # 6 hours in seconds
    
    # Dataset parameters
    min_triples: int = 5000
    power_alpha: float = 0.05
    power_target: float = 0.80
    
    # Model parameters
    model_name: str = "t5-small"
    max_seq_length: int = 512
    batch_size: int = 8
    learning_rate: float = 3e-5
    epochs: int = 10
    
    # Evaluation parameters
    n_tasks_default: int = 100
    use_streaming: bool = True
    
    @classmethod
    def from_env(cls, project_root: Optional[Path] = None) -> 'ProjectConfig':
        """
        Initialize configuration from environment variables.
        
        Constitution Principle I: All critical configuration must be
        explicitly set via environment variables or config file.
        
        Args:
            project_root: Optional override for project root path.
            
        Returns:
            ProjectConfig instance with validated values.
            
        Raises:
            ValueError: If required environment variables are missing.
        """
        root = project_root or DEFAULT_PROJECT_ROOT
        
        # Required paths
        data_raw = os.getenv('LLMXIVE_DATA_RAW', str(root / 'code' / 'data' / 'raw'))
        data_processed = os.getenv('LLMXIVE_DATA_PROCESSED', str(root / 'code' / 'data' / 'processed'))
        data_eval = os.getenv('LLMXIVE_DATA_EVALUATION', str(root / 'code' / 'data' / 'evaluation'))
        models_dir = os.getenv('LLMXIVE_MODELS_DIR', str(root / 'code' / 'models'))
        state_dir = os.getenv('LLMXIVE_STATE_DIR', str(root / 'state'))
        results_dir = os.getenv('LLMXIVE_RESULTS_DIR', str(root / 'code' / 'data' / 'results'))
        
        # Required seeds
        seed_str = os.getenv('LLMXIVE_RANDOM_SEED')
        if seed_str is None:
            raise ValueError("Constitution Principle I: LLMXIVE_RANDOM_SEED environment variable must be set")
        try:
            seed = int(seed_str)
        except ValueError:
            raise ValueError(f"LLMXIVE_RANDOM_SEED must be an integer, got: {seed_str}")
        
        # Optional parameters with defaults
        cpu_only_str = os.getenv('LLMXIVE_CPU_ONLY', 'true')
        cpu_only = cpu_only_str.lower() in ('true', '1', 'yes')
        
        max_time_str = os.getenv('LLMXIVE_MAX_EXECUTION_TIME', '21600')
        max_time = int(max_time_str)
        
        min_triples_str = os.getenv('LLMXIVE_MIN_TRIPLES', '5000')
        min_triples = int(min_triples_str)
        
        power_alpha_str = os.getenv('LLMXIVE_POWER_ALPHA', '0.05')
        power_alpha = float(power_alpha_str)
        
        power_target_str = os.getenv('LLMXIVE_POWER_TARGET', '0.80')
        power_target = float(power_target_str)
        
        model_name = os.getenv('LLMXIVE_MODEL_NAME', 't5-small')
        max_seq_str = os.getenv('LLMXIVE_MAX_SEQ_LENGTH', '512')
        max_seq_length = int(max_seq_str)
        batch_size_str = os.getenv('LLMXIVE_BATCH_SIZE', '8')
        batch_size = int(batch_size_str)
        lr_str = os.getenv('LLMXIVE_LEARNING_RATE', '3e-5')
        learning_rate = float(lr_str)
        epochs_str = os.getenv('LLMXIVE_EPOCHS', '10')
        epochs = int(epochs_str)
        
        n_tasks_str = os.getenv('LLMXIVE_N_TASKS', '100')
        n_tasks_default = int(n_tasks_str)
        
        streaming_str = os.getenv('LLMXIVE_USE_STREAMING', 'true')
        use_streaming = streaming_str.lower() in ('true', '1', 'yes')
        
        # Validate paths exist or create them
        paths = {
            'data_raw_dir': Path(data_raw),
            'data_processed_dir': Path(data_processed),
            'data_evaluation_dir': Path(data_eval),
            'models_dir': Path(models_dir),
            'state_dir': Path(state_dir),
            'results_dir': Path(results_dir),
        }
        
        for name, path in paths.items():
            if not path.exists():
                logger.info(f"Creating directory: {path}")
                path.mkdir(parents=True, exist_ok=True)
        
        return cls(
            project_root=root,
            data_raw_dir=paths['data_raw_dir'],
            data_processed_dir=paths['data_processed_dir'],
            data_evaluation_dir=paths['data_evaluation_dir'],
            models_dir=paths['models_dir'],
            state_dir=paths['state_dir'],
            results_dir=paths['results_dir'],
            random_seed=seed,
            torch_seed=seed,
            numpy_seed=seed,
            cpu_only=cpu_only,
            max_execution_time=max_time,
            min_triples=min_triples,
            power_alpha=power_alpha,
            power_target=power_target,
            model_name=model_name,
            max_seq_length=max_seq_length,
            batch_size=batch_size,
            learning_rate=learning_rate,
            epochs=epochs,
            n_tasks_default=n_tasks_default,
            use_streaming=use_streaming,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'project_root': str(self.project_root),
            'data_raw_dir': str(self.data_raw_dir),
            'data_processed_dir': str(self.data_processed_dir),
            'data_evaluation_dir': str(self.data_evaluation_dir),
            'models_dir': str(self.models_dir),
            'state_dir': str(self.state_dir),
            'results_dir': str(self.results_dir),
            'random_seed': self.random_seed,
            'torch_seed': self.torch_seed,
            'numpy_seed': self.numpy_seed,
            'cpu_only': self.cpu_only,
            'max_execution_time': self.max_execution_time,
            'min_triples': self.min_triples,
            'power_alpha': self.power_alpha,
            'power_target': self.power_target,
            'model_name': self.model_name,
            'max_seq_length': self.max_seq_length,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'epochs': self.epochs,
            'n_tasks_default': self.n_tasks_default,
            'use_streaming': self.use_streaming,
        }
    
    def save_to_file(self, path: Optional[Path] = None) -> None:
        """Save configuration to JSON file."""
        save_path = path or DEFAULT_CONFIG_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to: {save_path}")
    
    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> 'ProjectConfig':
        """Load configuration from JSON file."""
        load_path = path or DEFAULT_CONFIG_PATH
        if not load_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {load_path}")
        
        with open(load_path, 'r') as f:
            config_dict = json.load(f)
        
        # Convert string paths back to Path objects
        for key in ['project_root', 'data_raw_dir', 'data_processed_dir', 
                    'data_evaluation_dir', 'models_dir', 'state_dir', 'results_dir']:
            if key in config_dict:
                config_dict[key] = Path(config_dict[key])
        
        return cls(**config_dict)
    
    def apply_seeds(self) -> None:
        """Apply random seeds for reproducibility."""
        logger.info(f"Applying random seeds: {self.random_seed}")
        random.seed(self.random_seed)
        
        try:
            import numpy as np
            np.random.seed(self.numpy_seed)
        except ImportError:
            logger.warning("numpy not available, skipping numpy seed")
        
        try:
            import torch
            torch.manual_seed(self.torch_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.torch_seed)
            else:
                logger.info("CUDA not available, skipping CUDA seed")
        except ImportError:
            logger.warning("torch not available, skipping torch seed")
        
        # Verify CPU-only constraint
        if self.cpu_only:
            try:
                import torch
                if torch.cuda.is_available():
                    raise RuntimeError(
                        "Constitution Principle VI: CUDA detected but cpu_only=True. "
                        "Set LLMXIVE_CPU_ONLY=false or use a CPU-only environment."
                    )
            except ImportError:
                pass  # torch not installed, can't check

# Global configuration instance (singleton pattern)
_config_instance: Optional[ProjectConfig] = None

def get_config(project_root: Optional[Path] = None) -> ProjectConfig:
    """
    Get the global configuration instance.
    
    Constitution Principle I: All code should use this function to
    access configuration, ensuring a single source of truth.
    
    Args:
        project_root: Optional override for project root path.
        
    Returns:
        ProjectConfig instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig.from_env(project_root)
    return _config_instance

def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None

def validate_config(config: ProjectConfig) -> bool:
    """
    Validate configuration values.
    
    Constitution Principle I: Configuration must be validated before use.
    
    Args:
        config: ProjectConfig instance to validate.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    errors = []
    
    # Validate paths
    required_dirs = [
        config.data_raw_dir,
        config.data_processed_dir,
        config.data_evaluation_dir,
        config.models_dir,
        config.state_dir,
        config.results_dir,
    ]
    
    for path in required_dirs:
        if not path.exists():
            errors.append(f"Directory does not exist: {path}")
    
    # Validate seeds
    if not (0 <= config.random_seed <= 2**32 - 1):
        errors.append(f"Random seed out of range: {config.random_seed}")
    
    # Validate power analysis parameters
    if not (0 < config.power_alpha < 1):
        errors.append(f"Invalid alpha: {config.power_alpha}")
    if not (0 < config.power_target < 1):
        errors.append(f"Invalid power target: {config.power_target}")
    
    # Validate model parameters
    if config.max_seq_length <= 0:
        errors.append(f"Invalid max_seq_length: {config.max_seq_length}")
    if config.batch_size <= 0:
        errors.append(f"Invalid batch_size: {config.batch_size}")
    if config.learning_rate <= 0:
        errors.append(f"Invalid learning_rate: {config.learning_rate}")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
    
    return True

def set_environment_variables(config: ProjectConfig) -> None:
    """
    Set environment variables from configuration.
    
    Useful for subprocesses or external tools that read env vars.
    Constitution Principle I: Ensure consistency across all components.
    """
    os.environ['LLMXIVE_DATA_RAW'] = str(config.data_raw_dir)
    os.environ['LLMXIVE_DATA_PROCESSED'] = str(config.data_processed_dir)
    os.environ['LLMXIVE_DATA_EVALUATION'] = str(config.data_evaluation_dir)
    os.environ['LLMXIVE_MODELS_DIR'] = str(config.models_dir)
    os.environ['LLMXIVE_STATE_DIR'] = str(config.state_dir)
    os.environ['LLMXIVE_RESULTS_DIR'] = str(config.results_dir)
    os.environ['LLMXIVE_RANDOM_SEED'] = str(config.random_seed)
    os.environ['LLMXIVE_CPU_ONLY'] = 'true' if config.cpu_only else 'false'
    os.environ['LLMXIVE_MIN_TRIPLES'] = str(config.min_triples)
    os.environ['LLMXIVE_POWER_ALPHA'] = str(config.power_alpha)
    os.environ['LLMXIVE_POWER_TARGET'] = str(config.power_target)
    os.environ['LLMXIVE_MODEL_NAME'] = config.model_name
    os.environ['LLMXIVE_MAX_SEQ_LENGTH'] = str(config.max_seq_length)
    os.environ['LLMXIVE_BATCH_SIZE'] = str(config.batch_size)
    os.environ['LLMXIVE_LEARNING_RATE'] = str(config.learning_rate)
    os.environ['LLMXIVE_EPOCHS'] = str(config.epochs)
    os.environ['LLMXIVE_N_TASKS'] = str(config.n_tasks_default)
    os.environ['LLMXIVE_USE_STREAMING'] = 'true' if config.use_streaming else 'false'
    logger.info("Environment variables set from configuration")

def main():
    """
    Main entry point for configuration management CLI.
    
    Usage:
        python -m utils.config --init           # Create default config file
        python -m utils.config --validate      # Validate current config
        python -m utils.config --show          # Display current config
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration management for llmXive")
    parser.add_argument('--init', action='store_true', help='Initialize config file')
    parser.add_argument('--validate', action='store_true', help='Validate configuration')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--project-root', type=Path, help='Project root path')
    
    args = parser.parse_args()
    
    try:
        config = get_config(args.project_root)
        
        if args.init:
            config.save_to_file()
            print(f"Configuration initialized at: {DEFAULT_CONFIG_PATH}")
        
        if args.validate:
            validate_config(config)
            print("Configuration is valid.")
        
        if args.show:
            print(json.dumps(config.to_dict(), indent=2))
        
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
