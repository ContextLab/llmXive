import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config.settings import get_paths, get_config, ensure_directories
from code.src.inference.load_model import load_model_for_inference
from code.src.inference.prompt_templates import (
    get_bug_detection_prompt,
    SeverityLabel,
    format_severity_label,
    create_inference_request,
)
from code.src.inference.schema import InferenceResponse, InferenceStatus
from code.src.utils.timeout_wrapper import check_timeout, enforce_timeout, TimeoutContext
from code.src.utils.memory_watchdog import check_memory_limit, MemoryLimitExceeded
from code.src.utils.logger import get_logger

logger = get_logger(__name__)

def parse_llm_output(raw_output: str, pr_id: str) -> Dict[str, Any]:
    """
    Parse the raw LLM output string into a structured detection result.
    Handles JSON parsing errors and returns a standardized structure.
    """
    try:
        # Expect JSON output from the model
        data = json.loads(raw_output)
        
        # Validate required fields
        required_fields = ['severity', 'description']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Normalize severity to standard labels
        raw_severity = data.get('severity', 'minor')
        severity = format_severity_label(raw_severity)
        
        # Extract line information if available, otherwise default to None
        line_start = data.get('line_start')
        line_end = data.get('line_end')
        file_path = data.get('file_path')
        
        return {
            'pr_id': pr_id,
            'file_path': file_path,
            'line_start': line_start,
            'line_end': line_end,
            'severity': severity,
            'description': data.get('description', ''),
            'llm_error_flag': False
        }
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse LLM output for PR {pr_id}: {e}")
        return {
            'pr_id': pr_id,
            'file_path': None,
            'line_start': None,
            'line_end': None,
            'severity': None,
            'description': f"Parse error: {str(e)}",
            'llm_error_flag': True
        }

def process_single_pr(
    pr_data: Dict[str, Any],
    model: Any,
    tokenizer: Any,
    timeout_context: Optional[TimeoutContext] = None
) -> Dict[str, Any]:
    """
    Process a single PR through the LLM for bug detection.
    Returns a structured detection result.
    """
    pr_id = pr_data.get('pr_id', 'unknown')
    diff_content = pr_data.get('diff', '')
    
    # Check timeout before processing
    if timeout_context and check_timeout(timeout_context):
        logger.warning(f"Timeout reached for PR {pr_id}, skipping")
        return {
            'pr_id': pr_id,
            'file_path': None,
            'line_start': None,
            'line_end': None,
            'severity': None,
            'description': 'Timeout exceeded',
            'llm_error_flag': True
        }
    
    # Check memory before processing
    try:
        check_memory_limit()
    except MemoryLimitExceeded as e:
        logger.warning(f"Memory limit exceeded for PR {pr_id}, skipping: {e}")
        return {
            'pr_id': pr_id,
            'file_path': None,
            'line_start': None,
            'line_end': None,
            'severity': None,
            'description': f'Memory limit exceeded: {str(e)}',
            'llm_error_flag': True
        }
    
    # Build prompt
    prompt = get_bug_detection_prompt(diff_content, pr_id)
    
    # Run inference
    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse output
        result = parse_llm_output(raw_output, pr_id)
        return result
        
    except Exception as e:
        logger.error(f"Inference failed for PR {pr_id}: {e}")
        return {
            'pr_id': pr_id,
            'file_path': None,
            'line_start': None,
            'line_end': None,
            'severity': None,
            'description': f'Inference error: {str(e)}',
            'llm_error_flag': True
        }

def run_batch_inference(
    prs: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    timeout_seconds: int = 3600
) -> List[Dict[str, Any]]:
    """
    Run batch inference on a list of PRs with timeout and memory monitoring.
    """
    results = []
    start_time = time.time()
    
    logger.info(f"Starting batch inference for {len(prs)} PRs")
    
    with TimeoutContext(timeout_seconds) as timeout_ctx:
        for i, pr in enumerate(prs):
            pr_id = pr.get('pr_id', f'pr_{i}')
            logger.info(f"Processing PR {i+1}/{len(prs)}: {pr_id}")
            
            result = process_single_pr(pr, model, tokenizer, timeout_ctx)
            results.append(result)
            
            # Log progress
            elapsed = time.time() - start_time
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1} PRs in {elapsed:.2f}s")
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save inference results to the specified output path.
    Creates the directory if it doesn't exist.
    """
    ensure_directories([output_path.parent])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """
    Main entry point for running LLM inference on PRs and saving results.
    """
    config = get_config()
    paths = get_paths()
    
    # Load model
    logger.info("Loading model for inference...")
    model, tokenizer = load_model_for_inference()
    logger.info("Model loaded successfully")
    
    # Load input data (from split datasets or raw)
    input_path = paths.get('derived_split_human', paths.get('data_derived'))
    # For T024, we assume input is already split and available
    # We'll look for the split dataset or use raw data as fallback
    input_file = input_path / 'llm_code_split.json'
    if not input_file.exists():
        input_file = paths.get('data_raw') / 'pr_data.json'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        prs = json.load(f)
    
    logger.info(f"Loaded {len(prs)} PRs from {input_file}")
    
    # Run inference
    output_path = paths.get('data_derived') / 'llm_detections.json'
    
    results = run_batch_inference(
        prs, 
        model, 
        tokenizer, 
        timeout_seconds=config.get('max_inference_time_seconds', 3600)
    )
    
    # Save results
    save_results(results, output_path)
    
    # Log summary
    error_count = sum(1 for r in results if r.get('llm_error_flag', False))
    success_count = len(results) - error_count
    logger.info(f"Inference complete: {success_count} successful, {error_count} errors")
    logger.info(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
