import json
import logging
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from code.config.settings import get_config, get_paths, ensure_directories
from code.src.utils.logger import get_logger, start_runtime_tracking, stop_runtime_tracking, log_runtime_stats
from code.src.utils.timeout_wrapper import set_global_timeout, check_timeout, TimeoutExceeded, enforce_timeout
from code.src.utils.memory_watchdog import check_memory_limit, MemoryLimitExceeded
from code.src.inference.load_model import load_model_for_inference
from code.src.inference.prompt_templates import get_bug_detection_prompt, create_inference_request, format_severity_label
from code.src.inference.schema import InferenceRequest, InferenceResponse, InferenceStatus
from code.src.detection.schema import LLMCodeDetectionResult, ConfidenceLevel

# Configure logger
logger = get_logger(__name__)

def parse_llm_output(output_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse the raw LLM output string into a structured dictionary.
    Attempts to extract JSON blocks or parse line-by-line structured output.
    Returns None if parsing fails.
    """
    try:
        # Clean up potential markdown code blocks
        clean_text = output_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        # Attempt direct JSON parsing
        return json.loads(clean_text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM output as JSON: {output_text[:200]}...")
        return None

def process_single_pr(
    pr_data: Dict[str, Any],
    model: Any,
    tokenizer: Any,
    timeout_seconds: int,
    memory_limit_gb: float
) -> InferenceResponse:
    """
    Process a single PR through the LLM for bug detection.
    Enforces per-PR timeout and memory limits.
    """
    pr_id = pr_data.get("pr_id", "unknown")
    file_path = pr_data.get("file_path", "unknown")
    diff_content = pr_data.get("diff", "")

    # Check global timeout first
    if check_timeout():
        raise TimeoutExceeded(f"Global timeout exceeded before processing PR {pr_id}")

    # Check memory before starting
    try:
        check_memory_limit(memory_limit_gb)
    except MemoryLimitExceeded:
        logger.error(f"Memory limit exceeded before processing PR {pr_id}")
        return InferenceResponse(
            pr_id=pr_id,
            file_path=file_path,
            status=InferenceStatus.SKIPPED_MEMORY,
            error_message="Memory limit exceeded",
            detections=[]
        )

    # Construct prompt
    prompt = get_bug_detection_prompt(diff_content)
    request = create_inference_request(prompt)

    start_time = time.time()
    try:
        # Enforce per-PR timeout using a wrapper or threading
        # We use a simple threading approach for timeout enforcement
        result_container = {"output": None, "error": None}

        def run_inference():
            try:
                inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=256,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                result_container["output"] = tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception as e:
                result_container["error"] = str(e)

        thread = threading.Thread(target=run_inference)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            # Timeout occurred
            logger.warning(f"PR {pr_id} exceeded timeout ({timeout_seconds}s). Skipping.")
            return InferenceResponse(
                pr_id=pr_id,
                file_path=file_path,
                status=InferenceStatus.TIMEOUT,
                error_message=f"Inference timeout after {timeout_seconds}s",
                detections=[]
            )

        if result_container["error"]:
            logger.error(f"PR {pr_id} inference error: {result_container['error']}")
            return InferenceResponse(
                pr_id=pr_id,
                file_path=file_path,
                status=InferenceStatus.ERROR,
                error_message=result_container["error"],
                detections=[]
            )

        if not result_container["output"]:
            logger.error(f"PR {pr_id} produced no output.")
            return InferenceResponse(
                pr_id=pr_id,
                file_path=file_path,
                status=InferenceStatus.ERROR,
                error_message="No output generated",
                detections=[]
            )

        # Parse output
        parsed = parse_llm_output(result_container["output"])
        if not parsed:
            logger.warning(f"PR {pr_id} output could not be parsed.")
            return InferenceResponse(
                pr_id=pr_id,
                file_path=file_path,
                status=InferenceStatus.ERROR,
                error_message="Output parsing failed",
                detections=[]
            )

        # Extract detections
        detections = []
        if isinstance(parsed, list):
            detections = parsed
        elif isinstance(parsed, dict) and "detections" in parsed:
            detections = parsed["detections"]
        else:
            # Assume single detection if dict
            detections = [parsed]

        # Validate detections
        valid_detections = []
        for det in detections:
            if not isinstance(det, dict):
                continue
            # Ensure required fields
            if "severity" in det and "line_start" in det and "line_end" in det:
                valid_detections.append(det)
            else:
                logger.debug(f"Invalid detection format in PR {pr_id}: {det}")

        elapsed = time.time() - start_time
        logger.info(f"PR {pr_id} processed successfully in {elapsed:.2f}s. Found {len(valid_detections)} detections.")

        return InferenceResponse(
            pr_id=pr_id,
            file_path=file_path,
            status=InferenceStatus.SUCCESS,
            error_message=None,
            detections=valid_detections,
            latency_seconds=elapsed
        )

    except Exception as e:
        logger.exception(f"Unexpected error processing PR {pr_id}: {e}")
        return InferenceResponse(
            pr_id=pr_id,
            file_path=file_path,
            status=InferenceStatus.ERROR,
            error_message=str(e),
            detections=[]
        )

def run_batch_inference(
    pr_list: List[Dict[str, Any]],
    model: Any,
    tokenizer: Any,
    per_pr_timeout: int,
    memory_limit_gb: float
) -> List[InferenceResponse]:
    """
    Run inference on a batch of PRs.
    Enforces per-PR timeout and memory limits for each item.
    """
    results = []
    for i, pr in enumerate(pr_list):
        logger.info(f"Processing PR {i+1}/{len(pr_list)}: {pr.get('pr_id')}")
        try:
            response = process_single_pr(pr, model, tokenizer, per_pr_timeout, memory_limit_gb)
            results.append(response)
        except TimeoutExceeded:
            logger.critical("Global timeout reached. Stopping batch inference.")
            break
        except Exception as e:
            logger.exception(f"Fatal error in batch processing: {e}")
            break
    return results

def save_results(results: List[InferenceResponse], output_path: Path):
    """
    Save inference results to a JSON file.
    """
    ensure_directories([output_path.parent])
    data = []
    for res in results:
        entry = {
            "pr_id": res.pr_id,
            "file_path": res.file_path,
            "status": res.status.value,
            "error_message": res.error_message,
            "detections": res.detections,
            "latency_seconds": getattr(res, 'latency_seconds', None)
        }
        data.append(entry)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for running inference with timeout enforcement.
    """
    config = get_config()
    paths = get_paths()
    
    # Get parameters
    per_pr_timeout = config.get("inference", {}).get("per_pr_timeout_seconds", 300)
    memory_limit_gb = config.get("inference", {}).get("memory_limit_gb", 7.0)
    model_id = config.get("model", {}).get("model_id", "bigcode/starcoder2-3b")
    
    input_path = paths.get("derived_llm_detections_split", paths.get("derived_dir", Path("data/derived"))) / "llm_detections_split.json"
    output_path = paths.get("derived_dir", Path("data/derived")) / "llm_detections.json"
    
    ensure_directories([input_path.parent, output_path.parent])

    # Load data
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run split_dataset.py first.")
        sys.exit(1)
    
    with open(input_path, "r") as f:
        pr_data_list = json.load(f)
    
    logger.info(f"Loaded {len(pr_data_list)} PRs for inference.")

    # Setup runtime tracking
    start_runtime_tracking()

    # Load model
    logger.info(f"Loading model: {model_id}")
    model, tokenizer = load_model_for_inference(model_id)
    logger.info("Model loaded successfully.")

    # Run inference
    logger.info(f"Starting batch inference with {per_pr_timeout}s timeout per PR.")
    results = run_batch_inference(pr_data_list, model, tokenizer, per_pr_timeout, memory_limit_gb)

    # Save results
    save_results(results, output_path)

    # Log stats
    stop_runtime_tracking()
    log_runtime_stats()

    logger.info("Inference pipeline completed.")

if __name__ == "__main__":
    main()
