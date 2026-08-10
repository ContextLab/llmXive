import os
import json
import csv
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

from utils import get_model, get_embedding, cosine_similarity
from config import get_experiment_config, get_seeds
from logging_config import get_logger, log_experiment_entry

# Configure logger
logger = get_logger(__name__)

class SkillLibrary:
    """Manages the collection of skills and their embeddings."""
    
    def __init__(self, skills: List[Dict[str, Any]], model_name: str = "all-MiniLM-L6-v2"):
        self.skills = skills
        self.model_name = model_name
        self.model = get_model(model_name)
        self.embeddings = None
        self._embed()

    def _embed(self):
        """Pre-compute embeddings for all skills."""
        logger.info(f"Embedding {len(self.skills)} skills...")
        skill_texts = [s['code'] for s in self.skills]
        self.embeddings = get_embedding(self.model, skill_texts)
        logger.info("Embedding complete.")

    def retrieve(self, task_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k skills based on cosine similarity."""
        similarities = cosine_similarity(task_embedding, self.embeddings)
        top_k_indices = similarities.argsort()[0][-k:][::-1]
        return [self.skills[i] for i in top_k_indices]

    def get_skill_by_id(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific skill by its ID."""
        for skill in self.skills:
            if skill['id'] == skill_id:
                return skill
        return None

def calculate_retrieval_precision(retrieved_ids: List[int], ground_truth_ids: List[int]) -> float:
    """
    Calculate Retrieval Precision using Jaccard similarity.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    if not retrieved_ids and not ground_truth_ids:
        return 1.0
    if not retrieved_ids or not ground_truth_ids:
        return 0.0
    
    set_retrieved = set(retrieved_ids)
    set_ground_truth = set(ground_truth_ids)
    
    intersection = len(set_retrieved.intersection(set_ground_truth))
    union = len(set_retrieved.union(set_ground_truth))
    
    return intersection / union if union > 0 else 0.0

def calculate_retrieval_diversity(retrieved_skills: List[Dict[str, Any]], 
                                  task_embedding: np.ndarray, 
                                  ground_truth_ids: List[int],
                                  library: SkillLibrary) -> float:
    """
    Calculate Retrieval Diversity as the inverse of the variance of cosine similarities
    of the retrieved skills against the ground-truth set.
    
    Note: The task description says "against the ground-truth set". 
    We interpret this as calculating the similarity of each retrieved skill 
    to the centroid (or average embedding) of the ground-truth skills.
    """
    if not retrieved_skills:
        return 0.0

    # Get embeddings for ground truth skills
    gt_skills = [library.get_skill_by_id(gid) for gid in ground_truth_ids if library.get_skill_by_id(gid)]
    if not gt_skills:
        return 0.0
    
    gt_embeddings = get_embedding(library.model, [s['code'] for s in gt_skills])
    if gt_embeddings.shape[0] == 0:
        return 0.0
        
    # Centroid of ground truth
    gt_centroid = gt_embeddings.mean(axis=0)
    if len(gt_centroid.shape) == 1:
        gt_centroid = gt_centroid.reshape(1, -1)

    similarities = []
    for skill in retrieved_skills:
        skill_emb = get_embedding(library.model, [skill['code']])[0]
        sim = cosine_similarity(skill_emb.reshape(1, -1), gt_centroid)[0][0]
        similarities.append(sim)

    if len(similarities) < 2:
        return 0.0
        
    variance = np.var(similarities)
    if variance == 0:
        return 1.0 # Max diversity if all similar (or undefined variance)
    
    # Inverse variance (normalized or simple inverse)
    # To avoid huge numbers, we can use 1 / (1 + variance) or similar, 
    # but the spec says "inverse of the variance".
    # Let's use a normalized inverse to keep it bounded [0, 1] roughly.
    # Or strictly: 1/variance. If variance is small, diversity is high.
    # Let's use a simple scaling: 1 / (1 + variance) to prevent infinity.
    return 1.0 / (1.0 + variance)

def execute_skill(skill_code: str, task_input: Dict[str, Any]) -> Tuple[bool, Any, str]:
    """
    Safely execute a skill's code against a task input.
    Returns (success, result, error_message).
    """
    # Create a safe namespace
    safe_globals = {"__builtins__": __builtins__}
    safe_locals = {}
    
    try:
        # Compile the code
        compiled = compile(skill_code, "<string>", "exec")
        exec(compiled, safe_globals, safe_locals)
        
        # The skill is expected to define a function named 'run' or similar?
        # Based on the "Digital Colleague" context, skills are likely functions.
        # We assume the generated code defines a function `run` that takes `input_data`.
        # If the generated code is just a block, we try to evaluate it?
        # Let's assume the standard pattern: the code defines `def run(data): ...`
        
        if 'run' in safe_locals:
            result = safe_locals['run'](task_input)
            return True, result, ""
        else:
            # Fallback: try to find any callable that isn't 'run' but might be the entry
            # Or if the code is just an expression (unlikely for a skill)
            # For robustness, let's assume the skill defines a function named 'execute' or 'run'
            # If neither, we fail.
            return False, None, "Skill code did not define a callable 'run' function."
            
    except Exception as e:
        return False, None, str(e)

def run_task(task: Dict[str, Any], 
             retrieved_skills: List[Dict[str, Any]], 
             library: SkillLibrary) -> Tuple[bool, Any, str]:
    """
    Execute the retrieved skills to solve the task.
    Compares the output against the ground-truth solution path.
    
    Logic:
    1. Extract task input.
    2. Iterate through retrieved skills.
    3. Execute each skill.
    4. If a skill produces the expected output (or matches the ground truth path logic), return success.
    5. If no skill works, return failure.
    
    Note: Since we are comparing against a "ground-truth solution path" (list of skill IDs),
    we check if the *combination* of retrieved skills contains the necessary skills to form the path,
    OR if executing the retrieved skills yields the same result as the ground truth execution.
    
    Given the synthetic nature, we assume:
    - The task has a 'ground_truth_path' (list of skill IDs).
    - The 'retrieved_skills' are candidates.
    - If the intersection of retrieved IDs and ground truth IDs is non-empty (and sufficient), 
      we might consider it a partial success, but the spec says "compare output".
    
    Refined Logic for "Compare Output":
    - We simulate the execution of the Ground Truth Path (GT) to get the "Correct Answer".
    - We simulate the execution of the Retrieved Path (or just the retrieved skills) to get the "Agent Answer".
    - If Agent Answer == Correct Answer, Success.
    """
    
    # 1. Determine the correct answer by executing the ground truth path
    gt_path = task.get('ground_truth_path', [])
    task_input = task.get('input', {})
    expected_output = None
    gt_success = False
    
    # Execute GT path sequentially (assuming skills are composable or the last one matters)
    # For simplicity in this synthetic setup, we assume the last skill in the GT path produces the final output.
    # Or we execute all and check if the final state matches.
    # Let's assume the task's 'expected_output' field is pre-calculated or we compute it.
    # Since tasks.json is generated, it likely has 'expected_output' or we compute it.
    # If not, we compute it here.
    
    if 'expected_output' in task:
        expected_output = task['expected_output']
    else:
        # Fallback: execute GT skills
        for gid in gt_path:
            skill = library.get_skill_by_id(gid)
            if skill:
                success, res, err = execute_skill(skill['code'], task_input)
                if success:
                    expected_output = res
                    gt_success = True
                else:
                    break # GT failed, weird for synthetic data
    
    # 2. Execute retrieved skills
    # Strategy: Try each retrieved skill. If any produces the expected output, success.
    # Or, if the retrieved set contains the GT skills, we might just trust the logic?
    # The spec says "compare output".
    
    agent_success = False
    agent_output = None
    
    for skill in retrieved_skills:
        success, res, err = execute_skill(skill['code'], task_input)
        if success:
            agent_output = res
            # Compare outputs
            if expected_output is not None:
                # Handle type differences (e.g. float precision)
                try:
                    if isinstance(expected_output, float) and isinstance(res, float):
                        if abs(expected_output - res) < 1e-6:
                            agent_success = True
                            break
                    elif res == expected_output:
                        agent_success = True
                        break
                except:
                    if res == expected_output:
                        agent_success = True
                        break
            else:
                # If no expected output defined, assume success if it ran?
                # No, we need a comparison. If GT failed, we can't compare.
                pass
    
    return agent_success, agent_output, "Success" if agent_success else "Output mismatch or execution failed"

def append_to_log(entry: Dict[str, Any], log_path: str):
    """Append an entry to the CSV log file."""
    file_exists = os.path.isfile(log_path)
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)
        f.flush()
        os.fsync(f.fileno())

def main():
    """
    Main entry point for the agent execution.
    Loads tasks, skills, runs the experiment, and logs results.
    """
    # Load configuration
    config = get_experiment_config()
    seeds = get_seeds()
    
    # Load data
    tasks_path = "data/raw/tasks.json"
    skills_path = "data/raw/skills.json"
    
    if not os.path.exists(tasks_path) or not os.path.exists(skills_path):
        logger.error("Data files not found. Run generate_data.py first.")
        return

    with open(tasks_path, 'r') as f:
        tasks = json.load(f)
    with open(skills_path, 'r') as f:
        skills = json.load(f)
    
    logger.info(f"Loaded {len(tasks)} tasks and {len(skills)} skills.")
    
    # Initialize library
    library = SkillLibrary(skills)
    
    log_path = "data/results/experiment_log.csv"
    
    # Run tasks
    for task in tasks:
        start_time = time.time()
        
        # Embed task
        task_emb = get_embedding(library.model, [task['input']['query']])[0]
        
        # Retrieve
        retrieved = library.retrieve(task_emb, k=5)
        retrieved_ids = [s['id'] for s in retrieved]
        gt_ids = task.get('ground_truth_path', [])
        
        # Calculate metrics
        precision = calculate_retrieval_precision(retrieved_ids, gt_ids)
        diversity = calculate_retrieval_diversity(retrieved, task_emb, gt_ids, library)
        
        # Execute
        success, output, msg = run_task(task, retrieved, library)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Log
        entry = {
            "task_id": task['id'],
            "skill_id": retrieved_ids[0] if retrieved_ids else None, # Primary skill
            "success": success,
            "latency": latency,
            "tokens": len(task['input']['query']) * 4, # Approximate tokens
            "retrieval_precision": precision,
            "retrieval_diversity": diversity,
            "pruning_risk_count": 0, # Placeholder for T028
            "library_size": len(skills),
            "pruning_enabled": False
        }
        
        append_to_log(entry, log_path)
        logger.info(f"Task {task['id']}: Success={success}, Precision={precision:.4f}, Latency={latency:.4f}s")

if __name__ == "__main__":
    main()