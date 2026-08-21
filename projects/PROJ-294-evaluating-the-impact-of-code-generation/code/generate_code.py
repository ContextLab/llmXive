import os
import sys
import json
import logging
import time
import re
from typing import Dict, Any, List, Optional
from utils import setup_logging, get_logger, set_task_id, get_task_id

def ensure_dirs():
    """Ensure output directories exist."""
    os.makedirs("data/generated", exist_ok=True)
    os.makedirs("code/prompt_templates", exist_ok=True)

def load_prompt_template():
    """Load HumanEval prompt template."""
    path = "code/prompt_templates/humaneval.txt"
    if not os.path.exists(path):
        # Create default template
        template = "Complete the following function:\n\n{prompt}\n\n"
        with open(path, "w") as f:
            f.write(template)
    with open(path, "r") as f:
        return f.read()

def load_human_samples():
    """Load human reference samples."""
    path = "data/generated/human_samples.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Human samples not found: {path}")
    samples = []
    with open(path, "r") as f:
        for line in f:
            samples.append(json.loads(line))
    return samples

def load_model(model_name: str = "Salesforce/codegen-mono-350M"):
    """Load model with fallback logic."""
    logger = setup_logging(task_id="T012")
    logger.info(f"Loading model: {model_name}")
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        return model, tokenizer
    except Exception as e:
        if "350M" in model_name:
            raise RuntimeError(f"Failed to load model {model_name}: {e}")
        # Fallback logic would go here
        raise

def generate_code_with_model(model, tokenizer, prompt: str, max_length: int = 512) -> str:
    """Generate code using the loaded model."""
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def generate_code_for_task(model, tokenizer, task: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code for a single task."""
    template = load_prompt_template()
    prompt = template.format(prompt=task["prompt"])
    
    try:
        generated = generate_code_with_model(model, tokenizer, prompt)
        return {
            "task_id": task["task_id"],
            "generated_code": generated,
            "prompt": task["prompt"],
            "test": task.get("test", ""),
            "status": "success"
        }
    except Exception as e:
        return {
            "task_id": task["task_id"],
            "generated_code": None,
            "prompt": task["prompt"],
            "test": task.get("test", ""),
            "status": "failed",
            "error": str(e)
        }

def generate_code_batch(samples: List[Dict[str, Any]], model_name: str = "Salesforce/codegen-mono-350M"):
    """Generate code for a batch of samples."""
    logger = setup_logging(task_id="T012")
    logger.info(f"Starting code generation for {len(samples)} tasks")
    
    model, tokenizer = load_model(model_name)
    
    results = []
    for i, sample in enumerate(samples):
        logger.info(f"Processing task {i+1}/{len(samples)}: {sample['task_id']}")
        result = generate_code_for_task(model, tokenizer, sample)
        results.append(result)
        
        # Retry logic for failures
        if result["status"] == "failed":
            logger.warning(f"Retrying failed task: {sample['task_id']}")
            time.sleep(1)  # Backoff
            result = generate_code_for_task(model, tokenizer, sample)
            results[-1] = result
    
    return results

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str):
    """Save data to JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

def main():
    logger = setup_logging(task_id="T012")
    logger.info("Starting Code Generation (T012)")
    
    try:
        samples = load_human_samples()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    results = generate_code_batch(samples)
    save_to_jsonl(results, "data/generated/codegen_samples.json")
    
    logger.info(f"Saved generated code to data/generated/codegen_samples.json")

if __name__ == "__main__":
    main()
