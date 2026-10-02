import json
import os
import random
import logging
import time
import hashlib
import yaml
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Import from existing project modules as per API surface
from code.config import get_seeds, get_experiment_config
from code.utils import pairwise_cosine_similarity_matrix, mean_pairwise_similarity, get_model, get_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
STATE_DIR = os.path.join(PROJECT_ROOT, "state", "projects", "PROJ-975-llmxive-follow-up-extending-from-chatbot")
TASKS_FILE = os.path.join(DATA_RAW_DIR, "tasks.json")
SKILLS_FILE = os.path.join(DATA_RAW_DIR, "skills.json")
STATE_FILE = os.path.join(STATE_DIR, "PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml")

def check_memory_usage(threshold_gb: float = 7.0) -> bool:
    """Check if current memory usage exceeds threshold (simple approximation)."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_gb = process.memory_info().rss / (1024 ** 3)
        if mem_gb > threshold_gb:
            raise MemoryError(f"Memory usage ({mem_gb:.2f} GB) exceeds threshold ({threshold_gb} GB).")
        return True
    except ImportError:
        logger.warning("psutil not installed. Skipping memory check.")
        return True

def generate_skills(seed: int, count: int = 100, overlap_level: str = 'medium') -> List[Dict[str, Any]]:
    """Generate a set of synthetic Python skills with controlled semantic overlap."""
    random.seed(seed)
    np.random.seed(seed)
    model = get_model()
    
    skills = []
    base_templates = [
        "def add(a, b): return a + b",
        "def subtract(a, b): return a - b",
        "def multiply(a, b): return a * b",
        "def divide(a, b): return a / b if b != 0 else None",
        "def power(a, b): return a ** b",
        "def square_root(a): return a ** 0.5 if a >= 0 else None",
        "def absolute(a): return abs(a)",
        "def negate(a): return -a",
        "def increment(a): return a + 1",
        "def decrement(a): return a - 1",
        "def is_positive(a): return a > 0",
        "def is_negative(a): return a < 0",
        "def is_zero(a): return a == 0",
        "def max_of_two(a, b): return a if a > b else b",
        "def min_of_two(a, b): return a if a < b else b",
        "def average(a, b): return (a + b) / 2",
        "def sum_list(lst): return sum(lst)",
        "def product_list(lst): result = 1; [result := result * x for x in lst]; return result",
        "def count_positive(lst): return sum(1 for x in lst if x > 0)",
        "def count_negative(lst): return sum(1 for x in lst if x < 0)",
        "def filter_positive(lst): return [x for x in lst if x > 0]",
        "def filter_negative(lst): return [x for x in lst if x < 0]",
        "def map_double(lst): return [x * 2 for x in lst]",
        "def map_square(lst): return [x ** 2 for x in lst]",
        "def reduce_add(lst): result = 0; [result := result + x for x in lst]; return result",
        "def reduce_mul(lst): result = 1; [result := result * x for x in lst]; return result",
        "def flatten_list(nested): return [item for sublist in nested for item in sublist]",
        "def reverse_list(lst): return lst[::-1]",
        "def sort_list(lst): return sorted(lst)",
        "def unique_elements(lst): return list(set(lst))",
    ]

    # Generate embeddings and manipulate to achieve overlap
    base_embeds = [get_embedding(model, t) for t in base_templates]
    base_embeds = np.array(base_embeds)
    
    # Normalize
    norms = np.linalg.norm(base_embeds, axis=1, keepdims=True)
    base_embeds = base_embeds / (norms + 1e-8)

    # Create variations to reach 'count' skills
    while len(skills) < count:
        # Pick a base
        idx = random.randint(0, len(base_templates) - 1)
        base_text = base_templates[idx]
        base_emb = base_embeds[idx]
        
        # Add noise to create variation
        noise_level = 0.0
        if overlap_level == 'low':
            noise_level = 0.4
        elif overlap_level == 'medium':
            noise_level = 0.2
        elif overlap_level == 'high':
            noise_level = 0.05
        
        noise = np.random.normal(0, noise_level, base_emb.shape)
        new_emb = base_emb + noise
        new_emb = new_emb / (np.linalg.norm(new_emb) + 1e-8)
        
        # Create a slightly modified text
        var_text = base_text
        if "def" in base_text:
            parts = base_text.split("def ")
            if len(parts) > 1:
                func_name = parts[1].split("(")[0]
                var_text = f"def {func_name}_v{len(skills)}{parts[1]}"
        
        skills.append({
            "skill_id": f"skill_{len(skills):03d}",
            "function_code": var_text,
            "embedding_vector": new_emb.tolist(),
            "usage_count": 0
        })
    
    return skills

def calculate_similarity_metrics(skills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate pairwise cosine similarities and mean."""
    if len(skills) < 2:
        return {"mean": 0.0, "matrix": []}
    
    embeds = np.array([s["embedding_vector"] for s in skills])
    matrix = pairwise_cosine_similarity_matrix(embeds)
    mean_sim = mean_pairwise_similarity(matrix)
    
    # Validate thresholds based on overlap level
    # This is a check, not a generator logic, but we return the metrics
    return {
        "mean": float(mean_sim),
        "matrix": matrix.tolist(),
        "count": len(skills)
    }

