"""
Unit tests for renderer execution task (T015b).
Verifies that renderer generates correct ASCII grids and JSON logs.
"""
import os
import json
import tempfile
import pytest
import yaml
from renderer import run_renderer, generate_ascii_grid, validate_ascii_grid

def test_renderer_generates_files():
    """Test that renderer generates expected output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        seeds = [42, 123]
        
        # Create seeds config
        seeds_config = os.path.join(temp_dir, 'seeds.yaml')
        with open(seeds_config, 'w') as f:
            yaml.dump({'seeds': seeds}, f)
        
        output_dir = os.path.join(temp_dir, 'output')
        
        # Run renderer
        run_renderer(seeds, output_dir)
        
        # Check that files were created
        for seed in seeds:
            ascii_file = os.path.join(output_dir, f"seeds_{seed}.ascii")
            json_file = os.path.join(output_dir, f"seeds_{seed}.json")
            
            assert os.path.exists(ascii_file), f"ASCII file not created for seed {seed}"
            assert os.path.exists(json_file), f"JSON file not created for seed {seed}"
            
            # Validate ASCII grid
            with open(ascii_file, 'r') as f:
                grid_content = f.read()
            assert validate_ascii_grid(grid_content), f"Invalid ASCII grid for seed {seed}"
            
            # Validate JSON log
            with open(json_file, 'r') as f:
                event_log = json.load(f)
            assert isinstance(event_log, list), f"Event log is not a list for seed {seed}"
            assert len(event_log) > 0, f"Empty event log for seed {seed}"

def test_ascii_grid_format():
    """Test that ASCII grids have correct format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        seeds = [999]
        run_renderer(seeds, temp_dir)
        
        ascii_file = os.path.join(temp_dir, "seeds_999.ascii")
        with open(ascii_file, 'r') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        assert len(lines) == 15, "Grid height should be 15"
        assert all(len(line) == 20 for line in lines), "Grid width should be 20 for all rows"

def test_json_log_structure():
    """Test that JSON logs have correct structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        seeds = [888]
        run_renderer(seeds, temp_dir)
        
        json_file = os.path.join(temp_dir, "seeds_888.json")
        with open(json_file, 'r') as f:
            event_log = json.load(f)
        
        # Check structure
        assert isinstance(event_log, list)
        for event in event_log:
            assert 'step' in event
            assert 'action' in event
            assert 'state' in event
            assert 'observation' in event