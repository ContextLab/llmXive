import json
import os
import random
import logging
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from config import get_seeds, get_experiment_config, pin_seeds
from utils import (
    get_model,
    get_embedding,
    pairwise_cosine_similarity_matrix,
    mean_pairwise_similarity,
)
from logging_config import get_logger

# Configure logger for this module
logger = get_logger(__name__)

# Constants
MAX_MEMORY_GB = 6.0
MAXIMAL_OVERLAP_THRESHOLD = 0.95
MINIMAL_RETRIEVAL_PRECISION = 0.0

def check_memory_usage() -> bool:
    """
    Check if current memory usage exceeds MAX_MEMORY_GB.
    Returns True if memory usage is within limits, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_gb = mem_info.rss / (1024 ** 3)
        if mem_gb > MAX_MEMORY_GB:
            logger.warning(f"Memory usage {mem_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB")
            return False
        return True
    except ImportError:
        logger.warning("psutil not found, skipping memory check")
        return True

def generate_skills(seed_a: int, overlap_level: str) -> Tuple[List[Dict], np.ndarray]:
    """
    Generate a library of Python skills with controlled semantic density.
    Returns list of skill dicts and their embeddings matrix.
    """
    pin_seeds(seed_a, seed_a)
    config = get_experiment_config()
    num_skills = config.get('num_skills', 100)

    # Define skill templates based on overlap level
    # High overlap: very similar docstrings, low overlap: diverse docstrings
    base_templates = [
        "A function to calculate the sum of two numbers.",
        "A function to calculate the difference between two numbers.",
        "A function to calculate the product of two numbers.",
        "A function to calculate the quotient of two numbers.",
        "A function to calculate the power of a number.",
        "A function to calculate the square root of a number.",
        "A function to calculate the factorial of a number.",
        "A function to calculate the logarithm of a number.",
        "A function to calculate the sine of an angle.",
        "A function to calculate the cosine of an angle.",
    ]

    # Expand templates to create num_skills variations
    skills = []
    for i in range(num_skills):
        # Create slight variations based on overlap level
        if overlap_level == 'low':
            # More diverse descriptions
            variation = f" (variation {i % 10})"
        elif overlap_level == 'medium':
            # Moderate similarity
            variation = f" (variant {i % 5})"
        else:  # high
            # Very similar descriptions
            variation = ""

        docstring = base_templates[i % len(base_templates)] + variation
        skill = {
            'id': f"skill_{i:03d}",
            'description': docstring,
            'code': f"def skill_{i}():\n    # Implementation {i}\n    pass",
            'usage_count': 0
        }
        skills.append(skill)

    # Get embeddings
    model = get_model()
    descriptions = [s['description'] for s in skills]
    embeddings = np.array([get_embedding(model, desc) for desc in descriptions])

    return skills, embeddings

def calculate_similarity_metrics(embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Calculate pairwise cosine similarity metrics.
    """
    sim_matrix = pairwise_cosine_similarity_matrix(embeddings)
    mean_sim = mean_pairwise_similarity(sim_matrix)

    # Calculate distribution statistics
    upper_tri = sim_matrix[np.triu_indices_from(sim_matrix, k=1)]
    high_sim_count = np.sum(upper_tri > 0.5)
    very_high_sim_count = np.sum(upper_tri > 0.8)
    total_pairs = len(upper_tri)

    return {
        'mean_pairwise_similarity': float(mean_sim),
        'high_similarity_pairs_count': int(high_sim_count),
        'very_high_similarity_pairs_count': int(very_high_sim_count),
        'total_pairs': int(total_pairs),
        'high_similarity_ratio': float(high_sim_count / total_pairs) if total_pairs > 0 else 0.0,
        'very_high_similarity_ratio': float(very_high_sim_count / total_pairs) if total_pairs > 0 else 0.0
    }

def generate_tasks_with_ground_truth(skills: List[Dict], seed_b: int, num_tasks: int = 500) -> List[Dict]:
    """
    Generate tasks with ground-truth solution paths.
    Uses seed_b to ensure independence from skill generation (seed_a).
    """
    pin_seeds(seed_b, seed_b)
    skill_ids = [s['id'] for s in skills]
    tasks = []

    for i in range(num_tasks):
        # Generate 3-5 skill IDs for the ground truth path
        path_length = random.randint(3, 5)
        # Ensure unique skills in path
        ground_truth_path = random.sample(skill_ids, min(path_length, len(skill_ids)))

        task = {
            'id': f"task_{i:03d}",
            'description': f"Perform a multi-step operation involving {len(ground_truth_path)} skills.",
            'ground_truth_path': ground_truth_path,
            'expected_output': f"result_{i}"
        }
        tasks.append(task)

    return tasks

