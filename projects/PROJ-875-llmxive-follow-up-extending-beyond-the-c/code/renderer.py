"""
Renderer module for converting visual states to ASCII grids and generating event logs.

This module implements the core rendering logic for the llmXive project,
ensuring consistent conversion between visual representations and ASCII grids
for text-based agent interaction.
"""
import json
import os
import argparse
from typing import List, Dict, Any, Tuple, Optional
import random
import yaml
import numpy as np
from PIL import Image

# Constants for grid rendering
GRID_WIDTH = 20
GRID_HEIGHT = 20
CELL_SIZE = 10  # pixels per cell in visual representation
BACKGROUND_COLOR = (255, 255, 255)  # White
WALL_COLOR = (0, 0, 0)  # Black
PLAYER_COLOR = (255, 0, 0)  # Red
KEY_COLOR = (0, 255, 0)  # Green
DOOR_COLOR = (0, 0, 255)  # Blue
GOAL_COLOR = (255, 255, 0)  # Yellow

# ASCII representations
ASCII_WALL = '#'
ASCII_PLAYER = '@'
ASCII_KEY = 'k'
ASCII_DOOR = 'd'
ASCII_GOAL = '*'
ASCII_EMPTY = ' '

def validate_grid_coordinates(x: int, y: int, width: int, height: int) -> bool:
    """Validate that coordinates are within grid bounds."""
    return 0 <= x < width and 0 <= y < height

def validate_grid_bounds(grid: List[List[Any]], width: int, height: int) -> bool:
    """Validate that grid dimensions match expected bounds."""
    if len(grid) != height:
        return False
    for row in grid:
        if len(row) != width:
            return False
    return True

def validate_ascii_grid(ascii_grid: str) -> bool:
    """Validate that an ASCII grid string is properly formatted."""
    if not ascii_grid:
        return False
    
    lines = ascii_grid.strip().split('\n')
    if not lines:
        return False
    
    # Check that all lines have the same length
    first_len = len(lines[0])
    for line in lines:
        if len(line) != first_len:
            return False
    
    return True

def render_error_block() -> str:
    """Return the standardized error block for corrupted states."""
    return "ERROR: STATE_CORRUPT"

def generate_ascii_grid(state: Dict[str, Any]) -> str:
    """
    Generate an ASCII grid representation from a game state.
    
    Args:
        state: Dictionary containing 'grid' (2D list) and 'player_pos' (x, y)
    
    Returns:
        String representation of the grid
    """
    if not state or 'grid' not in state:
        return render_error_block()
    
    grid = state['grid']
    player_pos = state.get('player_pos', (0, 0))
    width = len(grid[0]) if grid else 0
    height = len(grid)
    
    if not validate_grid_bounds(grid, width, height):
        return render_error_block()
    
    if not validate_grid_coordinates(player_pos[0], player_pos[1], width, height):
        return render_error_block()
    
    ascii_lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            cell = grid[y][x]
            if (x, y) == player_pos:
                line += ASCII_PLAYER
            elif cell == 'wall':
                line += ASCII_WALL
            elif cell == 'key':
                line += ASCII_KEY
            elif cell == 'door':
                line += ASCII_DOOR
            elif cell == 'goal':
                line += ASCII_GOAL
            else:
                line += ASCII_EMPTY
        ascii_lines.append(line)
    
    return '\n'.join(ascii_lines)

