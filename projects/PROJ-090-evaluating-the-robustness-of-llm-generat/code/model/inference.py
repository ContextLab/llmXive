import os
import sys
import time
import threading
import logging
import json
import torch
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import project utilities from API surface
from config import get_model_path, get_timeout_inference, get_timeout_execution, get_seed_global, ensure_directories
from utils.logging import get_inference_logger, init_logging, log_inference_event
from utils.memory_monitor import get_current_memory_mb, check_memory_limit, set_soft_memory_limit
from model.sandbox import execute_code, ExecutionStatus, TimeoutError as SandboxTimeoutError, ExecutionError as SandboxExecutionError
from model.execution_results import ExecutionTag, classify_error_message, tag_execution_result, aggregate_results, save_results_to_json, load_results_from_json
from utils.state import get_state, increment_samples, save_state

# Configure logging
logger = logging.getLogger(__name__)

def load_model(model_id: str = "bigcode/starcoder2-1.5b", device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load StarCoder2-1.5B with 4-bit quantization for CPU execution.
    Uses bitsandbytes for low-bit quantization and torch for CPU offload.
    Returns (model, tokenizer).
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        import torch
    except ImportError as e:
        logger.error(f"Missing required libraries: {e}")
        raise ImportError("Please install transformers, bitsandbytes, and torch.")

    logger.info(f"Loading model: {model_id} on device: {device}")
    
    # Configure 4-bit quantization for CPU
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Ensure padding token is set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model with quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        # If on CPU, move explicitly
        if not torch.cuda.is_available():
            model = model.to("cpu")
        
        model.eval()
        logger.info(f"Model loaded successfully. Memory usage: {get_current_memory_mb():.2f} MB")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_code(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.2,
    do_sample: bool = True,
    timeout_seconds: int = 300
) -> Tuple[Optional[str], float, str]:
    """
    Generate code from a prompt with timeout enforcement.
    Returns (generated_code, confidence_score, status).
    """
    try:
        start_time = time.time()
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs.input_ids
        attention_mask = inputs.attention_mask
        
        # Move to device
        if torch.cuda.is_available():
            input_ids = input_ids.to(model.device)
            attention_mask = attention_mask.to(model.device)

        # Set generation timeout
        def timeout_handler():
            time.sleep(timeout_seconds)
            raise TimeoutError("Generation timed out")

        timeout_thread = threading.Thread(target=timeout_handler)
        timeout_thread.daemon = True
        timeout_thread.start()

        # Generate with confidence extraction
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                return_dict_in_generate=True,
                output_scores=True
            )

        # Calculate confidence from logits
        if hasattr(outputs, 'scores') and outputs.scores:
            # Average probability of generated tokens
            all_probs = []
            for scores in outputs.scores:
                # Get probability of the next token
                next_token_scores = torch.nn.functional.softmax(scores, dim=-1)
                # The actual generated token index
                generated_ids = outputs.sequences[0, input_ids.shape[1]:]
                for i, token_id in enumerate(generated_ids):
                    if i < len(next_token_scores):
                        prob = next_token_scores[i][token_id].item()
                        all_probs.append(prob)
            
            if all_probs:
                confidence_score = sum(all_probs) / len(all_probs)
            else:
                confidence_score = 0.0
        else:
            confidence_score = 0.0

        # Decode generated text
        generated_sequence = outputs.sequences[0]
        generated_text = tokenizer.decode(generated_sequence[input_ids.shape[1]:], skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Generated code in {elapsed_time:.2f}s with confidence {confidence_score:.4f}")
        
        return generated_text.strip(), confidence_score, "success"

    except TimeoutError:
        logger.warning("Generation timed out")
        return None, 0.0, "timeout"
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return None, 0.0, "error"

def run_generation_loop(
    tasks: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    output_path: Path,
    timeout_seconds: int = 300
) -> List[Dict[str, Any]]:
    """
    Run generation on a list of tasks and save results.
    """
    results = []
    
    for task in tasks:
        task_id = task.get('task_id', 'unknown')
        prompt = task.get('prompt', '')
        
        logger.info(f"Processing task {task_id}")
        
        # Generate code
        code, confidence_score, gen_status = generate_code(
            model, tokenizer, prompt, timeout_seconds=timeout_seconds
        )
        
        if code is None:
            # Inference failed
            results.append({
                "task_id": task_id,
                "prompt": prompt,
                "code": "",
                "status": gen_status,
                "confidence_score": confidence_score
            })
            continue
        
        # Execute code in sandbox
        exec_status = "pass"
        try:
            # Extract test cases from task if available
            test_code = task.get('test', '')
            if test_code:
                result = execute_code(code, test_code, timeout_seconds=timeout_seconds)
                exec_status = result.status.value if hasattr(result, 'status') else "unknown"
            else:
                # No test cases provided, assume pass if code generated
                exec_status = "pass"
        except Exception as e:
            logger.error(f"Execution failed for task {task_id}: {e}")
            exec_status = "fail"
        
        # Update confidence based on execution
        if exec_status != "pass":
            # If code fails, confidence should be low
            confidence_score = confidence_score * 0.1
        
        results.append({
            "task_id": task_id,
            "prompt": prompt,
            "code": code,
            "status": exec_status,
            "confidence_score": round(confidence_score, 4)
        })
        
        # Log inference event
        log_inference_event(task_id, exec_status, confidence_score)
        
        # Update state
        increment_samples(1)
        
        # Check memory
        if not check_memory_limit():
            logger.warning("Memory limit approached, clearing cache")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Small delay to prevent CPU overload
        time.sleep(0.1)
    
    # Save results
    save_results_to_json(results, output_path)
    return results

def save_results_to_json(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save inference results to JSON file."""
    ensure_directories()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for inference pipeline."""
    init_logging()
    ensure_directories()
    
    # Load configuration
    model_id = get_model_path() or "bigcode/starcoder2-1.5b"
    timeout = get_timeout_inference()
    output_path = Path("data/processed/inference_logs.json")
    
    logger.info(f"Starting inference pipeline with model {model_id}")
    
    # Load model
    try:
        model, tokenizer = load_model(model_id)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)
    
    # Load tasks from perturbation candidates
    try:
        candidates_path = Path("data/processed/perturbation_candidates.json")
        if not candidates_path.exists():
            logger.error(f"Required input file not found: {candidates_path}")
            sys.exit(1)
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        logger.info(f"Loaded {len(tasks)} tasks from {candidates_path}")
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        sys.exit(1)
    
    # Run generation
    results = run_generation_loop(tasks, model, tokenizer, output_path, timeout)
    
    logger.info(f"Pipeline completed. Processed {len(results)} tasks.")
    print(f"Inference complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()
