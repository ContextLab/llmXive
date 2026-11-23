"""
code/data/generator.py

Implements synthetic data generation for the llmXive benchmark.
Generates Test Set (T005) and Warm-up Set (T005a).
"""
import json
import os
import random
import hashlib
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Constants for domains and steps
DOMAINS = ["Physics", "Chemistry", "Biology"]
STEP_COUNTS = [1, 2, 3, 4, 5]
BASE_SEED_TEST = 2509
BASE_SEED_WARMUP = 1000
TEST_SET_SIZE = 500
WARMUP_SET_SIZE = 100

def generate_random_float(seed: int, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Generate a random float based on a seed."""
    random.seed(seed)
    return random.uniform(min_val, max_val)

def generate_random_int(seed: int, min_val: int, max_val: int) -> int:
    """Generate a random integer based on a seed."""
    random.seed(seed)
    return random.randint(min_val, max_val)

def calculate_ground_truth(prompt: str, steps: int, seed: int) -> str:
    """
    Calculate a deterministic ground truth string based on prompt, steps, and seed.
    This simulates a scientific calculation result.
    """
    # Create a deterministic hash based on inputs
    data_str = f"{prompt}:{steps}:{seed}"
    hash_obj = hashlib.sha256(data_str.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Simulate a scientific value (e.g., a float) derived from the hash
    # Take first 8 hex chars and convert to a float
    val_int = int(hash_hex[:8], 16)
    scientific_value = (val_int % 10000) / 100.0
    
    return f"Result: {scientific_value:.4f} (steps={steps})"

def generate_query(seed: int, domain: str, steps: int) -> Dict[str, Any]:
    """Generate a single synthetic query object."""
    # Generate a prompt template based on domain
    templates = {
        "Physics": [
            "Calculate the kinetic energy of a {mass}kg object moving at {velocity}m/s.",
            "Determine the force required to accelerate a {mass}kg mass at {acceleration}m/s².",
            "Find the wavelength of light with frequency {frequency}Hz."
        ],
        "Chemistry": [
            "Balance the reaction: H2 + O2 -> H2O with coefficients {c1}, {c2}, {c3}.",
            "Calculate the molar mass of a compound with elements {elements}.",
            "Determine the pH of a solution with concentration {concentration}M."
        ],
        "Biology": [
            "Calculate the population growth rate given initial {initial} and growth {rate}.",
            "Determine the number of cells after {divisions} divisions starting with {initial}.",
            "Calculate the metabolic rate for an organism of mass {mass}kg."
        ]
    }
    
    template = random.Random(seed).choice(templates[domain])
    
    # Generate parameter values
    params = {}
    if "{mass}" in template:
        params["mass"] = generate_random_int(seed, 1, 100)
    if "{velocity}" in template:
        params["velocity"] = generate_random_int(seed, 10, 100)
    if "{acceleration}" in template:
        params["acceleration"] = generate_random_int(seed, 1, 20)
    if "{frequency}" in template:
        params["frequency"] = generate_random_int(seed, 100, 10000)
    if "{c1}" in template:
        params["c1"], params["c2"], params["c3"] = generate_random_int(seed, 1, 5), generate_random_int(seed+1, 1, 5), generate_random_int(seed+2, 1, 5)
    if "{elements}" in template:
        params["elements"] = "C, H, O"
    if "{concentration}" in template:
        params["concentration"] = generate_random_float(seed, 0.01, 1.0)
    if "{initial}" in template:
        params["initial"] = generate_random_int(seed, 10, 1000)
    if "{rate}" in template:
        params["rate"] = generate_random_float(seed, 0.01, 0.1)
    if "{divisions}" in template:
        params["divisions"] = generate_random_int(seed, 3, 10)
    
    # Format prompt
    prompt = template.format(**params)
    
    # Calculate ground truth
    ground_truth = calculate_ground_truth(prompt, steps, seed)
    
    return {
        "prompt": prompt,
        "ground_truth": ground_truth,
        "steps": steps,
        "seed": seed,
        "domain": domain
    }

def generate_dataset(
    base_seed: int, 
    size: int, 
    output_path: str, 
    domain_distribution: Optional[List[str]] = None,
    step_distribution: Optional[List[int]] = None
) -> None:
    """
    Generate a dataset of synthetic queries and save to JSON.
    
    Args:
        base_seed: Starting seed for random number generation.
        size: Number of queries to generate.
        output_path: Path to save the JSON file.
        domain_distribution: List of domains to use. Defaults to DOMAINS.
        step_distribution: List of step counts to use. Defaults to STEP_COUNTS.
    """
    domains = domain_distribution if domain_distribution else DOMAINS
    steps = step_distribution if step_distribution else STEP_COUNTS
    
    queries = []
    
    # Ensure we have a deterministic way to distribute domains and steps
    # For warmup, we want equal distribution. For test, we can be random but stratified.
    
    for i in range(size):
        current_seed = base_seed + i
        
        # Determine domain and steps
        if len(domains) == 1:
            domain = domains[0]
        else:
            # Stratified sampling: cycle through domains
            domain = domains[i % len(domains)]
        
        if len(steps) == 1:
            step = steps[0]
        else:
            # Stratified sampling: cycle through steps
            step = steps[i % len(steps)]
        
        query = generate_query(current_seed, domain, step)
        queries.append(query)
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)
    
    print(f"Generated {size} queries for {output_path}")

def generate_test_set(output_path: str = "data/derived/synthetic_queries_test.json") -> None:
    """Generate the Test Set (500 queries)."""
    generate_dataset(
        base_seed=BASE_SEED_TEST,
        size=TEST_SET_SIZE,
        output_path=output_path,
        domain_distribution=DOMAINS,
        step_distribution=STEP_COUNTS
    )

def generate_warmup_set(output_path: str = "data/derived/synthetic_queries_warmup.json") -> None:
    """Generate the Warm-up Set (100 queries) with equal domain/step distribution."""
    generate_dataset(
        base_seed=BASE_SEED_WARMUP,
        size=WARMUP_SET_SIZE,
        output_path=output_path,
        domain_distribution=DOMAINS,
        step_distribution=STEP_COUNTS
    )

def main():
    """Main entry point to generate all datasets."""
    # Generate Test Set
    generate_test_set()
    
    # Generate Warm-up Set
    generate_warmup_set()
    
    print("All datasets generated successfully.")

if __name__ == "__main__":
    main()
