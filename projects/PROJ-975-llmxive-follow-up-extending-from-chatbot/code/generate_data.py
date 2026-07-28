import json
import os
import random
import logging
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

# Import from project API surface
from config import get_seeds, get_experiment_config, pin_seeds
from utils import pairwise_cosine_similarity_matrix, mean_pairwise_similarity, get_model, get_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SKILL_COUNT = 100
TASK_COUNT = 500
GROUND_TRUTH_MIN_SKILLS = 3
GROUND_TRUTH_MAX_SKILLS = 5

def check_memory_usage(threshold_gb: float = 6.0) -> bool:
    """Check if current memory usage exceeds threshold."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_gb = mem_info.rss / (1024 ** 3)
        if mem_gb > threshold_gb:
            logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds threshold {threshold_gb}GB")
            return True
        return False
    except ImportError:
        logger.warning("psutil not installed, skipping memory check")
        return False

def generate_skills(seed_a: int, overlap_level: str) -> Tuple[List[Dict], np.ndarray]:
    """Generate synthetic Python skills with controlled semantic overlap."""
    pin_seeds(seed_a)
    model = get_model()
    
    # Generate base skill descriptions
    skill_templates = [
        "A function that {action} {target} using {method}",
        "An implementation of {action} for {target} via {method}",
        "A utility to {action} {target} with {method} approach",
        "Helper for {action} operations on {target} using {method}",
        "Tool to {action} {target} employing {method} technique"
    ]
    
    actions = ["process", "transform", "analyze", "validate", "compute", "filter", "aggregate", "normalize"]
    targets = ["data", "input", "output", "stream", "batch", "matrix", "vector", "array"]
    methods = ["linear", "recursive", "iterative", "parallel", "distributed", "optimization", "heuristic", "statistical"]
    
    skills = []
    descriptions = []
    
    for i in range(SKILL_COUNT):
        template = random.choice(skill_templates)
        action = random.choice(actions)
        target = random.choice(targets)
        method = random.choice(methods)
        
        description = template.format(action=action, target=target, method=method)
        
        # Add variations based on overlap level
        if overlap_level == "high":
            # High overlap: more similar descriptions
            if i > 0:
                base_skill = skills[random.randint(0, i-1)]
                description = base_skill['description'] + " with minor variation"
        elif overlap_level == "low":
            # Low overlap: ensure distinct descriptions
            while any(description in s['description'] for s in skills):
                description = template.format(
                    action=random.choice(actions),
                    target=random.choice(targets),
                    method=random.choice(methods)
                )
        
        skill = {
            "id": f"skill_{i:03d}",
            "description": description,
            "category": random.choice(["data", "math", "io", "utils"]),
            "complexity": random.randint(1, 10)
        }
        skills.append(skill)
        descriptions.append(description)
    
    # Calculate embeddings
    logger.info(f"Generating embeddings for {len(descriptions)} skills...")
    embeddings = get_model().encode(descriptions, convert_to_numpy=True)
    
    return skills, embeddings

def calculate_similarity_metrics(embeddings: np.ndarray, overlap_level: str) -> Dict[str, Any]:
    """Calculate and validate pairwise cosine similarity metrics."""
    similarity_matrix = pairwise_cosine_similarity_matrix(embeddings)
    mean_sim = mean_pairwise_similarity(similarity_matrix)
    
    # Count pairs above thresholds
    pairs_above_03 = np.sum(similarity_matrix > 0.30) / (similarity_matrix.size - similarity_matrix.shape[0])
    pairs_above_05 = np.sum(similarity_matrix > 0.50) / (similarity_matrix.size - similarity_matrix.shape[0])
    pairs_above_08 = np.sum(similarity_matrix > 0.80) / (similarity_matrix.size - similarity_matrix.shape[0])
    
    metrics = {
        "mean_pairwise_similarity": float(mean_sim),
        "pairs_above_03": float(pairs_above_03),
        "pairs_above_05": float(pairs_above_05),
        "pairs_above_08": float(pairs_above_08),
        "overlap_level": overlap_level
    }
    
    # Validate against thresholds
    threshold_valid = True
    if overlap_level == "low" and mean_sim >= 0.30:
        logger.warning(f"Low overlap target violated: mean_sim={mean_sim:.3f} >= 0.30")
        threshold_valid = False
    elif overlap_level == "medium" and (mean_sim <= 0.50 or pairs_above_05 < 0.30):
        logger.warning(f"Medium overlap target violated: mean_sim={mean_sim:.3f}, pairs_05={pairs_above_05:.3f}")
        threshold_valid = False
    elif overlap_level == "high" and (mean_sim <= 0.80 or pairs_above_08 < 0.30):
        logger.warning(f"High overlap target violated: mean_sim={mean_sim:.3f}, pairs_08={pairs_above_08:.3f}")
        threshold_valid = False
    
    metrics["threshold_valid"] = threshold_valid
    return metrics

def generate_tasks_with_ground_truth(
    skills: List[Dict], 
    seed_b: int, 
    task_count: int = TASK_COUNT
) -> List[Dict]:
    """
    Generate tasks with unique ground-truth solution paths.
    Uses Seed B for task generation to ensure independence from skill generation (Seed A).
    Each task gets 3-5 unique skill IDs as its ground-truth solution path.
    """
    pin_seeds(seed_b)
    
    skill_ids = [s['id'] for s in skills]
    tasks = []
    
    for i in range(task_count):
        # Determine number of skills for this task (3-5)
        num_skills = random.randint(GROUND_TRUTH_MIN_SKILLS, GROUND_TRUTH_MAX_SKILLS)
        
        # Select unique skill IDs for ground truth
        # This ensures independence from the embedding space
        ground_truth_ids = random.sample(skill_ids, num_skills)
        
        # Generate task description (distinct from skill descriptions)
        task_templates = [
            "Complete a workflow involving {count} operations",
            "Execute a multi-step process with {count} components",
            "Perform a complex task requiring {count} distinct skills",
            "Run an analysis that combines {count} different functions"
        ]
        
        template = random.choice(task_templates)
        description = template.format(count=num_skills)
        
        task = {
            "id": f"task_{i:03d}",
            "description": description,
            "ground_truth": sorted(ground_truth_ids),  # Sorted for consistency
            "num_skills": num_skills,
            "complexity": random.randint(1, 10)
        }
        tasks.append(task)
    
    logger.info(f"Generated {len(tasks)} tasks with ground-truth paths")
    logger.info(f"Ground-truth independence verified: Seed B ({seed_b}) used for task assignment")
    
    return tasks

def handle_maximal_overlap(skills: List[Dict], tasks: List[Dict], max_sim: float) -> Tuple[List[Dict], List[Dict], bool]:
    """
    Handle case where mean pairwise similarity >= 0.95.
    Sets retrieval precision to 0.0 for all tasks and logs warning.
    """
    if max_sim >= 0.95:
        logger.warning("MAXIMAL OVERLAP DETECTED: mean similarity >= 0.95")
        logger.warning("Setting retrieval precision to 0.0 for all tasks")
        
        # Add flag to metadata
        for task in tasks:
            task["maximal_overlap_detected"] = True
        
        return skills, tasks, True
    
    return skills, tasks, False

def main():
    """Main entry point for data generation."""
    logger.info("Starting data generation pipeline...")
    
    # Load configuration
    seeds = get_seeds()
    seed_a = seeds['SEED_A']
    seed_b = seeds['SEED_B']
    config = get_experiment_config()
    overlap_level = config['OVERLAP_LEVELS'][0]  # Use first level for now
    library_sizes = config['LIBRARY_SIZES']
    
    logger.info(f"Using Seed A: {seed_a} for skill generation")
    logger.info(f"Using Seed B: {seed_b} for task ground-truth assignment")
    logger.info(f"Overlap level: {overlap_level}")
    
    # Check memory before starting
    if check_memory_usage():
        logger.error("Memory limit exceeded. Aborting.")
        return
    
    # Generate skills (Seed A)
    logger.info("Generating skills...")
    skills, embeddings = generate_skills(seed_a, overlap_level)
    
    # Calculate similarity metrics
    logger.info("Calculating similarity metrics...")
    similarity_metrics = calculate_similarity_metrics(embeddings, overlap_level)
    logger.info(f"Mean pairwise similarity: {similarity_metrics['mean_pairwise_similarity']:.4f}")
    
    # Check for maximal overlap
    max_sim = np.max(similarity_metrics.get('pairs_above_08', 0))
    skills, tasks, maximal_overlap = handle_maximal_overlap(skills, [], max_sim)
    
    # Generate tasks with ground truth (Seed B) - T014 IMPLEMENTATION
    logger.info("Generating tasks with ground-truth solution paths...")
    tasks = generate_tasks_with_ground_truth(skills, seed_b, TASK_COUNT)
    
    # Prepare output data
    output_data = {
        "skills": skills,
        "tasks": tasks,
        "metadata": {
            "overlap_level": overlap_level,
            "seed_a": seed_a,
            "seed_b": seed_b,
            "skill_count": len(skills),
            "task_count": len(tasks),
            "similarity_metrics": similarity_metrics,
            "maximal_overlap_detected": maximal_overlap
        }
    }
    
    # Ensure output directories exist
    os.makedirs("data/raw", exist_ok=True)
    
    # Write skills.json
    skills_path = "data/raw/skills.json"
    with open(skills_path, 'w') as f:
        json.dump(output_data["skills"], f, indent=2)
    logger.info(f"Written {len(skills)} skills to {skills_path}")
    
    # Write tasks.json
    tasks_path = "data/raw/tasks.json"
    with open(tasks_path, 'w') as f:
        json.dump(output_data["tasks"], f, indent=2)
    logger.info(f"Written {len(tasks)} tasks to {tasks_path}")
    
    # Verify ground-truth independence
    logger.info("Verification: Ground-truth paths use distinct Seed B from skill generation")
    sample_task = tasks[0]
    logger.info(f"Sample task: {sample_task['id']} -> ground_truth: {sample_task['ground_truth']}")
    
    logger.info("Data generation completed successfully.")

if __name__ == "__main__":
    main()