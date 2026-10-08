"""
Prompt engineering module for generating Baseline, Experimental, and Control prompts.
Implements T013 and T013b.
"""
import json
import os
import sys
import csv
import random
import string
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromptEngineError(Exception):
    """Base exception for prompt engine errors."""
    pass

class SceneDescriptionNotFoundError(PromptEngineError):
    """Raised when a scene description is not found."""
    pass

class PhysicsConstraintNotFoundError(PromptEngineError):
    """Raised when physics constraints are not found."""
    pass

def load_scene_descriptions(csv_path: str) -> Dict[str, str]:
    """Load scene descriptions from CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise SceneDescriptionNotFoundError(f"Scene descriptions file not found: {csv_path}")
    
    results = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scene_id = row.get('scene_id', row.get('id', ''))
            description = row.get('description', row.get('text', ''))
            if scene_id and description:
                results[scene_id] = description
    
    return results

def load_physics_constraints(json_dir: str, scene_id: str) -> Optional[Dict]:
    """Load physics constraints for a specific scene."""
    constraint_path = Path(json_dir) / f"{scene_id}.json"
    if not constraint_path.exists():
        return None
    
    with open(constraint_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_physics_constraints(constraints: Dict) -> str:
    """Format physics constraints into natural language."""
    if not constraints:
        return ""
    
    parts = []
    if 'bounding_boxes' in constraints:
        for obj in constraints['bounding_boxes']:
            obj_name = obj.get('name', 'object')
            x, y, w, h = obj.get('x', 0), obj.get('y', 0), obj.get('width', 0), obj.get('height', 0)
            parts.append(f"{obj_name} at position ({x}, {y}) with size ({w}x{h})")
    
    if 'collision_rules' in constraints:
        for rule in constraints['collision_rules']:
            parts.append(f"Collision rule: {rule.get('description', 'N/A')}")
    
    return " | ".join(parts)

def generate_baseline_prompt(scene_description: str, physics_constraints: Dict) -> str:
    """Generate baseline prompt from scene description and physics constraints."""
    constraint_text = format_physics_constraints(physics_constraints)
    if constraint_text:
        return f"{scene_description}. Physics constraints: {constraint_text}"
    return scene_description

def generate_experimental_prompt(scene_description: str, physics_constraints: Dict) -> str:
    """Generate experimental prompt with enhanced physics descriptors."""
    base_prompt = generate_baseline_prompt(scene_description, physics_constraints)
    # Add experimental modifiers
    modifiers = [
        "with precise physical relationships",
        "ensuring realistic object interactions",
        "maintaining spatial consistency",
        "with accurate gravity and collision dynamics"
    ]
    modifier = random.choice(modifiers)
    return f"{base_prompt}, {modifier}"

def generate_control_prompt(scene_description: str, physics_constraints: Dict) -> str:
    """
    Generate control prompt with length-matched random noise descriptor.
    Implements T013b requirement for matched control group.
    """
    # Calculate target length from baseline prompt
    base_prompt = generate_baseline_prompt(scene_description, physics_constraints)
    target_length = len(base_prompt)
    
    # Generate random noise descriptor of similar length
    noise_words = [
        "abstract", "random", "pattern", "texture", "gradient",
        "blur", "noise", "static", "flicker", "distortion",
        "fragment", "pixel", "digital", "synthetic", "artificial"
    ]
    
    noise_parts = []
    current_length = 0
    while current_length < target_length:
        word = random.choice(noise_words)
        noise_parts.append(word)
        current_length += len(word) + 1  # +1 for space
    
    noise_descriptor = " ".join(noise_parts[:20])  # Limit to reasonable length
    noise_descriptor = noise_descriptor[:target_length]
    
    return f"{scene_description}. Control descriptor: {noise_descriptor}"

def write_prompt_file(prompts: Dict[str, str], output_path: str):
    """Write prompts to individual text files."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    for group, prompt in prompts.items():
        if group == 'Control':
            fname = f"{path.stem}_control.txt"
        else:
            fname = f"{path.stem}_{group.lower()}.txt"
        
        fpath = path.parent / fname
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        logger.info(f"Written prompt for {group} to {fpath}")

def run_prompt_engineering(
    scenes_csv: str, 
    physics_dir: str, 
    output_dir: str
):
    """Run prompt engineering for all scenes."""
    # Load scene descriptions
    scenes = load_scene_descriptions(scenes_csv)
    
    for scene_id, description in scenes.items():
        # Load physics constraints
        constraints = load_physics_constraints(physics_dir, scene_id)
        if constraints is None:
            logger.warning(f"No physics constraints for {scene_id}, using description only")
            constraints = {}
        
        # Generate prompts
        prompts = {
            'Baseline': generate_baseline_prompt(description, constraints),
            'Experimental': generate_experimental_prompt(description, constraints),
            'Control': generate_control_prompt(description, constraints)
        }
        
        # Write prompts
        output_path = Path(output_dir) / scene_id
        write_prompt_file(prompts, str(output_path))
    
    logger.info(f"Prompt engineering complete for {len(scenes)} scenes")

def main():
    """Entry point for prompt engineering."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run prompt engineering pipeline")
    parser.add_argument('--scenes', required=True, help='Path to scene descriptions CSV')
    parser.add_argument('--physics-dir', required=True, help='Directory containing physics constraints JSON')
    parser.add_argument('--output-dir', required=True, help='Directory to save generated prompts')
    
    args = parser.parse_args()
    
    run_prompt_engineering(
        scenes_csv=args.scenes,
        physics_dir=args.physics_dir,
        output_dir=args.output_dir
    )

if __name__ == '__main__':
    main()
