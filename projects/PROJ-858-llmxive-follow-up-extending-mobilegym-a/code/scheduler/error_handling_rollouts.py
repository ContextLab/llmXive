"""
Module for handling malformed JSON rollouts during batch processing.
Implements T027: Skip malformed JSON rollouts without crashing the batch.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from utils.logging import get_task_logger, log_error, log_with_context

logger = get_task_logger(__name__)

def load_rollout_safe(rollout_path: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Safely load a JSON rollout file.
    
    Args:
        rollout_path: Path to the JSON file.
        
    Returns:
        Tuple of (data, status). 
        If successful: (data_dict, "success")
        If failed: (None, "error: <reason>")
    """
    if not os.path.exists(rollout_path):
        return None, f"error: File not found - {rollout_path}"
        
    try:
        with open(rollout_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, dict):
            return None, f"error: Malformed JSON structure at {rollout_path} (expected dict, got {type(data).__name__})"
            
        return data, "success"
        
    except json.JSONDecodeError as e:
        return None, f"error: Invalid JSON syntax at {rollout_path} - {str(e)}"
    except Exception as e:
        return None, f"error: Unexpected error reading {rollout_path} - {str(e)}"

def process_rollout_batch(
    rollout_paths: List[str],
    processor_func: callable
) -> List[Dict[str, Any]]:
    """
    Process a batch of rollout files, skipping malformed ones without crashing.
    
    Args:
        rollout_paths: List of paths to JSON rollout files.
        processor_func: Function to apply to valid rollout data. 
                        Signature: (data: Dict) -> Any
                        
    Returns:
        List of results from successful processing.
    """
    results = []
    skipped_count = 0
    success_count = 0
    
    for path in rollout_paths:
        data, status = load_rollout_safe(path)
        
        if status != "success":
            logger.warning(f"Skipping malformed rollout: {status}")
            skipped_count += 1
            # Log error but continue
            continue
            
        try:
            result = processor_func(data)
            results.append({
                "path": path,
                "status": "success",
                "result": result
            })
            success_count += 1
        except Exception as e:
            error_msg = f"Error processing valid JSON at {path}: {str(e)}"
            logger.error(error_msg)
            results.append({
                "path": path,
                "status": "processing_error",
                "error": str(e)
            })
            
    logger.info(f"Batch processing complete: {success_count} succeeded, {skipped_count} skipped.")
    return results

def main():
    """
    Demo entry point for error handling in rollout processing.
    Creates a temporary directory with valid and invalid JSON files,
    then processes them to demonstrate skipping behavior.
    """
    import tempfile
    import shutil
    
    # Setup temp directory for demo
    temp_dir = tempfile.mkdtemp(prefix="rollout_demo_")
    logger.info(f"Created temporary demo directory: {temp_dir}")
    
    # Create test files
    valid_rollout = {
        "task_id": "demo_task",
        "states": [{"dark_mode": True}, {"dark_mode": False}],
        "success": True
    }
    
    invalid_json_content = "{ invalid json content }"
    
    valid_path = os.path.join(temp_dir, "valid_rollout.json")
    invalid_path = os.path.join(temp_dir, "invalid_rollout.json")
    missing_path = os.path.join(temp_dir, "missing_rollout.json")
    
    with open(valid_path, 'w') as f:
        json.dump(valid_rollout, f)
        
    with open(invalid_path, 'w') as f:
        f.write(invalid_json_content)
        
    batch_paths = [valid_path, invalid_path, missing_path]
    
    # Define a simple processor
    def simple_processor(data: Dict) -> str:
        return f"Processed {data.get('task_id', 'unknown')}"
        
    # Process batch
    results = process_rollout_batch(batch_paths, simple_processor)
    
    # Report results
    for r in results:
        if r["status"] == "success":
            logger.info(f"Success: {r['path']} -> {r['result']}")
        else:
            logger.warning(f"Skipped/Failed: {r['path']} -> {r.get('error', 'skipped')}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    logger.info("Demo completed and cleaned up.")

if __name__ == "__main__":
    main()
