"""
Physics Simulation Engine using PyMunk.
Simulates basic physics on CPU to generate JSON constraints and detect logical contradictions.
"""
import json
import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pymunk
from pymunk import Vec2d

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GRAVITY = -9.81
SIMULATION_TIME_STEP = 1.0 / 60.0
SIMULATION_STEPS = 600  # 10 seconds of simulation
BOX_SIZE = 50  # pixels
COLLISION_MARGIN = 5  # pixels for overlap detection

class SceneDescriptionNotFoundError(Exception):
    """Raised when a scene description file is not found."""
    pass

class InvalidSceneDescriptionError(Exception):
    """Raised when a scene description is malformed."""
    pass

class SimulationError(Exception):
    """Raised when a simulation fails."""
    pass

class PhysicsConstraint:
    """Represents a physics constraint derived from a scene simulation."""
    
    def __init__(self, scene_id: str):
        self.scene_id = scene_id
        self.bounding_boxes: List[Dict[str, Any]] = []
        self.collision_rules: List[Dict[str, Any]] = []
        self.is_valid: bool = True
        self.contradiction_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "bounding_boxes": self.bounding_boxes,
            "collision_rules": self.collision_rules,
            "is_valid": self.is_valid,
            "contradiction_reason": self.contradiction_reason
        }

