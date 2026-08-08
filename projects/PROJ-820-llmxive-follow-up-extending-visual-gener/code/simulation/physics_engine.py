"""
Physics Engine Module
Simulates basic physics on CPU using pymunk to generate JSON constraints
and detect logical contradictions in scene descriptions.
"""
import json
import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import pymunk, raise error if not available
try:
    import pymunk
    import pymunk.space_debug_draw_options
except ImportError:
    raise ImportError(
        "pymunk is required for physics simulation. "
        "Install it via: pip install pymunk"
    )


class SceneDescriptionNotFoundError(Exception):
    """Raised when scene description file is not found."""
    pass


class InvalidSceneDescriptionError(Exception):
    """Raised when scene description format is invalid."""
    pass


class SimulationError(Exception):
    """Raised when physics simulation fails."""
    pass


def load_scene_descriptions(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load scene descriptions from a CSV file.

    Args:
        csv_path: Path to the CSV file containing scene descriptions.

    Returns:
        List of dictionaries containing scene data.

    Raises:
        SceneDescriptionNotFoundError: If the file doesn't exist.
        InvalidSceneDescriptionError: If the file format is invalid.
    """
    path = Path(csv_path)
    if not path.exists():
        raise SceneDescriptionNotFoundError(f"Scene description file not found: {csv_path}")

    scenes = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'scene_id' not in row or 'description' not in row:
                    raise InvalidSceneDescriptionError(
                        f"Invalid scene description format: missing required fields. Row: {row}"
                    )
                scenes.append(row)
    except Exception as e:
        raise InvalidSceneDescriptionError(f"Failed to parse CSV file: {e}")

    return scenes


def parse_scene_description(description: str) -> Dict[str, Any]:
    """
    Parse a scene description string into structured data.

    This is a simplified parser that extracts objects and their relationships.
    In a real implementation, this would use NLP or a more sophisticated parser.

    Args:
        description: Natural language scene description.

    Returns:
        Dictionary containing parsed objects and relationships.
    """
    # Simplified parsing logic for demonstration
    # In reality, this would use NLP to extract objects and relationships
    objects = []
    relationships = []

    # Basic tokenization and pattern matching
    words = description.lower().split()

    # Detect common object patterns (simplified)
    common_objects = ['ball', 'box', 'cube', 'sphere', 'block', 'object']
    for i, word in enumerate(words):
        if any(obj in word for obj in common_objects):
            objects.append({
                'id': f"obj_{len(objects)}",
                'type': word.rstrip('s'),  # Remove plural
                'position': [0.0, 0.0]  # Will be set by simulation
            })

    # Detect relationships
    if len(objects) >= 2:
        # Check for "on" relationship
        if 'on' in words:
            idx = words.index('on')
            if idx > 0 and idx < len(words) - 1:
                relationships.append({
                    'type': 'on',
                    'subject': objects[0]['id'],
                    'object': objects[1]['id'] if len(objects) > 1 else None
                })

        # Check for "next to" relationship
        if 'next' in words and 'to' in words:
            relationships.append({
                'type': 'next_to',
                'subject': objects[0]['id'],
                'object': objects[1]['id'] if len(objects) > 1 else None
            })

    return {
        'objects': objects,
        'relationships': relationships
    }


def simulate_physics(parsed_scene: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Run physics simulation on the parsed scene.

    Args:
        parsed_scene: Parsed scene description with objects and relationships.

    Returns:
        Tuple of (simulation_results, list of contradictions).
    """
    contradictions = []
    results = {
        'objects': [],
        'bounding_boxes': [],
        'collisions': []
    }

    if not parsed_scene.get('objects'):
        return results, contradictions

    # Create physics space
    space = pymunk.Space()
    space.gravity = (0.0, -9.81)  # Earth gravity

    # Create ground
    ground = pymunk.Segment(space.static_shape, (0, 0), (1000, 0), 0.5)
    ground.friction = 1.0
    space.add(ground)

    # Create bodies and shapes for each object
    bodies = []
    shapes = []

    for i, obj in enumerate(parsed_scene['objects']):
        # Create dynamic body
        mass = 1.0
        size = 1.0
        moment = pymunk.moment_for_box(mass, size * 2, size * 2)
        body = pymunk.Body(mass, moment)
        body.position = (i * 2.0 + 1.0, 10.0)  # Start above ground
        bodies.append(body)

        # Create shape
        shape = pymunk.Poly.create_box(body, (size * 2, size * 2))
        shape.friction = 0.5
        shape.elasticity = 0.1
        shapes.append(shape)
        space.add(body, shape)

        # Store initial info
        results['objects'].append({
            'id': obj['id'],
            'type': obj['type'],
            'initial_position': list(body.position)
        })

    # Apply relationships
    for rel in parsed_scene.get('relationships', []):
        if rel['type'] == 'on' and rel['object']:
            # Find the bodies for subject and object
            subject_idx = next(
                (i for i, o in enumerate(parsed_scene['objects']) if o['id'] == rel['subject']),
                None
            )
            object_idx = next(
                (i for i, o in enumerate(parsed_scene['objects']) if o['id'] == rel['object']),
                None
            )

            if subject_idx is not None and object_idx is not None:
                # Place subject on top of object
                if object_idx < len(bodies) and subject_idx < len(bodies):
                    subject_body = bodies[subject_idx]
                    object_body = bodies[object_idx]

                    # Move subject to be on top of object
                    subject_body.position = (
                        object_body.position.x,
                        object_body.position.y + 2.0
                    )

    # Run simulation
    for step in range(100):
        space.step(1/60.0)

    # Collect final results
    for i, body in enumerate(bodies):
        if i < len(parsed_scene['objects']):
          obj_id = parsed_scene['objects'][i]['id']
          # Calculate bounding box (simplified as the body's AABB)
          bb = body.shape.get_aabb()
          results['bounding_boxes'].append({
              'id': obj_id,
              'x': bb[0][0],
              'y': bb[0][1],
              'width': bb[1][0] - bb[0][0],
              'height': bb[1][1] - bb[0][1]
          })

    # Check for contradictions
    # Example: Check if objects are overlapping when they shouldn't be
    for i, shape1 in enumerate(shapes):
        for j, shape2 in enumerate(shapes):
            if i < j:
                # Check for collision
                if shape1.aabb.intersects(shape2.aabb):
                    obj1_id = parsed_scene['objects'][i]['id'] if i < len(parsed_scene['objects']) else f"obj_{i}"
                    obj2_id = parsed_scene['objects'][j]['id'] if j < len(parsed_scene['objects']) else f"obj_{j}"
                    contradictions.append(f"Unexpected overlap between {obj1_id} and {obj2_id}")

    return results, contradictions


def update_contradiction_log(log_path: str, scene_id: str, contradictions: List[str]) -> None:
    """
    Update the contradiction log with results for a scene.

    Args:
        log_path: Path to the contradiction log JSON file.
        scene_id: ID of the current scene.
        contradictions: List of contradictions found.
    """
    log_data = {'contradictions': []}

    # Load existing log if it exists
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = {'contradictions': []}

    # Add new contradictions
    for contradiction in contradictions:
        log_data['contradictions'].append({
            'scene_id': scene_id,
            'contradiction': contradiction
        })

    # Write updated log
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)


