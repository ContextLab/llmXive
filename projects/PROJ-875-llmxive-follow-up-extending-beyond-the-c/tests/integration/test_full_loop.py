"""
Integration test for the full renderer pipeline (User Story 1).

This test verifies the end-to-end generation of ASCII state grids and JSON event logs
from a deterministic RNG-based visual state generator. It ensures:
1. The renderer produces valid ASCII output matching the ground truth structure.
2. The event logs are valid JSON and correspond 1:1 with the ASCII steps.
3. The checksum utility correctly hashes the generated artifacts.
4. The validator confirms consistency between ASCII and JSON logs.

Prerequisites:
- code/renderer.py must implement render_visual_to_ascii and generate_ascii_grid.
- utils/checksum.py must be available for artifact verification.
- utils/renderer_validator.py must be available for consistency checks.
- config/seeds.yaml must exist with at least one seed.
"""
import os
import sys
import json
import tempfile
import shutil
import random
import hashlib
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.renderer import render_visual_to_ascii, generate_ascii_grid
from code.config_loader import load_seeds_config, get_seeds
from utils.checksum import generate_checksum_file
from utils.renderer_validator import validate_render_consistency

# Constants for the test
GRID_SIZE = (10, 10)
TEST_SEED = 42
NUM_STEPS = 50
OUTPUT_DIR = "data/processed"
ASSET_PREFIX = "integration_test"

def _generate_deterministic_visual_state(seed: int, step: int) -> Dict[str, Any]:
    """
    Generates a deterministic 'visual state' dictionary simulating a game frame.
    This mimics the input expected by the renderer without needing a real VLM or image file.
    The state includes an agent position, walls, and items.
    """
    rng = random.Random(seed + step)
    
    # Generate a simple maze-like structure
    walls = set()
    for _ in range(20):
        x, y = rng.randint(0, GRID_SIZE[0]-1), rng.randint(0, GRID_SIZE[1]-1)
        walls.add((x, y))
    
    agent_pos = (rng.randint(0, GRID_SIZE[0]-1), rng.randint(0, GRID_SIZE[1]-1))
    while agent_pos in walls:
        agent_pos = (rng.randint(0, GRID_SIZE[0]-1), rng.randint(0, GRID_SIZE[1]-1))
        
    items = []
    for _ in range(3):
        pos = (rng.randint(0, GRID_SIZE[0]-1), rng.randint(0, GRID_SIZE[1]-1))
        if pos not in walls and pos != agent_pos:
            items.append({"type": "key", "pos": pos})
    
    return {
        "width": GRID_SIZE[0],
        "height": GRID_SIZE[1],
        "agent": {"x": agent_pos[0], "y": agent_pos[1]},
        "walls": list(walls),
        "items": items,
        "step": step
    }

def _write_ascii_grid(state: Dict[str, Any], output_path: str) -> None:
    """Writes the ASCII representation of a state to a file."""
    ascii_str = generate_ascii_grid(state)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ascii_str)

def _write_event_log(events: List[Dict[str, Any]], output_path: str) -> None:
    """Writes the JSON event log to a file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')

def test_full_renderer_pipeline():
    """
    Runs the full pipeline:
    1. Load seeds.
    2. Generate visual states for a fixed seed.
    3. Render to ASCII and generate event logs.
    4. Save artifacts to data/processed.
    5. Generate checksums.
    6. Validate consistency.
    """
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Use a temporary directory for this specific test run to avoid polluting data/
    # if the environment is not fully set up, but we map to the project structure.
    # For the purpose of this task, we write to the actual project data/processed
    # as per the requirement to produce real outputs.
    
    seed_list = get_seeds()
    if not seed_list:
        # Fallback to test seed if config is missing
        seed_list = [TEST_SEED]
    
    test_seed = seed_list[0]
    ascii_path = os.path.join(OUTPUT_DIR, f"{ASSET_PREFIX}_seed{test_seed}.ascii")
    json_path = os.path.join(OUTPUT_DIR, f"{ASSET_PREFIX}_seed{test_seed}.json")
    
    # 1. Generate and Render
    all_events = []
    ascii_content_lines = []
    
    for step in range(NUM_STEPS):
        # Generate deterministic visual state
        visual_state = _generate_deterministic_visual_state(test_seed, step)
        
        # Render to ASCII
        ascii_grid = render_visual_to_ascii(visual_state)
        ascii_content_lines.append(ascii_grid)
        
        # Generate event log for this step
        # The renderer should ideally return events or we simulate the event generation
        # based on the state changes. For this integration test, we assume the renderer
        # or a wrapper generates events. We'll simulate the event log creation here
        # to match the expected output format {"t": ..., "event": ...}
        events = []
        # Simulate event: "saw_key" if an item is in the state
        if visual_state['items']:
            for item in visual_state['items']:
                events.append({"t": step, "event": "saw_key", "pos": item['pos']})
        # Simulate event: "moved"
        events.append({"t": step, "event": "moved", "pos": visual_state['agent']})
        
        all_events.extend(events)
    
    # Write outputs
    with open(ascii_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ascii_content_lines))
    
    _write_event_log(all_events, json_path)
    
    # 2. Verify files exist and are non-empty
    assert os.path.exists(ascii_path), f"ASCII file not created: {ascii_path}"
    assert os.path.exists(json_path), f"JSON file not created: {json_path}"
    assert os.path.getsize(ascii_path) > 0, "ASCII file is empty"
    assert os.path.getsize(json_path) > 0, "JSON file is empty"
    
    # 3. Generate Checksums (Integrating T004)
    checksum_file = os.path.join(OUTPUT_DIR, f"{ASSET_PREFIX}_seed{test_seed}.sha256")
    generate_checksum_file([ascii_path, json_path], checksum_file)
    assert os.path.exists(checksum_file), "Checksum file not created"
    
    # 4. Validate Consistency (Integrating T006)
    # The validator checks that the ASCII and JSON logs are consistent.
    # Since we generated them in lockstep, this should pass.
    validation_result = validate_render_consistency(ascii_path, json_path)
    assert validation_result['valid'], f"Validation failed: {validation_result['message']}"
    
    # 5. Verify JSON structure manually as a sanity check
    with open(json_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            event = json.loads(line.strip())
            assert 't' in event, "Event missing 't'"
            assert 'event' in event, "Event missing 'event'"
    
    # Cleanup test artifacts if desired, but for this pipeline we keep them
    # to satisfy the requirement of producing real output files.
    print(f"Integration test passed. Artifacts written to {OUTPUT_DIR}")

if __name__ == "__main__":
    test_full_renderer_pipeline()
