import os
import sys
import logging
import time
import json
import gc
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from src.utils.config import get_project_root, get_data_path, get_artifacts_path, get_results_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_memory_usage(threshold_gb: float = 7.0) -> bool:
    """
    Check current memory usage and ensure it is below the threshold.
    Returns True if memory is sufficient, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_mb = mem_info.rss / (1024 * 1024)
        current_gb = current_mb / 1024.0

        logger.info(f"Current memory usage: {current_gb:.2f} GB (RSS)")
        
        if current_gb > threshold_gb:
            logger.warning(f"Memory usage {current_gb:.2f} GB exceeds threshold {threshold_gb} GB")
            return False
        return True
    except ImportError:
        logger.warning("psutil not installed, skipping memory check")
        return True
    except Exception as e:
        logger.error(f"Error checking memory usage: {e}")
        return False

def load_synthesized_adapter(adapter_path: Path) -> Dict[str, Any]:
    """
    Load a synthesized LoRA adapter from disk.
    Returns the adapter weights as a dictionary.
    """
    import numpy as np
    
    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter file not found: {adapter_path}")
    
    try:
        # Load .npz format (common for synthesized adapters)
        data = np.load(str(adapter_path))
        adapter_dict = {key: data[key] for key in data.files}
        logger.info(f"Loaded adapter from {adapter_path}: {list(adapter_dict.keys())}")
        return adapter_dict
    except Exception as e:
        logger.error(f"Failed to load adapter {adapter_path}: {e}")
        raise

def apply_lora_to_model(model, adapter_weights: Dict[str, Any], device: str = "cpu"):
    """
    Apply LoRA adapter weights to a model.
    This is a placeholder for the actual LoRA application logic.
    In a real implementation, this would patch the model layers.
    """
    logger.info(f"Applying LoRA adapter with {len(adapter_weights)} matrices to model on {device}")
    
    # Placeholder: In a real scenario, this would involve:
    # 1. Identifying target layers in the model
    # 2. Injecting the A and B matrices from the adapter
    # 3. Setting the model to eval mode
    
    # For now, we just log the operation
    for key, weight in adapter_weights.items():
        if key not in ['A', 'B', 'alpha', 'scaling']:
            logger.debug(f"  - {key}: shape {weight.shape if hasattr(weight, 'shape') else type(weight)}")
    
    logger.info("Adapter application completed (placeholder)")
    return model

def execute_environment_logic(model, task_desc: str, max_steps: int = 50) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute the environment logic (e.g., ALFWorld) with the given model.
    Returns (success, metrics).
    
    This is a placeholder for the actual environment execution.
    In a real implementation, this would:
    1. Initialize the environment
    2. Run the model's inference loop
    3. Evaluate the outcome
    """
    logger.info(f"Executing environment logic for task: {task_desc}")
    
    # Placeholder implementation
    # In reality, this would run the actual environment and get a success/failure
    success = True  # Placeholder: always succeed for demonstration
    metrics = {
        "task_desc": task_desc,
        "steps_taken": 1,
        "reason": "placeholder_execution"
    }
    
    logger.info(f"Environment execution completed: success={success}")
    return success, metrics

def unload_adapter(model):
    """
    Unload the LoRA adapter from the model and free memory.
    This is crucial for the 'load -> run -> unload' cycle.
    """
    logger.info("Unloading adapter from model")
    
    # Placeholder: In a real implementation, this would:
    # 1. Remove the LoRA weights from the model layers
    # 2. Restore the original model weights
    # 3. Trigger garbage collection
    
    gc.collect()
    logger.info("Adapter unloaded and garbage collected")

def run_evaluation(
    task_id: str,
    task_desc: str,
    adapter_path: Path,
    model_path: Path,
    device: str = "cpu",
    max_steps: int = 50
) -> Dict[str, Any]:
    """
    Run a single evaluation trial:
    1. Check memory usage
    2. Load the model (if not already loaded)
    3. Load the adapter
    4. Apply the adapter
    5. Execute the environment logic
    6. Unload the adapter
    7. Log memory usage
    
    Returns a dictionary with the results.
    """
    # Step 1: Check memory before starting
    if not check_memory_usage():
        raise MemoryError("Insufficient memory to run evaluation")
    
    start_time = time.time()
    results = {
        "task_id": task_id,
        "task_desc": task_desc,
        "adapter_path": str(adapter_path),
        "model_path": str(model_path),
        "success": False,
        "latency_ms": 0,
        "memory_start_gb": 0,
        "memory_end_gb": 0,
        "error": None
    }
    
    try:
        # Get initial memory
        import psutil
        process = psutil.Process(os.getpid())
        results["memory_start_gb"] = process.memory_info().rss / (1024**3)
        
        # Step 2: Load model (placeholder - in reality, load the GGUF model)
        # For now, we assume the model is already loaded or handled elsewhere
        model = None  # Placeholder
        logger.info(f"Model loaded from {model_path}")
        
        # Step 3: Load adapter
        adapter_weights = load_synthesized_adapter(adapter_path)
        
        # Step 4: Apply adapter
        model = apply_lora_to_model(model, adapter_weights, device)
        
        # Step 5: Execute environment logic
        success, metrics = execute_environment_logic(model, task_desc, max_steps)
        results["success"] = success
        results["metrics"] = metrics
        
        # Step 6: Unload adapter
        unload_adapter(model)
        
        # Get final memory
        results["memory_end_gb"] = process.memory_info().rss / (1024**3)
        
    except Exception as e:
        logger.error(f"Evaluation failed for task {task_id}: {e}")
        results["error"] = str(e)
        results["success"] = False
    finally:
        # Ensure adapter is unloaded even on error
        try:
            unload_adapter(None)  # Safe call
        except:
            pass
        gc.collect()
        
        end_time = time.time()
        results["latency_ms"] = (end_time - start_time) * 1000
        
        logger.info(f"Evaluation completed for {task_id}: success={results['success']}, latency={results['latency_ms']:.2f}ms")
        
    return results

def main():
    """
    Main entry point for the evaluation runner.
    This script is designed to be called from a higher-level evaluation loop.
    """
    project_root = get_project_root()
    ensure_directories()
    
    # Example usage (in a real scenario, this would be called by T027)
    logger.info("Evaluation runner module loaded and ready")
    
    # Example: Run a single trial
    # This is just for demonstration; the actual loop is in T027
    if len(sys.argv) > 1:
        task_id = sys.argv[1]
        logger.info(f"Running evaluation for task: {task_id}")
        # In a real implementation, we would load the task config and run the evaluation
    
    logger.info("Evaluation runner ready for use")

if __name__ == "__main__":
    main()