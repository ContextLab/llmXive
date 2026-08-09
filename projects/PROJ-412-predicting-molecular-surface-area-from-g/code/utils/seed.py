import os
import random
import hashlib
from typing import Optional, Dict, Any, Callable, List
import numpy as np
from .logging import get_logger

logger = get_logger(__name__)

# Default seed as per project convention
DEFAULT_SEED = 42

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).
    
    This function ensures deterministic behavior in:
    - Python's built-in random module
    - NumPy's random number generator
    - PyTorch's CPU and GPU operations (if installed)
    - CuDNN (if available) for deterministic behavior
    
    Args:
        seed: Random seed value. Defaults to 42.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")
    
    logger.debug(f"Setting global random seed to {seed}")
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set PyTorch seeds if available
    try:
        import torch
        torch.manual_seed(seed)
        
        # Set seeds for GPU if available
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            
        logger.debug("PyTorch seeds set successfully")
    except ImportError:
        logger.debug("PyTorch not available, skipping PyTorch seed setting")
    except Exception as e:
        logger.warning(f"Failed to set PyTorch seeds: {e}")

def get_seed_from_env(env_var: str = "RANDOM_SEED", default: int = DEFAULT_SEED) -> int:
    """
    Get random seed from environment variable.
    
    Args:
        env_var: Environment variable name to read from.
        default: Default seed if env var not set or invalid.
        
    Returns:
        Seed value as integer.
    """
    seed_str = os.getenv(env_var)
    if seed_str is None:
        logger.debug(f"Environment variable {env_var} not set, using default seed {default}")
        return default
    
    try:
        seed = int(seed_str)
        if seed < 0:
            logger.warning(f"Negative seed {seed} provided, using default {default}")
            return default
        logger.debug(f"Loaded seed {seed} from environment variable {env_var}")
        return seed
    except ValueError:
        logger.warning(f"Invalid seed value '{seed_str}' in {env_var}, using default {default}")
        return default

def verify_seed_reproducibility(seed: int, test_func: Callable[[], Any], iterations: int = 3) -> bool:
    """
    Verify that a function produces reproducible results with a fixed seed.
    
    This utility runs the provided function multiple times with the same seed
    and checks if all results are identical. This is useful for validating
    that a pipeline or model training process is truly deterministic.
    
    Args:
        seed: Seed to test.
        test_func: Function to test (must be deterministic and return comparable results).
        iterations: Number of times to run the test.
        
    Returns:
        True if all runs produce identical results, False otherwise.
        
    Raises:
        ValueError: If iterations is less than 2.
    """
    if iterations < 2:
        raise ValueError("iterations must be at least 2 to verify reproducibility")
    
    logger.info(f"Verifying reproducibility with seed {seed} over {iterations} iterations")
    
    results: List[Any] = []
    for i in range(iterations):
        set_seed(seed)
        try:
            result = test_func()
            results.append(result)
            logger.debug(f"Iteration {i+1} completed")
        except Exception as e:
            logger.error(f"Iteration {i+1} failed with error: {e}")
            return False
    
    # Compare all results to the first one
    first_result = results[0]
    for i, result in enumerate(results[1:], start=2):
        if result != first_result:
            logger.error(f"Iteration {i} produced different result: {result} != {first_result}")
            return False
    
    logger.info(f"Reproducibility verified: all {iterations} iterations produced identical results")
    return True

def generate_seed_hash(seed: int) -> str:
    """
    Generate a hash for a seed value for logging and tracking purposes.
    
    This provides a compact, unique identifier for a seed that can be used
    in experiment tracking, result file naming, or log correlation.
    
    Args:
        seed: Seed value to hash.
        
    Returns:
        Hex string hash (first 16 characters of SHA-256).
    """
    hash_obj = hashlib.sha256(str(seed).encode())
    return hash_obj.hexdigest()[:16]

class seed_context:
    """
    Context manager to temporarily set a random seed and restore state afterwards.
    
    This is useful for testing or running specific code blocks with a known
    random state without affecting the global seed setting.
    
    Example:
        with seed_context(123):
            # Code here uses seed 123
            result = some_function()
        # Global state restored
    """
    def __init__(self, seed: int):
        if not isinstance(seed, int) or seed < 0:
            raise ValueError(f"Seed must be a non-negative integer, got {seed}")
        self.seed = seed
        self.original_state: Optional[Dict[str, Any]] = None
    
    def __enter__(self):
        # Save current states
        self.original_state = {
            'random': random.getstate(),
            'numpy': np.random.get_state()
        }
        
        # Set new seed
        set_seed(self.seed)
        
        # Save PyTorch state if available
        try:
            import torch
            self.original_state['torch'] = torch.get_rng_state()
            if torch.cuda.is_available():
                self.original_state['torch_cuda'] = torch.cuda.get_rng_state_all()
        except ImportError:
            self.original_state['torch'] = None
            self.original_state['torch_cuda'] = None
        
        logger.debug(f"Entered seed context with seed {self.seed}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_state:
            # Restore states
            random.setstate(self.original_state['random'])
            np.random.set_state(self.original_state['numpy'])
            
            # Restore PyTorch state if available
            if self.original_state['torch'] is not None:
                try:
                    import torch
                    torch.set_rng_state(self.original_state['torch'])
                    if self.original_state['torch_cuda'] is not None and torch.cuda.is_available():
                        torch.cuda.set_rng_state_all(self.original_state['torch_cuda'])
                except Exception as e:
                    logger.warning(f"Failed to restore PyTorch state: {e}")
            
            logger.debug(f"Exited seed context, state restored")
        
        # Don't suppress exceptions
        return False

def get_seed_info() -> Dict[str, Any]:
    """
    Get current seed information for logging and reporting.
    
    Returns:
        Dictionary containing seed values and reproducibility settings.
    """
    try:
        import torch
        has_torch = True
        torch_seed = torch.initial_seed() if torch.initial_seed() is not None else None
        cuda_available = torch.cuda.is_available()
    except ImportError:
        has_torch = False
        torch_seed = None
        cuda_available = False
    
    return {
        'python_seed': random.getrandbits(32),  # Current state indicator
        'numpy_seed': np.random.get_state()[1][0],  # Current state indicator
        'torch_seed': torch_seed,
        'has_torch': has_torch,
        'cuda_available': cuda_available,
        'environment_seed': os.getenv('RANDOM_SEED', 'not set')
    }