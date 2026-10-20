import os
import json
import csv
import time
import logging
import argparse
import random
import uuid
import psutil
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

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
        for skill in self.skills:
            # Use pre-computed embedding if available, otherwise compute
            if 'embedding_vector' in skill:
                skill_emb = np.array(skill['embedding_vector'])
            else:
                skill_emb = get_embedding(self.model, skill['function_code'])
            
            sim = cosine_similarity(task_embedding, skill_emb)
            similarities.append((skill, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in similarities[:k]]

def calculate_retrieval_precision(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str]) -> float:
    if not ground_truth_ids:
        return 0.0
    retrieved_ids = {s['skill_id'] for s in retrieved_skills}
    ground_truth_set = set(ground_truth_ids)
    intersection = retrieved_ids.intersection(ground_truth_set)
    return len(intersection) / len(retrieved_ids) if retrieved_ids else 0.0

def calculate_retrieval_diversity(retrieved_skills: List[Dict[str, Any]], ground_truth_ids: List[str], model, task_description: str) -> float:
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
    variance_val = sum((x - mean_sim)**2 for x in sims) / len(sims)
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

def run_task(task: Dict[str, Any], library: SkillLibrary, pruning_enabled: bool = False) -> Dict[str, Any]:
    task_id = task['task_id']
    description = task['description']
    ground_truth_ids = task.get('ground_truth_path', [])
    
    start_time = time.time()
    edge_case = ""
    
    try:
        # Memory limit check (SC-005 / Edge Case)
        mem = psutil.virtual_memory()
        if mem.used > 6 * 1024**3: # 6GB
            edge_case = "memory_limit"

        retrieved = library.retrieve_top_k(description, k=5)
        retrieved_ids = [s['skill_id'] for s in retrieved]
        
        # Check for missing skill edge case
        library_ids = {s['skill_id'] for s in library.skills}
        if any(gt not in library_ids for gt in ground_truth_ids):
            edge_case = "missing_skill"

        # Check for maximal overlap edge case (mean sim of top-k > 0.95)
        task_emb = get_embedding(library.model, description)
        sims = [cosine_similarity(task_emb, np.array(s.get('embedding_vector', get_embedding(library.model, s['function_code'])))) for s in retrieved]
        if sims and (sum(sims)/len(sims)) > 0.95:
            edge_case = "maximal_overlap"

        # Success logic: Does retrieval contain any of the ground truth skills?
        success = any(rid in ground_truth_ids for rid in retrieved_ids)
        
        # Execute the best retrieved skill to simulate real call
        if retrieved:
            execute_skill(retrieved[0], {})

        latency_ms = (time.time() - start_time) * 1000
        precision = calculate_retrieval_precision(retrieved, ground_truth_ids)
        diversity = calculate_retrieval_diversity(retrieved, ground_truth_ids, library.model, description)

        # Map failure_reason to enum: ["timeout", "missing_skill", "false_prune", "logic_error", ""]
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
            'tokens': 0, # Synthetic deterministic
            'retrieval_precision': precision,
            'retrieval_diversity': diversity,
            'retrieved_skill_ids': retrieved_ids,
            'edge_case': edge_case,
            'failure_reason': failure_reason
        }

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        return {
            'task_id': task_id, 
            'success': False, 
            'latency_ms': 0, 
            'tokens': 0, 
            'retrieval_precision': 0, 
            'retrieval_diversity': 0, 
            'retrieved_skill_ids': [], 
            'edge_case': 'error', 
            'failure_reason': 'logic_error'
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library-size", type=int, default=50)
    parser.add_argument("--pruning", choices=["on", "off"], default="off")
    parser.add_argument("--overlap", choices=["LOW", "MEDIUM", "HIGH"], default="HIGH")
    parser.add_argument("--task-sample", type=int, default=100)
    args = parser.parse_args()

    pin_seeds()
    
    tasks_path = 'data/raw/tasks.json'
    skills_path = 'data/raw/skills.json'
    
    if not os.path.exists(tasks_path) or not os.path.exists(skills_path):
        logger.error("Data files not found.")
        return

    with open(tasks_path, 'r') as f:
        tasks_data = json.load(f)
        tasks = tasks_data['tasks'] if isinstance(tasks_data, dict) else tasks_data
    with open(skills_path, 'r') as f:
        skills_data = json.load(f)
        skills = skills_data['skills'] if isinstance(skills_data, dict) else skills_data

    # Sample library
    random.shuffle(skills)
    sampled_skills = skills[:args.library_size]
    library = SkillLibrary(sampled_skills)
    
    # Sample tasks
    random.shuffle(tasks)
    sampled_tasks = tasks[:args.task_sample]

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    exec_log_dir = "data/results/execution_logs"
    os.makedirs(exec_log_dir, exist_ok=True)
    exec_log_path = os.path.join(exec_log_dir, f"{run_id}.jsonl")
    
    exp_logger = get_logger()
    
    with open(exec_log_path, 'w') as jsonl_file:
        for task in sampled_tasks:
            res = run_task(task, library, pruning_enabled=(args.pruning == "on"))
            
            # CSV Logging (T005)
            # Columns: task_id, skill_id, success, latency, tokens, retrieval_precision, 
            # retrieval_diversity, pruning_risk_count, library_size, pruning_enabled, edge_case
            log_entry = {
                "task_id": res['task_id'],
                "skill_id": res['retrieved_skill_ids'][0] if res['retrieved_skill_ids'] else "none",
                "success": res['success'],
                "latency": res['latency_ms'],
                "tokens": res['tokens'],
                "retrieval_precision": res['retrieval_precision'],
                "retrieval_diversity": res['retrieval_diversity'],
                "pruning_risk_count": 0,
                "library_size": args.library_size,
                "pruning_enabled": args.pruning == "on",
                "edge_case": res['edge_case']
            }
            log_experiment_entry(log_entry)
            
            # JSON-L Logging (T006)
            exec_entry = {
                "log_id": str(uuid.uuid4()),
                "task_id": res['task_id'],
                "library_size": args.library_size,
                "pruning_enabled": args.pruning == "on",
                "success": res['success'],
                "failure_reason": res['failure_reason'],
                "token_usage": res['tokens'],
                "latency_ms": res['latency_ms'],
                "retrieved_skill_ids": res['retrieved_skill_ids'],
                "timestamp": datetime.utcnow().isoformat()
            }
            jsonl_file.write(json.dumps(exec_entry) + "\n")
                
    logger.info(f"Completed run {run_id}: processed {len(sampled_tasks)} tasks.")

if __name__ == "__main__":
    main()