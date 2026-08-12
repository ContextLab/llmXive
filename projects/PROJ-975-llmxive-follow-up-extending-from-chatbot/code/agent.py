import os
import json
import csv
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

# Importing from sibling modules as per API surface
from config import get_seeds, pin_seeds, get_experiment_config
from utils import get_model, get_embedding, cosine_similarity
from logging_config import get_logger, log_experiment_entry

logger = logging.getLogger(__name__)

class SkillLibrary:
    def __init__(self, skills: List[Dict[str, Any]]):
        self.skills = skills
        self.library_size = len(skills)
        self.model = get_model()

    def retrieve_top_k(self, task_description: str, k: int = 5) -> List[Dict[str, Any]]:
        task_embedding = get_embedding(self.model, task_description)
        similarities = []
        for idx, skill in enumerate(self.skills):
            skill_embedding = get_embedding(self.model, skill['function_code'])
            sim = cosine_similarity(task_embedding, skill_embedding)
            similarities.append((idx, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in similarities[:k]]
        return [self.skills[i] for i in top_indices]

def calculate_retrieval_precision(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str]) -> float:
    if not ground_truth_ids:
        return 0.0
    retrieved_ids = {s['skill_id'] for s in retrieved_skills}
    ground_truth_set = set(ground_truth_ids)
    intersection = retrieved_ids.intersection(ground_truth_set)
    return len(intersection) / len(retrieved_ids) if retrieved_ids else 0.0

def calculate_retrieval_diversity(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str], model) -> float:
    if not retrieved_skills or not ground_truth_ids:
        return 0.0
    
    # Calculate similarities of retrieved skills against the task (or avg ground truth embedding)
    # For simplicity and consistency with typical diversity metrics in this context:
    # We calculate the variance of similarities between retrieved skills and the task embedding.
    task_embedding = None # In a real scenario, we'd need the task embedding here. 
                          # Assuming the caller passes it or we derive it. 
                          # To avoid circular dependency in this snippet, we assume task_embedding is available 
                          # or we calculate pairwise among retrieved. 
                          # Let's calculate pairwise similarity variance among retrieved skills as a proxy for diversity.
    
    embeddings = [get_embedding(model, s['function_code']) for s in retrieved_skills]
    n = len(embeddings)
    if n < 2:
        return 0.0
    
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(cosine_similarity(embeddings[i], embeddings[j]))
    
    if not sims:
        return 0.0
    
    mean_sim = sum(sims) / len(sims)
    variance = sum((s - mean_sim) ** 2 for s in sims) / len(sims)
    return 1.0 / (1.0 + variance) if variance > 0 else 1.0

def execute_skill(skill: Dict[str, Any], inputs: Dict[str, Any]) -> Tuple[bool, Any, str]:
    """
    Executes a skill function. Returns (success, result, error_message).
    Handles missing skills or execution errors gracefully.
    """
    skill_id = skill.get('skill_id', 'unknown')
    func_code = skill.get('function_code', '')
    
    try:
        # Create a safe namespace for execution
        local_vars = {}
        exec(func_code, {}, local_vars)
        
        # Find the function name (assuming the code defines a function)
        func_name = None
        for k, v in local_vars.items():
            if callable(v) and not k.startswith('_'):
                func_name = k
                break
        
        if not func_name:
            return False, None, f"No executable function found in skill {skill_id}"
        
        func = local_vars[func_name]
        result = func(**inputs)
        return True, result, ""
    except Exception as e:
        return False, None, f"Execution error in {skill_id}: {str(e)}"

