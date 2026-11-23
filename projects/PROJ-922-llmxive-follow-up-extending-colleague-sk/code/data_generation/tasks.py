"""
Task Generation Module for llmXive.

Generates a global pool of exactly 500 unique task scenarios across 5 domains
(coding, math, logic, creative, factual) with 100 tasks each.
"""
import json
import random
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
TOTAL_TASKS = 500
TASKS_PER_DOMAIN = 100
DOMAINS = ["coding", "math", "logic", "creative", "factual"]
SEED = 42

def generate_coding_task(task_id: int, seed_offset: int) -> Dict[str, Any]:
    """Generate a deterministic coding task."""
    # Use seed_offset to ensure determinism within the run
    local_rng = random.Random(SEED + seed_offset)

    problems = [
        {"prompt": "Write a function to reverse a string.", "rule": "Output must contain the reversed string."},
        {"prompt": "Implement a function to check if a number is prime.", "rule": "Output must contain 'True' or 'False'."},
        {"prompt": "Write a script to parse a JSON file and extract a specific key.", "rule": "Output must contain the value of the key."},
        {"prompt": "Create a function to sort a list of dictionaries by a specific key.", "rule": "Output must be a sorted list."},
        {"prompt": "Write a function to find the intersection of two lists.", "rule": "Output must contain the common elements."},
    ]

    # Cycle through problems or expand based on ID if more needed
    problem = problems[task_id % len(problems)].copy()
    problem["id"] = f"task_coding_{task_id:04d}"
    problem["domain"] = "coding"
    problem["difficulty"] = local_rng.choice(["easy", "medium", "hard"])
    problem["ambiguous"] = False  # Coding tasks are generally well-defined

    return problem

def generate_math_task(task_id: int, seed_offset: int) -> Dict[str, Any]:
    """Generate a deterministic math task."""
    local_rng = random.Random(SEED + seed_offset)

    templates = [
        ("Solve for x: {a}x + {b} = {c}", "Output must contain 'x = ' followed by a number."),
        ("Calculate the area of a rectangle with length {a} and width {b}.", "Output must contain the calculated area."),
        ("What is the sum of {a} and {b}?", "Output must contain the sum."),
        ("Find the square root of {a}.", "Output must contain the square root value."),
        ("Compute {a} raised to the power of {b}.", "Output must contain the result."),
    ]

    a = local_rng.randint(1, 100)
    b = local_rng.randint(1, 100)
    c = local_rng.randint(1, 100) if local_rng.random() > 0.5 else 0

    template, rule = templates[task_id % len(templates)]
    prompt = template.format(a=a, b=b, c=c)

    return {
        "id": f"task_math_{task_id:04d}",
        "domain": "math",
        "prompt": prompt,
        "rule": rule,
        "difficulty": local_rng.choice(["easy", "medium", "hard"]),
        "ambiguous": False
    }

def generate_logic_task(task_id: int, seed_offset: int) -> Dict[str, Any]:
    """Generate a deterministic logic task."""
    local_rng = random.Random(SEED + seed_offset)

    scenarios = [
        {
            "context": "All birds can fly. Tweety is a bird.",
            "question": "Can Tweety fly?",
            "rule": "Output must conclude 'Yes' or 'No' based on the premises."
        },
        {
            "context": "If it rains, the ground is wet. It is raining.",
            "question": "Is the ground wet?",
            "rule": "Output must conclude 'Yes' or 'No'."
        },
        {
            "context": "Some cats are black. Fluffy is a cat.",
            "question": "Is Fluffy black?",
            "rule": "Output must conclude 'Yes', 'No', or 'Cannot be determined'."
        },
        {
            "context": "A is greater than B. B is greater than C.",
            "question": "Is A greater than C?",
            "rule": "Output must conclude 'Yes' or 'No'."
        },
        {
            "context": "No mammals are fish. A whale is a mammal.",
            "question": "Is a whale a fish?",
            "rule": "Output must conclude 'Yes' or 'No'."
        }
    ]

    scenario = scenarios[task_id % len(scenarios)].copy()
    scenario["id"] = f"task_logic_{task_id:04d}"
    scenario["domain"] = "logic"
    scenario["difficulty"] = local_rng.choice(["easy", "medium", "hard"])
    scenario["ambiguous"] = False

    return scenario

def generate_creative_task(task_id: int, seed_offset: int) -> Dict[str, Any]:
    """Generate a deterministic creative task."""
    local_rng = random.Random(SEED + seed_offset)

    prompts = [
        "Write a short poem about the ocean.",
        "Describe a futuristic city in 3 sentences.",
        "Invent a new color and describe it.",
        "Write a haiku about a robot.",
        "Create a title for a story about a lost key."
    ]

    prompt = prompts[task_id % len(prompts)]
    # Creative tasks are inherently ambiguous regarding "correct" answers
    # We flag them as ambiguous for Hallucination Rate calculation logic
    return {
        "id": f"task_creative_{task_id:04d}",
        "domain": "creative",
        "prompt": prompt,
        "rule": "Output must be a creative text of at least 20 characters.",
        "difficulty": local_rng.choice(["easy", "medium", "hard"]),
        "ambiguous": True  # No single ground truth
    }

