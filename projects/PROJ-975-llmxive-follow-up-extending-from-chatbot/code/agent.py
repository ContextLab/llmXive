import os
import json
import csv
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

# Local imports matching API surface
from utils import get_model, get_embedding, cosine_similarity, pairwise_cosine_similarity_matrix
from logging_config import CSVLogHandler, get_logger, log_experiment_entry
from config import get_seeds, get_experiment_config

# --- Constants ---
LOG_PATH = "data/results/experiment_log.csv"
SKILLS_PATH = "data/raw/skills.json"
TASKS_PATH = "data/raw/tasks.json"

# --- Global Model Cache ---
_model_cache: Optional[SentenceTransformer] = None

def _get_cached_model() -> SentenceTransformer:
    global _model_cache
    if _model_cache is None:
        _model_cache = get_model()
    return _model_cache

class SkillLibrary:
    """Manages the collection of skills, their embeddings, and retrieval logic."""
    
    def __init__(self, skills_data: List[Dict[str, Any]]):
        self.skills = skills_data
        self.skill_map = {s['id']: s for s in skills_data}
        self.embeddings = np.array([np.array(s['embedding']) for s in skills_data])
        self.skill_ids = [s['id'] for s in skills_data]
        self.logger = get_logger(__name__)

    def retrieve_top_k(self, task_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k skills based on cosine similarity to task embedding."""
        if len(self.embeddings) == 0:
            return []
        
        sims = cosine_similarity(task_embedding, self.embeddings)
        top_k_indices = np.argsort(sims)[-k:][::-1]
        
        retrieved = []
        for idx in top_k_indices:
            retrieved.append({
                'id': self.skill_ids[idx],
                'skill': self.skills[idx],
                'similarity': float(sims[idx])
            })
        return retrieved

    def execute_skill(self, skill_id: str, inputs: Dict[str, Any]) -> Any:
        """
        Execute a skill by ID.
        
        Returns the result of the skill execution.
        Raises KeyError if skill_id is not found in the library.
        """
        if skill_id not in self.skill_map:
            # This is the critical edge case for T024
            raise KeyError(f"Skill with ID '{skill_id}' not found in library.")
        
        skill_def = self.skill_map[skill_id]
        # Simulate execution based on skill definition
        # In a real scenario, this would eval/compile and run the function
        # For this synthetic environment, we simulate based on metadata
        return f"Executed {skill_id} with inputs {inputs}"

def calculate_retrieval_precision(retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
    """Calculate Jaccard similarity between retrieved and ground truth sets."""
    if not ground_truth_ids:
        return 0.0
    if not retrieved_ids:
        return 0.0
    
    r_set = set(retrieved_ids)
    g_set = set(ground_truth_ids)
    intersection = len(r_set.intersection(g_set))
    union = len(r_set.union(g_set))
    return intersection / union if union > 0 else 0.0

def calculate_retrieval_diversity(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str]) -> float:
    """
    Calculate Retrieval Diversity as inverse of variance of cosine similarities
    of top-k retrieved skills against the ground truth set.
    """
    if not retrieved_skills or not ground_truth_ids:
        return 0.0
    
    # Get embeddings for ground truth skills
    gt_ids = set(ground_truth_ids)
    similarities = []
    
    for skill_entry in retrieved_skills:
        if skill_entry['id'] in gt_ids:
            similarities.append(skill_entry['similarity'])
    
    if not similarities:
        return 0.0
    
    # Variance of similarities
    var = np.var(similarities)
    if var == 0:
        return float('inf') # Perfectly diverse (all same similarity? or no variance)
    return 1.0 / var

def append_to_log(entry: Dict[str, Any], path: str = LOG_PATH):
    """Append a dictionary entry to the CSV log file."""
    file_exists = os.path.isfile(path)
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

def run_task(
    task: Dict[str, Any], 
    library: SkillLibrary, 
    k: int = 5,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Execute a single task against the skill library.
    
    Handles missing skill edge cases gracefully (T024):
    - Catches KeyError if a ground-truth skill is missing.
    - Logs the missing skill ID.
    - Records failure in the log without crashing.
    """
    task_id = task['id']
    task_embedding = np.array(task['embedding'])
    ground_truth_ids = task['ground_truth']
    
    # Initialize logger if not provided
    if logger is None:
        logger = get_logger(__name__)
    
    start_time = time.time()
    
    try:
        # 1. Retrieve skills
        retrieved = library.retrieve_top_k(task_embedding, k=k)
        retrieved_ids = [r['id'] for r in retrieved]
        
        # 2. Calculate Metrics
        precision = calculate_retrieval_precision(retrieved_ids, ground_truth_ids)
        diversity = calculate_retrieval_diversity(retrieved, ground_truth_ids)
        
        # 3. Execute Ground Truth Skills (Simulation)
        # We attempt to execute the skills in the ground truth path
        execution_success = True
        missing_skill_id = None
        
        for skill_id in ground_truth_ids:
            try:
                # This will raise KeyError if the skill is missing from the library
                library.execute_skill(skill_id, task.get('inputs', {}))
            except KeyError as e:
                # T024: Handle missing skill edge case
                missing_skill_id = skill_id
                execution_success = False
                logger.warning(f"Task {task_id} failed: Missing skill '{skill_id}' in library.")
                # Log the specific missing skill to the main logger for audit
                logger.error(f"MISSING_SKILL: task_id={task_id}, missing_skill_id={skill_id}")
                break # Stop execution for this task
        
        end_time = time.time()
        latency = end_time - start_time
        
        # 4. Prepare Log Entry
        entry = {
            'task_id': task_id,
            'skill_id': missing_skill_id if not execution_success else retrieved_ids[0] if retrieved else None,
            'success': execution_success,
            'latency': latency,
            'tokens': len(ground_truth_ids) * 10, # Simulated token count
            'retrieval_precision': precision,
            'retrieval_diversity': diversity,
            'pruning_risk_count': 0, # Placeholder, updated by pruning logic
            'library_size': len(library.skills),
            'pruning_enabled': False # Placeholder
        }
        
        return entry

    except Exception as e:
        # Fallback for any other unexpected errors
        logger.error(f"Unexpected error running task {task_id}: {e}")
        end_time = time.time()
        return {
            'task_id': task_id,
            'skill_id': None,
            'success': False,
            'latency': end_time - start_time,
            'tokens': 0,
            'retrieval_precision': 0.0,
            'retrieval_diversity': 0.0,
            'pruning_risk_count': 0,
            'library_size': len(library.skills),
            'pruning_enabled': False
        }

def main():
    """Main entry point for the agent execution."""
    logger = get_logger(__name__)
    logger.info("Starting Agent Execution")
    
    # Load data
    if not os.path.exists(SKILLS_PATH):
        raise FileNotFoundError(f"Skills file not found at {SKILLS_PATH}. Run generate_data.py first.")
    if not os.path.exists(TASKS_PATH):
        raise FileNotFoundError(f"Tasks file not found at {TASKS_PATH}. Run generate_data.py first.")
    
    with open(SKILLS_PATH, 'r') as f:
        skills_data = json.load(f)['skills']
    
    with open(TASKS_PATH, 'r') as f:
        tasks_data = json.load(f)['tasks']
    
    library = SkillLibrary(skills_data)
    
    # Run a subset or all tasks
    # For this task, we run a small subset to demonstrate the missing skill handling
    # In a real run, this would iterate all tasks
    subset = tasks_data[:10] 
    
    for task in subset:
        result = run_task(task, library, logger=logger)
        append_to_log(result)
        logger.info(f"Completed task {task['id']}: Success={result['success']}")
    
    logger.info("Agent Execution Complete")

if __name__ == "__main__":
    main()