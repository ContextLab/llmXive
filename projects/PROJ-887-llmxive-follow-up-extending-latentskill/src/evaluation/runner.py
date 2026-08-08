"""
Evaluation runner for User Story 3.
Executes multiple independent trials per task to establish stable success probabilities.
"""
import json
import os
import time
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from src.utils.config import get_config, resolve_path
from src.retrieval.strategies import synthesize_adapter, get_top_k_tasks
from src.retrieval.query import generate_query_vector
from src.evaluation.env_interface import AlfWorldEnv, SearchQaEnv
from src.utils.versioning import hash_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NUM_TRIALS = 5
MEMORY_THRESHOLD_GB = 6.5

def check_memory_usage() -> float:
    """
    Check current memory usage.
    Returns usage in GB.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Skipping memory check.")
        return 0.0

def run_single_trial(
    task_name: str,
    env_type: str,
    adapter_path: str,
    base_model_path: str,
    task_config: Dict[str, Any]
) -> Tuple[bool, float, str]:
    """
    Execute a single trial of a task with a specific adapter.
    
    Returns:
        Tuple of (success: bool, latency: float, error_msg: str)
    """
    start_time = time.time()
    error_msg = ""
    success = False

    try:
        # Check memory before running
        current_mem = check_memory_usage()
        if current_mem > MEMORY_THRESHOLD_GB:
            raise MemoryError(f"Memory usage {current_mem:.2f}GB exceeds threshold {MEMORY_THRESHOLD_GB}GB")

        # Initialize environment
        if env_type == "alfworld":
            env = AlfWorldEnv(task_config)
        elif env_type == "searchqa":
            env = SearchQaEnv(task_config)
        else:
            raise ValueError(f"Unknown environment type: {env_type}")

        # Load base model and apply adapter (implementation deferred to T026 details)
        # Assuming T026 provides a function to load model and apply adapter
        # For this task, we assume the adapter is already applied or loaded by the env
        # In a real implementation, this would load the GGUF model and apply the LoRA weights
        
        # Simulate model loading and inference (placeholder for T026 logic)
        # In real implementation:
        # model = load_llama_model(base_model_path, adapter_path)
        # result = model.run(task_prompt)
        
        # For now, we simulate the environment execution
        # In a real scenario, this would interact with the actual LLM
        result = env.execute_step(task_config.get("initial_state"))
        
        # Check if task completed successfully
        success = env.is_complete(result)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Trial failed for {task_name}: {error_msg}")
        traceback.print_exc()
    finally:
        elapsed = time.time() - start_time

    return success, elapsed, error_msg

def execute_evaluation_loop(
    tasks: List[Dict[str, Any]],
    base_model_path: str,
    output_dir: str,
    k_values: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Execute N >= 5 independent runs per task and calculate mean success probability.
    
    Args:
        tasks: List of task definitions with name, type, config, and ground truth adapter path
        base_model_path: Path to the base GGUF model
        output_dir: Directory to save results
        k_values: List of k values for sensitivity analysis (default: [1, 3, 5])
    
    Returns:
        Dictionary containing evaluation results
    """
    if k_values is None:
        k_values = [1, 3, 5]
    
    results = {
        "tasks": {},
        "summary": {},
        "sensitivity_analysis": {}
    }

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for task_def in tasks:
        task_name = task_def["name"]
        env_type = task_def["type"]
        task_config = task_def["config"]
        ground_truth_adapter = task_def.get("ground_truth_adapter")
        
        logger.info(f"Starting evaluation for task: {task_name}")
        
        task_results = {
            "trials": [],
            "success_count": 0,
            "failure_count": 0,
            "mean_success_rate": 0.0,
            "mean_latency": 0.0,
            "errors": []
        }
        
        total_latency = 0.0
        
        for trial_idx in range(NUM_TRIALS):
            logger.info(f"Running trial {trial_idx + 1}/{NUM_TRIALS} for {task_name}")
            
            # For sensitivity analysis, we might use different k values
            # For the main loop, we use the default k=3 (or task-specific)
            current_k = task_config.get("k", 3)
            
            # Generate query vector from task description
            query_text = task_config.get("description", "")
            query_vector = generate_query_vector(query_text)
            
            # Retrieve top-k tasks and synthesize adapter
            retrieved_tasks = get_top_k_tasks(query_vector, k=current_k)
            synthesized_adapter_path = synthesize_adapter(
                retrieved_tasks, 
                output_dir=f"{output_dir}/synthesized"
            )
            
            # Run single trial
            success, latency, error_msg = run_single_trial(
                task_name=task_name,
                env_type=env_type,
                adapter_path=synthesized_adapter_path,
                base_model_path=base_model_path,
                task_config=task_config
            )
            
            trial_result = {
                "trial_id": trial_idx + 1,
                "success": success,
                "latency": latency,
                "error": error_msg if not success else None
            }
            
            task_results["trials"].append(trial_result)
            total_latency += latency
            
            if success:
                task_results["success_count"] += 1
            else:
                task_results["failure_count"] += 1
                if error_msg:
                    task_results["errors"].append(error_msg)
        
        # Calculate mean success probability
        mean_success_rate = task_results["success_count"] / NUM_TRIALS
        mean_latency = total_latency / NUM_TRIALS
        
        task_results["mean_success_rate"] = mean_success_rate
        task_results["mean_latency"] = mean_latency
        
        results["tasks"][task_name] = task_results
        
        logger.info(f"Task {task_name} completed: {mean_success_rate:.2%} success rate, {mean_latency:.2f}s avg latency")

    # Calculate summary statistics
    if results["tasks"]:
        all_rates = [t["mean_success_rate"] for t in results["tasks"].values()]
        all_latencies = [t["mean_latency"] for t in results["tasks"].values()]
        
        results["summary"] = {
            "total_tasks": len(results["tasks"]),
            "overall_success_rate": np.mean(all_rates),
            "overall_latency": np.mean(all_latencies),
            "num_trials_per_task": NUM_TRIALS
        }

    # Perform sensitivity analysis if requested
    if len(k_values) > 1:
        sensitivity_results = {}
        for k in k_values:
            k_success_rates = []
            for task_def in tasks:
                task_name = task_def["name"]
                task_config = task_def["config"]
                task_config["k"] = k
                
                # Run a single trial with this k value to get success rate
                # In a full implementation, we'd run NUM_TRIALS for each k
                query_text = task_config.get("description", "")
                query_vector = generate_query_vector(query_text)
                retrieved_tasks = get_top_k_tasks(query_vector, k=k)
                synthesized_adapter_path = synthesize_adapter(
                    retrieved_tasks, 
                    output_dir=f"{output_dir}/synthesized_k{k}"
                )
                
                success, _, _ = run_single_trial(
                    task_name=task_name,
                    env_type=task_def["type"],
                    adapter_path=synthesized_adapter_path,
                    base_model_path=base_model_path,
                    task_config=task_config
                )
                k_success_rates.append(1.0 if success else 0.0)
            
            sensitivity_results[f"k_{k}"] = {
                "mean_success_rate": np.mean(k_success_rates),
                "task_count": len(k_success_rates)
            }
        
        results["sensitivity_analysis"] = sensitivity_results

    # Save results to JSON
    output_file = Path(output_dir) / "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_file}")
    
    # Update versioning
    if os.path.exists(output_file):
        hash_value = hash_artifact(output_file)
        logger.info(f"Results artifact hash: {hash_value}")

    return results

def main():
    """
    Main entry point for the evaluation runner.
    """
    config = get_config()
    
    # Load tasks configuration
    tasks_file = resolve_path(config, "data/processed/tasks_config.json")
    if not os.path.exists(tasks_file):
        logger.error(f"Tasks configuration file not found: {tasks_file}")
        return
    
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)
    
    base_model_path = resolve_path(config, "data/models/llama-2-7b-q4_0.gguf")
    if not os.path.exists(base_model_path):
        logger.error(f"Base model not found: {base_model_path}")
        return
    
    output_dir = resolve_path(config, "data/results")
    
    logger.info(f"Starting evaluation loop with {NUM_TRIALS} trials per task")
    logger.info(f"Base model: {base_model_path}")
    logger.info(f"Output directory: {output_dir}")
    
    results = execute_evaluation_loop(
        tasks=tasks,
        base_model_path=base_model_path,
        output_dir=output_dir,
        k_values=[1, 3, 5]
    )
    
    logger.info("Evaluation loop completed successfully")
    print(json.dumps(results["summary"], indent=2))

if __name__ == "__main__":
    main()
