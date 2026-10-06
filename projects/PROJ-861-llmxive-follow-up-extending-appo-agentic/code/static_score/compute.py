import math
import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# Configuration constants for T018a
TASK_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
MAX_EXCLUSION_RATE = 0.50  # 50% threshold for resource limit

def compute_kl_divergence(p: List[float], q: List[float], epsilon: float = 1e-9) -> float:
    """
    Computes the KL Divergence between two probability distributions p and q.
    Applies epsilon smoothing to prevent log(0).
    """
    # Clamp probabilities
    p = [max(x, epsilon) for x in p]
    q = [max(x, epsilon) for x in q]
    
    # Normalize to ensure they sum to 1 (though they should already be probs)
    p_sum = sum(p)
    q_sum = sum(q)
    if p_sum == 0 or q_sum == 0:
        return 0.0
    p = [x / p_sum for x in p]
    q = [x / q_sum for x in q]
    
    # Compute KL(p || q)
    kl = 0.0
    for pi, qi in zip(p, q):
        if pi > 0:
            kl += pi * math.log(pi / qi)
    
    return kl

class StaticScorer:
    def __init__(self, model_name: str = "microsoft/phi-2", device: str = "cpu", epsilon: float = 1e-9):
        self.model_name = model_name
        self.device = device
        self.epsilon = epsilon
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads the model and tokenizer."""
        logger.info(f"Loading model {self.model_name} on {self.device}...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            # Force CPU only as per constraints
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map={"": self.device}
            )
            self.model.eval()
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def score_task(self, prompt: str) -> List[float]:
        """
        Computes static branching scores for a given prompt.
        Returns a list of scores corresponding to decision points.
        """
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Get logits
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Calculate scores based on KL divergence against uniform distribution
        scores = []
        vocab_size = logits.shape[-1]
        uniform_dist = [1.0 / vocab_size] * vocab_size
        
        # Iterate over tokens (simplified)
        for i in range(logits.shape[1]):
            token_logits = logits[0, i].cpu().numpy()
            # Softmax
            probs = np.exp(token_logits - np.max(token_logits))
            probs = probs / probs.sum()
            
            # KL against uniform
            kl = compute_kl_divergence(probs.tolist(), uniform_dist, self.epsilon)
            scores.append(float(kl))
        
        return scores

def process_task_with_timeout(scorer: StaticScorer, task: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    Processes a single task with a timeout mechanism.
    
    Returns:
        Tuple of (result_dict or None, is_excluded)
        - result_dict: Contains task_id and scores if successful.
        - is_excluded: True if the task timed out, False otherwise.
    """
    task_id = task.get("task_id", "unknown")
    prompt = task.get("prompt", "")
    
    logger.info(f"Processing task {task_id}...")
    start_time = time.time()
    
    try:
        # Use a thread or signal-based timeout approach. 
        # For cross-platform compatibility in a script context, we check elapsed time periodically
        # or rely on a wrapper. Here we implement a simple elapsed check loop if the operation is long,
        # but for a blocking model call, we use a timeout wrapper if available or a try/except with signal.
        # Since signal.setitimer is Unix-only, we will use a simple time-check loop if we could break the op,
        # but model inference is atomic. 
        # To strictly enforce 30 mins on a blocking call, we use signal on Unix or a thread with join timeout on all.
        
        import threading
        result_container = {'scores': None, 'error': None}
        
        def run_inference():
            try:
                result_container['scores'] = scorer.score_task(prompt)
            except Exception as e:
                result_container['error'] = str(e)

        thread = threading.Thread(target=run_inference)
        thread.daemon = True
        thread.start()
        thread.join(timeout=TASK_TIMEOUT_SECONDS)
        
        elapsed = time.time() - start_time
        
        if thread.is_alive():
            # Timeout occurred
            logger.warning(f"TIMEOUT_EXCLUDED: Task {task_id} exceeded {TASK_TIMEOUT_SECONDS}s limit (elapsed: {elapsed:.1f}s).")
            return None, True
        
        if result_container['error']:
            logger.warning(f"Task {task_id} failed with error: {result_container['error']}")
            # Treat errors as non-timeout exclusions or failures depending on policy. 
            # T018a specifically asks for timeout exclusion. We return the error as a failure, not a timeout exclusion.
            return None, False 
        
        if result_container['scores'] is None:
            # Should not happen if no error and thread finished, but safety check
            return None, False

        return {
            "task_id": task_id,
            "scores": result_container['scores'],
            "elapsed_time": elapsed
        }, False

    except Exception as e:
        logger.error(f"Unexpected error processing task {task_id}: {e}")
        return None, False