def run_physics_simulation(
    csv_path: str,
    output_dir: str,
    log_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run physics simulation on all scenes in the CSV file.

    Args:
        csv_path: Path to the scene descriptions CSV.
        output_dir: Directory to save output JSON files.
        log_path: Optional path to the contradiction log file.

    Returns:
        Summary statistics of the simulation run.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load scenes
    scenes = load_scene_descriptions(csv_path)

    stats = {
        'total_scenes': len(scenes),
        'successful_simulations': 0,
        'failed_simulations': 0,
        'total_contradictions': 0
    }

    for scene in scenes:
        scene_id = scene['scene_id']
        description = scene['description']

        try:
            # Parse scene
            parsed = parse_scene_description(description)

            # Run simulation
            results, contradictions = simulate_physics(parsed)

            # Save results
            output_file = output_path / f"{scene_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scene_id': scene_id,
                    'description': description,
                    'physics_constraints': results,
                    'contradictions': contradictions
                }, f, indent=2)

            # Update contradiction log
            if log_path and contradictions:
                update_contradiction_log(log_path, scene_id, contradictions)

            stats['successful_simulations'] += 1
            stats['total_contradictions'] += len(contradictions)

            logger.info(f"Successfully simulated scene {scene_id}: {len(contradictions)} contradictions")

        except Exception as e:
            stats['failed_simulations'] += 1
            logger.error(f"Failed to simulate scene {scene_id}: {e}")

    return stats


def main():
    """Main entry point for the physics engine script."""
    import argparse

    parser = argparse.ArgumentParser(description='Run physics simulation on scene descriptions.')
    parser.add_argument('--input', '-i', required=True, help='Path to input CSV file')
    parser.add_argument('--output', '-o', required=True, help='Path to output directory')
    parser.add_argument('--log', '-l', default='data/derived/physics_constraints/contradiction_log.json',
                        help='Path to contradiction log file')

    args = parser.parse_args()

    logger.info(f"Starting physics simulation with input: {args.input}")

    try:
        stats = run_physics_simulation(args.input, args.output, args.log)
        logger.info(f"Simulation complete. Stats: {stats}")
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()