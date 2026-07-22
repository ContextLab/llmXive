import json
import random
from pathlib import Path
from typing import List, Dict, Any
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Define domains and their characteristics
# Per T006: 2 profiles per domain (coding, math, logic, creative, factual)
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

def generate_profiles(count: int = 10, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate expert profiles for the COLLEAGUE.SKILL follow-up study.
    
    Per T006 requirements:
    - Generates exactly 10 profiles (2 per domain).
    - Domains: coding, math, logic, creative, factual.
    - Schema: {"id": str, "domain": str, "capability_rules": str, "behavior_keywords": [str]}.
    - Validates non-empty rules/keywords; skips malformed profiles.
    - Raises on fatal errors (e.g., disk write failure).
    
    Args:
        count: Total number of profiles to generate (default 10).
        seed: Random seed for reproducibility.
        
    Returns:
        List of valid profile dictionaries.
        
    Raises:
        RuntimeError: If a fatal error occurs during generation.
    """
    set_global_seed(seed)
    profiles = []
    
    # Enforce 2 per domain as per task description
    profiles_per_domain = 2
    domain_keys = list(DOMAINS.keys())
    
    # Ensure we have enough domains for the requested count
    if len(domain_keys) * profiles_per_domain < count:
        logger.warning(f"Requested {count} profiles, but domain structure limits to {len(domain_keys) * profiles_per_domain}. Adjusting count.")
        count = len(domain_keys) * profiles_per_domain
    
    profile_id = 0
    for domain in domain_keys:
        characteristics = DOMAINS[domain]
        
        # Validate domain definition before generating
        if not characteristics.get("capability_rules") or not characteristics.get("behavior_keywords"):
            logger.error(f"Domain '{domain}' has malformed characteristics (empty rules or keywords). Skipping.")
            continue
            
        for i in range(profiles_per_domain):
            profile_id += 1
            try:
                # Construct profile
                profile = {
                    "id": f"prof_{profile_id:03d}",
                    "domain": domain,
                    "capability_rules": characteristics["capability_rules"],
                    "behavior_keywords": list(characteristics["behavior_keywords"]) # Ensure it's a list
                }
                
                # Validation Logic: Check for non-empty rules and keywords
                if not profile["capability_rules"] or not profile["behavior_keywords"]:
                    logger.error(f"Generated profile {profile['id']} is malformed (missing keys). Skipping.")
                    continue
                    
                profiles.append(profile)
                
            except Exception as e:
                logger.error(f"Fatal error generating profile for domain {domain}: {e}")
                raise RuntimeError(f"Internal generator failure: {e}")
    
    if len(profiles) == 0:
        raise RuntimeError("Fatal: No valid profiles could be generated.")
        
    logger.info(f"Successfully generated {len(profiles)} valid profiles.")
    return profiles

def save_profiles(profiles: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save profiles to a JSONL file.
    
    Args:
        profiles: List of profile dictionaries.
        output_path: Path to save the file.
        
    Raises:
        RuntimeError: If file writing fails (strict failure).
    """
    try:
        ensure_dir(output_path.parent)
        with open(output_path, 'w', encoding='utf-8') as f:
            for profile in profiles:
                f.write(json.dumps(profile, ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(profiles)} profiles to {output_path}")
    except IOError as e:
        logger.critical(f"Failed to write profiles to disk: {e}")
        raise RuntimeError(f"Fatal disk write error: {e}")

def load_profiles(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load profiles from a JSONL file.
    
    Args:
        input_path: Path to the file.
        
    Returns:
        List of profile dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Profiles file not found: {input_path}")
    
    profiles = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    profiles.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON line in profiles file: {e}")
    return profiles

def main():
    """Main entry point for profile generation."""
    set_global_seed(42)
    
    # Output path as per project structure
    output_path = get_data_dir() / "interim" / "profiles.jsonl"
    
    # Generate exactly 10 profiles (2 per domain)
    profiles = generate_profiles(count=10)
    
    # Save to disk
    save_profiles(profiles, output_path)
    
    logger.info(f"Profile generation complete: {len(profiles)} profiles written to {output_path}")

if __name__ == "__main__":
    main()