def run_task(task: Dict[str, Any], library: SkillLibrary, pruning_enabled: bool = False, pruning_interval: int = 10) -> Dict[str, Any]:
    """
    Runs a single task against the agent.
    Handles missing skills edge cases gracefully.
    """
    task_id = task['task_id']
    description = task['description']
    ground_truth_ids = task.get('ground_truth', [])
    
    start_time = time.time()
    tokens_used = 0 # Placeholder for token counting logic if integrated with an LLM
    
    try:
        retrieved = library.retrieve_top_k(description, k=5)
        
        # Check for missing skills (skills in retrieved that might be invalid or missing logic)
        # In this context, 'missing' could mean the skill exists in the list but fails execution
        # or if the ground truth skill is not in the library at all.
        
        execution_results = []
        success = False
        final_result = None
        error_msg = None
        
        # Check if any ground truth skill is missing from the library entirely
        library_ids = {s['skill_id'] for s in library.skills}
        missing_ground_truth = [gt for gt in ground_truth_ids if gt not in library_ids]
        
        if missing_ground_truth:
            # Log the missing skill IDs
            logger.warning(f"Task {task_id}: Ground truth skills missing from library: {missing_ground_truth}")
            # Record failure without crashing
            success = False
            error_msg = f"Missing ground truth skills: {missing_ground_truth}"
            retrieval_precision = 0.0
            retrieval_diversity = 0.0
        else:
            # Execute retrieved skills
            for skill in retrieved:
                # Simulate inputs (in a real scenario, task would define inputs)
                inputs = {} 
                is_success, result, err = execute_skill(skill, inputs)
                
                if is_success:
                    final_result = result
                    success = True
                    break
                else:
                    # Log missing/failed skill execution gracefully
                    logger.warning(f"Task {task_id}: Skill {skill['skill_id']} execution failed: {err}")
                    execution_results.append({'skill_id': skill['skill_id'], 'status': 'failed', 'error': err})
            
            if not success and not error_msg:
                error_msg = "All retrieved skills failed execution."
            
            # Calculate metrics
            retrieval_precision = calculate_retrieval_precision(retrieved, ground_truth_ids)
            retrieval_diversity = calculate_retrieval_diversity(retrieved, ground_truth_ids, library.model)

        end_time = time.time()
        latency = end_time - start_time

        return {
            'task_id': task_id,
            'success': success,
            'latency': latency,
            'tokens': tokens_used,
            'retrieval_precision': retrieval_precision,
            'retrieval_diversity': retrieval_diversity,
            'error': error_msg,
            'pruning_risk_count': 0 # Placeholder, to be updated by T028 logic if integrated
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed with unhandled exception: {e}")
        return {
            'task_id': task_id,
            'success': False,
            'latency': 0.0,
            'tokens': 0,
            'retrieval_precision': 0.0,
            'retrieval_diversity': 0.0,
            'error': str(e),
            'pruning_risk_count': 0
        }

def append_to_log(entry: Dict[str, Any], log_path: str):
    """
    Appends a log entry to the CSV file.
    Ensures headers are written once.
    """
    fieldnames = [
        'task_id', 'skill_id', 'success', 'latency', 'tokens', 
        'retrieval_precision', 'retrieval_diversity', 'pruning_risk_count', 
        'library_size', 'pruning_enabled', 'error'
    ]
    
    file_exists = os.path.isfile(log_path)
    
    with open(log_path, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        # Ensure all fields are present, filling missing with empty string or 0
        row = {k: entry.get(k, '') for k in fieldnames}
        writer.writerow(row)
        f.flush()
        os.fsync(f.fileno())

def main():
    """
    Main entry point for running the agent experiment.
    """
    pin_seeds()
    config = get_experiment_config()
    
    # Load data
    tasks_path = 'data/raw/tasks.json'
    skills_path = 'data/raw/skills.json'
    
    if not os.path.exists(tasks_path) or not os.path.exists(skills_path):
        logger.error("Data files not found. Run generate_data.py first.")
        return

    with open(tasks_path, 'r') as f:
        tasks = json.load(f)
    with open(skills_path, 'r') as f:
        skills = json.load(f)

    library = SkillLibrary(skills)
    log_path = 'data/results/experiment_log.csv'
    
    # Clear log file if it exists to start fresh for this run (optional, depending on requirements)
    if os.path.exists(log_path):
        os.remove(log_path)

    for task in tasks:
        result = run_task(task, library)
        append_to_log(result, log_path)
        logger.info(f"Completed task {task['task_id']}: Success={result['success']}")

if __name__ == "__main__":
    main()