import json
import os
from typing import List, Union, Dict, Any, Tuple, Optional
import random

# Constants for ASCII grid characters
EMPTY_CELL = '.'
WALL_CELL = '#'
PLAYER_CELL = 'M'
KEY_CELL = 'K'
EXIT_CELL = 'E'

def generate_ascii_grid(grid: List[List[str]]) -> str:
    """
    Convert a 2D grid of characters to an ASCII string representation.
    
    Args:
        grid: 2D list of characters representing the maze state
        
    Returns:
        String representation of the grid
    """
    if not grid or not grid[0]:
        return ""
    
    return '\n'.join([''.join(row) for row in grid])

def render_visual_to_ascii(visual_state: Dict[str, Any]) -> str:
    """
    Render a visual state dictionary to ASCII grid.
    
    Args:
        visual_state: Dictionary containing grid and player position
        
    Returns:
        ASCII string representation
    """
    grid = visual_state.get('grid', [])
    player_pos = visual_state.get('player_pos', (0, 0))
    
    if not grid:
        return ""
    
    # Create a copy of the grid to avoid modifying the original
    ascii_grid = [row[:] for row in grid]
    
    # Place player on the grid
    if 0 <= player_pos[0] < len(ascii_grid) and 0 <= player_pos[1] < len(ascii_grid[0]):
        ascii_grid[player_pos[0]][player_pos[1]] = PLAYER_CELL
    
    return generate_ascii_grid(ascii_grid)

def validate_grid_bounds(grid: List[str]) -> Tuple[bool, str]:
    """
    Validate that the grid has consistent row lengths.
    
    Args:
        grid: List of strings representing grid rows
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not grid:
        return False, "Grid is empty"
    
    row_length = len(grid[0])
    for i, row in enumerate(grid):
        if len(row) != row_length:
            return False, f"Row {i} has length {len(row)}, expected {row_length}"
    
    return True, "Valid bounds"

def validate_grid_coordinates(grid: List[str]) -> Tuple[bool, str]:
    """
    Validate that all characters in the grid are valid.
    
    Args:
        grid: List of strings representing grid rows
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_chars = {EMPTY_CELL, WALL_CELL, PLAYER_CELL, KEY_CELL, EXIT_CELL}
    
    for i, row in enumerate(grid):
        for j, char in enumerate(row):
            if char not in valid_chars:
                return False, f"Invalid character '{char}' at ({i}, {j})"
    
    return True, "Valid coordinates"

def validate_ascii_grid(grid: List[str]) -> Tuple[bool, str]:
    """
    Perform comprehensive validation of an ASCII grid.
    
    Args:
        grid: List of strings representing grid rows
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check bounds
    is_valid, msg = validate_grid_bounds(grid)
    if not is_valid:
        return False, msg
    
    # Check coordinates
    is_valid, msg = validate_grid_coordinates(grid)
    if not is_valid:
        return False, msg
    
    # Check for at least one player
    player_count = sum(row.count(PLAYER_CELL) for row in grid)
    if player_count != 1:
        return False, f"Expected 1 player, found {player_count}"
    
    return True, "Valid grid"

def render_error_block(error_type: str, details: str) -> str:
    """
    Generate a standardized error block for out-of-bounds or invalid states.
    
    Args:
        error_type: Type of error (e.g., "OUT_OF_BOUNDS", "STATE_CORRUPT")
        details: Additional error details
        
    Returns:
        Formatted error block string
    """
    return f"ERROR: {error_type}\nDetails: {details}\n"

def generate_event_log(events: List[Dict[str, Any]]) -> str:
    """
    Generate a JSON event log from a list of events.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        JSON string of events
    """
    return json.dumps(events, indent=2)

def validate_event_log(log_content: str) -> Tuple[bool, str]:
    """
    Validate that an event log is properly formatted JSON.
    
    Args:
        log_content: JSON string of events
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        events = json.loads(log_content)
        if not isinstance(events, list):
            return False, "Event log must be a list of events"
        
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                return False, f"Event {i} is not a dictionary"
            if 't' not in event or 'event' not in event:
                return False, f"Event {i} missing required fields 't' or 'event'"
        
        return True, "Valid event log"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
