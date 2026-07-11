"""
Base abstract class for HeuristicSelector.

This module defines the abstract interface that all heuristic
implementations must follow for attention block selection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

class HeuristicSelector(ABC):
    """
    Abstract base class for attention block selection heuristics.
    
    All heuristic implementations must inherit from this class
    and implement the core selection logic.
    
    Attributes:
        name: The name of the heuristic implementation.
        config: Configuration dictionary for the heuristic.
        logger: Optional logger instance.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the heuristic selector.
        
        Args:
            name: Name of the heuristic.
            config: Optional configuration dictionary.
        """
        self.name = name
        self.config = config or {}
        self.logger = None
        
    def set_logger(self, logger):
        """Set the logger for this heuristic."""
        self.logger = logger
        
    @abstractmethod
    def compute_scores(
        self, 
        attention_logits: np.ndarray, 
        **kwargs
    ) -> np.ndarray:
        """
        Compute selection scores for attention blocks.
        
        This is the core abstract method that all heuristics must implement.
        The scores determine which blocks should be kept or pruned.
        
        Args:
            attention_logits: Attention logits tensor of shape 
                              (batch_size, num_heads, seq_len, seq_len) or 
                              (num_heads, seq_len, seq_len) for a single batch.
            **kwargs: Additional keyword arguments specific to the heuristic.
        
        Returns:
            numpy.ndarray: Selection scores of shape (batch_size, num_blocks) or 
                           (num_blocks) for a single batch. Higher scores indicate
                           blocks that should be kept.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement compute_scores")
    
    @abstractmethod
    def select_blocks(
        self, 
        scores: np.ndarray, 
        k: int, 
        **kwargs
    ) -> np.ndarray:
        """
        Select the top-k blocks based on computed scores.
        
        Args:
            scores: Selection scores from compute_scores().
            k: Number of blocks to select.
            **kwargs: Additional keyword arguments.
        
        Returns:
            numpy.ndarray: Boolean mask or indices of selected blocks.
        
        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement select_blocks")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration of the heuristic.
        
        Returns:
            Dictionary of configuration parameters.
        """
        return self.config.copy()
    
    def update_config(self, **kwargs):
        """
        Update the configuration of the heuristic.
        
        Args:
            **kwargs: Configuration parameters to update.
        """
        self.config.update(kwargs)
    
    def validate_input(self, attention_logits: np.ndarray) -> bool:
        """
        Validate that the input attention logits have the expected shape.
        
        Args:
            attention_logits: Input attention logits.
        
        Returns:
            bool: True if input is valid, False otherwise.
        """
        if attention_logits is None:
            return False
        if not isinstance(attention_logits, np.ndarray):
            return False
        if attention_logits.ndim < 3:
            return False
        return True
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, config={self.config})"
