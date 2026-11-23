import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# Configure logging for the validator module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for workflow validation failures."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}

# SC-005 Requirement: Workflow must contain specific variables
# Based on task description: "tool outputs, state snapshots"
REQUIRED_TOP_LEVEL_KEYS = {
    "workflow_id",
    "timestamp",
    "agent_id",
    "decision_tree",
    "tool_outputs",
    "state_snapshots"
}

REQUIRED_DECISION_TREE_KEYS = {
    "nodes",
    "root_id"
}

REQUIRED_NODE_KEYS = {
    "node_id",
    "action_type",
    "parameters"
}

REQUIRED_TOOL_OUTPUT_KEYS = {
    "tool_name",
    "output_data",
    "timestamp"
}

REQUIRED_STATE_SNAPSHOT_KEYS = {
    "snapshot_id",
    "timestamp",
    "state_data"
}

def validate_workflow(workflow: Dict[str, Any], workflow_id: Optional[str] = None) -> bool:
    """
    Validates a single workflow dictionary against SC-005 requirements.
    
    Args:
        workflow: The workflow dictionary to validate.
        workflow_id: Optional ID for logging purposes.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If validation fails.
    """
    wf_id = workflow_id or workflow.get("workflow_id", "unknown")
    
    # Check top-level keys
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(workflow.keys())
    if missing_keys:
        logger.error(f"[SC-005] Workflow {wf_id} missing required top-level keys: {missing_keys}")
        raise ValidationError(
            f"Workflow {wf_id} missing required top-level keys",
            {"missing_keys": list(missing_keys)}
        )
    
    # Validate decision_tree structure
    decision_tree = workflow.get("decision_tree")
    if not isinstance(decision_tree, dict):
        raise ValidationError(f"Workflow {wf_id}: decision_tree must be a dictionary")
    
    missing_dt_keys = REQUIRED_DECISION_TREE_KEYS - set(decision_tree.keys())
    if missing_dt_keys:
        raise ValidationError(
            f"Workflow {wf_id}: decision_tree missing keys {missing_dt_keys}"
        )
    
    # Validate nodes if present
    nodes = decision_tree.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValidationError(f"Workflow {wf_id}: decision_tree.nodes must be a list")
    
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValidationError(f"Workflow {wf_id}: Node {i} is not a dictionary")
        
        missing_node_keys = REQUIRED_NODE_KEYS - set(node.keys())
        if missing_node_keys:
            raise ValidationError(
                f"Workflow {wf_id}: Node {i} missing keys {missing_node_keys}"
            )
    
    # Validate tool_outputs
    tool_outputs = workflow.get("tool_outputs", [])
    if not isinstance(tool_outputs, list):
        raise ValidationError(f"Workflow {wf_id}: tool_outputs must be a list")
    
    for i, output in enumerate(tool_outputs):
        if not isinstance(output, dict):
            raise ValidationError(f"Workflow {wf_id}: tool_output {i} is not a dictionary")
        
        missing_out_keys = REQUIRED_TOOL_OUTPUT_KEYS - set(output.keys())
        if missing_out_keys:
            raise ValidationError(
                f"Workflow {wf_id}: tool_output {i} missing keys {missing_out_keys}"
            )
    
    # Validate state_snapshots
    state_snapshots = workflow.get("state_snapshots", [])
    if not isinstance(state_snapshots, list):
        raise ValidationError(f"Workflow {wf_id}: state_snapshots must be a list")
    
    for i, snapshot in enumerate(state_snapshots):
        if not isinstance(snapshot, dict):
            raise ValidationError(f"Workflow {wf_id}: state_snapshot {i} is not a dictionary")
        
        missing_snap_keys = REQUIRED_STATE_SNAPSHOT_KEYS - set(snapshot.keys())
        if missing_snap_keys:
            raise ValidationError(
                f"Workflow {wf_id}: state_snapshot {i} missing keys {missing_snap_keys}"
            )
    
    logger.info(f"[SC-005] Workflow {wf_id} validation passed")
    return True

def validate_workflow_file(file_path: str) -> bool:
    """
    Validates a workflow stored in a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If file cannot be read or validation fails.
        FileNotFoundError: If file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in {file_path}: {str(e)}")
    
    return validate_workflow(workflow, workflow_id=path.stem)

def validate_workflow_batch(file_paths: List[str]) -> Dict[str, bool]:
    """
    Validates a batch of workflow files.
    
    Args:
        file_paths: List of paths to JSON files.
        
    Returns:
        Dictionary mapping file paths to validation status (True/False).
    """
    results = {}
    for file_path in file_paths:
        try:
            results[file_path] = validate_workflow_file(file_path)
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {str(e)}")
            results[file_path] = False
    return results
