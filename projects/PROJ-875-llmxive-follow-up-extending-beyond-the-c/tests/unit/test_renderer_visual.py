import os
import tempfile
import pytest
from PIL import Image
import sys
import random

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.renderer import (
    render_visual_to_ascii, 
    validate_grid_bounds, 
    GRID_SIZE, 
    CELL_SIZE,
    run_renderer
)
from code.config_loader import load_seeds_config

class TestVisualRenderer:
    def test_render_visual_to_ascii_dimensions(self):
        """Verify that the generated image has correct dimensions."""
        grid = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        grid[2][2] = 'P'
        state = {'grid': grid}
        
        img = render_visual_to_ascii(state)
        
        expected_width = GRID_SIZE * CELL_SIZE
        expected_height = GRID_SIZE * CELL_SIZE
        
        assert img.width == expected_width, f"Width mismatch: {img.width} != {expected_width}"
        assert img.height == expected_height, f"Height mismatch: {img.height} != {expected_height}"
        assert img.mode == 'RGB', f"Mode mismatch: {img.mode} != RGB"

    def test_render_visual_to_ascii_content(self):
        """Verify that specific cells are drawn with expected colors."""
        # Create a grid with a specific item
        grid = [[' ' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        grid[0][0] = 'W' # Wall
        grid[1][1] = 'K' # Key
        
        state = {'grid': grid}
        img = render_visual_to_ascii(state)
        pixels = img.load()
        
        # Check a pixel inside the top-left cell (Wall)
        # Cell (0,0) starts at (0,0), size 32. Check center (16,16)
        wall_pixel = pixels[16, 16]
        # Wall color is (100, 100, 100)
        assert wall_pixel == (100, 100, 100), f"Wall color mismatch: {wall_pixel}"
        
        # Check a pixel inside the (1,1) cell (Key)
        # Starts at (32, 32). Check center (48, 48)
        key_pixel = pixels[48, 48]
        # Key color is (255, 215, 0)
        assert key_pixel == (255, 215, 0), f"Key color mismatch: {key_pixel}"

    def test_run_renderer_visual_output(self):
        """Test the full pipeline for visual mode generation."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            seeds = [42, 123]
            # Write a temporary seeds file
            seeds_path = os.path.join(tmpdir, "seeds.yaml")
            with open(seeds_path, 'w') as f:
                f.write("seeds:\n  - 42\n  - 123\n")
            
            output_dir = os.path.join(tmpdir, "output")
            
            # Run the renderer
            files = run_renderer(seeds, output_dir, mode='visual')
            
            # Verify files exist
            assert len(files) == 2
            for f in files:
                assert os.path.exists(f)
                assert f.endswith('.png')
                
                # Verify it's a valid image
                img = Image.open(f)
                img.load()
                assert img.width == GRID_SIZE * CELL_SIZE
                assert img.height == GRID_SIZE * CELL_SIZE

    def test_run_renderer_visual_mode_cli_simulation(self):
        """Simulate the CLI command behavior for T015c."""
        with tempfile.TemporaryDirectory() as tmpdir:
            seeds_file = os.path.join(tmpdir, "seeds.yaml")
            with open(seeds_file, 'w') as f:
                f.write("seeds:\n  - 99\n")
            
            output_dir = os.path.join(tmpdir, "data_processed")
            
            # Simulate the call that T015c performs
            files = run_renderer([99], output_dir, mode='visual')
            
            expected_file = os.path.join(output_dir, "seeds_99.png")
            assert expected_file in files
            assert os.path.exists(expected_file)