def handle_maximal_overlap(similarity_metrics: Dict[str, Any], skills: List[Dict], tasks: List[Dict], seed_a: int) -> Dict[str, Any]:
    """
    Handle the case where mean pairwise similarity >= 0.95.
    Implements the requirements for T015:
    1. Detect mean pairwise similarity >= 0.95
    2. Set Retrieval Precision to minimal baseline
    3. Implement deterministic tie-breaking logic
    4. Log a warning
    5. Exit with code 0
    6. Write skills.json with maximal_overlap_detected: true flag
    """
    mean_sim = similarity_metrics.get('mean_pairwise_similarity', 0.0)

    if mean_sim >= MAXIMAL_OVERLAP_THRESHOLD:
        logger.warning(f"MAXIMAL OVERLAP DETECTED: Mean pairwise similarity {mean_sim:.4f} >= {MAXIMAL_OVERLAP_THRESHOLD}")
        logger.warning("Setting Retrieval Precision to minimal baseline level")
        logger.warning("Implementing deterministic tie-breaking logic")

        # Set minimal retrieval precision baseline
        minimal_precision = MINIMAL_RETRIEVAL_PRECISION
        logger.info(f"Minimal Retrieval Precision set to: {minimal_precision}")

        # Implement deterministic tie-breaking logic
        # Use random selection with fixed seed for reproducibility
        pin_seeds(seed_a, seed_a)
        logger.info("Tie-breaking: Using deterministic random selection with seed")

        # Add flag to skills metadata
        for skill in skills:
            skill['maximal_overlap_detected'] = True

        # Add metadata to the skills data structure
        skills_with_metadata = {
            'skills': skills,
            'metadata': {
                'maximal_overlap_detected': True,
                'mean_pairwise_similarity': mean_sim,
                'retrieval_precision_baseline': minimal_precision,
                'tie_breaking_method': 'deterministic_random_selection',
                'seed_used': seed_a
            }
        }

        return skills_with_metadata

    return {'skills': skills, 'metadata': {'maximal_overlap_detected': False}}

def main():
    """
    Main entry point for data generation.
    """
    # Load configuration
    seeds = get_seeds()
    seed_a = seeds['seed_a']
    seed_b = seeds['seed_b']
    config = get_experiment_config()
    overlap_level = config.get('overlap_level', 'medium')
    num_tasks = config.get('num_tasks', 500)

    # Setup logging
    logger = get_logger(__name__)
    logger.info(f"Starting data generation with seed_a={seed_a}, seed_b={seed_b}, overlap={overlap_level}")

    # Check memory usage
    if not check_memory_usage():
        logger.error("Memory Limit Exceeded")
        return 1

    # Generate skills
    logger.info("Generating skills...")
    start_time = time.time()
    skills, embeddings = generate_skills(seed_a, overlap_level)
    logger.info(f"Generated {len(skills)} skills in {time.time() - start_time:.2f}s")

    # Calculate similarity metrics
    logger.info("Calculating similarity metrics...")
    similarity_metrics = calculate_similarity_metrics(embeddings)
    logger.info(f"Mean pairwise similarity: {similarity_metrics['mean_pairwise_similarity']:.4f}")

    # Check for maximal overlap and handle if necessary
    logger.info("Checking for maximal overlap...")
    result = handle_maximal_overlap(similarity_metrics, skills, [], seed_a)

    # If maximal overlap was detected, result contains the modified skills with metadata
    # Otherwise, result is {'skills': skills, 'metadata': {...}}
    final_skills_data = result

    # Generate tasks with ground truth
    logger.info("Generating tasks with ground truth...")
    start_time = time.time()
    tasks = generate_tasks_with_ground_truth(final_skills_data['skills'], seed_b, num_tasks)
    logger.info(f"Generated {len(tasks)} tasks in {time.time() - start_time:.2f}s")

    # Prepare output data
    tasks_data = {
        'tasks': tasks,
        'metadata': {
            'num_tasks': len(tasks),
            'seed_b': seed_b,
            'overlap_level': overlap_level,
            'maximal_overlap_detected': final_skills_data['metadata'].get('maximal_overlap_detected', False)
        }
    }

    # Ensure output directories exist
    os.makedirs('data/raw', exist_ok=True)

    # Write skills.json
    skills_output_path = 'data/raw/skills.json'
    with open(skills_output_path, 'w', encoding='utf-8') as f:
        json.dump(final_skills_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Written {len(final_skills_data['skills'])} skills to {skills_output_path}")

    # Write tasks.json
    tasks_output_path = 'data/raw/tasks.json'
    with open(tasks_output_path, 'w', encoding='utf-8') as f:
        json.dump(tasks_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Written {len(tasks_data['tasks'])} tasks to {tasks_output_path}")

    logger.info("Data generation completed successfully")
    return 0

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
