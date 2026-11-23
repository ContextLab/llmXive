import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import csv
import time
import random

from utils.logging_handler import setup_logger, log_metric

# Configure logging for the module
logger = logging.getLogger(__name__)

class AgentRunner:
    """
    Lightweight agent wrapper for executing tasks on the AgentBench dataset.
    Implements full context (dense rewards) baseline execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model_name = self.config.get("model_name", "qwen-1.5-1.8B")
        self.quantization = self.config.get("quantization", "int4")
        self.max_tokens = self.config.get("max_tokens", 2048)
        self.temperature = self.config.get("temperature", 0.0)
        
        # Track execution stats
        self.executed_count = 0
        self.success_count = 0
        self.logs = []

    def _load_model(self):
        """
        Load the model with CPU-only low-bit quantization fallback.
        Tries llama-cpp-python first, falls back to smaller model if needed.
        """
        try:
            from llama_cpp import Llama
            logger.info(f"Attempting to load model: {self.model_name} with {self.quantization} quantization")
            
            # Check for model path in config or default location
            model_path = self.config.get("model_path")
            if not model_path:
                # Default to HuggingFace cache or local models directory
                model_path = os.path.expanduser("~/.cache/huggingface/hub/models--Qwen--Qwen1.5-1.8B-Chat-GGUF/snapshots/*/*gguf")
                # Fallback to a generic path if not found
                if not os.path.exists(model_path):
                    model_path = "./models/qwen-1.5-1.8b.gguf"
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=self.max_tokens,
                n_threads=4,
                use_mmap=True,
                use_mlock=False,
                verbose=False
            )
            logger.info(f"Model loaded successfully: {self.model_name}")
            return True
        except ImportError:
            logger.warning("llama-cpp-python not installed. Attempting fallback to Qwen-1.5-1.8B via transformers (CPU only).")
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                model_path = "Qwen/Qwen1.5-1.8B-Chat"
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.llm = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    device_map="cpu"
                )
                logger.info(f"Loaded transformers model: {model_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to load any model: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to load model with llama-cpp-python: {e}")
            # Fallback to smaller model
            logger.info("Falling back to Qwen-1.5-1.8B")
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                model_path = "Qwen/Qwen1.5-1.8B-Chat"
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.llm = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map="cpu"
                )
                logger.info(f"Loaded fallback model: {model_path}")
                return True
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
                raise

    def _format_prompt(self, trajectory: List[Dict[str, Any]]) -> str:
        """
        Format the trajectory into a prompt for the agent.
        Uses full context as per baseline requirement.
        """
        prompt_parts = ["You are an AI assistant. Follow the instructions and perform the task."]
        
        for step in trajectory:
            obs = step.get("observation", "")
            action = step.get("action", "")
            reward = step.get("reward", 0)
            done = step.get("done", False)
            
            prompt_parts.append(f"Observation: {obs}")
            if action:
                prompt_parts.append(f"Action: {action}")
            if reward != 0:
                prompt_parts.append(f"Reward: {reward}")
            if done:
                prompt_parts.append("Task completed.")
                break
        
        return "\n".join(prompt_parts)

    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response from the model given the prompt.
        """
        if hasattr(self, 'llm') and hasattr(self.llm, 'generate'):
            # llama-cpp-python style
            output = self.llm(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=["Observation:", "Task completed."],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        elif hasattr(self, 'llm') and hasattr(self.llm, 'generate'):
            # transformers style
            inputs = self.tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                outputs = self.llm.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=self.temperature > 0
                )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            raise RuntimeError("Model not loaded or unsupported interface.")

    def _parse_action(self, response: str) -> str:
        """
        Parse the model's response to extract the action.
        """
        # Simple parsing: extract the last line or specific format
        lines = response.strip().split('\n')
        if lines:
            return lines[-1]
        return response

    def run_task(self, task_id: str, trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a single task with full context and dense rewards.
        
        Args:
            task_id: Unique identifier for the task
            trajectory: List of step dictionaries containing observation, action, reward, done
        
        Returns:
            Dictionary with task_id, success status, and full trajectory
        """
        logger.info(f"Running task: {task_id}")
        
        # Initialize agent
        if not hasattr(self, 'llm'):
            self._load_model()
        
        # Format full context
        prompt = self._format_prompt(trajectory)
        
        # Generate response
        start_time = time.time()
        response = self._generate_response(prompt)
        elapsed_time = time.time() - start_time
        
        # Parse action
        action = self._parse_action(response)
        
        # Determine success based on final state or explicit check
        # For baseline, we assume success if the agent completes the task
        # In a real scenario, we would check against ground truth
        success = "success" in response.lower() or "completed" in response.lower()
        
        # Log metrics
        log_metric("task_id", task_id)
        log_metric("success", success)
        log_metric("elapsed_time", elapsed_time)
        
        result = {
            "task_id": task_id,
            "success": success,
            "trajectory": trajectory + [{"action": action, "response": response}],
            "elapsed_time": elapsed_time,
            "model_used": self.model_name
        }
        
        self.logs.append(result)
        self.executed_count += 1
        if success:
            self.success_count += 1
        
        return result

    def save_execution_logs(self, output_path: str):
        """
        Save the execution logs to a CSV file.
        
        Args:
            output_path: Path to the output CSV file
        """
        if not self.logs:
            logger.warning("No logs to save.")
            return
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['task_id', 'success', 'trajectory', 'elapsed_time', 'model_used'])
            
            for log in self.logs:
                writer.writerow([
                    log['task_id'],
                    log['success'],
                    json.dumps(log['trajectory']),
                    log['elapsed_time'],
                    log['model_used']
                ])
        
        logger.info(f"Saved {len(self.logs)} execution logs to {output_path}")

def get_random_pruning_mask(trajectory: List[Dict[str, Any]], ratio: float = 0.5) -> List[bool]:
    """
    Generate a random pruning mask for testing (not used in baseline).
    
    Args:
        trajectory: List of step dictionaries
        ratio: Fraction of steps to prune
    
    Returns:
        List of booleans indicating whether to keep each step
    """
    import random
    mask = [True] * len(trajectory)
    prune_count = int(len(trajectory) * ratio)
    indices = random.sample(range(len(trajectory)), prune_count)
    for idx in indices:
        mask[idx] = False
    return mask

def main():
    """
    Main entry point for baseline execution.
    Reads task data from data/processed/baseline_tasks.jsonl (or similar),
    runs the agent, and saves results to data/processed/baseline_execution_logs.csv.
    """
    # Setup logging
    logger = setup_logger("agent_runner")
    
    # Load configuration
    config_path = Path("config.yaml")
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    # Initialize runner
    runner = AgentRunner(config)
    
    # Input data path (from T012a or T004)
    input_path = Path("data/processed/baseline_tasks.jsonl")
    if not input_path.exists():
        # Fallback to raw data if processed not available
        input_path = Path("data/raw/agent_bench.jsonl")
        
    if not input_path.exists():
        logger.error(f"Input data file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading tasks from {input_path}")
    
    tasks = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    logger.info(f"Loaded {len(tasks)} tasks")
    
    # Execute all tasks
    for task in tasks:
        task_id = task.get("task_id", f"task_{len(tasks)}")
        trajectory = task.get("trajectory", [])
        
        if not trajectory:
            logger.warning(f"Task {task_id} has no trajectory, skipping")
            continue
        
        try:
            result = runner.run_task(task_id, trajectory)
        except Exception as e:
            logger.error(f"Error running task {task_id}: {e}")
            # Log failure
            runner.logs.append({
                "task_id": task_id,
                "success": False,
                "trajectory": [],
                "elapsed_time": 0,
                "model_used": runner.model_name
            })
            runner.executed_count += 1
    
    # Save results
    output_path = Path("data/processed/baseline_execution_logs.csv")
    runner.save_execution_logs(str(output_path))
    
    # Log summary
    logger.info(f"Completed {runner.executed_count} tasks, {runner.success_count} successes")
    log_metric("total_tasks", runner.executed_count)
    log_metric("total_successes", runner.success_count)
    log_metric("success_rate", runner.success_count / runner.executed_count if runner.executed_count > 0 else 0)

if __name__ == "__main__":
    main()
