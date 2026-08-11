import json
import os
import random
import hashlib
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Constants for reproducibility
DEFAULT_SEED = 42
RANDOM_DOMAINS = [
    "physics", "biology", "chemistry", "computer_science", 
    "mathematics", "astronomy", "neuroscience", "genetics"
]

def generate_random_float(min_val: float = 0.0, max_val: float = 1.0, seed: int = None) -> float:
    """Generate a random float within a range."""
    if seed is not None:
        random.seed(seed)
    return random.uniform(min_val, max_val)

def generate_random_int(min_val: int = 1, max_val: int = 100, seed: int = None) -> int:
    """Generate a random integer within a range."""
    if seed is not None:
        random.seed(seed)
    return random.randint(min_val, max_val)

def calculate_ground_truth(domain: str, steps: List[str], seed: int) -> str:
    """
    Calculate a deterministic 'ground truth' based on domain, steps, and seed.
    This simulates a complex reasoning result without importing heavy models.
    The logic is epistemologically independent of the EywaOrchestra pipeline.
    """
    # Deterministic hashing based on inputs
    input_str = f"{domain}:{':'.join(steps)}:{seed}"
    hash_obj = hashlib.sha256(input_str.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Create a pseudo-deterministic "result" string
    # We use the hash to select specific scientific-sounding terms
    terms = [
        "quantum", "neural", "molecular", "algorithmic", "topological",
        "entropic", "kinetic", "gravitational", "electromagnetic", "biological"
    ]
    
    result_parts = []
    for i in range(3):
        idx = (int(hash_hex[i*4:(i*4)+4], 16)) % len(terms)
        result_parts.append(terms[idx])
    
    return f"Result: {'-'.join(result_parts)} (Seed: {seed})"

def generate_query(index: int, domain: str, seed: int) -> Dict[str, Any]:
    """
    Generate a single synthetic benchmark query.
    Schema: { "prompt", "ground_truth", "steps", "seed", "domain" }
    """
    # Create a deterministic seed for this specific query
    query_seed = seed + index
    random.seed(query_seed)
    
    # Generate steps (simulating a reasoning chain)
    num_steps = generate_random_int(2, 5, query_seed)
    steps = []
    step_templates = [
        "Analyze the initial conditions of {domain} system.",
        "Identify the key variables affecting the outcome.",
        "Apply the relevant theoretical framework.",
        "Simulate the interaction between components.",
        "Validate the results against known constraints.",
        "Derive the final conclusion from the intermediate states."
    ]
    
    for i in range(num_steps):
        template = step_templates[i % len(step_templates)]
        steps.append(template.format(domain=domain))
    
    prompt = f"Please solve the following {domain} problem: {' '.join(steps)}"
    ground_truth = calculate_ground_truth(domain, steps, query_seed)
    
    return {
        "prompt": prompt,
        "ground_truth": ground_truth,
        "steps": steps,
        "seed": query_seed,
        "domain": domain
    }

def generate_dataset(num_queries: int, output_path: str, seed: int = DEFAULT_SEED, dataset_type: str = "general") -> None:
    """
    Generate a dataset of synthetic queries and save to JSON.
    
    Args:
        num_queries: Number of queries to generate.
        output_path: Path to save the JSON file.
        seed: Base seed for reproducibility.
        dataset_type: Type of dataset (e.g., 'test', 'warmup').
    """
    if not output_path.endswith('.json'):
        output_path = f"{output_path}.json"
        
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    queries = []
    base_seed = seed
    
    for i in range(num_queries):
        # Rotate through domains to ensure diversity
        domain = RANDOM_DOMAINS[i % len(RANDOM_DOMAINS)]
        
        # Add some randomness to the seed per query but keep it deterministic
        query_seed = base_seed + i
        
        query_data = generate_query(i, domain, query_seed)
        queries.append(query_data)
        
        # Log progress for large datasets
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1}/{num_queries} queries...")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(queries, f, indent=2)
        
    print(f"Successfully generated {num_queries} queries for '{dataset_type}' set to {output_path}")

def main():
    """
    Main entry point to generate datasets.
    This function is called by the pipeline or can be run directly.
    """
    # Define output paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "derived"
    
    # T005: Test Set (500 queries)
    test_output = data_dir / "synthetic_queries_test.json"
    generate_dataset(
        num_queries=500,
        output_path=str(test_output),
        seed=42,
        dataset_type="test"
    )
    
    # T005a: Warm-up Set (100 queries)
    warmup_output = data_dir / "synthetic_queries_warmup.json"
    generate_dataset(
        num_queries=100,
        output_path=str(warmup_output),
        seed=123, # Distinct seed for warmup set
        dataset_type="warmup"
    )

if __name__ == "__main__":
    main()