def render_visual_to_ascii(img_array: np.ndarray) -> str:
    """
    Convert a visual image (numpy array) to ASCII grid representation.
    
    This function analyzes the visual frame and reconstructs the grid state,
    then generates the corresponding ASCII representation.
    
    Args:
        img_array: NumPy array of shape (height, width, 3) or (height, width)
    
    Returns:
        String representation of the grid
    """
    if img_array.ndim == 2:
        # Grayscale image, convert to RGB
        img_array = np.stack([img_array] * 3, axis=-1)
    
    height, width, _ = img_array.shape
    
    # Calculate cell size based on image dimensions
    # Assuming the image covers the entire grid
    cell_height = height // GRID_HEIGHT
    cell_width = width // GRID_WIDTH
    
    if cell_height <= 0 or cell_width <= 0:
        return render_error_block()
    
    # Reconstruct grid from visual
    grid = []
    player_pos = None
    
    for y in range(GRID_HEIGHT):
        row = []
        for x in range(GRID_WIDTH):
            # Sample the center of each cell
            center_y = y * cell_height + cell_height // 2
            center_x = x * cell_width + cell_width // 2
            
            if center_y >= height or center_x >= width:
                row.append('empty')
                continue
            
            pixel = img_array[center_y, center_x]
            r, g, b = pixel[0], pixel[1], pixel[2]
            
            # Determine cell type based on color
            if r < 50 and g < 50 and b < 50:  # Black (wall)
                cell_type = 'wall'
            elif r > 200 and g < 50 and b < 50:  # Red (player)
                cell_type = 'empty'
                player_pos = (x, y)
            elif r < 50 and g > 200 and b < 50:  # Green (key)
                cell_type = 'key'
            elif r < 50 and g < 50 and b > 200:  # Blue (door)
                cell_type = 'door'
            elif r > 200 and g > 200 and b < 50:  # Yellow (goal)
                cell_type = 'goal'
            else:  # White or other (empty)
                cell_type = 'empty'
            
            row.append(cell_type)
        grid.append(row)
    
    if player_pos is None:
        # Default player position if not found
        player_pos = (0, 0)
    
    state = {
        'grid': grid,
        'player_pos': player_pos
    }
    
    return generate_ascii_grid(state)

def validate_grid_bounds_for_visual(img_shape: Tuple[int, int]) -> bool:
    """Validate that an image has appropriate dimensions for the grid."""
    height, width = img_shape
    return height >= GRID_HEIGHT and width >= GRID_WIDTH

