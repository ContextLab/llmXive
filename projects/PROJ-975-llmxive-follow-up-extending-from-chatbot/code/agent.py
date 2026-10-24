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

from config import get_seeds, pin_seeds
from utils import get_model, get_embedding, cosine_similarity
from logging_config import get_logger, log_experiment_entry

logger = logging.getLogger(__name__)

class SkillLibrary:
    def __init__(self, skills: List[Dict[str, Any]]):
        self.skills = skills
        self.library_size = len(skills)
        self.model = get_model()
        
        # Verify embedding dimensions (384)
        for s in self.skills:
            emb = np.array(s.get('embedding_vector', get_embedding(self.model, s['function_code'])))
            if emb.shape != (384,):
                raise ValueError(f"Embedding dimension mismatch: expected 384, got {emb.shape}")

    def retrieve_top_k(self, task_description: str, k: int = 5) -> List[Dict[str, Any]]:
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
    edge_case = "none"
    
    try:
        # Memory limit check (SC-005)
        mem = psutil.virtual_memory()
        if mem.used > 6 * 1024**3: # 6GB
            raise MemoryError("Memory Limit Exceeded")

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

        # Success logic: All ground truth skills must be retrieved to solve the multi-step task
        success = set(ground_truth_ids).issubset(set(retrieved_ids))
        
        # Simulate execution of retrieved skills
        for s in retrieved:
            execute_skill(s, {})

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

    except MemoryError as me:
        logger.error(f"Task {task_id} failed: {me}")
        raise me
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

    # Run ID for this configuration
    run_id = f"run_{args.library_size}_{args.pruning}_{args.overlap}"
    exec_log_dir = "data/results/execution_logs"
    os.makedirs(exec_log_dir, exist_ok=True)
    exec_log_path = os.path.join(exec_log_dir, f"{run_id}.jsonl")
    
    with open(exec_log_path, 'w') as jsonl_file:
        for task in sampled_tasks:
            res = run_task(task, library, pruning_enabled=(args.pruning == "on"))
            
            # CSV Logging (Strictly matching LOG_COLUMNS from logging_config.py)
            # run_id, task_id, library_size, pruning_enabled, success, latency_ms, tokens_used, retrieval_precision, retrieval_diversity, edge_case
            log_entry = {
                "run_id": run_id,
                "task_id": res['task_id'],
                "library_size": args.library_size,
                "pruning_enabled": args.pruning == "on",
                "success": res['success'],
                "latency_ms": res['latency_ms'],
                "tokens_used": res['tokens'],
                "retrieval_precision": res['retrieval_precision'],
                "retrieval_diversity": res['retrieval_diversity'],
                "edge_case": res['edge_case']
            }
            log_experiment_entry(log_entry)
            
            # JSON-L Logging (Strictly matching contracts/execution_log.schema.yaml)
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
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            jsonl_file.write(json.dumps(exec_entry) + "\n")
                
        logger.info(f"Completed run {run_id}: processed {len(sampled_tasks)} tasks.")

if __name__ == "__main__":
    main()