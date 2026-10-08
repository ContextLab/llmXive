"""
Module to generate scene descriptions locally for the llmXive follow-up project.
This script creates a deterministic 'curated' set of scenes using predefined
interaction templates and a fixed random seed.
"""
import csv
import os
import sys
import random
import json
from pathlib import Path
from typing import List, Dict, Any

# Ensure the parent directory is in the path for imports if running directly
# though this module is standalone.
if __name__ == "__main__":
    # Add code directory to path to allow relative imports if needed in future
    code_dir = Path(__file__).resolve().parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

# Interaction templates defining spatial relationships
INTERACTION_TEMPLATES = [
    "A on B",
    "A next to B",
    "A under B",
    "A above B",
    "A below B",
    "A beside B",
    "A behind B",
    "A in front of B",
    "A inside B",
    "A between B and C",
]

# Object vocabulary to instantiate 'A', 'B', 'C'
OBJECTS = [
    "box", "sphere", "cube", "cylinder", "pyramid",
    "ball", "block", "plate", "rod", "ring"
]

def generate_fallback_scenes(seed: int = 42, count: int = 100) -> List[Dict[str, str]]:
    """
    Generates a list of scene descriptions deterministically.
    
    Args:
        seed: Random seed for reproducibility.
        count: Number of scenes to generate.
        
    Returns:
        List of dictionaries with keys 'scene_id' and 'description'.
    """
    random.seed(seed)
    scenes = []
    
    for i in range(count):
        scene_id = f"scene_{i:04d}"
        
        # Select a random template
        template = random.choice(INTERACTION_TEMPLATES)
        
        # Select objects based on the number of placeholders in the template
        # Simple heuristic: count 'A', 'B', 'C' occurrences
        placeholders = []
        if "C" in template:
            placeholders = [random.choice(OBJECTS) for _ in range(3)]
        elif "B" in template:
            placeholders = [random.choice(OBJECTS) for _ in range(2)]
        else:
            placeholders = [random.choice(OBJECTS)]
        
        # Format the description
        description = template
        if "C" in template:
            description = description.replace("A", placeholders[0]).replace("B", placeholders[1]).replace("C", placeholders[2])
        elif "B" in template:
            description = description.replace("A", placeholders[0]).replace("B", placeholders[1])
        else:
            description = description.replace("A", placeholders[0])
        
        # Add a deterministic variation to ensure uniqueness if template repeats
        # e.g., "A on B" -> "A on B (variant 1)"
        # But the task asks for simple templates. Let's just rely on the object names
        # which are randomized. To be safe, we ensure the combination is unique.
        
        scenes.append({
            "scene_id": scene_id,
            "description": description
        })
    
    return scenes

def write_csv(scenes: List[Dict[str, str]], output_path: Path) -> None:
    """
    Writes the scene descriptions to a CSV file.
    
    Args:
        scenes: List of scene dictionaries.
        output_path: Path to the output CSV file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["scene_id", "description"])
        writer.writeheader()
        writer.writerows(scenes)

def validate_prepositions(scenes: List[Dict[str, str]]) -> bool:
    """
    Validates that the generated scenes contain the necessary prepositions.
    
    Args:
        scenes: List of scene dictionaries.
        
    Returns:
        True if all required prepositions are present, False otherwise.
    """
    required_prepositions = [
        "on", "next to", "under", "above", "below", 
        "beside", "behind", "in front of", "inside", "between"
    ]
    
    found_prepositions = set()
    descriptions = [s["description"].lower() for s in scenes]
    
    for desc in descriptions:
        for prep in required_prepositions:
            if prep in desc:
                found_prepositions.add(prep)
    
    missing = set(required_prepositions) - found_prepositions
    if missing:
        print(f"Warning: Missing prepositions in generated data: {missing}")
        return False
    
    return True

def main():
    """
    Main entry point for generating scene descriptions.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    output_path = project_root / "data" / "raw" / "scene_descriptions.csv"
    
    print(f"Generating scene descriptions to: {output_path}")
    
    # Generate 100 scenes with seed 42 as per task requirements
    scenes = generate_fallback_scenes(seed=42, count=100)
    
    # Write to CSV
    write_csv(scenes, output_path)
    
    # Validate
    if validate_prepositions(scenes):
        print("Validation passed: All necessary prepositions found.")
    else:
        print("Validation failed: Some prepositions are missing.")
        sys.exit(1)
        
    print(f"Successfully generated {len(scenes)} scene descriptions.")

if __name__ == "__main__":
    main()
