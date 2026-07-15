import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utility from the existing project structure
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback for direct execution if path setup differs
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# --- Configuration Constants ---
DEFAULT_SAMPLE_SIZE = 100
RESEARCH_MD_PATH = Path("specs/001-evoconflict-filtering/research.md")
OUTPUT_PATH = Path("data/raw/synthetic_pairs.json")

# Templates for generating realistic state patches
BASE_FACTS = [
    "The system temperature is set to {value} degrees Celsius.",
    "The user {username} has admin privileges.",
    "The database connection pool size is {value}.",
    "The current memory usage is at {value} percent.",
    "The active session timeout is {value} minutes.",
    "The API rate limit is set to {value} requests per second.",
    "The log retention policy is {value} days.",
    "The encryption key rotation schedule is {value} days.",
]

NON_CONTRADICTION_FACTS = [
    "The system color theme is set to {theme}.",
    "The default language is {language}.",
    "The notification sound is set to {sound}.",
    "The backup frequency is {frequency}.",
]

THEMES = ["dark", "light", "auto"]
LANGUAGES = ["en", "es", "fr", "de", "zh"]
SOUNDS = ["chime", "bell", "buzz", "silent"]
FREQUENCIES = ["hourly", "daily", "weekly"]


def read_sample_size_from_research_md() -> int:
    """
    Reads the sample_size from research.md if it exists.
    Returns DEFAULT_SAMPLE_SIZE if the file or key is missing.
    """
    if not RESEARCH_MD_PATH.exists():
        logger.warning(f"{RESEARCH_MD_PATH} not found. Using default sample size.")
        return DEFAULT_SAMPLE_SIZE

    try:
        content = RESEARCH_MD_PATH.read_text()
        for line in content.splitlines():
            if line.strip().startswith("sample_size:"):
                # Parse "sample_size: 123"
                parts = line.split(":")
                if len(parts) >= 2:
                    val = parts[1].strip()
                    return int(val)
        logger.warning(f"sample_size key not found in {RESEARCH_MD_PATH}. Using default.")
        return DEFAULT_SAMPLE_SIZE
    except Exception as e:
        logger.error(f"Error reading sample_size from {RESEARCH_MD_PATH}: {e}")
        return DEFAULT_SAMPLE_SIZE


def generate_base_patch() -> str:
    """Generates a random base state patch string."""
    fact = random.choice(BASE_FACTS)
    if "{value}" in fact:
        fact = fact.format(value=random.randint(1, 1000))
    return fact


def generate_contradiction_pair() -> Dict[str, Any]:
    """
    Generates a pair where patch_b contradicts patch_a.
    Logic: Negate a key fact in patch_b relative to patch_a.
    """
    base_fact = generate_base_patch()
    
    # Simple negation logic for the specific templates
    if "temperature is set to" in base_fact:
        # Extract value and change it significantly
        try:
            val = int(base_fact.split("set to ")[1].split(" degrees")[0])
            new_val = val + 50 if val < 900 else val - 50
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("set to", "is NOT set to")
    elif "admin privileges" in base_fact:
        contradiction_fact = base_fact.replace("has admin privileges", "does NOT have admin privileges")
    elif "pool size is" in base_fact:
        try:
            val = int(base_fact.split("is ")[1].split(".")[0])
            new_val = max(1, val // 2)
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("is", "is not")
    elif "memory usage is at" in base_fact:
        try:
            val = int(base_fact.split("at ")[1].split(" percent")[0])
            new_val = 100 - val if val < 100 else val
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("at", "not at")
    elif "timeout is" in base_fact:
         try:
            val = int(base_fact.split("is ")[1].split(" minutes")[0])
            new_val = val * 2
            contradiction_fact = base_fact.replace(str(val), str(new_val))
         except:
            contradiction_fact = base_fact.replace("is", "is not")
    elif "rate limit is set to" in base_fact:
        try:
            val = int(base_fact.split("to ")[1].split(" requests")[0])
            new_val = val * 10
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("set to", "not set to")
    elif "policy is" in base_fact:
        try:
            val = int(base_fact.split("is ")[1].split(" days")[0])
            new_val = val // 2
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("is", "is not")
    elif "schedule is" in base_fact:
        try:
            val = int(base_fact.split("is ")[1].split(" days")[0])
            new_val = val * 2
            contradiction_fact = base_fact.replace(str(val), str(new_val))
        except:
            contradiction_fact = base_fact.replace("is", "is not")
    else:
        # Fallback negation
        contradiction_fact = base_fact.replace("is", "is not")

    return {
        "patch_a": base_fact,
        "patch_b": contradiction_fact,
        "is_contradiction": True
    }


def generate_non_contradiction_pair() -> Dict[str, Any]:
    """
    Generates a pair where patch_b updates an unrelated fact relative to patch_a.
    Logic: patch_a has Fact X, patch_b has Fact Y (where Y is unrelated to X).
    """
    base_fact = generate_base_patch()
    
    # Generate a completely unrelated fact
    unrelated_fact = random.choice(NON_CONTRADICTION_FACTS)
    if "{theme}" in unrelated_fact:
        unrelated_fact = unrelated_fact.format(theme=random.choice(THEMES))
    elif "{language}" in unrelated_fact:
        unrelated_fact = unrelated_fact.format(language=random.choice(LANGUAGES))
    elif "{sound}" in unrelated_fact:
        unrelated_fact = unrelated_fact.format(sound=random.choice(SOUNDS))
    elif "{frequency}" in unrelated_fact:
        unrelated_fact = unrelated_fact.format(frequency=random.choice(FREQUENCIES))

    return {
        "patch_a": base_fact,
        "patch_b": unrelated_fact,
        "is_contradiction": False
    }


def generate_synthetic_pairs(n: int) -> List[Dict[str, Any]]:
    """
    Generates a list of n labeled JSON pairs.
    Roughly 50% contradiction, 50% non-contradiction.
    """
    pairs = []
    for i in range(n):
        if i % 2 == 0:
            pairs.append(generate_contradiction_pair())
        else:
            pairs.append(generate_non_contradiction_pair())
    
    # Shuffle to avoid ordering bias
    random.shuffle(pairs)
    return pairs


def main():
    """
    Main entry point for the synthetic pairs generator.
    Reads sample size from research.md (or uses default), generates data,
    and writes to data/raw/synthetic_pairs.json.
    """
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Determine N
    n = read_sample_size_from_research_md()
    logger.info(f"Generating {n} synthetic pairs based on sample_size.")

    # Generate data
    pairs = generate_synthetic_pairs(n)

    # Write to disk
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, indent=2)

    logger.info(f"Successfully wrote {len(pairs)} pairs to {OUTPUT_PATH}")
    print(f"Generated {len(pairs)} pairs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
