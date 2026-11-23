import logging
import os
import random
import sys
from typing import Dict, Optional, Union
import numpy as np

def fix_seed(seed: int = 42) -> None:
    """Fix random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # If torch is available, fix its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

def setup_logging(name: Optional[Union[str, bool]] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        name: Logger name. If None, returns root logger. 
              If False, returns a logger without configuration.
              If a string, returns a named logger.
        level: Logging level.
    
    Returns:
        Configured logger instance.
    """
    # Handle different call patterns
    if name is False:
        # Return a logger without configuration (for backward compatibility)
        return logging.getLogger()
    
    if name is None:
        # Return root logger with basic config
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        return logging.getLogger()
    
    # Named logger
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(ch)
    
    return logger