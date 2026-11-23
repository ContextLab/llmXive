"""
Prompt-Based Cohort Generator (T033)

Generates a "Prompt-Based" cohort of LLM code using natural language prompts
derived from commit messages, without access to the original file content.

CRITICAL: If generation fails or exceeds time limits, this task MUST generate
spec_amendment_request.md detailing the failure and HALT the pipeline.
Do NOT fall back to filtering or synthetic data.

Output: data/processed/prompt_based_cohort.parquet
"""

import os
import sys
import time
import signal
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from datasets import load_dataset

# Import from project utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.config import get_config, ensure_directories
from utils.models import CodeSnippet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GENERATION_TIMEOUT_SECONDS = 30  # Per snippet timeout
MIN_SUCCESS_RATE = 0.95  # Minimum acceptable success rate

class TimeoutError(Exception):
    """Custom timeout exception for generation failures."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Generation timed out")

def generate_snippet_with_timeout(prompt: str, model, tokenizer, timeout: int = 30) -> Optional[str]:
    """
    Generate a code snippet with a timeout.
    
    Args:
        prompt: Natural language prompt derived from commit message
        model: LLM model instance
        tokenizer: Model tokenizer
        timeout: Timeout in seconds
        
    Returns:
        Generated code snippet or None if failed
    """
    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        
        # Generate with constraints
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode and clean
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the code part (after prompt)
        code_part = generated[len(prompt):].strip()
        
        signal.alarm(0)  # Cancel alarm
        signal.signal(signal.SIGALRM, old_handler)  # Restore handler
        
        return code_part
        
    except TimeoutError:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        logger.warning(f"Generation timed out for prompt: {prompt[:50]}...")
        return None
    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        logger.error(f"Generation failed: {str(e)}")
        return None

def create_prompt_from_commit_message(commit_message: str) -> str:
    """
    Create a code generation prompt from a commit message.
    
    Args:
        commit_message: The original commit message
        
    Returns:
        Formatted prompt for code generation
    """
    # Simple heuristic: use commit message as the task description
    # In a real implementation, this could be more sophisticated
    prompt = f"""Implement the following code change described in the commit message:
    
    {commit_message}
    
    Provide only the code implementation, no explanations or markdown."""
    
    return prompt

def load_model_and_tokenizer(model_name: str = "codellama/CodeLlama-7b-hf") -> Tuple[Any, Any]:
    """
    Load the LLM model and tokenizer.
    
    Args:
        model_name: HuggingFace model identifier
        
    Returns:
        Tuple of (model, tokenizer)
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        logger.info(f"Loading model: {model_name}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # CPU-tractable
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        if not torch.cuda.is_available():
            model = model.cpu()
        
        logger.info("Model loaded successfully")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

def run_prompt_cohort_generation(
    input_data_path: str,
    output_path: str,
    model_name: str = "codellama/CodeLlama-7b-hf",
    max_snippets: int = 100
) -> bool:
    """
    Run the prompt-based cohort generation pipeline.
    
    Args:
        input_data_path: Path to input PR data (parquet)
        output_path: Path for output parquet file
        model_name: HuggingFace model identifier
        max_snippets: Maximum number of snippets to generate
        
    Returns:
        True if successful, False if generation failed
    """
    ensure_directories([output_path])
    
    # Load input data
    logger.info(f"Loading input data from {input_data_path}")
    try:
        df = pd.read_parquet(input_data_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {str(e)}")
        return False
    
    # Load model
    try:
        model, tokenizer = load_model_and_tokenizer(model_name)
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False
    
    # Generate prompts and code
    results = []
    success_count = 0
    failure_count = 0
    
    logger.info(f"Starting generation for up to {min(len(df), max_snippets)} snippets")
    
    for idx, row in df.head(max_snippets).iterrows():
        commit_message = row.get('commit_message', '')
        if not commit_message:
            continue
        
        prompt = create_prompt_from_commit_message(commit_message)
        
        # Generate with timeout
        code = generate_snippet_with_timeout(prompt, model, tokenizer, GENERATION_TIMEOUT_SECONDS)
        
        if code:
            success_count += 1
            results.append({
                'pr_id': row.get('pr_id', f'pr_{idx}'),
                'repo_id': row.get('repo_id', 'unknown'),
                'author_type': 'llm_prompt_based',
                'generation_source': 'prompt_from_commit',
                'original_commit_message': commit_message,
                'generated_code': code,
                'generation_timestamp': datetime.now().isoformat(),
                'success': True
            })
        else:
            failure_count += 1
            results.append({
                'pr_id': row.get('pr_id', f'pr_{idx}'),
                'repo_id': row.get('repo_id', 'unknown'),
                'author_type': 'llm_prompt_based',
                'generation_source': 'prompt_from_commit',
                'original_commit_message': commit_message,
                'generated_code': None,
                'generation_timestamp': datetime.now().isoformat(),
                'success': False
            })
        
        if idx % 10 == 0:
            logger.info(f"Progress: {idx}/{min(len(df), max_snippets)} processed")
    
    # Create DataFrame
    result_df = pd.DataFrame(results)
    
    # Calculate success rate
    success_rate = success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0.0
    logger.info(f"Generation complete. Success rate: {success_rate:.2%} ({success_count}/{success_count + failure_count})")
    
    # Check if success rate is acceptable
    if success_rate < MIN_SUCCESS_RATE:
        logger.error(f"Success rate {success_rate:.2%} below minimum {MIN_SUCCESS_RATE:.2%}")
        return False
    
    # Write output
    try:
        result_df.to_parquet(output_path, index=False)
        logger.info(f"Output written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {str(e)}")
        return False

def create_spec_amendment_request(failure_reason: str, output_path: str = "data/processed/spec_amendment_request.md"):
    """
    Create a spec amendment request when generation fails.
    
    Args:
        failure_reason: Description of why generation failed
        output_path: Path for the amendment request file
    """
    ensure_directories([output_path])
    
    timestamp = datetime.now().isoformat()
    
    content = f"""# Specification Amendment Request - T033 Prompt-Based Cohort Generation

## Timestamp
{timestamp}

## Task ID
T033

## User Story
US4 - Prompt-Based Cohort Validation

## Failure Description
The mandatory generation task for the prompt-based cohort has failed:

{failure_reason}

## Impact
- Cannot proceed with prompt-based cohort validation
- Cannot validate causal claim (FR-008)
- Analysis pipeline blocked

## Recommended Actions
1. Review model compatibility and resource requirements
2. Consider alternative CPU-tractable models
3. Adjust timeout parameters if appropriate
4. Evaluate feasibility of distributed generation

## Next Steps
This pipeline has been halted. Please review and update the specification accordingly.

---
*Automatically generated by T033 pipeline*
"""
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Spec amendment request written to {output_path}")

def main():
    """Main entry point for the prompt cohort generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate prompt-based code cohort')
    parser.add_argument('--input', type=str, default='data/processed/merged_pr_data.parquet',
                      help='Input parquet file path')
    parser.add_argument('--output', type=str, default='data/processed/prompt_based_cohort.parquet',
                      help='Output parquet file path')
    parser.add_argument('--model', type=str, default='codellama/CodeLlama-7b-hf',
                      help='HuggingFace model identifier')
    parser.add_argument('--max-snippets', type=int, default=100,
                      help='Maximum number of snippets to generate')
    
    args = parser.parse_args()
    
    logger.info("Starting prompt-based cohort generation")
    
    success = run_prompt_cohort_generation(
        input_data_path=args.input,
        output_path=args.output,
        model_name=args.model,
        max_snippets=args.max_snippets
    )
    
    if not success:
        logger.error("Generation failed. Creating spec amendment request.")
        create_spec_amendment_request(
            f"Generation pipeline failed with input: {args.input}, output: {args.output}"
        )
        sys.exit(1)
    
    logger.info("Prompt-based cohort generation completed successfully")
    sys.exit(0)

if __name__ == '__main__':
    main()