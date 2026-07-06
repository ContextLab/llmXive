import argparse
import csv
import logging
import sys
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Optional, Tuple

# Local imports matching API surface
from utils.logging import get_logger, setup_logging
from utils.config import ensure_directories
from inference.model_loader import load_model, unload_model
from inference.metrics_calculator import calculate_metrics

logger = get_logger(__name__)

# Configuration constants
DEFAULT_TIMEOUT_PER_SNIPPET = 300  # 5 minutes per snippet
DEFAULT_TOTAL_TIMEOUT = 7200       # 2 hours total runtime
MIN_SNIPPET_THRESHOLD = 800        # Minimum snippets for "complete" status

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference pipeline with timeout controls")
    parser.add_argument("--input-csv", type=str, required=True, help="Path to input snippets CSV")
    parser.add_argument("--output-csv", type=str, required=True, help="Path to output results CSV")
    parser.add_argument("--model-id", type=str, default="Salesforce/codegen-350M-mono", help="Model identifier")
    parser.add_argument("--timeout-per-snippet", type=int, default=DEFAULT_TIMEOUT_PER_SNIPPET, help="Timeout per snippet in seconds")
    parser.add_argument("--total-timeout", type=int, default=DEFAULT_TOTAL_TIMEOUT, help="Total runtime timeout in seconds")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of parallel workers")
    return parser.parse_args()

def load_snippets(input_path: str) -> List[Dict[str, Any]]:
    """Load snippets from CSV file."""
    snippets = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            snippets.append(row)
    logger.info(f"Loaded {len(snippets)} snippets from {input_path}")
    return snippets

def save_results(results: List[Dict[str, Any]], output_path: str, status: str):
    """Save results to CSV file and append status metadata."""
    if not results:
        logger.warning("No results to save")
        return

    fieldnames = list(results[0].keys()) + ['run_status', 'total_runtime_seconds', 'snippets_processed']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            result['run_status'] = status
            writer.writerow(result)
    
    # Append a summary line to a metadata file
    meta_path = Path(output_path).parent / f"{Path(output_path).stem}_metadata.json"
    import json
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({
            "status": status,
            "total_runtime_seconds": sum(r.get('inference_time', 0) for r in results),
            "snippets_processed": len(results),
            "min_threshold_met": len(results) >= MIN_SNIPPET_THRESHOLD
        }, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path} with status: {status}")

def process_snippet_with_timeout(
    snippet: Dict[str, Any], 
    model: Any, 
    tokenizer: Any, 
    timeout: int
) -> Optional[Dict[str, Any]]:
    """Process a single snippet with timeout protection."""
    start_time = time.time()
    try:
        result = calculate_metrics(
            snippet_content=snippet.get('snippet_content', ''),
            model=model,
            tokenizer=tokenizer,
            timeout=timeout
        )
        result['inference_time'] = time.time() - start_time
        result['snippet_id'] = snippet.get('snippet_id', 'unknown')
        result['status'] = 'success'
        return result
    except FuturesTimeoutError:
        logger.warning(f"Timeout processing snippet {snippet.get('snippet_id')}")
        return {
            'snippet_id': snippet.get('snippet_id', 'unknown'),
            'perplexity': float('nan'),
            'functional_correctness_rate': float('nan'),
            'inference_time': time.time() - start_time,
            'status': 'timeout'
        }
    except Exception as e:
        logger.error(f"Error processing snippet {snippet.get('snippet_id')}: {e}")
        traceback.print_exc()
        return {
            'snippet_id': snippet.get('snippet_id', 'unknown'),
            'perplexity': float('nan'),
            'functional_correctness_rate': float('nan'),
            'inference_time': time.time() - start_time,
            'status': 'error'
        }

def run_inference_pipeline(
    input_csv: str, 
    output_csv: str, 
    model_id: str,
    timeout_per_snippet: int,
    total_timeout: int,
    num_workers: int
):
    """Run the full inference pipeline with global timeout control."""
    ensure_directories()
    setup_logging(level=logging.INFO)
    
    start_total_time = time.time()
    snippets = load_snippets(input_csv)
    
    if not snippets:
        logger.error("No snippets to process")
        return

    logger.info(f"Starting inference pipeline with {len(snippets)} snippets")
    logger.info(f"Total timeout: {total_timeout}s, Per-snippet timeout: {timeout_per_snippet}s")
    
    model = None
    tokenizer = None
    results = []
    
    try:
        # Load model once for all workers
        logger.info(f"Loading model: {model_id}")
        model, tokenizer = load_model(model_id)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for snippet in snippets:
                # Check global timeout before starting new inference
                elapsed = time.time() - start_total_time
                if elapsed >= total_timeout:
                    logger.warning(f"Total timeout reached ({elapsed:.1f}s). Stopping new inferences.")
                    break
                
                # Submit task
                future = executor.submit(
                    process_snippet_with_timeout, 
                    snippet, 
                    model, 
                    tokenizer, 
                    timeout_per_snippet
                )
                
                try:
                    result = future.result(timeout=timeout_per_snippet + 10) # Add buffer
                    if result:
                        results.append(result)
                        logger.info(f"Processed snippet {result['snippet_id']}: {result['status']}")
                except FuturesTimeoutError:
                    logger.warning(f"Future timed out for snippet {snippet.get('snippet_id')}")
                    results.append({
                        'snippet_id': snippet.get('snippet_id', 'unknown'),
                        'perplexity': float('nan'),
                        'functional_correctness_rate': float('nan'),
                        'inference_time': timeout_per_snippet,
                        'status': 'timeout'
                    })
                except Exception as e:
                    logger.error(f"Future exception: {e}")
                    traceback.print_exc()
    
    finally:
        if model is not None:
            unload_model(model)
    
    # Determine final status
    total_runtime = time.time() - start_total_time
    snippets_processed = len(results)
    min_threshold_met = snippets_processed >= MIN_SNIPPET_THRESHOLD
    
    # Check if we stopped due to timeout
    stopped_by_timeout = (time.time() - start_total_time) >= total_timeout
    
    if stopped_by_timeout and not min_threshold_met:
        final_status = 'incomplete'
        logger.warning(f"Run marked as 'incomplete': Timeout reached with only {snippets_processed} snippets (min: {MIN_SNIPPET_THRESHOLD})")
    else:
        final_status = 'complete'
        if stopped_by_timeout:
            logger.info(f"Run marked as 'complete': Timeout reached but {snippets_processed} snippets processed (>= {MIN_SNIPPET_THRESHOLD})")
        else:
            logger.info(f"Run marked as 'complete': All {snippets_processed} snippets processed normally")
    
    save_results(results, output_csv, final_status)
    return final_status

def main():
    args = parse_args()
    try:
        status = run_inference_pipeline(
            input_csv=args.input_csv,
            output_csv=args.output_csv,
            model_id=args.model_id,
            timeout_per_snippet=args.timeout_per_snippet,
            total_timeout=args.total_timeout,
            num_workers=args.num_workers
        )
        logger.info(f"Pipeline finished with status: {status}")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()