"""
Script to generate data/raw/scene_descriptions.csv with N=100 scene descriptions.
Attempts to fetch from a real source (COCO Captions) and filters for object interactions.
Falls back to a deterministic template-based generator if the fetch fails.
"""
import csv
import os
import sys
import random
from pathlib import Path

# Ensure the code/utils directory is in the path if running as a script
# but rely on standard imports when run via the project structure
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

OUTPUT_PATH = "data/raw/scene_descriptions.csv"
TARGET_COUNT = 100
RANDOM_SEED = 42

# Predefined interaction templates for fallback generation
# Format: "A [preposition] B" or "A [verb] B"
INTERACTION_TEMPLATES = [
    "A {obj1} on top of a {obj2}",
    "{obj1} next to {obj2}",
    "{obj1} behind {obj2}",
    "{obj1} in front of {obj2}",
    "{obj1} above {obj2}",
    "{obj1} below {obj2}",
    "{obj1} inside {obj2}",
    "{obj1} outside {obj2}",
    "{obj1} touching {obj2}",
    "{obj1} colliding with {obj2}",
    "A {obj1} leaning against {obj2}",
    "{obj1} hanging from {obj2}",
    "{obj1} resting on {obj2}",
    "{obj1} supported by {obj2}",
    "{obj1} under {obj2}",
    "{obj1} over {obj2}",
    "A {obj1} beside {obj2}",
    "{obj1} near {obj2}",
    "{obj1} far from {obj2}",
    "{obj1} between {obj2} and {obj3}",
    "A {obj1} holding {obj2}",
    "{obj1} carrying {obj2}",
    "{obj1} pushing {obj2}",
    "{obj1} pulling {obj2}",
    "{obj1} dropping {obj2}",
    "{obj1} catching {obj2}",
    "{obj1} throwing {obj2}",
    "{obj1} hitting {obj2}",
    "{obj1} kicking {obj2}",
    "{obj1} jumping on {obj2}",
]

OBJECTS = [
    "car", "person", "dog", "cat", "chair", "table", "cup", "bottle",
    "book", "laptop", "phone", "ball", "tree", "dog", "bird", "horse",
    "truck", "bus", "motorcycle", "bicycle", "airplane", "train", "boat",
    "pizza", "apple", "banana", "orange", "cake", "donut", "hot dog",
    "teddy bear", "backpack", "umbrella", "handbag", "tie", "suitcase",
    "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket",
    "mouse", "keyboard", "remote", "cell phone", "microwave", "oven",
    "toaster", "refrigerator", "book", "scissors", "blender", "spoon",
    "fork", "knife", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake"
]

def generate_fallback_scenes(count: int, seed: int) -> list:
    """
    Generates a deterministic list of scene descriptions using templates
    if the real dataset cannot be fetched.
    """
    random.seed(seed)
    scenes = []
    for i in range(count):
        template = random.choice(INTERACTION_TEMPLATES)
        # Replace placeholders with random objects
        # We need to handle {obj1}, {obj2}, {obj3}
        obj1 = random.choice(OBJECTS)
        obj2 = random.choice(OBJECTS)
        obj3 = random.choice(OBJECTS)
        
        # Ensure obj1 and obj2 are different for better variety in interactions
        while obj2 == obj1:
            obj2 = random.choice(OBJECTS)
        
        scene = template.format(obj1=obj1, obj2=obj2, obj3=obj3)
        scenes.append(scene)
    return scenes

def fetch_and_filter_coco(count: int, seed: int) -> list:
    """
    Attempts to fetch object interaction scenes from the COCO Captions dataset.
    Filters for sentences containing spatial prepositions or interaction verbs.
    """
    if not HAS_DATASETS:
        raise ImportError("The 'datasets' library is not installed. "
                        "Install with: pip install datasets")
    
    random.seed(seed)
    print("Attempting to fetch COCO Captions dataset...")
    try:
        # Load a subset of the training data to speed up processing
        # We use streaming to avoid downloading the full dataset if possible
        # but for reliability we load a small split or use streaming with limit
        dataset = load_dataset("coco-captions", split="train", trust_remote_code=True)
        
        # Define keywords that suggest physical interaction or spatial relationship
        spatial_keywords = [
            "on", "in", "at", "by", "near", "next to", "beside", "behind", 
            "front", "above", "below", "under", "over", "between", "among",
            "touching", "holding", "carrying", "sitting", "standing", "lying",
            "leaning", "hanging", "resting", "supported", "colliding", "dropping"
        ]
        
        valid_scenes = []
        total_rows = len(dataset)
        
        # Shuffle indices to get a random sample
        indices = list(range(total_rows))
        random.shuffle(indices)
        
        for idx in indices:
            if len(valid_scenes) >= count:
                break
            
            caption = dataset[idx]['caption'].lower()
            
            # Check if caption contains any spatial/interaction keyword
            if any(kw in caption for kw in spatial_keywords):
                valid_scenes.append(caption)
        
        if len(valid_scenes) < count:
            print(f"Warning: Only found {len(valid_scenes)} valid scenes from COCO. "
                  f"Supplementing with fallback templates.")
            remaining = count - len(valid_scenes)
            fallback_scenes = generate_fallback_scenes(remaining, seed + 1)
            valid_scenes.extend(fallback_scenes)
        
        return valid_scenes

    except Exception as e:
        print(f"Error fetching COCO dataset: {e}")
        print("Falling back to deterministic template generation.")
        return generate_fallback_scenes(count, seed)

def write_csv(scenes: list, output_path: str):
    """Writes the list of scenes to a CSV file."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["scene_id", "description"])
        for i, scene in enumerate(scenes):
            # Clean up scene description: remove newlines, extra spaces
            clean_scene = " ".join(scene.split())
            writer.writerow([f"scene_{i:03d}", clean_scene])
    
    print(f"Successfully wrote {len(scenes)} scenes to {output_path}")

def main():
    """Main entry point for the script."""
    print(f"Starting scene description generation (Target: {TARGET_COUNT})...")
    
    try:
        scenes = fetch_and_filter_coco(TARGET_COUNT, RANDOM_SEED)
        write_csv(scenes, OUTPUT_PATH)
        print("Task T011 completed successfully.")
    except Exception as e:
        print(f"Critical error during T011 execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
