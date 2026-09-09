import os
import json
import time
import logging
import traceback
from pathlib import Path
import torch
import resource

from utils.logger import get_logger, log_resource_usage
import config

# Configure logger for this module
logger = get_logger(__name__)

def get_resource_usage():
    """
    Get current resource usage (RAM, CPU time).
    Returns a dictionary with 'peak_ram_mb', 'current_ram_mb', 'cpu_time'.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    peak_ram_kb = usage.ru_maxrss
    peak_ram_mb = peak_ram_kb / 1024.0
    
    return {
        "peak_ram_mb": peak_ram_mb,
        "cpu_time": usage.ru_utime + usage.ru_stime
    }

def load_model(model_name="Phi-3-mini-4k-instruct", quantization="4bit"):
    """
    Load the LLM model with fallback logic for memory constraints.
    
    Args:
        model_name: The name of the model to load (default: Phi-3-mini-4k-instruct)
        quantization: Initial quantization strategy ("4bit" or "16bit")
        
    Returns:
        A loaded model and tokenizer, or a fallback model if initial load fails.
        
    Fallback Logic:
        1. Attempt to load the requested model with the requested quantization.
        2. If it fails due to MemoryError (OOM):
           - If initial was "4bit", try "16bit" (often smaller model footprint for small models) 
             OR switch to a smaller model like "TinyLlama/TinyLlama-1.1B-Chat-v1.0".
           - If initial was "16bit" or fallback to smaller model also fails, raise the error.
           
    Note: This function ensures that we do not silently return a dummy model. 
    It strictly attempts real loads and raises if all strategies fail.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    
    fallback_models = [
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "microsoft/Phi-3-mini-4k-instruct" # Re-try Phi-3 with different config if needed
    ]
    
    current_model_name = model_name
    current_quantization = quantization
    attempt_count = 0
    max_attempts = 3
    
    while attempt_count < max_attempts:
        try:
            logger.info(f"Attempting to load model: {current_model_name} with {current_quantization} precision.")
            
            # Configure quantization if requested
            bnb_config = None
            if current_quantization == "4bit":
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
            
            # Prepare model arguments
            model_kwargs = {
                "device_map": "auto",
                "torch_dtype": torch.float16,
                "trust_remote_code": True
            }
            
            if bnb_config:
                model_kwargs["quantization_config"] = bnb_config
            
            tokenizer = AutoTokenizer.from_pretrained(current_model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(current_model_name, **model_kwargs)
            
            logger.info(f"Successfully loaded model: {current_model_name}")
            return model, tokenizer
            
        except MemoryError as e:
            logger.warning(f"MemoryError loading {current_model_name} ({current_quantization}): {str(e)}")
            attempt_count += 1
            
            if attempt_count >= max_attempts:
                logger.error("All model loading attempts failed due to memory constraints.")
                raise
            
            # Fallback Strategy
            if current_quantization == "4bit":
                logger.info("Attempting fallback: Switching to 16-bit precision for the same model.")
                current_quantization = "16bit"
            elif current_model_name == model_name:
                # If 4bit failed and we tried 16bit, or 16bit failed, try a smaller model
                if current_model_name == "TinyLlama/TinyLlama-1.1B-Chat-v1.0":
                    logger.error("Even TinyLlama failed. No more fallbacks available.")
                    raise MemoryError("All model loading strategies exhausted due to OOM.")
                else:
                    logger.info(f"Attempting fallback: Switching to smaller model: TinyLlama.")
                    current_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
                    current_quantization = "4bit" # Try 4bit first on the smaller model
            else:
                logger.error("Unexpected state in fallback logic.")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error loading model: {str(e)}")
            traceback.print_exc()
            raise

def truncate_context(prompt: str, max_tokens: int = 2048, tokenizer=None) -> str:
    """
    Truncate the prompt to fit within the model's context window.
    
    Args:
        prompt: The input text prompt.
        max_tokens: Maximum number of tokens allowed.
        tokenizer: The tokenizer instance to use.
        
    Returns:
        Truncated prompt string.
    """
    if tokenizer is None:
        # Fallback if tokenizer not provided (simple character truncation is unsafe for tokens)
        # Ideally, this should not happen in the pipeline
        logger.warning("Tokenizer not provided for truncation. Returning original prompt.")
        return prompt
        
    tokens = tokenizer.encode(prompt, add_special_tokens=False)
    
    if len(tokens) <= max_tokens:
        return prompt
        
    truncated_tokens = tokens[:max_tokens]
    truncated_text = tokenizer.decode(truncated_tokens, skip_special_tokens=True)
    
    logger.info(f"Context truncated from {len(tokens)} to {len(truncated_tokens)} tokens.")
    return truncated_text

def generate_answer(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    """
    Generate an answer using the loaded model.
    
    Args:
        model: The loaded LLM model.
        tokenizer: The loaded tokenizer.
        prompt: The input prompt string.
        max_new_tokens: Maximum number of tokens to generate.
        
    Returns:
        The generated answer string.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
    answer = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    return answer.strip()

def run_inference_pipeline(questions: list, memory_store: dict, model_name: str = "Phi-3-mini-4k-instruct"):
    """
    Run the inference pipeline for a list of questions using the specified memory store.
    
    Args:
        questions: List of question dictionaries.
        memory_store: The memory store dictionary (Coarse, Medium, or Fine).
        model_name: Name of the model to use.
        
    Returns:
        List of answer dictionaries.
    """
    logger.info("Starting inference pipeline...")
    start_time = time.time()
    
    results = []
    
    # Load model with fallback logic
    model, tokenizer = load_model(model_name=model_name)
    
    for i, q_data in enumerate(questions):
        try:
            logger.info(f"Processing question {i+1}/{len(questions)}")
            
            # Construct prompt (simplified for this task, assuming context is already retrieved)
            # In a real scenario, we would retrieve context from memory_store here
            # For T028, we focus on the model loading and fallback logic.
            prompt = f"Question: {q_data['question']}\nAnswer:"
            
            # Truncate context if necessary
            truncated_prompt = truncate_context(prompt, tokenizer=tokenizer)
            
            # Generate answer
            answer = generate_answer(model, tokenizer, truncated_prompt)
            
            results.append({
                "question_id": q_data.get("id", i),
                "question": q_data["question"],
                "answer": answer,
                "strategy": "inference_pipeline"
            })
            
        except Exception as e:
            logger.error(f"Error processing question {i+1}: {str(e)}")
            traceback.print_exc()
            # Continue processing other questions
            continue
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Inference pipeline completed in {duration:.2f} seconds.")
    
    # Record resource usage
    resource_usage = get_resource_usage()
    log_resource_usage("inference_pipeline", resource_usage)
    
    return results

def main():
    """
    Main entry point for the inference module.
    This is primarily for testing the fallback logic directly.
    """
    logger.info("Running inference module main...")
    
    # Mock data for testing
    mock_questions = [
        {"id": 1, "question": "What is the capital of France?"},
        {"id": 2, "question": "Describe the image content."}
    ]
    
    try:
        # This will trigger the fallback logic if the system is memory constrained
        results = run_inference_pipeline(mock_questions, {}, model_name="Phi-3-mini-4k-instruct")
        
        # Save results
        output_path = Path(config.PROJECT_ROOT) / "data" / "processed" / "inference_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()