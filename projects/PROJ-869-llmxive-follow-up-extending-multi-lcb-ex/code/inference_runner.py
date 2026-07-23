"""
Inference Runner: Executes the model on the dataset.
Implements T039: Re-verify Baseline by executing blind inference on the final filtered set.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from code.config import config
from code.utils.logger import get_logger
from code.utils.common import load_json, save_json
from code.prompt_builder import build_blind_prompt
from code.inference import load_model, generate_code
from code.sandbox import run_in_sandbox, SandboxResult

logger = get_logger(__name__)

def run_inference(tasks: List[Dict], mode: str = "guided") -> List[Dict]:
    """
    Run inference on a list of tasks.
    For T039, this is called with mode="blind".
    """
    results = []
    logger.info(f"Starting {mode} inference on {len(tasks)} tasks...")
    
    # Load the model once for the batch
    logger.info("Loading model...")
    model = load_model()
    if model is None:
        logger.error("Failed to load model. Aborting inference.")
        return []

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id", f"unknown_{idx}")
        logger.info(f"[{idx+1}/{len(tasks)}] Processing {task_id} ({mode})")
        
        start_time = time.time()
        
        try:
            # 1. Build Prompt
            if mode == "blind":
                prompt = build_blind_prompt(task)
            else:
                # Guided mode requires anchor, which might not exist if T013 not run,
                # but T039 is strictly blind.
                from code.prompt_builder import build_guided_prompt
                # Fallback if anchor missing, though T039 shouldn't use guided
                prompt = build_guided_prompt(task, anchor="") 

            # 2. Generate Code
            generated_code = generate_code(model, prompt)
            
            generation_time = time.time() - start_time
            
            # 3. Execute in Sandbox
            # Determine language from task (defaulting to 'rust' based on T018 context if not specified)
            language = task.get("language", "rust")
            
            # Prepare test cases (assuming they are in the task dict or loaded from a separate source)
            # The task dict from T018 usually contains ground truth logic but might need explicit test cases.
            # We assume the 'task' dict has 'test_cases' or we derive them. 
            # For T039, we assume the dataset structure includes necessary execution metadata.
            test_cases = task.get("test_cases", []) 
            
            # If no test cases explicitly in the task, we might need to load them from a separate file 
            # or rely on the sandbox to use the problem statement's implicit tests if available.
            # However, strictly following the API: run_in_sandbox expects code and tests.
            # We will attempt to run with available tests. If empty, we log as 'no_tests' but still record generation.
            
            sandbox_result: SandboxResult = run_in_sandbox(
                code=generated_code,
                language=language,
                test_cases=test_cases
            )

            end_time = time.time()
            total_time = end_time - start_time

            results.append({
                "task_id": task_id,
                "mode": mode,
                "status": "completed" if sandbox_result.passed else "failed",
                "passed": sandbox_result.passed,
                "output": generated_code,
                "execution_log": sandbox_result.log,
                "generation_time": generation_time,
                "execution_time": total_time,
                "error_type": sandbox_result.error_type if not sandbox_result.passed else None
            })

        except Exception as e:
            logger.error(f"Error processing {task_id}: {str(e)}", exc_info=True)
            results.append({
                "task_id": task_id,
                "mode": mode,
                "status": "error",
                "passed": False,
                "output": "",
                "execution_log": str(e),
                "generation_time": 0,
                "execution_time": 0,
                "error_type": "Runtime Error"
            })

    return results

def save_results(results: List[Dict], output_path: Path):
    """Save inference results."""
    save_json(results, output_path)
    logger.info(f"Saved {len(results)} results to {output_path}")

def run_blind_baseline() -> None:
    """
    T039 Implementation: Re-verify Baseline.
    Reads data/final_tasks_enriched.json, runs blind inference, 
    writes data/blind_baseline_logs.json and data/blind_baseline.yaml.
    """
    # 1. Load Final Dataset
    input_path = config.FINAL_TASKS_PATH
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    logger.info(f"Loading final tasks from {input_path}")
    data = load_json(input_path)
    tasks = data.get("tasks", [])
    
    if not tasks:
        logger.error("No tasks found in final dataset. Aborting.")
        return

    logger.info(f"Loaded {len(tasks)} tasks for blind baseline re-verification.")

    # 2. Run Inference
    # Mode is strictly "blind" for this task
    raw_results = run_inference(tasks, mode="blind")

    # 3. Calculate Metrics
    total_count = len(raw_results)
    pass_count = sum(1 for r in raw_results if r.get("passed", False))
    pass_rate = pass_count / total_count if total_count > 0 else 0.0

    # 4. Prepare Output Files
    # a) Raw Logs (JSON)
    logs_path = config.BLIND_BASELINE_LOGS_PATH
    save_results(raw_results, logs_path)
    
    # b) Summary (YAML)
    summary = {
        "pass_count": pass_count,
        "total_count": total_count,
        "pass_rate": pass_rate,
        "filtered_task_ids": [r["task_id"] for r in raw_results]
    }
    
    yaml_path = config.BLIND_BASELINE_YAML_PATH
    # Manual YAML serialization to avoid extra dependency if not in requirements, 
    # but requirements.txt usually includes pyyaml. 
    # Using json for simplicity if yaml not strictly enforced, but task asks for yaml.
    # We will use the yaml library as it's in the standard list for this project.
    import yaml
    with open(yaml_path, "w") as f:
        yaml.dump(summary, f, default_flow_style=False)
    
    logger.info(f"Blind baseline complete. Pass Rate: {pass_rate:.4f} ({pass_count}/{total_count})")
    logger.info(f"Outputs written to {logs_path} and {yaml_path}")

if __name__ == "__main__":
    run_blind_baseline()
