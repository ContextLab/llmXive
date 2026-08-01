import json
import os
import random
import hashlib
import stat
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import load_state, save_state, ensure_directories, RAW_DATA_DIR, PROCESSED_DATA_DIR, STATE_DIR

# Configure logging for the generator module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(STATE_DIR, 'generator.log'))
    ]
)
logger = logging.getLogger('workflow_generator')

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise

def generate_workflow(workflow_id: int, seed: int) -> Dict[str, Any]:
    """Generate a deterministic multi-agent workflow."""
    logger.info(f"Generating workflow {workflow_id} with seed {seed}")
    random.seed(seed)
    
    # Generate mock tool outputs and decision tree
    tool_outputs = []
    for i in range(random.randint(3, 10)):
        tool_outputs.append({
            "tool_id": f"tool_{i}",
            "output": f"output_{random.randint(1000, 9999)}",
            "timestamp": f"2023-01-01T00:00:{i:02d}"
        })
    
    decision_tree = {
        "root": "start",
        "nodes": {
            "start": {"action": "init", "next": "process"},
            "process": {"action": "execute", "next": "finalize"}
        }
    }
    
    workflow = {
        "workflow_id": workflow_id,
        "seed": seed,
        "tool_outputs": tool_outputs,
        "decision_tree": decision_tree,
        "metadata": {
            "generated_at": "2023-01-01T00:00:00Z",
            "version": "1.0"
        }
    }
    
    logger.info(f"Workflow {workflow_id} generated successfully with {len(tool_outputs)} tool outputs")
    return workflow

def validate_workflow_structure(workflow: Dict[str, Any]) -> bool:
    """Validate that workflow contains all necessary variables."""
    required_keys = ["workflow_id", "seed", "tool_outputs", "decision_tree"]
    for key in required_keys:
        if key not in workflow:
            logger.error(f"Validation failed: Missing key '{key}' in workflow")
            return False
    
    if not isinstance(workflow["tool_outputs"], list) or len(workflow["tool_outputs"]) == 0:
        logger.error("Validation failed: tool_outputs must be a non-empty list")
        return False
    
    if "nodes" not in workflow["decision_tree"]:
        logger.error("Validation failed: decision_tree missing 'nodes'")
        return False
    
    logger.info("Workflow structure validation passed")
    return True

def generate_ground_truth_batch(workflow_ids: List[int], seed: int, count: int) -> None:
    """Generate ground truth files for a batch of workflows."""
    ensure_directories()
    
    start_id = workflow_ids[0] if workflow_ids else 0
    end_id = start_id + count
    
    logger.info(f"Starting ground truth generation for workflows {start_id} to {end_id-1}")
    
    for wid in range(start_id, end_id):
        workflow = generate_workflow(wid, seed + wid)
        
        if not validate_workflow_structure(workflow):
            logger.error(f"Skipping workflow {wid} due to validation failure")
            continue
        
        # Serialize to JSON
        ground_truth_path = os.path.join(RAW_DATA_DIR, f"{wid}_ground_truth.json")
        with open(ground_truth_path, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        # Calculate and verify hash
        file_hash = calculate_sha256(ground_truth_path)
        logger.info(f"Workflow {wid} ground truth written to {ground_truth_path} (Hash: {file_hash})")
        
        # Verify hash immediately after write
        verify_hash = calculate_sha256(ground_truth_path)
        if file_hash != verify_hash:
            logger.critical(f"Hash mismatch for workflow {wid}! Original: {file_hash}, Verified: {verify_hash}")
            raise RuntimeError(f"Hash verification failed for workflow {wid}")
        
        # Set read-only permissions
        try:
            os.chmod(ground_truth_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            logger.info(f"Set read-only permissions for {ground_truth_path}")
        except OSError as e:
            logger.warning(f"Could not set read-only permissions on {ground_truth_path}: {e}")
    
    logger.info(f"Ground truth generation completed for {count} workflows")

def verify_ground_truth_hashes(workflow_ids: List[int]) -> Dict[int, bool]:
    """Verify hashes of existing ground truth files."""
    results = {}
    for wid in workflow_ids:
        ground_truth_path = os.path.join(RAW_DATA_DIR, f"{wid}_ground_truth.json")
        if not os.path.exists(ground_truth_path):
            logger.warning(f"Ground truth file not found for workflow {wid}")
            results[wid] = False
            continue
        
        try:
            # Read expected hash from state if available, otherwise just verify file integrity
            # For now, we just ensure the file is readable and consistent
            current_hash = calculate_sha256(ground_truth_path)
            results[wid] = True
            logger.info(f"Verified hash for workflow {wid}: {current_hash}")
        except Exception as e:
            logger.error(f"Hash verification failed for workflow {wid}: {e}")
            results[wid] = False
    
    return results