def load_scene_descriptions(csv_path: str) -> List[Dict[str, Any]]:
    """Load scene descriptions from a CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise SceneDescriptionNotFoundError(f"Scene descriptions file not found: {csv_path}")
    
    scenes = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'scene_id' not in row or 'description' not in row:
                raise InvalidSceneDescriptionError(f"Invalid row in CSV: {row}")
            scenes.append(row)
    
    logger.info(f"Loaded {len(scenes)} scene descriptions from {csv_path}")
    return scenes

def parse_scene_description(description: str) -> List[Tuple[str, str, str]]:
    """
    Parse a scene description string into a list of (object_a, preposition, object_b) tuples.
    Expected format: "A on B", "A next to B", "A under B", etc.
    """
    interactions = []
    # Simple parsing for known patterns
    patterns = [
        (r'(\w+)\s+on\s+(\w+)', 'on'),
        (r'(\w+)\s+next\s+to\s+(\w+)', 'next_to'),
        (r'(\w+)\s+under\s+(\w+)', 'under'),
        (r'(\w+)\s+above\s+(\w+)', 'above'),
        (r'(\w+)\s+below\s+(\w+)', 'below'),
        (r'(\w+)\s+left\s+of\s+(\w+)', 'left_of'),
        (r'(\w+)\s+right\s+of\s+(\w+)', 'right_of'),
    ]
    
    import re
    for pattern, preposition in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            interactions.append((match[0], preposition, match[1]))
    
    return interactions

def simulate_physics(scene_id: str, interactions: List[Tuple[str, str, str]]) -> PhysicsConstraint:
    """
    Simulate physics for a given set of interactions and detect contradictions.
    Returns a PhysicsConstraint object with simulation results.
    """
    constraint = PhysicsConstraint(scene_id)
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    
    # Create objects
    objects = {}
    for i, (obj_name, _, _) in enumerate(interactions):
        if obj_name not in objects:
            # Create a simple box for each object
            mass = 1
            size = BOX_SIZE
            moment = pymunk.moment_for_box(mass, (size, size))
            body = pymunk.Body(mass, moment)
            shape = pymunk.Poly.create_box(body, (size, size))
            shape.friction = 0.5
            shape.elasticity = 0.1
            
            # Initial position (scatter them)
            body.position = (100 + i * 100, 300)
            body.velocity = (0, 0)
            
            space.add(body, shape)
            objects[obj_name] = {
                'body': body,
                'shape': shape,
                'initial_pos': body.position,
                'final_pos': None
            }
    
    # Add constraints based on interactions
    for obj_a, preposition, obj_b in interactions:
        if obj_a not in objects or obj_b not in objects:
            continue
        
        body_a = objects[obj_a]['body']
        body_b = objects[obj_b]['body']
        
        # Apply constraints based on preposition
        if preposition == 'on':
            # A should be above B (y-coordinate of A < y-coordinate of B)
            # We'll simulate and check after
            pass
        elif preposition == 'under':
            # A should be below B
            pass
        elif preposition == 'above':
            # A should be above B
            pass
        elif preposition == 'below':
            # A should be below B
            pass
        elif preposition == 'left_of':
            # A should be left of B (x-coordinate of A < x-coordinate of B)
            pass
        elif preposition == 'right_of':
            # A should be right of B
            pass
        elif preposition == 'next_to':
            # A should be close to B
            pass
    
    # Run simulation
    for _ in range(SIMULATION_STEPS):
        space.step(SIMULATION_TIME_STEP)
    
    # Record final positions
    for obj_name, data in objects.items():
        data['final_pos'] = data['body'].position
        constraint.bounding_boxes.append({
            "object": obj_name,
            "x": int(data['body'].position.x),
            "y": int(data['body'].position.y),
            "width": BOX_SIZE,
            "height": BOX_SIZE
        })
    
    # Check for contradictions
    contradictions = []
    for obj_a, preposition, obj_b in interactions:
        if obj_a not in objects or obj_b not in objects:
            continue
        
        pos_a = objects[obj_a]['final_pos']
        pos_b = objects[obj_b]['final_pos']
        
        if preposition == 'on':
            # A should be above B (lower y value in screen coords, but higher in physics coords)
            # In physics, y increases upwards, so A.y > B.y + margin for "on"
            if pos_a.y < pos_b.y + BOX_SIZE:
                contradictions.append(f"{obj_a} is not on {obj_b} (y_diff={pos_a.y - pos_b.y})")
        
        elif preposition == 'under':
            # A should be below B
            if pos_a.y > pos_b.y - BOX_SIZE:
                contradictions.append(f"{obj_a} is not under {obj_b} (y_diff={pos_a.y - pos_b.y})")
        
        elif preposition == 'above':
            if pos_a.y <= pos_b.y:
                contradictions.append(f"{obj_a} is not above {obj_b} (y_diff={pos_a.y - pos_b.y})")
        
        elif preposition == 'below':
            if pos_a.y >= pos_b.y:
                contradictions.append(f"{obj_a} is not below {obj_b} (y_diff={pos_a.y - pos_b.y})")
        
        elif preposition == 'left_of':
            if pos_a.x >= pos_b.x:
                contradictions.append(f"{obj_a} is not left of {obj_b} (x_diff={pos_a.x - pos_b.x})")
        
        elif preposition == 'right_of':
            if pos_a.x <= pos_b.x:
                contradictions.append(f"{obj_a} is not right of {obj_b} (x_diff={pos_a.x - pos_b.x})")
        
        elif preposition == 'next_to':
            distance = (pos_a - pos_b).length
            if distance > BOX_SIZE * 2:
                contradictions.append(f"{obj_a} is not next to {obj_b} (distance={distance})")
    
    # Check for cycles in "above/below" relationships
    # Build a graph of vertical relationships
    vertical_graph = {}
    for obj_a, preposition, obj_b in interactions:
        if preposition in ['above', 'below', 'on', 'under']:
            if obj_a not in vertical_graph:
                vertical_graph[obj_a] = []
            if obj_b not in vertical_graph:
                vertical_graph[obj_b] = []
            
            if preposition in ['above', 'on']:
                vertical_graph[obj_a].append(('above', obj_b))
                vertical_graph[obj_b].append(('below', obj_a))
            elif preposition in ['below', 'under']:
                vertical_graph[obj_a].append(('below', obj_b))
                vertical_graph[obj_b].append(('above', obj_a))
    
    # Detect cycles using DFS
    def has_cycle(graph, start, visited, rec_stack):
        visited.add(start)
        rec_stack.add(start)
        
        for _, neighbor in graph.get(start, []):
            if neighbor not in visited:
                if has_cycle(graph, neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(start)
        return False
    
    visited = set()
    for node in vertical_graph:
        if node not in visited:
            if has_cycle(vertical_graph, node, visited, set()):
                contradictions.append("Cycle detected in vertical relationships")
                break
    
    # Check for direct contradictions (A above B AND B above A)
    for obj_a, preposition_a, obj_b in interactions:
        for obj_c, preposition_c, obj_d in interactions:
            if obj_a == obj_d and obj_b == obj_c:
                if (preposition_a in ['above', 'on'] and preposition_c in ['above', 'on']) or \
                   (preposition_a in ['below', 'under'] and preposition_c in ['below', 'under']):
                    contradictions.append(f"Direct contradiction: {obj_a} {preposition_a} {obj_b} AND {obj_c} {preposition_c} {obj_d}")
    
    if contradictions:
        constraint.is_valid = False
        constraint.contradiction_reason = "; ".join(contradictions)
        logger.warning(f"Contradictions found for scene {scene_id}: {constraint.contradiction_reason}")
    else:
        logger.info(f"No contradictions found for scene {scene_id}")
    
    return constraint

def update_contradiction_log(constraint: PhysicsConstraint, log_path: str):
    """
    Update the contradiction log file with the results of a scene simulation.
    If the scene has contradictions, it is marked as "Invalid Physics Rules".
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log or create new one
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    else:
        log_data = {
            "contradictions": [],
            "total_scenes": 0,
            "contradiction_count": 0,
            "log_entries": []
        }
    
    # Update total scenes
    log_data["total_scenes"] += 1
    
    # Add entry
    entry = {
        "scene_id": constraint.scene_id,
        "is_valid": constraint.is_valid,
        "contradiction_reason": constraint.contradiction_reason,
        "timestamp": str(Path(log_path).stat().st_mtime) if log_path.exists() else "new"
    }
    log_data["log_entries"].append(entry)
    
    # If invalid, add to contradictions list
    if not constraint.is_valid:
        log_data["contradiction_count"] += 1
        log_data["contradictions"].append({
            "scene_id": constraint.scene_id,
            "reason": constraint.contradiction_reason
        })
    
    # Calculate contradiction rate
    if log_data["total_scenes"] > 0:
        rate = log_data["contradiction_count"] / log_data["total_scenes"]
        log_data["contradiction_rate"] = rate
        logger.info(f"Current contradiction rate: {rate:.2%} ({log_data['contradiction_count']}/{log_data['total_scenes']})")
    
    # Write back
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)

