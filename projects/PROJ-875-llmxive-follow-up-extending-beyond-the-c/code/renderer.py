"""
Renderer module for converting visual states to ASCII grids and generating event logs.
Implements validation for out-of-bounds states and error handling.
"""
import json
import os
from typing import List, Union, Dict, Any, Tuple, Optional
import random

# Constants for error handling
ERROR_STATE_CORRUPT = "ERROR: STATE_CORRUPT"
DEFAULT_GRID_WIDTH = 10
DEFAULT_GRID_HEIGHT = 10
DEFAULT_CELL_SIZE = 3

def validate_grid_coordinates(x: int, y: int, width: int, height: int) -> bool:
    """
    Validate that coordinates are within grid bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
        width: Grid width
        height: Grid height
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    return 0 <= x < width and 0 <= y < height

def validate_grid_bounds(grid: List[List[Any]], expected_width: Optional[int] = None, 
                         expected_height: Optional[int] = None) -> bool:
    """
    Validate that a grid has consistent dimensions and is within expected bounds.
    
    Args:
        grid: 2D list representing the grid
        expected_width: Optional expected width
        expected_height: Optional expected height
        
    Returns:
        True if grid is valid, False otherwise
    """
    if not grid or not isinstance(grid, list):
        return False
        
    if len(grid) == 0:
        return False
        
    height = len(grid)
    if expected_height is not None and height != expected_height:
        return False
        
    width = len(grid[0]) if grid else 0
    if expected_width is not None and width != expected_width:
        return False
        
    # Check all rows have the same width
    for row in grid:
        if len(row) != width:
            return False
            
    return True

def validate_ascii_grid(grid_str: str) -> bool:
    """
    Validate an ASCII grid string format.
    
    Args:
        grid_str: String representation of the grid
        
    Returns:
        True if valid, False otherwise
    """
    if not grid_str or not isinstance(grid_str, str):
        return False
        
    lines = grid_str.strip().split('\n')
    if not lines:
        return False
        
    # Check that all lines have the same length (ignoring newline chars)
    first_len = len(lines[0])
    for line in lines[1:]:
        if len(line) != first_len:
            return False
            
    return True

def render_error_block(error_type: str) -> str:
    """
    Generate a standardized error block string.
    
    Args:
        error_type: Type of error (e.g., "STATE_CORRUPT")
        
    Returns:
        Formatted error block string
    """
    return f"ERROR: {error_type}"

def generate_ascii_grid(state: Dict[str, Any], width: int = DEFAULT_GRID_WIDTH, 
                        height: int = DEFAULT_GRID_HEIGHT) -> Union[str, str]:
    """
    Convert a visual state dictionary to an ASCII grid string.
    
    Args:
        state: Dictionary containing state information
        width: Grid width
        height: Grid height
        
    Returns:
        ASCII grid string or error block if state is invalid
    """
    # Validate state structure
    if not isinstance(state, dict):
        return render_error_block("STATE_CORRUPT")
        
    if "grid" not in state:
        return render_error_block("STATE_CORRUPT")
        
    grid_data = state["grid"]
    
    # Validate grid bounds
    if not validate_grid_bounds(grid_data, width, height):
        return render_error_block("STATE_CORRUPT")
        
    # Check for out-of-bounds items in state
    if "items" in state:
        for item in state["items"]:
            if "x" in item and "y" in item:
                if not validate_grid_coordinates(item["x"], item["y"], width, height):
                    return render_error_block("STATE_CORRUPT")
                    
    # Convert grid to ASCII string
    ascii_lines = []
    for row in grid_data:
        row_str = ""
        for cell in row:
            if cell is None or cell == "":
                row_str += " "
            else:
                row_str += str(cell)[0]  # Take first character if cell is string
        ascii_lines.append(row_str)
        
    return "\n".join(ascii_lines)

def render_visual_to_ascii(visual_state: Dict[str, Any]) -> str:
    """
    Render a visual state to ASCII representation.
    
    Args:
        visual_state: Visual state dictionary
        
    Returns:
        ASCII representation or error block
    """
    if not isinstance(visual_state, dict):
        return render_error_block("STATE_CORRUPT")
        
    width = visual_state.get("width", DEFAULT_GRID_WIDTH)
    height = visual_state.get("height", DEFAULT_GRID_HEIGHT)
    
    # Validate width and height
    if not isinstance(width, int) or width <= 0:
        return render_error_block("STATE_CORRUPT")
    if not isinstance(height, int) or height <= 0:
        return render_error_block("STATE_CORRUPT")
        
    return generate_ascii_grid(visual_state, width, height)

def validate_grid_bounds_for_visual(visual_state: Dict[str, Any]) -> bool:
    """
    Validate that a visual state has valid bounds and content.
    
    Args:
        visual_state: Visual state dictionary
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(visual_state, dict):
        return False
        
    if "grid" not in visual_state:
        return False
        
    width = visual_state.get("width")
    height = visual_state.get("height")
    
    if not isinstance(width, int) or width <= 0:
        return False
    if not isinstance(height, int) or height <= 0:
        return False
        
    grid_data = visual_state["grid"]
    if not validate_grid_bounds(grid_data, width, height):
        return False
        
    # Check items if present
    if "items" in visual_state:
        for item in visual_state["items"]:
            if not isinstance(item, dict):
                return False
            x = item.get("x")
            y = item.get("y")
            if x is None or y is None:
                return False
            if not validate_grid_coordinates(x, y, width, height):
                return False
                
    return True

