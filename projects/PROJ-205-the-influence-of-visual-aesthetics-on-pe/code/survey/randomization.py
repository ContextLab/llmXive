"""
Randomization logic for stimulus presentation.
Implements Balanced Latin Square design.
"""
import math
from typing import List, Tuple
import hashlib

from survey.constants import LATIN_SQUARE_SEQUENCES

def generate_latin_square(stimuli_list: List[str]) -> List[List[str]]:
    """
    Generate a balanced Latin Square for the given stimuli list.
    This is a placeholder for dynamic generation if needed, 
    but we use hardcoded sequences for reproducibility.
    """
    # For this project, we use the hardcoded sequences defined in constants.py
    # to ensure exact reproducibility.
    if len(stimuli_list) != 4:
        raise ValueError("This implementation expects exactly 4 stimuli.")
    
    return LATIN_SQUARE_SEQUENCES

def select_sequence(stimuli_list: List[str], participant_id: str) -> List[str]:
    """
    Select a sequence based on participant ID modulo N.
    """
    sequences = generate_latin_square(stimuli_list)
    n = len(sequences)
    
    # Use the last 8 characters of the participant ID to generate a number
    # This ensures a consistent distribution
    seed_str = participant_id[-8:]
    seed_val = int(seed_str, 16)
    
    index = seed_val % n
    return sequences[index]

def verify_latin_square_balance(sequences: List[List[str]]) -> bool:
    """
    Verify that the sequences form a balanced Latin Square.
    Every stimulus appears exactly once in each position across all sequences.
    """
    n = len(sequences)
    if n == 0:
        return False
    
    num_stimuli = len(sequences[0])
    
    # Check each position
    for pos in range(num_stimuli):
        stimuli_at_pos = [seq[pos] for seq in sequences]
        if len(set(stimuli_at_pos)) != num_stimuli:
            return False
    
    return True

def get_sequences_for_stimuli(stimuli_list: List[str]) -> List[List[str]]:
    """
    Get all sequences for the given stimuli list.
    """
    return generate_latin_square(stimuli_list)