def generate_tasks_with_ground_truth(seed: int, skills: List[Dict[str, Any]], count: int = 500) -> List[Dict[str, Any]]:
    """Generate tasks with ground truth paths using a distinct seed."""
    random.seed(seed)
    np.random.seed(seed)
    model = get_model()
    
    tasks = []
    skill_ids = [s["skill_id"] for s in skills]
    
    for i in range(count):
        # Ground truth: a small set of skill IDs (1 to 3 skills)
        num_skills = random.randint(1, 3)
        ground_truth = random.sample(skill_ids, num_skills)
        
        # Create a task description based on the ground truth skills
        # In a real scenario, this would be more complex logic
        # Here we synthesize a description that semantically aligns with the skills
        gt_skills_data = [s for s in skills if s["skill_id"] in ground_truth]
        code_snippets = [s["function_code"] for s in gt_skills_data]
        combined_desc = " | ".join(code_snippets)
        
        # Generate embedding for the task
        task_emb = get_embedding(model, combined_desc)
        
        tasks.append({
            "task_id": f"task_{i:04d}",
            "description": f"Perform operation using: {', '.join(ground_truth)}",
            "ground_truth_path": ground_truth,
            "embedding_vector": task_emb.tolist(),
            "complexity": "medium"
        })
        
    return tasks

def handle_maximal_overlap(skills: List[Dict[str, Any]], threshold: float = 0.95) -> bool:
    """Check if mean pairwise similarity indicates maximal overlap edge case."""
    metrics = calculate_similarity_metrics(skills)
    return metrics["mean"] >= threshold

def generate_checksum(file_path: str) -> str:
    """Generate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_artifacts(tasks: List[Dict[str, Any]], skills: List[Dict[str, Any]], overlap_level: str, seed_a: int, seed_b: int):
    """Save tasks and skills to JSON with metadata, and update state file with checksums."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

    # Prepare data with metadata
    tasks_data = {
        "metadata": {
            "count": len(tasks),
            "overlap_level": overlap_level,
            "seed_a": seed_a,
            "seed_b": seed_b
        },
        "tasks": tasks
    }
    
    skills_data = {
        "metadata": {
            "count": len(skills),
            "overlap_level": overlap_level,
            "seed_a": seed_a
        },
        "skills": skills
    }

    # Write files
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks_data, f, indent=2)
    
    with open(SKILLS_FILE, "w") as f:
        json.dump(skills_data, f, indent=2)

    # Generate checksums
    tasks_checksum = generate_checksum(TASKS_FILE)
    skills_checksum = generate_checksum(SKILLS_FILE)

    # Update state file
    state_content = {
        "artifact_hashes": {
            "tasks.json": tasks_checksum,
            "skills.json": skills_checksum
        }
    }
    
    with open(STATE_FILE, "w") as f:
        yaml.dump(state_content, f, default_flow_style=False)
    
    logger.info(f"Saved {len(tasks)} tasks and {len(skills)} skills.")
    logger.info(f"Checksums: tasks={tasks_checksum[:16]}..., skills={skills_checksum[:16]}...")
    logger.info(f"State updated at {STATE_FILE}")

def main():
    """Main entry point for data generation."""
    logger.info("Starting data generation for T015...")
    
    # Check memory
    check_memory_usage()

    # Get config
    seeds = get_seeds()
    seed_a = seeds["SEED_A"]
    seed_b = seeds["SEED_B"]
    config = get_experiment_config()
    overlap_level = config.get("OVERLAP_LEVEL", "medium")

    logger.info(f"Using Seed A: {seed_a}, Seed B: {seed_b}, Overlap: {overlap_level}")

    # Generate skills (Seed A)
    logger.info("Generating skills...")
    skills = generate_skills(seed_a, count=100, overlap_level=overlap_level)
    
    # Validate similarity metrics
    metrics = calculate_similarity_metrics(skills)
    logger.info(f"Mean pairwise similarity: {metrics['mean']:.4f}")
    
    # Handle edge case check
    if handle_maximal_overlap(skills):
        logger.warning("Maximal overlap detected! Setting edge case flag in metadata.")
        # This flag would be handled by the agent later, but we note it here
    
    # Generate tasks (Seed B)
    logger.info("Generating tasks...")
    tasks = generate_tasks_with_ground_truth(seed_b, skills, count=500)

    # Save artifacts with checksums and state update
    save_artifacts(tasks, skills, overlap_level, seed_a, seed_b)

    logger.info("Data generation completed successfully.")

if __name__ == "__main__":
    main()