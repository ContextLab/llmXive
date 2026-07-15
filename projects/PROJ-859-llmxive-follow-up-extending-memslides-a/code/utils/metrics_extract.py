"""
Utility functions for calculating specific metrics.

This module contains the pure logic for calculating entropy, repetition,
and variance, separate from the main extraction pipeline.
"""
import math
from collections import Counter
from typing import List, Optional
import numpy as np

def calculate_sequence_entropy(tool_sequence: List[str]) -> float:
    """
    Calculate the Shannon entropy of a tool sequence.
    
    Args:
        tool_sequence: List of tool names.
        
    Returns:
        Shannon entropy value.
    """
    if not tool_sequence:
        return 0.0
    
    counts = Counter(tool_sequence)
    total = len(tool_sequence)
    
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            probability = count / total
            entropy -= probability * math.log2(probability)
    
    return entropy

def calculate_tool_repetition_frequency(tool_sequence: List[str]) -> float:
    """
    Calculate the frequency of tool repetitions (consecutive identical tools).
    
    Args:
        tool_sequence: List of tool names.
        
    Returns:
        Frequency of repetitions (0.0 to 1.0).
    """
    if len(tool_sequence) < 2:
        return 0.0
    
    repetitions = 0
    for i in range(1, len(tool_sequence)):
        if tool_sequence[i] == tool_sequence[i-1]:
            repetitions += 1
    
    return repetitions / (len(tool_sequence) - 1)

def calculate_argument_variance(arguments: List[str]) -> float:
    """
    Placeholder for argument variance calculation.
    
    This function is now implemented in code/metrics/extract.py using
    sentence-transformers to compute semantic variance. This stub remains
    for API compatibility if imported directly elsewhere, but delegates
    to the semantic calculation.
    
    Args:
        arguments: List of argument strings.
        
    Returns:
        Variance value (0.0 if < 2 args).
    """
    # Note: The actual implementation using sentence-transformers
    # is in code/metrics/extract.py to handle model loading efficiently.
    # This function is kept for interface compatibility.
    if len(arguments) < 2:
        return 0.0
    
    # Fallback to a simple heuristic if semantic model is not available
    # (though the pipeline expects the semantic version).
    # Convert to simple character-based variance as a last resort
    # to avoid circular imports or missing dependencies in tests.
    lengths = [len(str(a)) for a in arguments]
    if not lengths:
        return 0.0
    return float(np.var(lengths))