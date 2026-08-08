"""
GPU Inference Task (T051): Generate code using Salesforce/codegen-350M-mono on GPU.

Constraints:
- Must use device="cuda" and load_in_8bit=True.
- Must detect if CPU execution fails or if USE_GPU=1 is set.
- Output: data/generated/codegen_samples_gpu.json
- Dependency: T010 (download_data.py)
"""
import os
import sys
import json
import logging
import time
import torch
from typing import List, Dict, Any, Optional

# Import shared utilities from utils.py (API Surface)
# Note: The API surface lists setup_logging, get_logger, set_task_id, get_task_id in utils.py
# However, generate_code.py also defines its own logging helpers.
# We will import from utils.py to ensure consistency with the "Shared-Module Contract" fix.
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback if utils.py doesn't export these directly (defensive coding)
    # This block ensures we don't crash if the import path changes slightly,
    # but we prefer the utils.py version to satisfy the contract.
    import logging
    def setup_logging(task_id: Optional[str] = None):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def get_logger():
        return logging.getLogger(__name__)
    
    def set_task_id(tid):
        pass
    
    def get_task_id():
        return "T051"

def check_gpu_availability() -> bool:
    """Check if a CUDA-capable GPU is available."""
    if not torch.cuda.is_available():
        logging.warning("No CUDA GPU detected. GPU task cannot proceed.")
        return False
    logging.info(f"CUDA GPU available: {torch.cuda.get_device_name(0)}")
    logging.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    return True

def load_model_gpu(model_name: str = "Salesforce/codegen-350M-mono"):
    """Load the model on GPU with 8-bit quantization."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError:
        raise ImportError("Required: pip install transformers bitsandbytes accelerate")

    logging.info(f"Loading model: {model_name} on GPU...")
    
    # Configure 8-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_compute_dtype=torch.float16,
        bnb_8bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Ensure padding token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto", # Automatically distribute to GPU
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    
    logging.info("Model loaded successfully on GPU.")
    return model, tokenizer

def generate_code_for_task(
    prompt: str, 
    model: Any, 
    tokenizer: Any, 
    max_new_tokens: int = 512
) -> str:
    """Generate code for a single task prompt."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.2,
            top_p=0.95,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # The model often repeats the prompt, so we try to extract just the completion
    # However, for HumanEval, we usually want the full completion after the prompt.
    # We'll return the full decoded text and let downstream processing handle it,
    # or strip the prompt if it's strictly repeated.
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):]
    
    return generated_text.strip()

def main():
    task_id = "T051"
    logger = setup_logging(task_id=task_id)
    set_task_id(task_id)
    
    logger.info(f"Starting GPU Inference Task ({task_id})")
    
    # 1. Check Environment and GPU
    use_gpu_env = os.environ.get("USE_GPU", "0") == "1"
    gpu_available = check_gpu_availability()
    
    if not gpu_available:
        if use_gpu_env:
            logger.critical("USE_GPU=1 set but no GPU available. Failing loudly.")
            sys.exit(1)
        else:
            logger.warning("No GPU available and USE_GPU not set. Skipping GPU generation.")
            # Create an empty output file to indicate the task was skipped safely
            output_path = "data/generated/codegen_samples_gpu.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump({"status": "skipped", "reason": "No GPU available", "samples": []}, f, indent=2)
            return

    # 2. Load Data (from T010)
    input_path = "data/raw/humaneval.parquet"
    if not os.path.exists(input_path):
        # Fallback to JSON if parquet isn't there (though T010 says parquet)
        # Checking for the actual file T010 produces
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} tasks from {input_path}")

    # 3. Load Model
    try:
        model, tokenizer = load_model_gpu()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # 4. Generate Code
    results = []
    start_time = time.time()
    
    for idx, row in df.iterrows():
        task_id_row = row.get("task_id", f"task_{idx}")
        prompt = row.get("prompt", "")
        
        logger.info(f"Processing {task_id_row} ({idx+1}/{len(df)})")
        
        try:
            generated_code = generate_code_for_task(prompt, model, tokenizer)
            results.append({
                "task_id": task_id_row,
                "source_type": "codegen_350m_gpu",
                "prompt": prompt,
                "generated_code": generated_code,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Generation failed for {task_id_row}: {e}")
            results.append({
                "task_id": task_id_row,
                "source_type": "codegen_350m_gpu",
                "prompt": prompt,
                "generated_code": None,
                "status": "error",
                "error": str(e)
            })

    elapsed = time.time() - start_time
    logger.info(f"Generation complete. Processed {len(results)} tasks in {elapsed:.2f}s")

    # 5. Save Output
    output_path = "data/generated/codegen_samples_gpu.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
