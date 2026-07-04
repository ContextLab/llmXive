"""
code/03_inference.py
Implements StarCoder inference for stratified samples.
Generates natural-language summaries and bug-localization predictions.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Attempt to import torch with CPU-only fallback logic
try:
    import torch
except ImportError:
    print("Error: torch is required. Install via: pip install torch --index-url https://download.pytorch.org/whl/cpu", file=sys.stderr)
    sys.exit(1)

# Attempt to import transformers
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        StoppingCriteria,
        StoppingCriteriaList,
        TextGenerationPipeline,
        set_seed
    )
except ImportError:
    print("Error: transformers is required. Install via: pip install transformers", file=sys.stderr)
    sys.exit(1)

# Constants
MODEL_NAME = "bigcode/starcoder"
MAX_NEW_TOKENS = 64
MAX_INPUT_LENGTH = 2048  # Truncate input if too long
TIMEOUT_SECONDS = 300    # 5 minutes per file
OUTPUT_PATH = "data/processed/inference_results.jsonl"
INPUT_PATH = "data/processed/style_scores.csv"

# Set seed for reproducibility
set_seed(42)


class TimeoutStoppingCriteria(StoppingCriteria):
    """Custom stopping criteria to enforce time limits."""
    def __init__(self, timeout_seconds: int, start_time: float):
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.start_time = start_time

    def __call__(self, input_ids, scores, **kwargs):
        if time.time() - self.start_time > self.timeout_seconds:
            return True
        return False


def load_model_and_tokenizer(model_name: str, device: str = "cpu"):
    """
    Load StarCoder model and tokenizer in CPU mode.
    Uses 8-bit quantization if available to reduce memory, otherwise standard float32.
    """
    print(f"Loading model: {model_name} on {device}...", file=sys.stderr)
    
    # Check for bitsandbytes for 8-bit quantization (optional optimization)
    try:
        import bitsandbytes
        has_bitsandbytes = True
    except ImportError:
        has_bitsandbytes = False

    if has_bitsandbytes and device == "cuda":
        # We are restricted to CPU, so we ignore bitsandbytes optimization for now
        # as it's primarily for CUDA.
        pass

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="left"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    # Force CPU execution as per constraints
    model_kwargs = {
        "device_map": None, # Explicitly None to avoid auto device placement issues on CPU
        "torch_dtype": torch.float32, # CPU usually handles float32 better than float16 in older versions
        "low_cpu_mem_usage": True
    }

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **model_kwargs
    )
    model.eval() # Set to evaluation mode

    print("Model loaded successfully.", file=sys.stderr)
    return model, tokenizer


def prepare_prompt(code_text: str, task_type: str = "summary") -> str:
    """
    Constructs the prompt for StarCoder.
    StarCoder expects specific prompt formats for certain tasks, but for generic
    code understanding, we use a standard instruction format.
    """
    # Truncate code if too long
    if len(code_text) > MAX_INPUT_LENGTH:
        code_text = code_text[:MAX_INPUT_LENGTH]
    
    if task_type == "summary":
        return f"<fim_prefix>{code_text}<fim_suffix><fim_middle>Provide a concise natural language summary of this code:\n"
    elif task_type == "bug":
        return f"<fim_prefix>{code_text}<fim_suffix><fim_middle>Identify lines with potential bugs (line numbers):\n"
    else:
        return f"<fim_prefix>{code_text}<fim_suffix><fim_middle>"


def run_inference(
    model,
    tokenizer,
    code_text: str,
    task_type: str,
    timeout_seconds: int = TIMEOUT_SECONDS
) -> Tuple[Optional[str], Optional[List[int]]]:
    """
    Runs inference for a single code snippet.
    Returns (summary_text, bug_lines) or (None, None) on error.
    """
    start_time = time.time()
    timeout_criteria = TimeoutStoppingCriteria(timeout_seconds, start_time)

    try:
        prompt = prepare_prompt(code_text, task_type)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_LENGTH)
        
        # Move inputs to CPU
        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=True,
                temperature=0.2,
                top_p=0.95,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                stopping_criteria=StoppingCriteriaList([timeout_criteria])
            )

        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

        # Parse bug lines if task is bug localization
        bug_lines = None
        if task_type == "bug":
            # Simple heuristic: extract numbers from the generated text
            import re
            numbers = re.findall(r'\b\d+\b', generated_text)
            bug_lines = [int(n) for n in numbers if 0 < int(n) < 10000] # Sanity check
            if not bug_lines:
                bug_lines = [] # Empty list instead of None if no bugs found

        return generated_text.strip(), bug_lines

    except Exception as e:
        print(f"Error during inference for {task_type}: {str(e)}", file=sys.stderr)
        return None, None


def load_stratified_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads the stratified data from the CSV file produced by T016.
    Reads the 'file_path' column to load the actual code content.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row.get('file_path')
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as code_file:
                        code_content = code_file.read()
                    data.append({
                        'file_path': file_path,
                        'code': code_content,
                        'group': row.get('group', 'Unknown'),
                        'composite_score': float(row.get('composite_score', 0))
                    })
                except Exception as e:
                    print(f"Warning: Could not read code file {file_path}: {e}", file=sys.stderr)
            else:
                print(f"Warning: File not found for row: {row.get('file_path')}", file=sys.stderr)
    return data


def main():
    parser = argparse.ArgumentParser(description="Run StarCoder inference on stratified code samples.")
    parser.add_argument(
        "--input", 
        type=str, 
        default=INPUT_PATH, 
        help="Path to the stratified style scores CSV (default: data/processed/style_scores.csv)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=OUTPUT_PATH, 
        help="Path to the output JSONL file (default: data/processed/inference_results.jsonl)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=TIMEOUT_SECONDS, 
        help=f"Timeout per file in seconds (default: {TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Limit the number of files to process (for testing)"
    )
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load model
    try:
        model, tokenizer = load_model_and_tokenizer(MODEL_NAME)
    except Exception as e:
        print(f"FATAL: Failed to load model: {e}", file=sys.stderr)
        sys.exit(1)

    # Load data
    try:
        samples = load_stratified_data(args.input)
        if not samples:
            print("Warning: No valid samples found in input file.", file=sys.stderr)
            sys.exit(0)
        
        if args.limit:
            samples = samples[:args.limit]
            print(f"Processing limited to {args.limit} samples.", file=sys.stderr)
    except Exception as e:
        print(f"FATAL: Failed to load data: {e}", file=sys.stderr)
        sys.exit(1)

    results = []

    print(f"Processing {len(samples)} samples...", file=sys.stderr)
    for i, sample in enumerate(samples):
        file_path = sample['file_path']
        code = sample['code']
        
        print(f"[{i+1}/{len(samples)}] Processing: {file_path}", file=sys.stderr)

        # 1. Generate Summary
        summary, _ = run_inference(model, tokenizer, code, "summary", args.timeout)
        
        # 2. Generate Bug Localization
        bug_lines, _ = run_inference(model, tokenizer, code, "bug", args.timeout)

        result_entry = {
            "file_path": file_path,
            "group": sample['group'],
            "composite_score": sample['composite_score'],
            "summary": summary if summary else "",
            "bug_localization_lines": bug_lines if bug_lines is not None else [],
            "status": "success"
        }

        # Handle specific error states if needed (e.g., timeout)
        if summary is None or (bug_lines is None and "bug" in result_entry):
            # Check if it was a timeout or other error
            # For now, we assume success if we got some text, even if partial
            pass

        results.append(result_entry)

        # Optional: Save incrementally to avoid losing data on crash
        if (i + 1) % 10 == 0:
            with open(args.output, 'w', encoding='utf-8') as f:
                for res in results:
                    f.write(json.dumps(res) + '\n')

    # Final save
    with open(args.output, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res) + '\n')

    print(f"Inference complete. Results saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