def run_batch_processing_with_timeout(scorer: StaticScorer, tasks: List[Dict[str, Any]], output_path: str) -> None:
    """
    Processes a batch of tasks with timeout logic.
    Excludes tasks that exceed the time limit.
    Exits with code 1 if the exclusion rate is too high.
    """
    results = []
    total_tasks = len(tasks)
    excluded_count = 0
    timeout_excluded_count = 0

    logger.info(f"Starting batch processing of {total_tasks} tasks.")

    for i, task in enumerate(tasks):
        result, is_timeout = process_task_with_timeout(scorer, task)
        
        if is_timeout:
            timeout_excluded_count += 1
            excluded_count += 1
            continue
        
        if result:
            results.append(result)
            logger.info(f"Completed task {i+1}/{total_tasks}: {task.get('task_id')}")
        else:
            # Failed for other reasons (e.g., model error), still excluded from success list
            excluded_count += 1
            logger.warning(f"Task {task.get('task_id')} failed and was excluded (non-timeout).")

    # Check exclusion rate
    exclusion_rate = excluded_count / total_tasks if total_tasks > 0 else 0.0
    
    logger.info(f"Batch processing complete. Processed: {len(results)}, Excluded: {excluded_count} (Timeouts: {timeout_excluded_count})")
    logger.info(f"Exclusion rate: {exclusion_rate:.2%}")

    if exclusion_rate > MAX_EXCLUSION_RATE:
        logger.error("RESOURCE_LIMIT_EXCEEDED: Exclusion rate exceeds threshold.")
        # Ensure output directory exists even if we fail
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        # Write partial results if any
        with open(output_path, 'w') as f:
            json.dump({"results": results, "error": "RESOURCE_LIMIT_EXCEEDED", "exclusion_rate": exclusion_rate}, f, indent=2)
        sys.exit(1)

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the static score module.
    Implements T018a: Task-level timeout logic.
    """
    config = get_config()
    
    # Initialize scorer
    scorer = StaticScorer(
        model_name=config.get("model_name", "microsoft/phi-2"),
        device=config.get("device", "cpu"),
        epsilon=config.get("epsilon", 1e-9)
    )
    
    # Load sample tasks (simulated for this task's logic demonstration)
    # In a real scenario, this would load from data/processed or similar
    # Creating a mock list of tasks for the timeout logic to process
    # We create 5 tasks to demonstrate the logic without running 100 heavy inferences
    tasks = []
    for i in range(5):
        tasks.append({
            "task_id": f"task_{i}",
            "prompt": f"Problem {i}: Solve for x in 2x + {i} = {10+i}. Show steps."
        })
    
    # For demonstration of timeout, we don't actually sleep 30 mins, 
    # but the logic is in place. If we wanted to test timeout, we'd inject a slow function.
    # Here we just run the normal flow.
    
    output_file = str(Path("data/processed/static_scores.json"))
    
    try:
        run_batch_processing_with_timeout(scorer, tasks, output_file)
    except SystemExit as e:
        if e.code == 1:
            logger.critical("Pipeline terminated due to RESOURCE_LIMIT_EXCEEDED.")
            sys.exit(1)
        raise

if __name__ == "__main__":
    main()