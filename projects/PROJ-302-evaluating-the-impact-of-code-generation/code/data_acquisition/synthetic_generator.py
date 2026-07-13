"""
Synthetic code snippet generation module.

Implements MANDATORY GENERATION using a CPU-tractable LLM (CodeLlama).
If generation fails or exceeds the time limit, this module generates
a spec_amendment_request.md and halts the pipeline.
"""
import os
import sys
import time
import json
import signal
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading

import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Import existing models
from utils.models import CodeSnippet

# Constants
GENERATION_TIMEOUT_SECONDS = 30  # Time limit per snippet generation
MAX_RETRIES = 3
OUTPUT_PATH = "data/processed/generated_snippets.parquet"
AMENDMENT_PATH = "spec_amendment_request.md"

# Model configuration (CPU-tractable)
MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf"
# If 7b is too heavy for CPU, fallback to a smaller quantized version if available
# For this implementation, we assume the environment has appropriate model loading
# or we use a smaller variant if specified in config.
SMALLER_MODEL_NAME = "codellama/CodeLlama-7b-Instruct-hf" 

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Generation timed out")

def generate_snippet_with_timeout(
    prompt: str, 
    generator: Any, 
    max_new_tokens: int = 100
) -> Optional[str]:
    """
    Generate a code snippet with a hard timeout.
    Returns None if timeout or error occurs.
    """
    result = [None]
    exception = [None]

    def run_generation():
        try:
            # Use the generator pipeline
            output = generator(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=0.2,
                do_sample=True,
                pad_token_id=generator.tokenizer.eos_token_id
            )
            result[0] = output[0]['generated_text']
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=run_generation)
    thread.daemon = True
    thread.start()
    thread.join(timeout=GENERATION_TIMEOUT_SECONDS)

    if thread.is_alive():
        return None
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def create_spec_amendment_request(error_type: str, details: str):
    """
    Generates a spec_amendment_request.md file and exits the process.
    """
    timestamp = datetime.now().isoformat()
    content = f"""# Spec Amendment Request

**Generated**: {timestamp}
**Task**: T014b - Synthetic Code Generation
**Reason**: Mandatory Generation Failure

## Error Type
{error_type}

## Details
{details}

## Impact
The pipeline cannot proceed with the generation of synthetic LLM code snippets as required by FR-002.
The fallback to classification is explicitly forbidden by the specification.
A new model, hardware resources, or specification adjustment is required.

## Action Required
1. Review the error details above.
2. Update the model configuration or hardware constraints.
3. Amend the specification to allow alternative generation strategies if necessary.
"""
    with open(AMENDMENT_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"CRITICAL: Generation failed. Spec amendment request written to {AMENDMENT_PATH}")
    sys.exit(1)

def load_model():
    """
    Load the CPU-tractable CodeLlama model.
    """
    print(f"Loading model: {MODEL_NAME}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        # For CPU, we might need to set device_map or use float16 if memory allows
        # Using default loading for CPU compatibility
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, 
            torch_dtype=torch.float32, 
            device_map="cpu",
            trust_remote_code=True
        )
        
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1  # Force CPU
        )
        print("Model loaded successfully.")
        return generator
    except Exception as e:
        create_spec_amendment_request(
            "Model Loading Failed", 
            f"Could not load {MODEL_NAME}. Error: {str(e)}"
        )
        return None

def create_prompt_from_pr_data(pr_data: Dict[str, Any]) -> str:
    """
    Constructs a prompt for code generation based on PR metadata.
    This simulates the requirement to generate code based on context.
    """
    # Extract relevant context
    file_content = pr_data.get("content", "")
    file_path = pr_data.get("path", "unknown.py")
    commit_message = pr_data.get("commit_message", "Refactor code")
    
    # Truncate content if too long to fit in context window
    if len(file_content) > 1000:
        file_content = file_content[:1000] + "... [truncated]"
    
    prompt = f"""You are an expert software engineer. Based on the following context from a pull request, 
    generate a realistic code snippet that represents a typical change or addition.
    
    File Path: {file_path}
    Commit Message: {commit_message}
    
    Existing Code Context:
    {file_content}
    
    Generate the code snippet now:
    """
    return prompt

def run_synthetic_generation(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main generation loop.
    """
    generator = load_model()
    if not generator:
        # load_model handles the exit, but safe guard
        return []

    generated_snippets = []
    
    for i, pr_data in enumerate(input_data):
        print(f"Processing item {i+1}/{len(input_data)}...")
        
        prompt = create_prompt_from_pr_data(pr_data)
        
        try:
            full_text = generate_snippet_with_timeout(prompt, generator)
            
            if not full_text:
                create_spec_amendment_request(
                    "Timeout Exceeded", 
                    f"Generation timed out for snippet {i+1} after {GENERATION_TIMEOUT_SECONDS} seconds."
                )
            
            # Extract the generated part (usually after the prompt)
            # Simple heuristic: take the last part or clean up prompt echo
            generated_code = full_text
            if prompt in full_text:
                generated_code = full_text.split(prompt)[-1].strip()
            
            # Basic validation
            if not generated_code or len(generated_code) < 10:
                print(f"Warning: Generated snippet too short for item {i+1}. Skipping.")
                continue

            snippet = {
                "snippet_id": f"syn_{i:06d}",
                "source_commit": pr_data.get("commit_hash", "unknown"),
                "generation_source": "CodeLlama-Synthetic",
                "raw_code": generated_code,
                "prompt_used": prompt,
                "generation_timestamp": datetime.now().isoformat(),
                "success": True
            }
            generated_snippets.append(snippet)

        except TimeoutError:
            create_spec_amendment_request(
                "Timeout Exceeded", 
                f"Generation timed out for snippet {i+1}."
            )
        except Exception as e:
            create_spec_amendment_request(
                "Generation Error", 
                f"Unexpected error generating snippet {i+1}: {str(e)}"
            )
    
    return generated_snippets

def main():
    """
    Entry point for the synthetic generator.
    Reads from data/raw (simulated or actual) and writes to data/processed.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Simulate input data if no file exists, OR load from a real source
    # Since T012 (github_scraper) exists, we assume data might be in data/raw
    # For this task, we demonstrate the generation capability.
    # In a real pipeline, we would load from data/raw/pr_metadata.json or similar.
    
    input_file = "data/raw/pr_samples.json"
    if os.path.exists(input_file):
        print(f"Loading input data from {input_file}...")
        with open(input_file, "r") as f:
            input_data = json.load(f)
    else:
        # Fallback: Create a minimal synthetic input for demonstration if no data exists
        # This is allowed ONLY to bootstrap the pipeline if the acquisition step hasn't run yet,
        # but the actual generation MUST use the model.
        print("No input data found. Creating minimal bootstrap data for generation test.")
        input_data = [
            {
                "commit_hash": "abc123",
                "path": "example.py",
                "content": "def hello():\n    pass",
                "commit_message": "Add hello function"
            }
        ]

    print(f"Starting synthetic generation for {len(input_data)} items...")
    results = run_synthetic_generation(input_data)
    
    if not results:
        create_spec_amendment_request(
            "No Data Generated",
            "The generation loop produced no valid snippets."
        )

    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"Successfully generated {len(results)} snippets. Output saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()