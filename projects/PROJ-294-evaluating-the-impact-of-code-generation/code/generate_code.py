import os
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def log_error(message: str, error: Exception, task_id: str) -> None:
    logger = logging.getLogger("llmXive")
    logger.error(f"[{task_id}] Error: {message} - {str(error)}")
    with open("errors.log", "a") as f:
        f.write(f"{datetime.now()} [{task_id}] {message}: {str(error)}\n")

def mark_sample_missing(sample_id: str, reason: str) -> Dict[str, Any]:
    return {
        "task_id": sample_id,
        "generated_code": None,
        "status": "missing",
        "error_reason": reason,
        "timestamp": datetime.now().isoformat()
    }

def generate_code_for_task(
    prompt: str,
    model_name: str = "Salesforce/codegen-mono-350M",
    max_new_tokens: int = 512,
    retries: int = 3
) -> Optional[str]:
    for attempt in range(retries):
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
            
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text
            
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2 ** attempt)
    
    return None

def generate_code_batch(
    tasks: List[Dict[str, Any]],
    output_path: str = "data/generated/code_samples.json",
    model_name: str = "Salesforce/codegen-mono-350M"
) -> List[Dict[str, Any]]:
    results = []
    
    for task in tasks:
        task_id = task["task_id"]
        prompt = task["prompt"]
        
        try:
            code = generate_code_for_task(prompt, model_name)
            if code:
                results.append({
                    "task_id": task_id,
                    "prompt": prompt,
                    "generated_code": code,
                    "canonical_solution": task.get("canonical_solution"),
                    "test": task.get("test"),
                    "status": "success"
                })
            else:
                results.append(mark_sample_missing(task_id, "Generation returned None"))
        except Exception as e:
            log_error(f"Failed to generate code for {task_id}", e, task_id)
            results.append(mark_sample_missing(task_id, str(e)))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    # Load sampled data
    input_path = "data/raw/humaneval_sampled.json"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run download_data.py first.")
        return
    
    with open(input_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
    
    print(f"Generating code for {len(tasks)} tasks...")
    results = generate_code_batch(tasks)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"Generated {success_count}/{len(results)} samples successfully.")

if __name__ == "__main__":
    main()
