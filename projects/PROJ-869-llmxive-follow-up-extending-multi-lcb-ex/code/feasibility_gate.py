"""
Model Feasibility Gate: Measure token throughput of the GGUF model.
Triggers GPU offload or adjusts N if necessary.
"""
import json
import time
import os
from pathlib import Path
from code.config import config, FEASIBILITY_LOG_PATH
from code.utils.logger import get_logger

logger = get_logger(__name__)

def measure_throughput(model_path: str) -> tuple[float, int]:
    """
    Measure token throughput of the model on the current runner.
    Returns (tokens_per_second, total_tokens_generated).
    
    Raises RuntimeError if model loading fails or generation crashes.
    """
    logger.info(f"Measuring throughput for model: {model_path}")
    
    # Verify file existence before attempting load
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. "
                                "Ensure the GGUF model is downloaded before running the gate.")

    try:
        from llama_cpp import Llama
    except ImportError:
        raise RuntimeError("llama-cpp-python is not installed. "
                           "Please install it via 'pip install llama-cpp-python' or check requirements.txt.")

    try:
        # Load model with standard CPU settings as per project constraints
        llm = Llama(
            model_path=model_path,
            n_ctx=config.model_max_context,
            n_threads=config.model_threads if hasattr(config, 'model_threads') else 4,
            n_batch=config.model_batch_size if hasattr(config, 'model_batch_size') else 512,
            verbose=False
        )
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")

    # Use a standard prompt to ensure consistent measurement
    prompt = "Write a function to add two numbers in Python."
    
    start_time = time.perf_counter()
    
    try:
        output = llm(
            prompt,
            max_tokens=config.test_generation_tokens if hasattr(config, 'test_generation_tokens') else 50,
            temperature=0.0,
            echo=False,
            stop=[],
            logprobs=0 # Ensure we get token usage if available in newer versions
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise RuntimeError(f"Model generation failed: {e}")
        
    end_time = time.perf_counter()

    generated_text = output['choices'][0]['text']
    
    # Determine token count:
    # 1. Try to use the usage info from the output if available (newer llama-cpp-python versions)
    # 2. Fallback to estimation if not available, but prefer exact count.
    total_tokens = 0
    if 'usage' in output and 'completion_tokens' in output['usage']:
        total_tokens = output['usage']['completion_tokens']
    else:
        # Fallback estimation: average ~4 chars per token for English code/text
        # This is less accurate but allows the gate to run if usage dict is missing.
        total_tokens = max(1, int(len(generated_text) / 4.0))
    
    duration = end_time - start_time
    if duration <= 0.0:
        duration = 0.001
    
    throughput = total_tokens / duration
    
    logger.info(f"Generated {total_tokens} tokens in {duration:.2f}s. Throughput: {throughput:.2f} tokens/sec")
    return throughput, total_tokens

def run_feasibility_gate():
    """
    Run the feasibility gate and write results to data/feasibility_log.json.
    
    Logic:
    1. Measure throughput.
    2. If throughput < config.min_throughput_tokens_per_sec (default 2.0):
       - Mark status as 'low_throughput'.
       - Trigger Dynamic N Adjustment: Reduce target N proportionally.
       - Set proceed=False (indicating CPU is too slow for full run).
    3. If throughput >= threshold:
       - Mark status as 'passed'.
       - Set proceed=True.
    
    Note: The 'GPU Escape Hatch' (triggering a Kaggle re-run) is a CI/CD signal.
    This script outputs the decision in JSON so the runner can act on it.
    """
    logger.info("Starting Feasibility Gate...")
    
    # Default thresholds if not explicitly set in config, but relying on config is safer
    min_throughput = getattr(config, 'min_throughput_tokens_per_sec', 2.0)
    target_n = getattr(config, 'target_n', 200)
    
    result = {
        "status": "unknown",
        "throughput": 0.0,
        "proceed": False,
        "adjusted_n": target_n,
        "reason": "",
        "config": {
            "model_path": config.model_path,
            "min_throughput": min_throughput,
            "original_n": target_n
        }
    }

    try:
        throughput, tokens_gen = measure_throughput(config.model_path)
        result["throughput"] = throughput
        result["tokens_generated"] = tokens_gen

        if throughput < min_throughput:
            result["status"] = "low_throughput"
            result["proceed"] = False
            result["reason"] = f"Throughput {throughput:.2f} < threshold {min_throughput} tokens/sec."
            
            # Dynamic N Adjustment
            # Heuristic: Scale N linearly with throughput ratio, floor at 50
            ratio = throughput / min_throughput
            new_n = int(target_n * ratio)
            if new_n < 50:
                new_n = 50
            if new_n > target_n:
                new_n = target_n # Should not happen if throughput < min
            
            result["adjusted_n"] = new_n
            result["reason"] += f" Dynamic N adjustment: Reduced target tasks from {target_n} to {new_n}."
            logger.warning(f"Feasibility Gate Warning: Adjusted N to {new_n} due to low throughput.")
        else:
            result["status"] = "passed"
            result["proceed"] = True
            result["reason"] = f"Throughput {throughput:.2f} >= threshold {min_throughput} tokens/sec."
            logger.info("Feasibility Gate Passed.")

    except FileNotFoundError as e:
        result["status"] = "model_not_found"
        result["reason"] = str(e)
        result["proceed"] = False
        logger.error(f"Feasibility Gate Failed: {e}")
    except RuntimeError as e:
        result["status"] = "runtime_error"
        result["reason"] = str(e)
        result["proceed"] = False
        logger.error(f"Feasibility Gate Failed: {e}")
    except Exception as e:
        result["status"] = "failed"
        result["reason"] = f"Unexpected error: {str(e)}"
        result["proceed"] = False
        logger.error(f"Feasibility Gate Failed with unexpected error: {e}", exc_info=True)

    # Write output to data/feasibility_log.json
    # Ensure the directory exists
    FEASIBILITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FEASIBILITY_LOG_PATH, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Feasibility gate completed. Result written to {FEASIBILITY_LOG_PATH}")
    return result

if __name__ == "__main__":
    run_feasibility_gate()