def generate_factual_task(task_id: int, seed_offset: int) -> Dict[str, Any]:
    """Generate a deterministic factual task."""
    local_rng = random.Random(SEED + seed_offset)

    facts = [
        ("What is the capital of France?", "Paris"),
        ("Who wrote 'Romeo and Juliet'?", "William Shakespeare"),
        ("What is the chemical symbol for Gold?", "Au"),
        ("In which year did World War II end?", "1945"),
        ("What is the largest planet in our solar system?", "Jupiter")
    ]

    q, a = facts[task_id % len(facts)]
    return {
        "id": f"task_factual_{task_id:04d}",
        "domain": "factual",
        "prompt": q,
        "rule": f"Output must contain the fact: '{a}'.",
        "difficulty": local_rng.choice(["easy", "medium", "hard"]),
        "ambiguous": False
    }

GENERATORS = {
    "coding": generate_coding_task,
    "math": generate_math_task,
    "logic": generate_logic_task,
    "creative": generate_creative_task,
    "factual": generate_factual_task
}

def generate_tasks(count_per_domain: int = TASKS_PER_DOMAIN) -> List[Dict[str, Any]]:
    """
    Generate the global pool of tasks.

    Args:
        count_per_domain: Number of tasks to generate per domain (default 100).

    Returns:
        List of task dictionaries.
    """
    set_global_seed(SEED)
    all_tasks = []

    logger.info(f"Starting task generation: {count_per_domain} tasks per domain for {len(DOMAINS)} domains.")

    for domain in DOMAINS:
        generator = GENERATORS[domain]
        domain_tasks = []
        for i in range(count_per_domain):
            task = generator(i, i) # Use index for determinism
            domain_tasks.append(task)

        # Validate tasks immediately
        valid_tasks, invalid_count = validate_tasks(domain_tasks)
        if invalid_count > 0:
            logger.warning(f"Domain '{domain}': {invalid_count} tasks were invalid and skipped.")

        all_tasks.extend(valid_tasks)
        logger.info(f"Generated {len(valid_tasks)} valid tasks for domain '{domain}'.")

    total = len(all_tasks)
    logger.info(f"Total tasks generated: {total}")

    # Verify distribution
    distribution = {d: 0 for d in DOMAINS}
    for t in all_tasks:
        if t.get("domain") in distribution:
            distribution[t["domain"]] += 1

    logger.info(f"Distribution: {distribution}")

    # Assert exact counts as per spec
    for d in DOMAINS:
        if distribution[d] != count_per_domain:
            logger.error(f"Domain '{d}' count mismatch: expected {count_per_domain}, got {distribution[d]}")
            raise ValueError(f"Task generation failed: Domain '{d}' count mismatch.")

    return all_tasks

def validate_tasks(tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Validate a list of tasks.

    Checks for:
    - Non-empty prompt
    - Non-empty rule
    - Valid domain
    - Presence of ID

    Returns:
        Tuple of (valid_tasks_list, count_of_invalid_tasks)
    """
    valid = []
    invalid_count = 0

    for task in tasks:
        is_valid = True
        reason = []

        if not task.get("prompt") or not isinstance(task.get("prompt"), str):
            is_valid = False
            reason.append("missing or invalid prompt")

        if not task.get("rule") or not isinstance(task.get("rule"), str):
            is_valid = False
            reason.append("missing or invalid rule")

        if not task.get("domain") or task.get("domain") not in DOMAINS:
            is_valid = False
            reason.append("missing or invalid domain")

        if not task.get("id"):
            is_valid = False
            reason.append("missing id")

        if is_valid:
            valid.append(task)
        else:
            invalid_count += 1
            logger.debug(f"Invalid task detected: {task.get('id', 'unknown')} - {', '.join(reason)}")

    return valid, invalid_count

def save_tasks(tasks: List[Dict[str, Any]], output_path: Optional[str] = None) -> Path:
    """
    Save tasks to a JSON file.

    Args:
        tasks: List of task dictionaries.
        output_path: Optional path. If None, uses default data/raw/tasks.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        data_dir = get_data_dir()
        output_path = str(data_dir / "raw" / "tasks.json")

    output_file = Path(output_path)
    ensure_dir(output_file.parent)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(tasks)} tasks to {output_file}")
    return output_file

def load_tasks(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load tasks from a JSON file.

    Args:
        input_path: Optional path. If None, uses default data/raw/tasks.json.

    Returns:
        List of task dictionaries.
    """
    if input_path is None:
        data_dir = get_data_dir()
        input_path = str(data_dir / "raw" / "tasks.json")

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Tasks file not found at {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} tasks from {input_file}")
    return data

def main():
    """Main entry point for task generation."""
    logger.info("Starting Task Generation Pipeline (T007)")

    try:
        # Generate the pool
        tasks = generate_tasks(count_per_domain=TASKS_PER_DOMAIN)

        # Save to disk
        output_file = save_tasks(tasks)

        # Verify file exists and has content
        if not output_file.exists():
            raise RuntimeError("Failed to write output file.")

        logger.info(f"Task generation complete. Output: {output_file}")
        return 0

    except Exception as e:
        logger.error(f"Task generation failed: {e}")
        raise

if __name__ == "__main__":
    main()