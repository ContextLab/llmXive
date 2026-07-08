"""
Utility functions for linguistic metric computation.
"""
import random
import re
import numpy as np
from typing import Optional, List, Tuple
import textstat


def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)


def calculate_mtld(text: str) -> float:
    """
    Calculate Measure of Textual Lexical Diversity (MTLD).
    
    Args:
        text: The input text string.
        
    Returns:
        The MTLD score.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    try:
        # textstat.mtld expects a string, not a list
        return textstat.mtld(text)
    except Exception:
        return 0.0


def calculate_flesch_kincaid(text: str) -> float:
    """
    Calculate Flesch-Kincaid Grade Level.
    
    Args:
        text: The input text string.
        
    Returns:
        The Flesch-Kincaid score.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    try:
        return textstat.flesch_kincaid_grade(text)
    except Exception:
        return 0.0


def calculate_average_sentence_length(text: str) -> float:
    """
    Calculate average sentence length (words per sentence).
    
    Args:
        text: The input text string.
        
    Returns:
        The average sentence length.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    try:
        # textstat.sent_count returns number of sentences
        # textstat.lexicon_count returns number of words
        num_sentences = textstat.sent_count(text)
        num_words = textstat.lexicon_count(text)
        
        if num_sentences == 0:
            return 0.0
            
        return num_words / num_sentences
    except Exception:
        return 0.0


def get_all_metrics(text: str) -> Tuple[float, float, float]:
    """
    Compute all linguistic metrics for a given text.
    
    Args:
        text: The input text string.
        
    Returns:
        A tuple of (flesch_kincaid, mtld, avg_sentence_length).
    """
    fk = calculate_flesch_kincaid(text)
    mtld_val = calculate_mtld(text)
    asl = calculate_average_sentence_length(text)
    return fk, mtld_val, asl
