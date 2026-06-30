import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datasets import load_dataset
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_MBPP_DIR = Path("data/benchmarks/raw/mbpp")
RAW_HUMANEVAL_DIR = Path("data/benchmarks/raw/humaneval")
PROCESSED_DIR = Path("data/benchmarks/processed")
CATALOG_PATH = PROCESSED_DIR / "catalog.json"
CONTRACT_SCHEMA_PATH = Path("contracts/task_catalog.schema.yaml")

# Ensure directories exist
RAW_MBPP_DIR.mkdir(parents=True, exist_ok=True)
RAW_HUMANEVAL_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_mbpp() -> List[Dict[str, Any]]:
    """Load MBPP dataset from Hugging Face."""
    try:
        logger.info("Loading MBPP dataset...")
        dataset = load_dataset("mbpp", split="train")
        return dataset.to_list()
    except Exception as e:
        logger.error(f"Failed to load MBPP dataset: {e}")
        return []

def save_mbpp_raw(data: List[Dict[str, Any]]) -> None:
    """Save raw MBPP data to disk."""
    output_path = RAW_MBPP_DIR / "mbpp_raw.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw MBPP data to {output_path}")

def load_and_save_mbpp_raw() -> List[Dict[str, Any]]:
    """Load MBPP and save raw data."""
    data = load_mbpp()
    if data:
        save_mbpp_raw(data)
    return data

def load_humaneval() -> List[Dict[str, Any]]:
    """Load HumanEval dataset from Hugging Face."""
    try:
        logger.info("Loading HumanEval dataset...")
        # HumanEval is typically loaded as 'test' split
        dataset = load_dataset("google-research-datasets/human_eval", split="test")
        return dataset.to_list()
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        return []

def save_humaneval_raw(data: List[Dict[str, Any]]) -> None:
    """Save raw HumanEval data to disk."""
    output_path = RAW_HUMANEVAL_DIR / "humaneval_raw.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw HumanEval data to {output_path}")

def load_and_save_humaneval_raw() -> List[Dict[str, Any]]:
    """Load HumanEval and save raw data."""
    data = load_humaneval()
    if data:
        save_humaneval_raw(data)
    return data

def extract_code_patterns(code: str) -> List[str]:
    """Extract code patterns (loops, conditionals, recursion) from code."""
    patterns = []
    if not code:
        return patterns

    # Check for loops
    if re.search(r'\b(for|while)\b', code):
        patterns.append("loops")

    # Check for conditionals
    if re.search(r'\b(if|else|elif|switch|case)\b', code):
        patterns.append("conditionals")

    # Check for recursion (simple heuristic: function calling itself)
    func_name_match = re.search(r'def\s+(\w+)', code)
    if func_name_match:
        func_name = func_name_match.group(1)
        if re.search(rf'\b{func_name}\s*\(', code[func_name_match.end():]):
            patterns.append("recursion")

    return list(set(patterns))

def estimate_difficulty(task: Dict[str, Any], dataset_source: str) -> str:
    """Estimate task difficulty based on heuristics."""
    prompt = task.get("prompt", "")
    solution = task.get("human_solution", "")
    test_suite = task.get("test_suite", task.get("test_list", ""))

    # Heuristics for difficulty
    prompt_len = len(prompt)
    solution_len = len(solution) if solution else 0
    test_count = len(re.findall(r'def test_', str(test_suite))) if test_suite else 0

    # Simple heuristic: longer solutions and more tests often indicate harder tasks
    if dataset_source == "mbpp":
        # MBPP has explicit difficulty in some versions, otherwise estimate
        if prompt_len > 200 or solution_len > 500 or test_count > 5:
            return "hard"
        elif prompt_len > 100 or solution_len > 200 or test_count > 3:
            return "medium"
        else:
            return "easy"
    else:  # humaneval
        # HumanEval difficulty estimation
        if solution_len > 400 or test_count > 8:
            return "hard"
        elif solution_len > 200 or test_count > 5:
            return "medium"
        else:
            return "easy"

