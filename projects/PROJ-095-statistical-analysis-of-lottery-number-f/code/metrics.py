"""
Metrics calculation module for Lottery Draw Integrity Analysis.

Implements valid metrics to replace the scientifically invalid per-draw Chi-Square:
- birthday_cluster_ratio: Measures the proportion of numbers in a draw that are <= 31.
- consecutive_pattern_count: Measures the presence of consecutive numbers in a draw.
"""
from typing import List, Union
import numpy as np

from constants import BIRTHDAY_THRESHOLD, NUMBERS_PER_DRAW


def calculate_birthday_ratio(draw_numbers: List[Union[int, float]]) -> float:
    """
    Calculate the ratio of numbers in a draw that fall within the "birthday" range (1-31).
    
    This metric quantifies the "Birthday Paradox" clustering often seen in human-selected
    lottery numbers (e.g., dates).
    
    Args:
        draw_numbers: A list of integers representing the numbers in a single draw.
                      Expected length is NUMBERS_PER_DRAW (6).
    
    Returns:
        float: The ratio of numbers <= BIRTHDAY_THRESHOLD. 
               Ranges from 0.0 (no birthdays) to 1.0 (all birthdays).
    
    Examples:
        >>> calculate_birthday_ratio([1, 2, 3, 4, 5, 6])
        1.0
        >>> calculate_birthday_ratio([32, 33, 34, 35, 36, 37])
        0.0
        >>> calculate_birthday_ratio([1, 2, 30, 32, 33, 34])
        0.5
    """
    if not draw_numbers:
        return 0.0
    
    count = 0
    for num in draw_numbers:
        # Handle potential float inputs from CSV parsing by converting to int
        val = int(num)
        if val <= BIRTHDAY_THRESHOLD:
            count += 1
    
    return float(count) / len(draw_numbers)


def calculate_consecutive_ratio(draw_numbers: List[Union[int, float]]) -> float:
    """
    Calculate the ratio of numbers involved in consecutive pairs within a draw.
    
    This metric quantifies the tendency for human-selected numbers to include
    consecutive sequences (e.g., 1, 2 or 30, 31).
    
    Logic:
    1. Sort the draw numbers.
    2. Identify pairs (i, i+1) where numbers are consecutive.
    3. Count how many unique numbers are part of at least one consecutive pair.
    4. Return the count divided by the total number of balls in the draw.
    
    Args:
        draw_numbers: A list of integers representing the numbers in a single draw.
    
    Returns:
        float: The ratio of numbers involved in consecutive patterns.
               Ranges from 0.0 to 1.0.
    
    Examples:
        >>> calculate_consecutive_ratio([1, 2, 3, 4, 5, 6])
        1.0  # All 6 numbers are part of consecutive chains
        >>> calculate_consecutive_ratio([1, 3, 5, 7, 9, 11])
        0.0  # No consecutive numbers
        >>> calculate_consecutive_ratio([1, 2, 10, 20, 30, 40])
        0.333... # Only 1 and 2 are consecutive (2/6)
    """
    if len(draw_numbers) < 2:
        return 0.0
    
    # Sort and deduplicate (though draws shouldn't have duplicates)
    sorted_nums = sorted(set(int(x) for x in draw_numbers))
    
    consecutive_indices = set()
    
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i+1] - sorted_nums[i] == 1:
            consecutive_indices.add(i)
            consecutive_indices.add(i+1)
    
    count = len(consecutive_indices)
    return float(count) / len(draw_numbers)