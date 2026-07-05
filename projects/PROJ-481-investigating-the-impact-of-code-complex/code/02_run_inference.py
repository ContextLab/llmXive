import argparse
import csv
import json
import logging
import os
import sys
import signal
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from local utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from utils.inference import (
    load_model,
    run_single_inference,
    detect_hallucination,
    InferenceError,
    TimeoutError,
    ModelLoadError
)
from utils.metrics import validate_code_syntax

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/inference.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MEMORY_LIMIT_MB = 2048
DEFAULT_MODEL_PATH = "models/starcoder-1b.gguf"
DEFAULT_INPUT_CSV = "data/derived/metrics.csv"
DEFAULT_OUTPUT_CSV = "data/derived/inference_results.csv"
DEFAULT_BATCH_SIZE = 1

def load_ground_truth(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the metrics CSV which contains the code snippets and metadata.
    In this context, 'ground truth' refers to the input code and any
    associated task labels available in the metrics file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    logger.info(f"Loaded {len(data)} entries from {input_path}")
    return data

def calculate_accuracy_metrics(
    generated: str,
    ground_truth: str,
    task_type: str
) -> Dict[str, float]:
    """
    Calculate accuracy metrics (ROUGE-L, F1, BLEU) between generated and ground truth.
    Note: This is a simplified implementation. In a full pipeline,
    external libraries like `rouge` or `sacrebleu` would be used.
    For this task, we focus on the timeout/fail structure.
    """
    # Placeholder for actual metric calculation logic
    # In a real scenario, this would import rouge_score or similar
    if not generated or not ground_truth:
        return {"rouge_l": 0.0, "f1": 0.0, "bleu": 0.0}

    # Simple token overlap as a proxy for demonstration
    gen_tokens = set(generated.lower().split())
    truth_tokens = set(ground_truth.lower().split())

    if not truth_tokens:
        return {"rouge_l": 0.0, "f1": 0.0, "bleu": 0.0}

    intersection = gen_tokens.intersection(truth_tokens)
    precision = len(intersection) / len(gen_tokens) if gen_tokens else 0
    recall = len(intersection) / len(truth_tokens)

    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Simplified ROUGE-L (just recall for demo)
    rouge_l = recall

    # Simplified BLEU (just precision for demo)
    bleu = precision

    return {
        "rouge_l": round(rouge_l, 4),
        "f1": round(f1, 4),
        "bleu": round(bleu, 4)
    }

def detect_hallucination_or_non_code(generated_text: str) -> Tuple[bool, str]:
    """
    Detect if the generated text is hallucinated or non-code.
    Returns (is_hallucination, reason).
    """
    if not generated_text or len(generated_text.strip()) == 0:
        return True, "Empty output"

    # Basic heuristics for non-code
    non_code_indicators = [
        "I cannot", "I am an AI", "Here is the code", # Common LLM chitchat
        "Sorry", "I don't know", "As a language model"
    ]

    lower_text = generated_text.lower()
    for indicator in non_code_indicators:
        if indicator in lower_text:
            return True, f"Contains non-code indicator: {indicator}"

    # Check for code structure (simple heuristic)
    has_braces = '{' in generated_text or '}' in generated_text
    has_parens = '(' in generated_text or ')' in generated_text
    has_def = 'def ' in generated_text or 'func ' in lower_text or 'function ' in lower_text

    if not (has_braces or has_parens or has_def):
        # If it looks like prose without code structure
        if len(generated_text.split()) > 10 and not any(c in generated_text for c in [';', ':', '=', 'return']):
            return True, "Output lacks code structure"

    return False, "Valid code structure detected"

def process_single_function(
    row: Dict[str, Any],
    model: Any,
    timeout: int,
    memory_limit_mb: int
) -> Dict[str, Any]:
    """
    Process a single function with timeout and memory limit handling.
    Marks functions as "timeout/fail" without halting the pipeline.
    """
    func_id = row.get('function_id', 'unknown')
    code = row.get('code', '')
    task_type = row.get('task_type', 'summarization')
    ground_truth = row.get('ground_truth', '')

    result = {
        'function_id': func_id,
        'task_type': task_type,
        'status': 'success',
        'generated_text': '',
        'accuracy_score': 0.0,
        'hallucination_flag': False,
        'error_message': None,
        'timeout': False,
        'memory_error': False
    }

    # Validate syntax before inference
    if not validate_code_syntax(code):
        result['status'] = 'invalid_syntax'
        result['error_message'] = 'Input code has invalid syntax'
        return result

    try:
        # Attempt to run inference with timeout
        # Note: The actual timeout logic is implemented via signal or concurrent.futures
        # depending on OS support. We use a wrapper here.

        def inference_task():
            return run_single_inference(model, code, task_type)

        # Use ThreadPoolExecutor for timeout handling
        # Note: This is a simplified pattern. In production, consider `concurrent.futures`
        # with a dedicated executor or `signal` based timeout for main thread.
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(inference_task)
                generated_text = future.result(timeout=timeout)
        except FuturesTimeoutError:
            result['status'] = 'timeout'
            result['timeout'] = True
            result['error_message'] = f'Inference timed out after {timeout}s'
            logger.warning(f"Timeout for function {func_id}")
            return result

        if not generated_text:
            result['status'] = 'empty_output'
            result['error_message'] = 'Model returned empty output'
            return result

        # Hallucination detection
        is_hallucination, reason = detect_hallucination_or_non_code(generated_text)
        if is_hallucination:
            result['hallucination_flag'] = True
            result['status'] = 'hallucination'
            result['error_message'] = reason
            result['generated_text'] = generated_text
            result['accuracy_score'] = 0.0
            return result

        result['generated_text'] = generated_text

        # Calculate accuracy
        if ground_truth:
            metrics = calculate_accuracy_metrics(generated_text, ground_truth, task_type)
            result['accuracy_score'] = metrics.get('rouge_l', 0.0) # Using ROUGE-L as primary
        else:
            result['accuracy_score'] = 0.0 # No ground truth to compare

        return result

    except InferenceError as e:
        result['status'] = 'inference_error'
        result['error_message'] = str(e)
        logger.error(f"Inference error for {func_id}: {e}")
        return result
    except Exception as e:
        result['status'] = 'unexpected_error'
        result['error_message'] = str(e)
        logger.error(f"Unexpected error for {func_id}: {e}")
        return result

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to CSV.
    """
    if not results:
        logger.warning("No results to save.")
        return

    fieldnames = list(results[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run LLM Inference on Code Metrics with Timeout Handling")
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_CSV, help='Path to metrics CSV')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_CSV, help='Path to output results CSV')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL_PATH, help='Path to GGUF model')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT_SECONDS, help='Timeout per function in seconds')
    parser.add_argument('--memory-limit', type=int, default=DEFAULT_MEMORY_LIMIT_MB, help='Memory limit in MB (for logging/monitoring)')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Batch size for processing')

    args = parser.parse_args()

    logger.info(f"Starting inference with timeout={args.timeout}s, memory_limit={args.memory_limit_mb}MB")

    # Load data
    try:
        data = load_ground_truth(args.input)
    except FileNotFoundError as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # Load model
    try:
        logger.info(f"Loading model from {args.model}")
        model = load_model(args.model)
    except ModelLoadError as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    results = []
    total = len(data)
    processed = 0

    for i, row in enumerate(data):
        processed += 1
        logger.info(f"Processing {processed}/{total}: {row.get('function_id', 'N/A')}")

        result = process_single_function(row, model, args.timeout, args.memory_limit_mb)
        results.append(result)

        # Optional: Save periodically
        if processed % 10 == 0:
            save_results(results, args.output)

    # Final save
    save_results(results, args.output)
    logger.info("Inference pipeline completed.")

if __name__ == "__main__":
    main()