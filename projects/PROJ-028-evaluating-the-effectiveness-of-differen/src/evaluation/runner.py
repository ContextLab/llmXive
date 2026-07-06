"""
Core evaluation runner for code generation tasks.
Implements the execution loop with robust error handling for generated code.
"""
import json
import time
import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.evaluation.prompts import create_zero_shot_prompt, extract_code_from_response
from src.evaluation.sandbox import (
    execute_sandbox,
    SandboxExecutionError,
    SandboxTimeoutError,
    SandboxMemoryError,
    SandboxSecurityError
)
from src.utils.logging import ResourceLogger, ensure_log_dir

class EvaluationRunner:
    """
    Orchestrates the evaluation of code generation models.
    Handles prompt generation, code execution, and result recording.
    """

    def __init__(self, model_loader, output_dir: str = "data/results"):
        self.model_loader = model_loader
        self.output_dir = Path(output_dir)
        ensure_log_dir(self.output_dir)
        self.logger = ResourceLogger(self.output_dir)
        
        # Ensure results directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _safe_execute_code(self, generated_code: str, test_code: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Executes generated code in a sandbox with error handling.
        
        Returns a dict with:
        - success: bool
        - error_type: str | None
        - error_message: str | None
        - execution_time: float
        """
        result = {
            "success": False,
            "error_type": None,
            "error_message": None,
            "execution_time": 0.0
        }

        if not generated_code or not generated_code.strip():
            result["error_type"] = "EmptyCode"
            result["error_message"] = "Generated code is empty or whitespace only"
            return result

        start_time = time.time()
        
        try:
            # Attempt to execute the code in the sandbox
            execution_result = execute_sandbox(
                user_code=generated_code,
                test_code=test_code,
                timeout_seconds=timeout
            )
            
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            
            if execution_result.get("passed", False):
                result["success"] = True
            else:
                result["error_type"] = "AssertionError"
                result["error_message"] = execution_result.get("error", "Test failed")
                
        except SandboxTimeoutError as e:
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            result["error_type"] = "Timeout"
            result["error_message"] = f"Execution timed out after {timeout}s"
            
        except SandboxMemoryError as e:
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            result["error_type"] = "MemoryLimit"
            result["error_message"] = str(e)
            
        except SandboxSecurityError as e:
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            result["error_type"] = "SecurityViolation"
            result["error_message"] = str(e)
            
        except SandboxExecutionError as e:
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            result["error_type"] = "RuntimeError"
            result["error_message"] = str(e)
            
        except Exception as e:
            # Catch-all for any unexpected errors during execution
            elapsed = time.time() - start_time
            result["execution_time"] = elapsed
            result["error_type"] = "UnexpectedError"
            result["error_message"] = f"Unexpected error: {str(e)}"

        return result

    def run_task(self, task: Dict[str, Any], seed: int = 0) -> Dict[str, Any]:
        """
        Runs a single evaluation task.
        
        Args:
            task: Dictionary containing 'task_id', 'prompt', 'test_list'
            seed: Random seed for reproducibility (used if model supports it)
        
        Returns:
            Dictionary with task evaluation results
        """
        task_id = task.get("task_id", "unknown")
        prompt_text = task.get("prompt", "")
        test_code = task.get("test_list", "")
        
        result = {
            "task_id": task_id,
            "seed": seed,
            "strategy": "zero-shot",
            "input_prompt": prompt_text,
            "generated_code": None,
            "execution_result": None,
            "passed": False,
            "error_type": None,
            "error_message": None,
            "execution_time": 0.0
        }

        try:
            # 1. Generate Prompt
            formatted_prompt = create_zero_shot_prompt(prompt_text)
            
            # 2. Generate Code using the model
            # Note: We assume model_loader has a method to generate text
            # If the model loader is not fully implemented, we simulate the call structure
            generated_response = self.model_loader.generate(formatted_prompt, seed=seed)
            
            # 3. Extract Code Block
            generated_code = extract_code_from_response(generated_response)
            result["generated_code"] = generated_code
            
            if not generated_code:
                result["error_type"] = "ParsingFailure"
                result["error_message"] = "Could not extract code block from model response"
                return result

            # 4. Execute Code with Error Handling
            exec_result = self._safe_execute_code(generated_code, test_code)
            result["execution_result"] = exec_result
            result["passed"] = exec_result["success"]
            result["execution_time"] = exec_result["execution_time"]
            
            if not exec_result["success"]:
                result["error_type"] = exec_result["error_type"]
                result["error_message"] = exec_result["error_message"]

        except Exception as e:
            # Catch any errors that occur during the generation or orchestration phase
            result["error_type"] = "PipelineError"
            result["error_message"] = f"Pipeline execution failed: {str(e)}"
            result["passed"] = False

        return result

    def run_batch(self, tasks: List[Dict[str, Any]], seed: int = 0) -> List[Dict[str, Any]]:
        """
        Runs a batch of tasks.
        
        Args:
            tasks: List of task dictionaries
            seed: Random seed for the batch
        
        Returns:
            List of result dictionaries
        """
        results = []
        for task in tasks:
            task_result = self.run_task(task, seed=seed)
            results.append(task_result)
        return results

    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """
        Saves evaluation results to a JSON file.
        
        Args:
            results: List of result dictionaries
            filename: Name of the output file (will be saved to output_dir)
        """
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        return output_path

def run_evaluation_pipeline(model_loader, tasks: List[Dict[str, Any]], seed: int = 0) -> List[Dict[str, Any]]:
    """
    Convenience function to run the evaluation pipeline.
    
    Args:
        model_loader: Instance of a model loader with a .generate() method
        tasks: List of task dictionaries
        seed: Random seed
        
    Returns:
        List of evaluation results
    """
    runner = EvaluationRunner(model_loader)
    return runner.run_batch(tasks, seed=seed)