def create_event_entry(step: int, action: str, state: Dict[str, Any], 
                      observation: str) -> Dict[str, Any]:
    """
    Create a single event log entry.
    
    Args:
        step: Step number
        action: Action taken
        state: Current state dictionary
        observation: Observation string
        
    Returns:
        Event log entry dictionary
    """
    return {
        "step": step,
        "action": action,
        "state_snapshot": {
            "grid": state.get("grid", []),
            "width": state.get("width", DEFAULT_GRID_WIDTH),
            "height": state.get("height", DEFAULT_GRID_HEIGHT)
        },
        "observation": observation
    }

def append_event_to_log(event_log: List[Dict[str, Any]], entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Append an event entry to the event log.
    
    Args:
        event_log: Existing event log list
        entry: New event entry
        
    Returns:
        Updated event log list
    """
    event_log.append(entry)
    return event_log

def save_event_log_to_file(event_log: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Save event log to a JSON file.
    
    Args:
        event_log: Event log list
        filepath: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(event_log, f, indent=2)
        return True
    except Exception:
        return False

def load_event_log_from_file(filepath: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load event log from a JSON file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Event log list or None if failed
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def validate_event_log(event_log: List[Dict[str, Any]]) -> bool:
    """
    Validate an event log structure.
    
    Args:
        event_log: Event log list
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(event_log, list):
        return False
        
    for entry in event_log:
        if not isinstance(entry, dict):
            return False
        required_keys = ["step", "action", "state_snapshot", "observation"]
        for key in required_keys:
            if key not in entry:
                return False
                
    return True

def generate_event_log(steps: List[Dict[str, Any]], output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate a complete event log from a list of step dictionaries.
    
    Args:
        steps: List of step dictionaries
        output_path: Optional path to save the log
        
    Returns:
        Generated event log
    """
    event_log = []
    for step_data in steps:
        entry = create_event_entry(
            step=step_data.get("step", len(event_log)),
            action=step_data.get("action", "unknown"),
            state=step_data.get("state", {}),
            observation=step_data.get("observation", "")
        )
        event_log = append_event_to_log(event_log, entry)
        
    if output_path:
        save_event_log_to_file(event_log, output_path)
        
    return event_log

# Main execution for testing
if __name__ == "__main__":
    # Test out-of-bounds validation
    test_state = {
        "grid": [["." for _ in range(5)] for _ in range(5)],
        "width": 5,
        "height": 5,
        "items": [{"x": 2, "y": 2, "type": "object"}]
    }
    
    result = generate_ascii_grid(test_state)
    print(f"Valid state result: {result}")
    
    # Test out-of-bounds item
    corrupt_state = {
        "grid": [["." for _ in range(5)] for _ in range(5)],
        "width": 5,
        "height": 5,
        "items": [{"x": 10, "y": 10, "type": "object"}]  # Out of bounds
    }
    
    corrupt_result = generate_ascii_grid(corrupt_state)
    print(f"Corrupt state result: {corrupt_result}")
    print(f"Error block matches: {corrupt_result == ERROR_STATE_CORRUPT}")