def run_physics_simulation(csv_path: str, output_dir: str, log_path: str):
    """
    Run physics simulation for all scenes in a CSV file.
    Outputs JSON constraints and updates the contradiction log.
    """
    scenes = load_scene_descriptions(csv_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure log path is in the correct directory
    log_path = Path(log_path)
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize log if it doesn't exist
    if not log_path.exists():
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump({
                "contradictions": [],
                "total_scenes": 0,
                "contradiction_count": 0,
                "log_entries": []
            }, f, indent=2)
    
    for scene in scenes:
        scene_id = scene['scene_id']
        description = scene['description']
        
        logger.info(f"Processing scene {scene_id}: {description}")
        
        try:
            interactions = parse_scene_description(description)
            constraint = simulate_physics(scene_id, interactions)
            
            # Save individual constraint file
            constraint_file = output_path / f"{scene_id}.json"
            with open(constraint_file, 'w', encoding='utf-8') as f:
                json.dump(constraint.to_dict(), f, indent=2)
            
            # Update contradiction log
            update_contradiction_log(constraint, str(log_path))
            
            logger.info(f"Completed simulation for scene {scene_id}")
            
        except Exception as e:
            logger.error(f"Error processing scene {scene_id}: {str(e)}")
            # Log as invalid
            error_constraint = PhysicsConstraint(scene_id)
            error_constraint.is_valid = False
            error_constraint.contradiction_reason = f"Simulation error: {str(e)}"
            update_contradiction_log(error_constraint, str(log_path))
    
    logger.info(f"Physics simulation complete. Output directory: {output_dir}")
    logger.info(f"Contradiction log updated: {log_path}")

def main():
    """Main entry point for the physics simulation engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run physics simulation on scene descriptions.')
    parser.add_argument('--input', type=str, required=True, help='Path to scene descriptions CSV')
    parser.add_argument('--output', type=str, default='data/derived/physics_constraints', help='Output directory for constraints')
    parser.add_argument('--log', type=str, default='data/derived/physics_constraints/contradiction_log.json', help='Path to contradiction log file')
    
    args = parser.parse_args()
    
    run_physics_simulation(args.input, args.output, args.log)

if __name__ == '__main__':
    main()
