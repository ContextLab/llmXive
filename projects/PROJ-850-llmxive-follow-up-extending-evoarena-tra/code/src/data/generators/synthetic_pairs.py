"""
Synthetic pairs generator for conflict detection validation.

This module generates labeled JSON pairs for testing the conflict detection
heuristic.
"""
import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.seeding import set_deterministic_seed


def read_sample_size_from_research_md(research_md_path: str = 'specs/001-evoconflict-filtering/research.md') -> int:
    """
    Read the sample size from research.md.
    
    Args:
        research_md_path (str): Path to the research.md file.
    
    Returns:
        int: Sample size from the file, or default 100 if not found.
    """
    try:
        with open(research_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for line in content.split('\n'):
            if line.strip().startswith('sample_size:'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    
    return 100  # Default fallback


def generate_base_patch() -> str:
    """
    Generate a base state patch.
    
    Returns:
        str: A randomly generated state patch.
    """
    states = [
        "User is logged in as admin",
        "Database connection is active",
        "Cache is cleared",
        "File system is read-only",
        "Network interface is up",
        "Service is running",
        "Configuration is loaded",
        "Session is valid",
        "Permissions are set",
        "Backup is completed"
    ]
    
    return random.choice(states)


def generate_contradiction_pair(base_patch: str) -> str:
    """
    Generate a contradiction pair by negating a key fact.
    
    Args:
        base_patch (str): The base state patch.
    
    Returns:
        str: A contradictory patch.
    """
    negations = {
        "logged in": "logged out",
        "active": "inactive",
        "cleared": "populated",
        "read-only": "writable",
        "up": "down",
        "running": "stopped",
        "loaded": "unloaded",
        "valid": "invalid",
        "set": "unset",
        "completed": "failed"
    }
    
    contradiction = base_patch
    for key, negation in negations.items():
        if key in contradiction.lower():
            contradiction = contradiction.replace(key, negation, 1)
            break
    
    return contradiction


def generate_non_contradiction_pair(base_patch: str) -> str:
    """
    Generate a non-contradiction pair by updating an unrelated fact.
    
    Args:
        base_patch (str): The base state patch.
    
    Returns:
        str: A non-contradictory patch.
    """
    unrelated_updates = [
        " additionally, logs are rotated",
        " and monitoring is enabled",
        " while maintaining current state",
        " with no conflicts detected",
        " as expected",
        " without errors",
        " successfully",
        " automatically",
        " periodically",
        " securely"
    ]
    
    return base_patch + random.choice(unrelated_updates)


def generate_synthetic_pairs(sample_size: int) -> List[Dict[str, Any]]:
    """
    Generate a dataset of synthetic pairs for conflict detection.
    
    Args:
        sample_size (int): Number of pairs to generate.
    
    Returns:
        List[Dict[str, Any]]: List of generated pairs.
    """
    pairs = []
    
    for _ in range(sample_size):
        base_patch = generate_base_patch()
        
        # Generate both contradiction and non-contradiction pairs
        # to ensure balanced dataset
        if random.random() > 0.5:
            patch_b = generate_contradiction_pair(base_patch)
            is_contradiction = True
        else:
            patch_b = generate_non_contradiction_pair(base_patch)
            is_contradiction = False
        
        pairs.append({
            "patch_a": base_patch,
            "patch_b": patch_b,
            "is_contradiction": is_contradiction
        })
    
    return pairs


def main():
    """Main function to generate synthetic pairs dataset."""
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Read sample size from research.md
    sample_size = read_sample_size_from_research_md()
    
    print(f"Generating {sample_size} synthetic pairs...")
    
    # Generate pairs
    pairs = generate_synthetic_pairs(sample_size)
    
    # Ensure output directory exists
    output_path = Path('data/raw/synthetic_pairs.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, indent=2)
    
    print(f"Generated {len(pairs)} pairs and saved to {output_path}")


if __name__ == '__main__':
    main()
