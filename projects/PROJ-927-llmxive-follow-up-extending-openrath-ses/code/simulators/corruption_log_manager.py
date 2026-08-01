import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import load_state, save_state, ensure_directories, PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)

CORRUPTION_MAP_FILENAME = "corruption_log.json"

def get_corruption_map_path() -> Path:
    """Return the absolute path to the central corruption log file."""
    return Path(PROCESSED_DATA_DIR) / CORRUPTION_MAP_FILENAME

def load_corruption_map() -> Dict[str, Any]:
    """
    Load the central corruption map from disk.
    If the file does not exist, return an empty structure.
    """
    path = get_corruption_map_path()
    if not path.exists():
        return {
            "version": "1.0",
            "description": "Central mapping of workflow_id -> corruption status",
            "entries": {}
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_corruption_map(data: Dict[str, Any]) -> None:
    """
    Save the central corruption map to disk atomically.
    Uses write-to-temp-then-rename strategy to prevent partial writes.
    """
    path = get_corruption_map_path()
    ensure_directories()
    
    # Atomic write: write to temp, then rename
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    os.replace(temp_path, path)
    logger.info(f"Saved corruption map to {path}")

def mark_workflow_corrupted(
    workflow_id: str,
    corruption_type: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Mark a specific workflow as corrupted in the central map.
    
    This is the SINGLE SOURCE OF TRUTH for corruption status.
    Do NOT create sidecar files or modify workflow JSON roots.
    
    Args:
        workflow_id: The unique identifier of the workflow.
        corruption_type: A string identifier for the type of corruption 
                         (e.g., 'file_deleted', 'field_modified', 'node_missing').
        details: Optional dictionary with specific details about the corruption.
    """
    map_data = load_corruption_map()
    
    entry = {
        "workflow_id": workflow_id,
        "corrupted": True,
        "corruption_type": corruption_type,
        "details": details or {},
        "marked_at": None  # Could add timestamp if needed, but keeping simple
    }
    
    map_data["entries"][workflow_id] = entry
    save_corruption_map(map_data)
    logger.info(f"Marked workflow {workflow_id} as corrupted ({corruption_type}) in central map.")

def is_workflow_corrupted(workflow_id: str) -> bool:
    """Check if a workflow is marked as corrupted in the central map."""
    map_data = load_corruption_map()
    return workflow_id in map_data.get("entries", {})

def get_corruption_details(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Get corruption details for a workflow if it exists in the map."""
    map_data = load_corruption_map()
    return map_data.get("entries", {}).get(workflow_id)

def clear_corruption_log() -> None:
    """
    Clear the corruption log (useful for fresh sweeps).
    This resets the central map to an empty state.
    """
    data = {
        "version": "1.0",
        "description": "Central mapping of workflow_id -> corruption status",
        "entries": {}
    }
    save_corruption_map(data)
    logger.info("Cleared corruption log.")
