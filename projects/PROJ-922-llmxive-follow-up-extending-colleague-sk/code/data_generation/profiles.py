import json
import random
from pathlib import Path
from typing import List, Dict, Any
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Define domains and their characteristics
DOMAINS = {
    "coding": {
        "capability_rules": "Must provide syntactically correct code. Must include comments explaining logic. Must handle edge cases.",
        "behavior_keywords": ["function", "algorithm", "debug", "optimize", "refactor", "test", "bug", "syntax"]
    },
    "math": {
        "capability_rules": "Must show step-by-step derivation. Must verify results. Must use standard notation.",
        "behavior_keywords": ["theorem", "proof", "equation", "derivative", "integral", "variable", "constant", "solution"]
    },
    "logic": {
        "capability_rules": "Must state premises clearly. Must derive conclusions logically. Must identify fallacies.",
        "behavior_keywords": ["premise", "conclusion", "valid", "invalid", "contradiction", "implication", "quantifier", "negation"]
    },
    "creative": {
        "capability_rules": "Must generate original content. Must maintain narrative consistency. Must evoke emotion.",
        "behavior_keywords": ["metaphor", "imagery", "narrative", "character", "plot", "theme", "symbolism", "tone"]
    },
    "factual": {
        "capability_rules": "Must cite sources. Must distinguish fact from opinion. Must avoid speculation.",
        "behavior_keywords": ["source", "evidence", "data", "research", "study", "statistic", "citation", "reference"]
    }
}

def generate_profiles(count: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic expert profiles.
    
    Args:
        count: Total number of profiles to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of profile dictionaries.
    """
    set_global_seed(seed)
    profiles = []
    profiles_per_domain = count // len(DOMAINS)
    
    profile_id = 0
    for domain, characteristics in DOMAINS.items():
        for i in range(profiles_per_domain):
            profile_id += 1
            profile = {
                "id": f"prof_{profile_id:03d}",
                "domain": domain,
                "capability_rules": characteristics["capability_rules"],
                "behavior_keywords": characteristics["behavior_keywords"]
            }
            profiles.append(profile)
    
    # If count is not evenly divisible, add remaining profiles randomly
    remaining = count - len(profiles)
    if remaining > 0:
        domains_list = list(DOMAINS.keys())
        for i in range(remaining):
            domain = random.choice(domains_list)
            profile_id += 1
            profile = {
                "id": f"prof_{profile_id:03d}",
                "domain": domain,
                "capability_rules": DOMAINS[domain]["capability_rules"],
                "behavior_keywords": DOMAINS[domain]["behavior_keywords"]
            }
            profiles.append(profile)
    
    return profiles

def save_profiles(profiles: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save profiles to a JSONL file.
    
    Args:
        profiles: List of profile dictionaries.
        output_path: Path to save the file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        for profile in profiles:
            f.write(json.dumps(profile, ensure_ascii=False) + '\n')
    logger.info(f"Saved {len(profiles)} profiles to {output_path}")

def load_profiles(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load profiles from a JSONL file.
    
    Args:
        input_path: Path to the file.
        
    Returns:
        List of profile dictionaries.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Profiles file not found: {input_path}")
    
    profiles = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                profiles.append(json.loads(line))
    return profiles

def main():
    """Main entry point for profile generation."""
    set_global_seed(42)
    
    output_path = get_data_dir() / "interim" / "profiles.jsonl"
    profiles = generate_profiles(count=50)
    save_profiles(profiles, output_path)
    logger.info(f"Generated and saved {len(profiles)} profiles")

if __name__ == "__main__":
    main()
