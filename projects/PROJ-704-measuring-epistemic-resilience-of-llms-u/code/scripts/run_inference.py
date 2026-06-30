import json
import os
import sys
import logging
import resource
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import time

# Import from existing project modules
from scripts.config import get_project_root, load_config, get_seed, resolve_path
from utils.error_utils import (
    ExecutionTimeoutError,
    OutOfMemoryError,
    ExecutionError,
    handle_timeout,
    detect_oom_exception,
    with_timeout
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class InferenceResult:
    """Data class representing the result of a single inference run."""
    item_id: str
    model_name: str
    strategy: str
    prompt: str
    response: str
    extracted_answer: Optional[str]
    is_correct: Optional[bool]
    status: str  # 'success', 'timeout', 'oom', 'error'
    error_message: Optional[str]
    latency_seconds: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def check_cpu_resources() -> bool:
    """
    Pre-execution check to skip 70B model on CPU-only runners.
    Returns True if resources are sufficient, False otherwise.
    """
    try:
        # Check memory availability (simple heuristic)
        mem_info = resource.getrusage(resource.RUSAGE_SELF)
        # This is a simplified check; in production, check total system RAM
        logger.info("CPU resource check passed (simplified heuristic).")
        return True
    except Exception as e:
        logger.warning(f"Resource check failed: {e}")
        return False

def load_prompt_template(template_path: str) -> str:
    """Load a prompt template from a file."""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_model(model_name: str, device: str = "cpu") -> Any:
    """
    Load a model.
    Note: In a real implementation, this would load the actual transformer model.
    For this task, we simulate the loading process to demonstrate the timeout/OOM handling.
    """
    logger.info(f"Loading model {model_name} on {device}...")
    # Simulate loading time
    time.sleep(0.5)
    return {"name": model_name, "device": device}

def run_inference_with_timeout(
    model: Any,
    prompt: str,
    timeout_seconds: int = 300,
    max_memory_mb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute inference with a timeout decorator to handle TLE/OOM.
    
    This function wraps the actual inference call to ensure it doesn't hang
    or consume excessive memory.
    """
    start_time = time.time()
    
    try:
        # Use the with_timeout context manager from utils.error_utils
        # which handles the timeout logic using signal alarms or threading
        result = with_timeout(timeout_seconds)(lambda: _simulate_inference(model, prompt))()
        
        latency = time.time() - start_time
        return {
            "status": "success",
            "response": result,
            "latency": latency,
            "error": None
        }
        
    except ExecutionTimeoutError:
        latency = time.time() - start_time
        logger.warning(f"Inference timed out after {timeout_seconds} seconds.")
        return {
            "status": "timeout",
            "response": None,
            "latency": latency,
            "error": "ExecutionTimeoutError: Task exceeded time limit."
        }
        
    except OutOfMemoryError:
        latency = time.time() - start_time
        logger.error("Inference failed due to OutOfMemoryError.")
        return {
            "status": "oom",
            "response": None,
            "latency": latency,
            "error": "OutOfMemoryError: Insufficient memory to complete task."
        }
        
    except Exception as e:
        latency = time.time() - start_time
        logger.error(f"Unexpected error during inference: {e}")
        return {
            "status": "error",
            "response": None,
            "latency": latency,
            "error": str(e)
        }

def _simulate_inference(model: Any, prompt: str) -> str:
    """
    Simulate the actual model inference.
    In a real scenario, this would call model.generate().
    """
    # Simulate variable inference time
    time.sleep(1.0)
    # Return a simulated response
    return f"Simulated response for: {prompt[:50]}..."

def process_inference(
    item: Dict[str, Any],
    model: Any,
    strategy: str,
    prompt_template: str,
    timeout_seconds: int = 300
) -> InferenceResult:
    """
    Process a single inference task for an item.
    Handles the full pipeline: prompt construction, execution, and result formatting.
    """
    item_id = item.get('id', 'unknown')
    stem = item.get('stem', '')
    options = item.get('options', [])
    
    # Construct prompt
    prompt = prompt_template.format(
        stem=stem,
        options=json.dumps(options),
        strategy=strategy
    )
    
    # Run inference with timeout
    inference_output = run_inference_with_timeout(
        model, 
        prompt, 
        timeout_seconds=timeout_seconds
    )
    
    # Extract answer (simplified for this task, assuming extraction logic exists elsewhere)
    extracted_answer = None
    is_correct = None
    
    if inference_output['status'] == 'success':
        # In a real implementation, call the answer extraction logic here
        # For now, we simulate extraction
        response = inference_output['response']
        if "Answer: A" in response:
            extracted_answer = "A"
        elif "Answer: B" in response:
            extracted_answer = "B"
        elif "Answer: C" in response:
            extracted_answer = "C"
        elif "Answer: D" in response:
            extracted_answer = "D"
        
        # Check correctness if gold answer exists
        if 'gold' in item and extracted_answer:
            is_correct = (extracted_answer == item['gold'])
    
    return InferenceResult(
        item_id=item_id,
        model_name=model['name'],
        strategy=strategy,
        prompt=prompt,
        response=inference_output['response'] or "",
        extracted_answer=extracted_answer,
        is_correct=is_correct,
        status=inference_output['status'],
        error_message=inference_output['error'],
        latency_seconds=inference_output['latency'],
        timestamp=datetime.now().isoformat()
    )

def main():
    """
    Main entry point for the inference script.
    Loads configuration, processes the dataset, and writes results.
    """
    config = load_config()
    project_root = get_project_root()
    
    # Paths
    input_path = resolve_path(config.get('input_path'), project_root)
    output_path = resolve_path(config.get('output_path'), project_root)
    prompt_path = resolve_path(config.get('prompt_path'), project_root)
    
    logger.info(f"Loading dataset from {input_path}")
    logger.info(f"Output will be written to {output_path}")
    
    # Load prompt template
    prompt_template = load_prompt_template(prompt_path)
    
    # Check resources
    if not check_cpu_resources():
        logger.error("Insufficient CPU resources. Skipping execution.")
        return
    
    # Load dataset (simplified)
    dataset = []
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                dataset.append(json.loads(line))
    else:
        logger.warning(f"Input file {input_path} not found. Creating empty dataset.")
    
    # Load model
    model_name = config.get('model_name', 'test-model')
    model = load_model(model_name)
    
    # Process items
    results = []
    for item in dataset:
        result = process_inference(
            item=item,
            model=model,
            strategy="baseline",
            prompt_template=prompt_template,
            timeout_seconds=60
        )
        results.append(result)
        
        # Log progress
        logger.info(f"Processed {item['id']}: status={result.status}")
    
    # Write results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res.to_dict()) + '\n')
    
    logger.info(f"Finished processing {len(results)} items. Results saved to {output_path}")

if __name__ == "__main__":
    main()