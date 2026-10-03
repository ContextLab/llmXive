"""
Script to generate the default density_terms.json configuration file.

This script checks for an existing user override file (code/config/user_terms.json).
If found, it uses those terms. Otherwise, it generates the default list of terms
and writes them to code/config/density_terms.json.

The output JSON follows the schema: {"terms": ["string", ...]}
"""
import json
import os
from pathlib import Path

# Default terms as specified in FR-008
DEFAULT_TERMS = [
    "entropy",
    "retrieval",
    "context",
    "density",
    "horizon",
    "masking",
    "trajectory",
    "agent",
    "search",
    "stale"
]

# File paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "code" / "config"
USER_TERMS_PATH = CONFIG_DIR / "user_terms.json"
OUTPUT_PATH = CONFIG_DIR / "density_terms.json"

def ensure_config_directory():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_user_terms():
    """
    Load terms from user_terms.json if it exists.
    
    Returns:
        list: List of terms from user file, or None if file doesn't exist.
    """
    if not USER_TERMS_PATH.exists():
        return None
    
    with open(USER_TERMS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, dict) or "terms" not in data:
        raise ValueError(f"Invalid format in {USER_TERMS_PATH}. Expected {{'terms': [...]}}")
    
    if not isinstance(data["terms"], list):
        raise ValueError(f"'terms' in {USER_TERMS_PATH} must be a list.")
    
    return data["terms"]

def generate_default_terms():
    """Generate the default list of terms."""
    return DEFAULT_TERMS

def write_terms_file(terms):
    """
    Write the terms list to density_terms.json.
    
    Args:
        terms (list): List of term strings.
    """
    output_data = {"terms": terms}
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully wrote {len(terms)} terms to {OUTPUT_PATH}")

def main():
    """Main entry point for the script."""
    ensure_config_directory()
    
    # Check for user override
    user_terms = load_user_terms()
    
    if user_terms is not None:
        print(f"Found user override at {USER_TERMS_PATH}. Using custom terms.")
        terms_to_use = user_terms
    else:
        print(f"No user override found at {USER_TERMS_PATH}. Using default terms.")
        terms_to_use = generate_default_terms()
    
    # Validate terms are strings
    if not all(isinstance(term, str) for term in terms_to_use):
        raise ValueError("All terms must be strings.")
    
    # Write the output file
    write_terms_file(terms_to_use)
    
    # Verification: Read back and confirm
    with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
        verification_data = json.load(f)
    
    if verification_data.get("terms") == terms_to_use:
        print("Verification successful: Output file matches expected content.")
    else:
        raise RuntimeError("Verification failed: Output file content mismatch.")

if __name__ == "__main__":
    main()
