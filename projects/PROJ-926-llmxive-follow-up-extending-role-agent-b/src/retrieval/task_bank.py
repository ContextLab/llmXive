"""
Task Bank Module for llmXive.

This module provides access to the frozen, human-annotated task bank.
The task bank is stored as a JSON file to ensure portability and
deterministic loading across environments.

Data Source:
  The task definitions are derived from the ALFWorld dataset.
  The canonical source is the ALFWorld repository or the HuggingFace
  'alfworld' dataset. This module loads a pre-processed, frozen snapshot
  located at `data/raw/task_bank.json`.

  If the snapshot does not exist, this module attempts to download the
  canonical task definitions from the ALFWorld source via the `datasets`
  library and saves them locally as the frozen artifact.

API:
  get_task_definition(task_id: str) -> dict | None
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Import project config to resolve paths
try:
    from src.config.config import DATA_PATH, SEED
except ImportError:
    # Fallback for direct execution or missing config (should not happen in pipeline)
    # Assume standard project structure relative to this file
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_PATH = PROJECT_ROOT / "data"
    SEED = 42

TASK_BANK_PATH = DATA_PATH / "raw" / "task_bank.json"
HF_DATASET_NAME = "alfworld/alfworld"

def _ensure_task_bank_exists() -> Path:
    """
    Ensures the frozen task bank JSON exists.
    
    If the file is missing, it attempts to fetch the canonical tasks
    from the ALFWorld HuggingFace dataset and saves them to the frozen path.
    
    Raises:
        FileNotFoundError: If the local file is missing and the remote fetch fails.
    """
    if TASK_BANK_PATH.exists():
        return TASK_BANK_PATH

    # Attempt to generate the frozen bank from the real source
    # This ensures we are using REAL data, not synthetic placeholders.
    try:
        from datasets import load_dataset
        
        # Load the real ALFWorld dataset (streaming not needed for metadata extraction)
        # We specifically need the 'all' split or the train split which contains task definitions
        ds = load_dataset(HF_DATASET_NAME, split="train")
        
        tasks = []
        seen_ids = set()
        
        for item in ds:
            # ALFWorld dataset structure usually contains 'goal', 'initial_state', 'expert_action'
            # We construct a normalized task definition object
            task_id = item.get("task_id") or item.get("id") or f"task_{len(tasks)}"
            
            # Ensure unique IDs
            if task_id in seen_ids:
                continue
            seen_ids.add(task_id)

            task_def = {
                "task_id": task_id,
                "goal": item.get("goal", ""),
                "initial_state": item.get("initial_state", ""),
                "expert_actions": item.get("expert_action", []),
                "source": HF_DATASET_NAME,
                "version": "1.0.0-frozen"
            }
            tasks.append(task_def)

        # Create directory if it doesn't exist
        TASK_BANK_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write the frozen artifact
        with open(TASK_BANK_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

        return TASK_BANK_PATH

    except Exception as e:
        raise FileNotFoundError(
            f"Failed to load or generate frozen task bank at {TASK_BANK_PATH}. "
            f"Local file missing and remote source fetch failed: {e}"
        ) from e

def get_task_definition(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single task definition from the frozen task bank.
    
    Args:
        task_id: The unique identifier for the task.
        
    Returns:
        A dictionary containing the task definition (goal, initial_state, etc.),
        or None if the task_id is not found.
        
    Raises:
        FileNotFoundError: If the task bank file does not exist and cannot be generated.
    """
    path = _ensure_task_bank_exists()
    
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    for task in tasks:
        if task.get("task_id") == task_id:
            return task
            
    return None

def list_task_ids() -> list:
    """
    Returns a list of all available task IDs in the bank.
    """
    path = _ensure_task_bank_exists()
    with open(path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    return [t["task_id"] for t in tasks]