def create_event_entry(timestamp: float, action: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Create a single event log entry."""
    return {
        "timestamp": timestamp,
        "action": action,
        "state": state,
        "ascii_grid": generate_ascii_grid(state)
    }

def append_event_to_log(event_log: List[Dict[str, Any]], event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Append an event to the event log."""
    event_log.append(event)
    return event_log

def save_event_log_to_file(event_log: List[Dict[str, Any]], filepath: str) -> None:
    """Save event log to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(event_log, f, indent=2)

def load_event_log_from_file(filepath: str) -> List[Dict[str, Any]]:
    """Load event log from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_event_log(event_log: List[Dict[str, Any]]) -> bool:
    """Validate the structure of an event log."""
    if not isinstance(event_log, list):
        return False
    
    for event in event_log:
        if not isinstance(event, dict):
            return False
        if 'timestamp' not in event or 'action' not in event or 'state' not in event:
            return False
    
    return True

def generate_event_log(seeds: List[int], steps: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a synthetic event log for testing purposes.
    
    Args:
        seeds: List of random seeds
        steps: Number of steps per seed
    
    Returns:
        List of event log entries
    """
    event_log = []
    
    for seed in seeds:
        random.seed(seed)
        np.random.seed(seed)
        
        # Generate a simple state
        grid = [['empty' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        player_pos = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        
        # Add some walls, keys, doors, and goals
        for _ in range(5):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'wall'
        
        for _ in range(2):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'key'
        
        for _ in range(2):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'door'
        
        x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
        grid[y][x] = 'goal'
        
        state = {
            'grid': grid,
            'player_pos': player_pos
        }
        
        # Generate events
        for step in range(steps):
            timestamp = step * 0.1
            action = random.choice(['move_up', 'move_down', 'move_left', 'move_right', 'wait'])
            
            # Update player position based on action
            if action == 'move_up':
                player_pos = (player_pos[0], max(0, player_pos[1]-1))
            elif action == 'move_down':
                player_pos = (player_pos[0], min(GRID_HEIGHT-1, player_pos[1]+1))
            elif action == 'move_left':
                player_pos = (max(0, player_pos[0]-1), player_pos[1])
            elif action == 'move_right':
                player_pos = (min(GRID_WIDTH-1, player_pos[0]+1), player_pos[1])
            
            state['player_pos'] = player_pos
            event = create_event_entry(timestamp, action, state)
            event_log.append(event)
    
    return event_log

def run_renderer(seeds: List[int], output_dir: str, mode: str = "ascii") -> None:
    """
    Run the renderer to generate ASCII grids and event logs.
    
    Args:
        seeds: List of random seeds
        output_dir: Directory to save output files
        mode: "ascii" for ASCII grids only, "visual" for visual frames, "both" for both
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for seed in seeds:
        random.seed(seed)
        np.random.seed(seed)
        
        # Generate a simple state
        grid = [['empty' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        player_pos = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        
        # Add some walls, keys, doors, and goals
        for _ in range(5):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'wall'
        
        for _ in range(2):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'key'
        
        for _ in range(2):
            x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
            grid[y][x] = 'door'
        
        x, y = random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1)
        grid[y][x] = 'goal'
        
        state = {
            'grid': grid,
            'player_pos': player_pos
        }
        
        # Generate ASCII grid
        ascii_grid = generate_ascii_grid(state)
        
        # Save ASCII grid
        ascii_filename = os.path.join(output_dir, f"seeds_{seed}.ascii")
        with open(ascii_filename, 'w', encoding='utf-8') as f:
            f.write(ascii_grid)
        
        # Generate event log
        event_log = generate_event_log([seed], steps=10)
        log_filename = os.path.join(output_dir, f"seeds_{seed}.json")
        save_event_log_to_file(event_log, log_filename)
        
        # Generate visual frame if requested
        if mode in ["visual", "both"]:
            # Create a simple visual representation
            img = Image.new('RGB', (GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE), BACKGROUND_COLOR)
            pixels = img.load()
            
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    cell = grid[y][x]
                    if cell == 'wall':
                        color = WALL_COLOR
                    elif cell == 'key':
                        color = KEY_COLOR
                    elif cell == 'door':
                        color = DOOR_COLOR
                    elif cell == 'goal':
                        color = GOAL_COLOR
                    else:
                        color = BACKGROUND_COLOR
                    
                    for py in range(y * CELL_SIZE, (y+1) * CELL_SIZE):
                        for px in range(x * CELL_SIZE, (x+1) * CELL_SIZE):
                            if py < img.height and px < img.width:
                                pixels[px, py] = color
            
            # Draw player
            px, py = player_pos
            for y in range(py * CELL_SIZE, (py+1) * CELL_SIZE):
                for x in range(px * CELL_SIZE, (px+1) * CELL_SIZE):
                    if y < img.height and x < img.width:
                        pixels[x, y] = PLAYER_COLOR
            
            visual_filename = os.path.join(output_dir, f"seeds_{seed}.png")
            img.save(visual_filename)

def main():
    """Main entry point for the renderer script."""
    parser = argparse.ArgumentParser(description="Renderer for llmXive project")
    parser.add_argument("--seeds", required=True, help="Path to seeds.yaml file")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--mode", default="ascii", choices=["ascii", "visual", "both"], help="Output mode")
    
    args = parser.parse_args()
    
    # Load seeds
    with open(args.seeds, 'r') as f:
        seeds_config = yaml.safe_load(f)
    
    seeds = seeds_config.get('seeds', [])
    
    if not seeds:
        print("No seeds found in configuration", file=sys.stderr)
        sys.exit(1)
    
    # Run renderer
    run_renderer(seeds, args.output, args.mode)
    print(f"Renderer completed. Output saved to {args.output}")

if __name__ == "__main__":
    main()
