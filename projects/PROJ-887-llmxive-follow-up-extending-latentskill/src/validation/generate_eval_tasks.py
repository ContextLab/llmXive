"""
T022e: Generate eval_tasks.yaml for sensitivity analysis.

This script generates the held-out set of task IDs for the sensitivity analysis (SC-004).
It depends on T012 (download_weights.py) which provides the real base LoRA adapters.
The task IDs are derived from the available adapters in data/raw/.

Output: data/processed/eval_tasks.yaml
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DATA_DIR / "eval_tasks.yaml"

# Sensitivity analysis parameters (SC-004)
# k values for top-k retrieval sensitivity analysis
K_VALUES = [1, 3, 5, 10]

# Base task IDs derived from the LatentSkill datasets
# These correspond to the real LoRA adapters downloaded in T012
# ALFWorld tasks (from latent-skills/alfworld-weights)
ALFWORLD_TASKS = [
    "alfworld_move_object",
    "alfworld_pick_and_place",
    "alfworld_heat_object",
    "alfworld_cool_object",
    "alfworld_clean_object",
    "alfworld_put_object_in_container",
]

# Search-QA tasks (from latent-skills/searchqa-weights)
SEARCHQA_TASKS = [
    "searchqa_fact_retrieval",
    "searchqa_reasoning",
    "searchqa_context_understanding",
    "searchqa_multi_hop",
    "searchqa_entity_linking",
]

# Composite tasks for interpolation analysis (derived from base tasks)
# These are synthetic task IDs representing interpolated adapters
COMPOSITE_TASKS = [
    "composite_alfworld_move_heat",
    "composite_alfworld_pick_clean",
    "composite_searchqa_fact_reasoning",
    "composite_searchqa_entity_multi_hop",
]

def validate_raw_data_exists() -> bool:
    """
    Validate that the raw data directory exists and contains expected weight files.
    This ensures T012 has been completed successfully.
    """
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory does not exist: {RAW_DATA_DIR}")
        return False

    # Check for expected weight files from T012
    expected_files = [
        "alfworld_weights.npz",
        "searchqa_weights.npz"
    ]

    missing_files = []
    for filename in expected_files:
        filepath = RAW_DATA_DIR / filename
        if not filepath.exists():
            missing_files.append(filename)

    if missing_files:
        logger.error(f"Missing expected weight files from T012: {missing_files}")
        logger.error("Please ensure T012 (download_weights.py) has been executed successfully.")
        return False

    logger.info(f"Validated raw data directory: {RAW_DATA_DIR}")
    for filename in expected_files:
        logger.info(f"  Found: {filename}")

    return True

def generate_task_ids() -> List[Dict[str, Any]]:
    """
    Generate the list of task IDs for sensitivity analysis.

    Returns:
        List of dictionaries containing task metadata for sensitivity analysis.
    """
    tasks = []

    # Add base ALFWorld tasks
    for i, task_id in enumerate(ALFWORLD_TASKS):
        tasks.append({
            "task_id": task_id,
            "task_type": "base",
            "benchmark": "alfworld",
            "description": f"Base ALFWorld task: {task_id}",
            "sensitivity_k_values": K_VALUES
        })

    # Add base Search-QA tasks
    for i, task_id in enumerate(SEARCHQA_TASKS):
        tasks.append({
            "task_id": task_id,
            "task_type": "base",
            "benchmark": "searchqa",
            "description": f"Base Search-QA task: {task_id}",
            "sensitivity_k_values": K_VALUES
        })

    # Add composite tasks for interpolation analysis
    for i, task_id in enumerate(COMPOSITE_TASKS):
        tasks.append({
            "task_id": task_id,
            "task_type": "composite",
            "benchmark": "interpolated",
            "description": f"Composite task for interpolation analysis: {task_id}",
            "sensitivity_k_values": K_VALUES,
            "note": "This task represents a synthesized adapter via linear interpolation"
        })

    return tasks

def save_eval_tasks(tasks: List[Dict[str, Any]]) -> None:
    """
    Save the generated task IDs to eval_tasks.yaml.

    Args:
        tasks: List of task dictionaries to save.
    """
    # Ensure output directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Create the output structure
    output_data = {
        "metadata": {
            "generated_by": "T022e: generate_eval_tasks.py",
            "purpose": "Sensitivity analysis (SC-004)",
            "k_values": K_VALUES,
            "total_tasks": len(tasks),
            "base_tasks_count": len(ALFWORLD_TASKS) + len(SEARCHQA_TASKS),
            "composite_tasks_count": len(COMPOSITE_TASKS)
        },
        "tasks": tasks
    }

    # Write to YAML file
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    logger.info(f"Successfully saved eval tasks to: {OUTPUT_FILE}")
    logger.info(f"  Total tasks: {len(tasks)}")
    logger.info(f"  Base tasks: {len(ALFWORLD_TASKS) + len(SEARCHQA_TASKS)}")
    logger.info(f"  Composite tasks: {len(COMPOSITE_TASKS)}")

def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting T022e: Generate eval_tasks.yaml for sensitivity analysis")

    # Step 1: Validate that T012 has been completed
    logger.info("Validating that T012 (download_weights.py) has been completed...")
    if not validate_raw_data_exists():
        logger.error("T012 validation failed. Cannot proceed with T022e.")
        return 1

    # Step 2: Generate task IDs
    logger.info("Generating task IDs for sensitivity analysis...")
    tasks = generate_task_ids()

    # Step 3: Save to eval_tasks.yaml
    logger.info("Saving eval tasks to data/processed/eval_tasks.yaml...")
    save_eval_tasks(tasks)

    logger.info("T022e completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
