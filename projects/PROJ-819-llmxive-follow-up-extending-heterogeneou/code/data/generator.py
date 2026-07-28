import json
import os
import random
import hashlib
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configuration for dataset generation
TEST_SET_SIZE = 500
WARMUP_SET_SIZE = 100
TEST_SET_PATH = Path("data/derived/synthetic_queries_test.json")
WARMUP_SET_PATH = Path("data/derived/synthetic_queries_warmup.json")

# Domain definitions for epistemologically independent synthetic generation
DOMAINS = [
    "physics",
    "chemistry",
    "biology",
    "mathematics",
    "computer_science"
]

# Seed for reproducibility
RANDOM_SEED = 42

def generate_random_float(min_val: float = 0.0, max_val: float = 100.0, seed: Optional[int] = None) -> float:
    """Generate a random float within a specified range."""
    if seed is not None:
        random.seed(seed)
    return random.uniform(min_val, max_val)

def generate_random_int(min_val: int = 1, max_val: int = 100, seed: Optional[int] = None) -> int:
    """Generate a random integer within a specified range."""
    if seed is not None:
        random.seed(seed)
    return random.randint(min_val, max_val)

def calculate_ground_truth(domain: str, steps: List[str], seed: int) -> str:
    """
    Calculate a deterministic ground truth based on domain, steps, and seed.
    This function simulates a 'correct' answer derived from the problem steps
    without relying on the EywaOrchestra pipeline logic.
    """
    # Deterministic seed for ground truth generation
    random.seed(seed)
    
    # Generate a deterministic "answer" based on the inputs
    # This ensures the ground truth is reproducible and independent of the inference engine
    base_value = sum(hashlib.sha256(s.encode()).digest()[0] for s in steps)
    variance = random.randint(-5, 5)
    
    if domain == "mathematics":
        return f"Result: {base_value + variance}"
    elif domain == "physics":
        return f"Solution: {base_value + variance} units"
    elif domain == "chemistry":
        return f"Compound formed: {base_value + variance}"
    elif domain == "biology":
        return f"Outcome: {base_value + variance} cells"
    else:
        return f"Answer: {base_value + variance}"

def generate_query(domain: str, seed: int) -> Dict[str, Any]:
    """
    Generate a single synthetic query object with prompt, ground_truth, steps, seed, and domain.
    """
    # Define prompt templates per domain to ensure variety and independence
    templates = {
        "physics": [
            "Calculate the force acting on an object of mass {mass} kg accelerating at {acc} m/s².",
            "Determine the kinetic energy of a {mass} kg object moving at {vel} m/s.",
            "Find the wavelength of light with frequency {freq} Hz."
        ],
        "chemistry": [
            "Balance the chemical equation for the reaction between {reactant1} and {reactant2}.",
            "Calculate the molar mass of {compound}.",
            "Determine the pH of a solution with concentration {conc} M."
        ],
        "biology": [
            "Explain the process of {process} in {organism}.",
            "Calculate the population growth rate given initial population {pop} and rate {rate}.",
            "Identify the function of {organelle} in a cell."
        ],
        "mathematics": [
            "Solve the quadratic equation ax² + bx + c = 0 where a={a}, b={b}, c={c}.",
            "Calculate the integral of {func} from {lower} to {upper}.",
            "Find the derivative of {func} with respect to x."
        ],
        "computer_science": [
            "Analyze the time complexity of {algorithm} algorithm.",
            "Explain the difference between {concept1} and {concept2}.",
            "Write a function to {task}."
        ]
    }

    if domain not in templates:
        domain = "mathematics"

    template = random.choice(templates[domain])
    
    # Generate random parameters for the template
    params = {
        "mass": generate_random_int(1, 1000, seed),
        "acc": generate_random_float(0.1, 20.0, seed),
        "vel": generate_random_float(1.0, 100.0, seed),
        "freq": generate_random_float(1e14, 1e15, seed),
        "reactant1": f"Chemical_A_{seed}",
        "reactant2": f"Chemical_B_{seed}",
        "compound": f"Compound_{seed}",
        "conc": generate_random_float(0.01, 1.0, seed),
        "process": f"Process_{seed}",
        "organism": f"Organism_{seed}",
        "pop": generate_random_int(100, 10000, seed),
        "rate": generate_random_float(0.01, 0.1, seed),
        "organelle": f"Organelle_{seed}",
        "a": generate_random_int(1, 10, seed),
        "b": generate_random_int(-10, 10, seed),
        "c": generate_random_int(-10, 10, seed),
        "func": f"x^{generate_random_int(2, 5, seed)}",
        "lower": generate_random_int(0, 5, seed),
        "upper": generate_random_int(6, 10, seed),
        "algorithm": f"Algorithm_{seed}",
        "concept1": f"Concept_A_{seed}",
        "concept2": f"Concept_B_{seed}",
        "task": f"task_{seed}"
    }

    # Fill the template
    try:
        prompt = template.format(**params)
    except KeyError:
        prompt = f"Generic query for {domain} with seed {seed}"

    # Generate logical steps (simulated reasoning path)
    steps = [
        f"Step 1: Analyze the problem statement regarding {domain}.",
        f"Step 2: Identify relevant variables: {list(params.keys())[:3]}.",
        f"Step 3: Apply domain-specific principles.",
        f"Step 4: Compute the result using seed {seed}."
    ]

    # Calculate ground truth
    ground_truth = calculate_ground_truth(domain, steps, seed)

    return {
        "prompt": prompt,
        "ground_truth": ground_truth,
        "steps": steps,
        "seed": seed,
        "domain": domain
    }

def generate_dataset(
    size: int,
    output_path: Path,
    start_seed: int = 0
) -> List[Dict[str, Any]]:
    """
    Generate a dataset of synthetic queries and save to JSON.
    
    Args:
        size: Number of queries to generate.
        output_path: Path to save the JSON file.
        start_seed: Starting seed for random generation.
        
    Returns:
        List of generated query dictionaries.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    queries = []
    current_seed = start_seed
    
    for i in range(size):
        # Select a domain
        domain = random.choice(DOMAINS)
        
        # Generate query
        query = generate_query(domain, current_seed)
        queries.append(query)
        
        # Increment seed for next query
        current_seed += 1
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(queries, f, indent=2)
        
    return queries

def main():
    """Main entry point to generate both Test and Warm-up sets."""
    # Ensure random state is set for reproducibility
    random.seed(RANDOM_SEED)
    
    print(f"Generating Test Set ({TEST_SET_SIZE} queries)...")
    test_queries = generate_dataset(TEST_SET_SIZE, TEST_SET_PATH, start_seed=0)
    print(f"Test Set saved to {TEST_SET_PATH}")
    
    # Reset seed for warmup set generation to ensure independence
    # but reproducibility. We start the warmup set at a different seed offset.
    random.seed(RANDOM_SEED)
    # Consume some random states to get different values for warmup
    for _ in range(1000):
        random.random()
        
    print(f"Generating Warm-up Set ({WARMUP_SET_SIZE} queries)...")
    warmup_queries = generate_dataset(WARMUP_SET_SIZE, WARMUP_SET_PATH, start_seed=10000)
    print(f"Warm-up Set saved to {WARMUP_SET_PATH}")
    
    print("Dataset generation complete.")

if __name__ == "__main__":
    main()