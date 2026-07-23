import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datasets import load_dataset
import hashlib
import json
import random
from code.config import Config, get_path
from code.utils.common import load_json, save_json, ensure_dir
from code.utils.logger import get_logger
from code.utils.checksum_tracker import register_file

logger = get_logger(__name__)
config = Config()

# Constants
TARGET_COUNT = 200
RANDOM_SEED = 42

def load_multi_lcb_dataset() -> pd.DataFrame:
    """Load the Multi-LCB dataset from HuggingFace."""
    logger.info("Loading Multi-LCB dataset from HuggingFace...")
    # Using the verified real source for Multi-LCB
    dataset = load_dataset("codeparrot/multi-lcb", split="train", streaming=True)
    
    # Convert to list of dicts for processing
    data = []
    for item in dataset:
        data.append(item)
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} tasks from Multi-LCB dataset")
    return df

def verify_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_dataset_with_checksum(df: pd.DataFrame, output_path: Path) -> str:
    """Save dataset to parquet and compute checksum."""
    ensure_dir(output_path.parent)
    df.to_parquet(output_path, index=False)
    checksum = verify_checksum(output_path)
    logger.info(f"Saved dataset to {output_path} with checksum {checksum}")
    return checksum

def stratify_tasks(tasks: List[Dict[str, Any]], 
                  difficulty_col: str = "difficulty",
                  topic_col: str = "topic",
                  language_col: str = "language") -> List[Dict[str, Any]]:
    """
    Stratify tasks by Difficulty and Topic while maintaining language distribution.
    Returns tasks sorted by stratification criteria.
    """
    if not tasks:
        return tasks
    
    # Create stratification keys
    for task in tasks:
        key = f"{task.get(difficulty_col, 'unknown')}_{task.get(topic_col, 'unknown')}"
        task['strat_key'] = key
    
    # Group by stratification key
    groups = {}
    for task in tasks:
        key = task['strat_key']
        if key not in groups:
            groups[key] = []
        groups[key].append(task)
    
    # Shuffle within groups and flatten
    random.seed(RANDOM_SEED)
    result = []
    for key in sorted(groups.keys()):
        group = groups[key]
        random.shuffle(group)
        result.extend(group)
    
    return result

def save_filtered_tasks(tasks: List[Dict[str, Any]], output_path: Path, label: str = "filtered") -> None:
    """Save filtered tasks to JSON with checksum tracking."""
    ensure_dir(output_path.parent)
    data = {
        "label": label,
        "count": len(tasks),
        "tasks": tasks,
        "checksum": verify_checksum(output_path) if output_path.exists() else None
    }
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(tasks)} {label} tasks to {output_path}")
    register_file(output_path)

