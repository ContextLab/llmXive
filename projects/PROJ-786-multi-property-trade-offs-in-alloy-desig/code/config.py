"""
Configuration management for llmXive alloy design project.
Handles CLI argument parsing and .env file loading for environment variables.
"""
import os
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Default configuration values
DEFAULTS = {
    "variance_threshold": 0.1,
    "seed": 42,
    "log_level": "INFO",
    "output_dir": "data/processed",
}

def load_environment(project_root: Path = None) -> dict:
    """
    Load environment variables from .env file if it exists.
    
    Args:
        project_root: Path to project root directory. Defaults to current working directory.
        
    Returns:
        Dictionary of loaded environment variables.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    env_file = project_root / ".env"
    
    if load_dotenv is not None and env_file.exists():
        load_dotenv(env_file)
    elif env_file.exists():
        # Fallback: manually parse .env if python-dotenv not installed
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
    
    return {
        "variance_threshold": os.getenv("VARIANCE_THRESHOLD"),
        "seed": os.getenv("SEED"),
        "log_level": os.getenv("LOG_LEVEL"),
    }

def parse_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the project.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Alloy Design Optimization Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Configuration arguments
    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=None,
        help="Variance threshold for filtering features (FR-006). "
             "Overrides .env and default values."
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility."
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Logging level."
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for processed data."
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to project root directory."
    )
    
    return parser.parse_args()

def get_config(cli_args: argparse.Namespace = None, project_root: Path = None) -> dict:
    """
    Get merged configuration from defaults, .env file, and CLI arguments.
    
    Priority: CLI > .env > defaults
    
    Args:
        cli_args: Parsed CLI arguments. If None, parse from sys.argv.
        project_root: Path to project root. If None, use current working directory.
        
    Returns:
        Dictionary of configuration values.
    """
    if cli_args is None:
        cli_args = parse_cli_args()
        
    if project_root is None:
        project_root = cli_args.project_root or Path.cwd()
    
    # Load from .env
    env_config = load_environment(project_root)
    
    # Start with defaults
    config = DEFAULTS.copy()
    
    # Override with .env values (if present)
    for key, value in env_config.items():
        if value is not None:
            if key == "variance_threshold":
                config[key] = float(value)
            elif key == "seed":
                config[key] = int(value)
            else:
                config[key] = value
    
    # Override with CLI arguments (if present)
    if cli_args.variance_threshold is not None:
        config["variance_threshold"] = cli_args.variance_threshold
    if cli_args.seed is not None:
        config["seed"] = cli_args.seed
    if cli_args.log_level is not None:
        config["log_level"] = cli_args.log_level
    if cli_args.output_dir is not None:
        config["output_dir"] = cli_args.output_dir
    
    # Ensure variance_threshold is float
    config["variance_threshold"] = float(config["variance_threshold"])
    
    return config

def verify_config(config: dict) -> bool:
    """
    Verify that configuration values are valid.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        True if configuration is valid, False otherwise.
    """
    # Check variance_threshold is positive
    if config["variance_threshold"] <= 0:
        raise ValueError(f"variance_threshold must be positive, got {config['variance_threshold']}")
    
    # Check seed is non-negative
    if config["seed"] < 0:
        raise ValueError(f"seed must be non-negative, got {config['seed']}")
    
    # Check log_level is valid
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config["log_level"] not in valid_levels:
        raise ValueError(f"log_level must be one of {valid_levels}, got {config['log_level']}")
    
    return True

if __name__ == "__main__":
    # Demo: print configuration
    args = parse_cli_args()
    config = get_config(args)
    print("Configuration loaded:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    verify_config(config)
    print("Configuration verified successfully.")
