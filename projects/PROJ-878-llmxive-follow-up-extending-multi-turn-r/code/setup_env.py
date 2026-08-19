"""
Environment configuration script for llmXive project.
Sets up random seeds and model paths via environment variables.
"""
import os
import random
import numpy as np
import torch

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_MODEL_PATH = "microsoft/phi-2"  # Common CPU-feasible model
DEFAULT_DEVICE = "cpu"
DEFAULT_MAX_TURNS = 50
DEFAULT_EXTENDED_MAX_TURNS = 1000
DEFAULT_DATA_PATH_RAW = "data/raw"
DEFAULT_DATA_PATH_PROCESSED = "data/processed"
DEFAULT_RESULTS_PATH = "results"

def configure_environment(seed: int = None, model_path: str = None, device: str = None):
    """
    Configure environment variables for reproducibility and model paths.
    
    Args:
        seed: Random seed for reproducibility (default: 42)
        model_path: Path to the pre-trained model (default: "microsoft/phi-2")
        device: Device to run on ("cpu" or "cuda") (default: "cpu")
    """
    # Set seed if provided
    if seed is not None:
        os.environ["LLMXIVE_SEED"] = str(seed)
    elif "LLMXIVE_SEED" not in os.environ:
        os.environ["LLMXIVE_SEED"] = str(DEFAULT_SEED)
    
    # Set model path if provided
    if model_path is not None:
        os.environ["LLMXIVE_MODEL_PATH"] = model_path
    elif "LLMXIVE_MODEL_PATH" not in os.environ:
        os.environ["LLMXIVE_MODEL_PATH"] = DEFAULT_MODEL_PATH
    
    # Set device if provided
    if device is not None:
        os.environ["LLMXIVE_DEVICE"] = device
    elif "LLMXIVE_DEVICE" not in os.environ:
        os.environ["LLMXIVE_DEVICE"] = DEFAULT_DEVICE
    
    # Set turn limits
    if "LLMXIVE_MAX_TURNS" not in os.environ:
        os.environ["LLMXIVE_MAX_TURNS"] = str(DEFAULT_MAX_TURNS)
    if "LLMXIVE_EXTENDED_MAX_TURNS" not in os.environ:
        os.environ["LLMXIVE_EXTENDED_MAX_TURNS"] = str(DEFAULT_EXTENDED_MAX_TURNS)
    
    # Set data paths
    if "LLMXIVE_DATA_RAW" not in os.environ:
        os.environ["LLMXIVE_DATA_RAW"] = DEFAULT_DATA_PATH_RAW
    if "LLMXIVE_DATA_PROCESSED" not in os.environ:
        os.environ["LLMXIVE_DATA_PROCESSED"] = DEFAULT_DATA_PATH_PROCESSED
    if "LLMXIVE_RESULTS_PATH" not in os.environ:
        os.environ["LLMXIVE_RESULTS_PATH"] = DEFAULT_RESULTS_PATH

    return get_environment_config()

def get_environment_config():
    """
    Retrieve current environment configuration.
    
    Returns:
        dict: Dictionary containing all configuration values
    """
    return {
        "seed": int(os.environ.get("LLMXIVE_SEED", DEFAULT_SEED)),
        "model_path": os.environ.get("LLMXIVE_MODEL_PATH", DEFAULT_MODEL_PATH),
        "device": os.environ.get("LLMXIVE_DEVICE", DEFAULT_DEVICE),
        "max_turns": int(os.environ.get("LLMXIVE_MAX_TURNS", DEFAULT_MAX_TURNS)),
        "extended_max_turns": int(os.environ.get("LLMXIVE_EXTENDED_MAX_TURNS", DEFAULT_EXTENDED_MAX_TURNS)),
        "data_raw": os.environ.get("LLMXIVE_DATA_RAW", DEFAULT_DATA_PATH_RAW),
        "data_processed": os.environ.get("LLMXIVE_DATA_PROCESSED", DEFAULT_DATA_PATH_PROCESSED),
        "results_path": os.environ.get("LLMXIVE_RESULTS_PATH", DEFAULT_RESULTS_PATH),
    }

def apply_seed(seed: int = None):
    """
    Apply random seed to all relevant libraries for reproducibility.
    
    Args:
        seed: Random seed (uses environment variable if not provided)
    """
    if seed is None:
        seed = int(os.environ.get("LLMXIVE_SEED", DEFAULT_SEED))
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def main():
    """Main entry point for environment setup."""
    print("Configuring llmXive environment...")
    
    # Configure with defaults
    config = configure_environment()
    
    print(f"Seed: {config['seed']}")
    print(f"Model Path: {config['model_path']}")
    print(f"Device: {config['device']}")
    print(f"Max Turns: {config['max_turns']}")
    print(f"Extended Max Turns: {config['extended_max_turns']}")
    print(f"Data Raw Path: {config['data_raw']}")
    print(f"Data Processed Path: {config['data_processed']}")
    print(f"Results Path: {config['results_path']}")
    
    # Apply seed
    apply_seed(config['seed'])
    print("Random seeds applied successfully.")
    
    return config

if __name__ == "__main__":
    main()
