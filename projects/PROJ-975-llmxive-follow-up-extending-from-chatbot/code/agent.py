import os
import json
import time
import logging
import argparse
import random
import uuid
import psutil
import numpy as np
from datetime import datetime
from itertools import product
from typing import List, Dict, Any, Tuple

from config import pin_seeds
from utils import get_model, get_embedding, cosine_similarity
from logging_config import log_experiment_entry
from pruning import prune_fr04

logger = logging.getLogger(__name__)

class SkillLibrary:
    """
    Wrapper around a list of skill dictionaries providing retrieval based on cosine similarity.
    """
    def __init__(self, skills: List[Dict[str, Any]]):
        self.skills = skills
        self.library_size = len(skills)
        self.model = get_model()

        # Verify embedding dimensions (384) for each skill
        for s in self.skills:
            emb = np.array(s.get('embedding_vector', get_embedding(self.model, s['function_code'])))
            if emb.shape != (384,):
                raise ValueError(f"Embedding dimension mismatch: expected 384, got {emb.shape}")

    def retrieve_top_k(self, task_description: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve the top‑k most similar skills to the given task description.
        """
        task_embedding = get_embedding(self.model, task_description)
        similarities = []
        for skill in self.skills:
            if 'embedding_vector' in skill:
                skill_emb = np.array(skill['embedding_vector'])
            else:
                skill_emb = get_embedding(self.model, skill['function_code'])
            sim = cosine_similarity(task_embedding, skill_emb)
            similarities.append((skill, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in similarities[:k]]

    def update_library(self, new_skills: List[Dict[str, Any]]) -> None:
        """
        Replace the internal skill list with a new (pruned) list.
        """
        self.skills = new_skills
        self.library_size = len(new_skills)

def calculate_retrieval_precision(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str]) -> float:
    if not ground_truth_ids:
        return 0.0
    retrieved_ids = {s['skill_id'] for s in retrieved_skills}
    ground_truth_set = set(ground_truth_ids)
    intersection = retrieved_ids.intersection(ground_truth_set)
    return len(intersection) / len(retrieved_ids) if retrieved_ids else 0.0

def calculate_retrieval_diversity(retrieved_skills: List[Dict[str, Any]],
                                  ground_truth_ids: List[str],
                                  model,
                                  task_description: str) -> float:
    if not retrieved_skills or not ground_truth_ids:
        return 0.0

    task_emb = get_embedding(model, task_description)
    sims = []
    for s in retrieved_skills:
        if 'embedding_vector' in s:
            s_emb = np.array(s['embedding_vector'])
        else:
            s_emb = get_embedding(model, s['function_code'])
        sims.append(cosine_similarity(task_emb, s_emb))

    if len(sims) < 2:
        return 0.0

    mean_sim = sum(sims) / len(sims)
    variance_val = sum((x - mean_sim) ** 2 for x in sims) / len(sims)
    return 1.0 / (1.0 + variance_val)

def execute_skill(skill: Dict[str, Any], inputs: Dict[str, Any]) -> Tuple[bool, Any, str]:
    skill_id = skill.get('skill_id', 'unknown')
    func_code = skill.get('function_code', '')
    try:
        local_vars = {}
        exec(func_code, {}, local_vars)
        func_name = next((k for k, v in local_vars.items() if callable(v) and not k.startswith('_')), None)
        if not func_name:
            return False, None, f"No executable function found in skill {skill_id}"
        result = local_vars[func_name](**inputs)
        return True, result, ""
    except Exception as e:
        return False, None, f"Execution error in {skill_id}: {str(e)}"

def run_task(task: Dict[str, Any],
             library: SkillLibrary,
             pruning_enabled: bool = False) -> Dict[str, Any]:
    """
    Execute a single task against the provided skill library.
    Returns a dictionary of metrics for logging.
    """
    task_id = task['task_id']
    description = task['description']
    # The schema expects ground_truth_skills; some datasets also provide ground_truth_path.
    ground_truth_ids = task.get('ground_truth_skills') or task.get('ground_truth_path') or []

    start_time = time.time()
    edge_case = "none"

    try:
        # Memory limit check (SC‑005)
        mem = psutil.virtual_memory()
        if mem.used > 6 * 1024**3:  # 6 GB
            raise MemoryError("Memory Limit Exceeded")

        retrieved = library.retrieve_top_k(description, k=5)
        retrieved_ids = [s['skill_id'] for s in retrieved]

        # Edge‑case: missing ground‑truth skill in the active library
        library_ids = {s['skill_id'] for s in library.skills}
        if any(gt not in library_ids for gt in ground_truth_ids):
            edge_case = "missing_skill"

        # Edge‑case: maximal overlap (mean similarity > 0.95)
        task_emb = get_embedding(library.model, description)
        sims = [
            cosine_similarity(task_emb,
                              np.array(s.get('embedding_vector',
                                             get_embedding(library.model, s['function_code']))))
            for s in retrieved
        ]
        if sims and (sum(sims) / len(sims)) > 0.95:
            edge_case = "maximal_overlap"

        # Success: all ground‑truth skills must be among the retrieved set
        success = set(ground_truth_ids).issubset(set(retrieved_ids))

        # Simulate execution of the retrieved skills (deterministic, no side‑effects)
        for s in retrieved:
            execute_skill(s, {})

        latency_ms = (time.time() - start_time) * 1000
        precision = calculate_retrieval_precision(retrieved, ground_truth_ids)
        diversity = calculate_retrieval_diversity(retrieved,
                                                  ground_truth_ids,
                                                  library.model,
                                                  description)

        failure_reason = ""
        if not success:
            if edge_case == "missing_skill":
                failure_reason = "missing_skill"
            else:
                failure_reason = "logic_error"

        return {
            'task_id': task_id,
            'success': success,
            'latency_ms': latency_ms,
            'tokens': 0,  # synthetic deterministic token count
            'retrieval_precision': precision,
            'retrieval_diversity': diversity,
            'retrieved_skill_ids': retrieved_ids,
            'edge_case': edge_case,
            'failure_reason': failure_reason
        }

    except MemoryError as me:
        logger.error(f"Task {task_id} failed: {me}")
        raise
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        return {
            'task_id': task_id,
            'success': False,
            'latency_ms': 0,
            'tokens': 0,
            'retrieval_precision': 0.0,
            'retrieval_diversity': 0.0,
            'retrieved_skill_ids': [],
            'edge_case': 'error',
            'failure_reason': 'logic_error'
        }

def main():
    """
    Entry point for the full factorial sweep.

    CLI flags:
      --library-sizes 10 20 30 ...   list of library sizes to test (required)
      --task-sample INT              number of tasks to sample from the 500‑task pool (default 500)
      --overlap LEVEL                optional; if omitted all three levels are used (LOW/MEDIUM/HIGH)
      --pruning [off|fr04|on] ...    optional; one or more pruning variants; 'on' is an alias for 'fr04'
      --seed INT                     optional seed for reproducibility
      --randomize-tasks              optional flag to shuffle tasks before sampling
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library-sizes",
        type=int,
        nargs="+",
        required=True,
        help="List of library sizes to evaluate (e.g., 10 20 30 ...)."
    )
    parser.add_argument(
        "--task-sample",
        type=int,
        default=500,
        help="Number of tasks to sample from the full task pool."
    )
    parser.add_argument(
        "--overlap",
        type=str,
        nargs="*",
        default=None,
        help="Overlap level(s) to use (LOW, MEDIUM, HIGH). If omitted, all three levels are evaluated."
    )
    parser.add_argument(
        "--pruning",
        nargs="+",
        default=["off"],
        choices=["off", "fr04", "on"],
        help="Pruning variant(s): 'off' disables pruning, 'fr04' or 'on' enables the FR‑004 heuristic."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducibility."
    )
    parser.add_argument(
        "--randomize-tasks",
        action="store_true",
        help="If set, shuffle the task list before sampling."
    )
    args = parser.parse_args()

    # Normalise overlap selection
    if args.overlap:
        overlap_levels = [lvl.upper() for lvl in args.overlap]
    else:
        overlap_levels = ["LOW", "MEDIUM", "HIGH"]

    # Normalise pruning flags (map 'on' -> 'fr04')
    pruning_flags = []
    for p in args.pruning:
        if p in ("fr04", "on"):
            pruning_flags.append("fr04")
        else:
            pruning_flags.append("off")

    # Set seeds if provided
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
        os.environ["SEED_A"] = str(args.seed)
        os.environ["SEED_B"] = str(args.seed)

    pin_seeds()

    # Load raw data
    tasks_path = os.path.join("data", "raw", "tasks.json")
    skills_path = os.path.join("data", "raw", "skills.json")

    if not os.path.exists(tasks_path) or not os.path.exists(skills_path):
        logger.error("Data files not found.")
        return

    with open(tasks_path, "r") as f:
        tasks_data = json.load(f)
        tasks = tasks_data["tasks"] if isinstance(tasks_data, dict) else tasks_data

    with open(skills_path, "r") as f:
        skills_data = json.load(f)
        skills = skills_data["skills"] if isinstance(skills_data, dict) else skills_data

    # Ensure deterministic ordering for reproducibility
    random.shuffle(skills)

    # Prepare execution‑log directory
    exec_log_dir = os.path.join("data", "results", "execution_logs")
    os.makedirs(exec_log_dir, exist_ok=True)

    # Clean any existing experiment CSV so we start fresh (remove placeholder rows)
    csv_path = os.path.join("data", "results", "experiment_log.csv")
    if os.path.exists(csv_path):
        try:
            os.remove(csv_path)
        except OSError as e:
            logger.warning(f"Could not delete existing CSV log: {e}")

    # Iterate over the Cartesian product of configurations
    for lib_size, overlap, pruning_flag in product(args.library_sizes, overlap_levels, pruning_flags):
        # Sample a fresh library for this configuration
        sampled_skills = skills[:lib_size]
        library = SkillLibrary(sampled_skills)

        pruning_enabled = pruning_flag == "fr04"

        # Create a unique run identifier
        run_id = f"run_{lib_size}_{pruning_flag}_{overlap}"
        exec_log_path = os.path.join(exec_log_dir, f"{run_id}.jsonl")

        # Determine which tasks to process (sample without replacement)
        if args.task_sample >= len(tasks):
            selected_tasks = tasks
        else:
            selected_tasks = random.sample(tasks, args.task_sample)

        # Optionally randomize order
        if args.randomize_tasks:
            random.shuffle(selected_tasks)

        # Open JSON‑L file for this run
        with open(exec_log_path, "w") as jsonl_file:
            # Process the selected tasks
            for idx, task in enumerate(selected_tasks):
                res = run_task(task, library, pruning_enabled=pruning_enabled)

                # CSV logging via the shared logger
                log_entry = {
                    "run_id": run_id,
                    "task_id": res["task_id"],
                    "library_size": library.library_size,  # may have changed due to pruning
                    "pruning_enabled": pruning_enabled,
                    "success": res["success"],
                    "latency_ms": res["latency_ms"],
                    "tokens_used": res["tokens"],
                    "retrieval_precision": res["retrieval_precision"],
                    "retrieval_diversity": res["retrieval_diversity"],
                    "edge_case": res["edge_case"]
                }
                log_experiment_entry(log_entry)

                # JSON‑L entry adhering to contracts/execution_log.schema.yaml
                exec_entry = {
                    "log_id": str(uuid.uuid4()),
                    "task_id": res["task_id"],
                    "library_size": library.library_size,
                    "pruning_enabled": pruning_enabled,
                    "success": res["success"],
                    "failure_reason": res["failure_reason"],
                    "token_usage": res["tokens"],
                    "latency_ms": res["latency_ms"],
                    "retrieved_skill_ids": res["retrieved_skill_ids"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                jsonl_file.write(json.dumps(exec_entry) + "\n")

                # Apply pruning after every 10 tasks if enabled
                if pruning_enabled and ((idx + 1) % 10 == 0):
                    pruned_lib, false_prune_count = prune_fr04(library.skills)
                    library.update_library(pruned_lib)
                    # false_prune_count is retained for downstream analysis but not logged here

        logger.info(
            f"Completed run {run_id}: processed {len(selected_tasks)} tasks "
            f"with pruning={'on' if pruning_enabled else 'off'} at overlap {overlap}."
        )

    logger.info("All configurations have been processed.")

if __name__ == "__main__":
    main()