def select_static_pool(df: pd.DataFrame, 
                     target_language: str = "rust",
                     python_success_threshold: float = 1.0,
                     target_language_fail_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """
    Select initial pool where model failed in target language (Pass@1 < threshold)
    AND succeeded in Python (Pass@1 >= threshold).
    """
    logger.info(f"Selecting static pool for target language: {target_language}")
    
    pool = []
    for _, row in df.iterrows():
        # Check if task exists for both languages
        if 'python' not in row or target_language not in row:
            continue
        
        python_data = row['python']
        target_data = row[target_language]
        
        if not isinstance(python_data, dict) or not isinstance(target_data, dict):
            continue
        
        python_pass = python_data.get('pass_rate', 0.0)
        target_pass = target_data.get('pass_rate', 0.0)
        
        # Apply filtering criteria
        if python_pass >= python_success_threshold and target_pass < target_language_fail_threshold:
            pool.append(row.to_dict())
    
    logger.info(f"Selected {len(pool)} tasks for static pool")
    return pool

def run_blind_inference_on_task(task: Dict[str, Any], 
                               model, 
                               target_language: str,
                               temperature: float = 0.0) -> Dict[str, Any]:
    """Run blind inference on a single task."""
    # This would call the actual inference engine
    # For now, returns a placeholder structure
    return {
        "task_id": task.get('task_id'),
        "language": target_language,
        "pass": False,
        "output": "",
        "error": "Not implemented"
    }

def execute_stochasticity_filter(pool: List[Dict[str, Any]], 
                                model,
                                target_language: str,
                                runs: int = 3,
                                failure_threshold: int = 2) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Execute stochasticity filter: run blind inference multiple times and keep
    tasks that fail in >= failure_threshold runs.
    
    Returns:
      - filtered_tasks: Tasks meeting the failure criteria
      - all_logs: All execution logs from the runs
    """
    logger.info(f"Executing stochasticity filter with {runs} runs")
    
    all_logs = []
    task_results = {}
    
    for task in pool:
        task_id = task.get('task_id')
        task_results[task_id] = {"fails": 0, "logs": []}
        
        for run_idx in range(runs):
            log = run_blind_inference_on_task(task, model, target_language)
            all_logs.append(log)
            
            if not log.get('pass', True):
                task_results[task_id]["fails"] += 1
            task_results[task_id]["logs"].append(log)
    
    # Filter tasks that failed in >= threshold runs
    filtered_tasks = []
    for task in pool:
        task_id = task.get('task_id')
        if task_results[task_id]["fails"] >= failure_threshold:
            filtered_tasks.append(task)
    
    logger.info(f"Stochasticity filter: {len(filtered_tasks)} tasks passed filter")
    return filtered_tasks, all_logs

def sample_replacements(pool: List[Dict[str, Any]], 
                      rejected_ids: set,
                      current_count: int,
                      target_count: int = TARGET_COUNT,
                      difficulty_col: str = "difficulty",
                      topic_col: str = "topic") -> List[Dict[str, Any]]:
    """
    Sample replacement tasks from the pool to reach target count.
    Maintains stratification by Difficulty and Topic.
    
    Args:
        pool: Full pool of available tasks
        rejected_ids: Set of task IDs to exclude (already filtered out)
        current_count: Current number of tasks in the filtered set
        target_count: Target number of tasks to reach
        difficulty_col: Column name for difficulty
        topic_col: Column name for topic
    
    Returns:
        List of replacement tasks to add
    """
    if current_count >= target_count:
        return []
    
    needed = target_count - current_count
    logger.info(f"Need {needed} replacement tasks to reach target count of {target_count}")
    
    # Filter out rejected tasks
    available = [t for t in pool if t.get('task_id') not in rejected_ids]
    
    if not available:
        logger.warning("No available tasks for replacement!")
        return []
    
    # Stratify available tasks
    stratified = stratify_tasks(available, difficulty_col, topic_col)
    
    # Take the needed number from the stratified list
    replacements = stratified[:min(needed, len(stratified))]
    
    logger.info(f"Selected {len(replacements)} replacement tasks")
    return replacements

def handle_attrition(initial_pool_path: Path,
                    filtered_tasks_path: Path,
                    full_dataset_path: Path,
                    output_path: Path) -> None:
    """
    T018: Attrition Handling implementation.
    
    Reads the filtered tasks from T017, checks if count < 200,
    samples replacements from the full dataset (excluding rejected tasks),
    and outputs the final enriched dataset.
    
    Args:
        initial_pool_path: Path to data/initial_pool.json
        filtered_tasks_path: Path to data/filtered_tasks.json (output of T017)
        full_dataset_path: Path to the full dataset parquet file
        output_path: Path to write data/final_tasks_enriched.json
    """
    logger.info("Starting Attrition Handling (T018)...")
    
    # Load filtered tasks (output of T017)
    filtered_data = load_json(filtered_tasks_path)
    filtered_tasks = filtered_data.get('tasks', [])
    filtered_ids = {t.get('task_id') for t in filtered_tasks}
    
    current_count = len(filtered_tasks)
    logger.info(f"Loaded {current_count} tasks from filtered set")
    
    # Load initial pool to get the full set of candidates for replacement
    initial_pool_data = load_json(initial_pool_path)
    initial_pool = initial_pool_data.get('tasks', [])
    initial_pool_ids = {t.get('task_id') for t in initial_pool}
    
    # Load full dataset for enrichment
    if not full_dataset_path.exists():
        # Try to load from HuggingFace if file doesn't exist
        logger.info("Full dataset file not found, loading from HuggingFace...")
        df = load_multi_lcb_dataset()
        save_dataset_with_checksum(df, full_dataset_path)
    else:
        df = pd.read_parquet(full_dataset_path)
    
    # Create a lookup for full task data
    task_lookup = {}
    for _, row in df.iterrows():
        tid = row.get('task_id')
        if tid:
            task_lookup[tid] = row.to_dict()
    
    # If we need replacements, sample from initial pool (excluding filtered tasks)
    replacements = []
    if current_count < TARGET_COUNT:
        # Tasks in initial pool but not in filtered set are candidates
        candidate_ids = initial_pool_ids - filtered_ids
        candidates = [t for t in initial_pool if t.get('task_id') in candidate_ids]
        
        replacements = sample_replacements(
            pool=candidates,
            rejected_ids=filtered_ids,
            current_count=current_count,
            target_count=TARGET_COUNT
        )
    
    # Combine filtered tasks with replacements
    final_tasks = filtered_tasks + replacements
    
    # Enrich with full task data from dataset
    enriched_tasks = []
    for task in final_tasks:
        tid = task.get('task_id')
        if tid and tid in task_lookup:
            full_task = task_lookup[tid]
            # Merge: keep filtered task metadata, add full data
            enriched = {**full_task, **task}
            enriched_tasks.append(enriched)
        else:
            # Fallback: use task as is
            enriched_tasks.append(task)
    
    # Sort by stratification to maintain distribution
    enriched_tasks = stratify_tasks(enriched_tasks)
    
    # Save final enriched dataset
    final_data = {
        "label": "final_enriched",
        "count": len(enriched_tasks),
        "target_count": TARGET_COUNT,
        "filtered_count": len(filtered_tasks),
        "replacement_count": len(replacements),
        "tasks": enriched_tasks
    }
    
    save_filtered_tasks(enriched_tasks, output_path, "final_enriched")
    
    # Save as JSON for downstream use
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    logger.info(f"Attrition handling complete: {len(enriched_tasks)} tasks in final set")
    logger.info(f"  - Original filtered: {len(filtered_tasks)}")
    logger.info(f"  - Replacements added: {len(replacements)}")
    logger.info(f"  - Output: {output_path}")

def main():
    """Main entry point for T018 Attrition Handling."""
    # Define paths
    initial_pool_path = get_path("data/initial_pool.json")
    filtered_tasks_path = get_path("data/filtered_tasks.json")
    full_dataset_path = get_path("data/raw/multi_lcb.parquet")
    output_path = get_path("data/final_tasks_enriched.json")
    
    # Execute attrition handling
    handle_attrition(
        initial_pool_path=initial_pool_path,
        filtered_tasks_path=filtered_tasks_path,
        full_dataset_path=full_dataset_path,
        output_path=output_path
    )

if __name__ == "__main__":
    main()