def normalize_task(task: Dict[str, Any], dataset_source: str, task_id_prefix: str) -> Optional[Dict[str, Any]]:
    """Normalize a task entry to the required catalog format."""
    # Extract required fields
    raw_task_id = task.get("task_id") or task.get("index") or str(hash(str(task)))
    task_id = f"{task_id_prefix}/{raw_task_id}"

    # Handle different field names across datasets
    prompt = task.get("prompt", "")
    human_solution = task.get("human_solution") or task.get("canonical_solution", "")
    
    # Handle test suite variations
    test_suite = task.get("test_suite") or task.get("test_list", "")
    if isinstance(test_suite, list):
        test_suite = "\n".join(test_suite)

    # Validate required fields
    if not prompt or not human_solution:
        logger.warning(f"Skipping task {task_id}: missing required fields (prompt or human_solution)")
        return None

    # Extract code patterns
    code_patterns = extract_code_patterns(human_solution)

    # Estimate difficulty
    difficulty = estimate_difficulty(task, dataset_source)

    # Create normalized entry
    normalized = {
        "task_id": task_id,
        "prompt": prompt,
        "human_solution": human_solution,
        "test_suite": test_suite,
        "test_suite_path": f"data/benchmarks/processed/tests/{task_id.replace('/', '_')}.py",
        "difficulty": difficulty,
        "code_patterns": code_patterns,
        "dataset_source": dataset_source
    }

    return normalized

def validate_catalog_entry(entry: Dict[str, Any]) -> bool:
    """Validate a catalog entry against required schema."""
    required_keys = ["task_id", "prompt", "human_solution", "test_suite_path", "difficulty", "code_patterns"]
    
    for key in required_keys:
        if key not in entry:
            logger.error(f"Missing required key '{key}' in catalog entry: {entry.get('task_id', 'unknown')}")
            return False
    
    # Validate types
    if not isinstance(entry.get("code_patterns"), list):
        logger.error(f"code_patterns must be a list in task {entry.get('task_id')}")
        return False

    if entry.get("difficulty") not in ["easy", "medium", "hard"]:
        logger.warning(f"Invalid difficulty '{entry.get('difficulty')}' in task {entry.get('task_id')}, defaulting to 'medium'")
        entry["difficulty"] = "medium"

    return True

def load_schema_from_contract() -> Optional[Dict[str, Any]]:
    """Load schema from contracts if it exists."""
    if CONTRACT_SCHEMA_PATH.exists():
        try:
            with open(CONTRACT_SCHEMA_PATH, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load contract schema: {e}")
    return None

def validate_against_schema(entry: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate entry against loaded schema."""
    # Basic schema validation
    if "required" in schema:
        for key in schema["required"]:
            if key not in entry:
                logger.error(f"Schema validation failed: missing required key '{key}'")
                return False
    return True

def validate_and_save_catalog() -> None:
    """Load MBPP and HumanEval, normalize, validate, and save to catalog."""
    logger.info("Starting catalog generation...")

    # Load raw data
    mbpp_data = load_and_save_mbpp_raw()
    humaneval_data = load_and_save_humaneval_raw()

    if not mbpp_data and not humaneval_data:
        logger.error("No data loaded from MBPP or HumanEval. Cannot generate catalog.")
        return

    # Load schema if available
    schema = load_schema_from_contract()

    # Normalize and validate entries
    catalog_entries = []
    total_tasks = len(mbpp_data) + len(humaneval_data)
    validated_count = 0

    # Process MBPP
    for task in mbpp_data:
        normalized = normalize_task(task, "mbpp", "MBPP")
        if normalized:
            if schema:
                if validate_against_schema(normalized, schema):
                    catalog_entries.append(normalized)
                    validated_count += 1
            else:
                if validate_catalog_entry(normalized):
                    catalog_entries.append(normalized)
                    validated_count += 1

    # Process HumanEval
    for task in humaneval_data:
        normalized = normalize_task(task, "humaneval", "HumanEval")
        if normalized:
            if schema:
                if validate_against_schema(normalized, schema):
                    catalog_entries.append(normalized)
                    validated_count += 1
            else:
                if validate_catalog_entry(normalized):
                    catalog_entries.append(normalized)
                    validated_count += 1

    # Save catalog
    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog_entries, f, indent=2, ensure_ascii=False)

    logger.info(f"Catalog saved to {CATALOG_PATH}")
    logger.info(f"Total tasks: {total_tasks}, Validated: {validated_count}")

def main():
    """Main entry point for catalog generation."""
    validate_and_save_catalog()

if __name__ == "__main__":
    main()
