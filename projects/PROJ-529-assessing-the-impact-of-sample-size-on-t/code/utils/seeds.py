"""Deterministic random seed management and logging utility."""

import os
import random
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class SeedManager:
    """
    Manages random seeds for reproducible experiments.
    
    Logs k, seed, and estimator_type per iteration as required.
    """
    
    def __init__(self, base_seed: Optional[int] = None, log_file: Optional[str] = None):
        """
        Initialize the SeedManager.
        
        Args:
            base_seed: Base seed for reproducibility. If None, uses system time.
            log_file: Optional path to log file for seed tracking.
        """
        self.base_seed = base_seed if base_seed is not None else int(datetime.now().timestamp())
        self.log_file = log_file
        self.current_seed = self.base_seed
        self.seed_history: List[Dict[str, Any]] = []
        
        # Set initial seeds
        random.seed(self.base_seed)
        np.random.seed(self.base_seed)
        
        if self.log_file:
            logger.info(f"SeedManager initialized with base seed {self.base_seed}, logging to {self.log_file}")
        else:
            logger.info(f"SeedManager initialized with base seed {self.base_seed}")
            
    def get_next_seed(self) -> int:
        """
        Get the next seed in the sequence.
        
        Returns:
            Next seed value.
        """
        seed = self.current_seed
        self.current_seed += 1
        return seed
        
    def log_iteration(self, k: int, seed: int, estimator_type: str, success: bool = True):
        """
        Log an iteration with k, seed, and estimator_type.
        
        Args:
            k: Number of studies in the subsample.
            seed: Random seed used.
            estimator_type: Type of estimator (e.g., 'REML', 'DL').
            success: Whether the iteration was successful.
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'k': k,
            'seed': seed,
            'estimator_type': estimator_type,
            'success': success
        }
        
        self.seed_history.append(log_entry)
        
        log_msg = f"Iteration: k={k}, seed={seed}, estimator={estimator_type}, success={success}"
        logger.info(log_msg)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{log_entry['timestamp']},{log_entry['k']},{log_entry['seed']},{log_entry['estimator_type']},{log_entry['success']}\n")
            except IOError as e:
                logger.error(f"Failed to write to log file: {e}")
                
    def reset(self, new_base_seed: Optional[int] = None):
        """
        Reset the seed manager with a new base seed.
        
        Args:
            new_base_seed: New base seed. If None, uses current time.
        """
        self.base_seed = new_base_seed if new_base_seed is not None else int(datetime.now().timestamp())
        self.current_seed = self.base_seed
        random.seed(self.base_seed)
        np.random.seed(self.base_seed)
        logger.info(f"SeedManager reset with base seed {self.base_seed}")