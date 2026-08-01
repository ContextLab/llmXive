"""
Corruption Injector Module for OpenRath Follow-up.

This module implements the logic to randomly select and modify or delete
log entries in the generated ground truth data based on a configurable
corruption rate. It adheres to the requirement of marking corruption
only in a central map, not modifying the source files directly.
"""
import json
import random
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import load_state, save_state, ensure_directories
from generators.workflow_generator import calculate_sha256

logger = logging.getLogger(__name__)

class CorruptionInjector:
    """
    Injects stochastic corruption into workflow logs.

    This class handles the selection of files and log entries to corrupt
    based on a configured rate. It distinguishes between 'modification'
    (changing data values) and 'deletion' (removing entries).

    Attributes:
        corruption_rate (float): Probability of corruption per entry (0.0 to 1.0).
        corruption_mode (str): 'mixed', 'delete_only', or 'modify_only'.
        corruption_log_path (Path): Path to the central corruption log file.
        state_file_path (Path): Path to the project state YAML file.
    """

    def __init__(
        self,
        corruption_rate: float = 0.1,
        corruption_mode: str = "mixed",
        output_dir: Optional[str] = None,
        state_file_path: Optional[str] = None
    ):
        """
        Initialize the CorruptionInjector.

        Args:
            corruption_rate: The probability (0.0-1.0) that a given log entry will be corrupted.
            corruption_mode: Strategy for corruption. 'mixed' (default), 'delete_only', 'modify_only'.
            output_dir: Directory where the corruption log will be written. Defaults to config.
            state_file_path: Path to the project state YAML. Defaults to config.
        """
        if not 0.0 <= corruption_rate <= 1.0:
            raise ValueError("corruption_rate must be between 0.0 and 1.0")
        
        if corruption_mode not in ["mixed", "delete_only", "modify_only"]:
            raise ValueError(f"Invalid corruption_mode: {corruption_mode}")

        self.corruption_rate = corruption_rate
        self.corruption_mode = corruption_mode
        
        # Resolve paths
        self.state_file_path = Path(state_file_path) if state_file_path else Path("state/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml")
        self.output_dir = Path(output_dir) if output_dir else Path("data/processed")
        
        # Ensure output directory exists
        ensure_directories()
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.corruption_log_path = self.output_dir / "corruption_log.json"
        
        # Initialize corruption log if it doesn't exist
        self._initialize_log()

    def _initialize_log(self) -> None:
        """Initialize the corruption log structure if it does not exist."""
        if not self.corruption_log_path.exists():
            initial_log = {
                "metadata": {
                    "corruption_rate": self.corruption_rate,
                    "corruption_mode": self.corruption_mode,
                    "total_files_processed": 0,
                    "total_entries_corrupted": 0,
                    "total_entries_deleted": 0,
                    "timestamp": None
                },
                "entries": [] # List of {workflow_id, file_path, entry_index, type, original_hash, new_hash}
            }
            with open(self.corruption_log_path, 'w') as f:
                json.dump(initial_log, f, indent=2)
            logger.info(f"Initialized corruption log at {self.corruption_log_path}")

    def _load_log(self) -> Dict[str, Any]:
        """Load the current corruption log."""
        with open(self.corruption_log_path, 'r') as f:
            return json.load(f)

    def _save_log(self, log_data: Dict[str, Any]) -> None:
        """Save the corruption log with atomic write pattern."""
        temp_path = self.corruption_log_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        os.replace(temp_path, self.corruption_log_path)
        logger.debug(f"Saved corruption log to {self.corruption_log_path}")

    def _corrupt_entry(self, entry: Dict[str, Any], entry_type: str) -> Dict[str, Any]:
        """
        Corrupt a single log entry.

        Args:
            entry: The dictionary representing the log entry.
            entry_type: 'modify' or 'delete'.

        Returns:
            The modified entry (or a placeholder if deleted).
        """
        if entry_type == "delete":
            # Mark as deleted by setting a specific flag and clearing content
            entry["corrupted"] = True
            entry["corruption_type"] = "deletion"
            entry["content"] = None
            # In a real scenario, we might remove the key from the parent list,
            # but for JSON structure preservation, we flag it.
            logger.debug("Marked entry for deletion")
        elif entry_type == "modify":
            entry["corrupted"] = True
            entry["corruption_type"] = "modification"
            # Corrupt string fields by appending garbage or scrambling
            for key, value in entry.items():
                if isinstance(value, str) and key not in ["id", "type", "corruption_type", "corrupted"]:
                    entry[key] = value + " [CORRUPTED]"
                elif isinstance(value, (int, float)) and key not in ["id"]:
                    entry[key] = value * -1 # Invert numbers
            logger.debug("Modified entry content")
        return entry

    def inject_corruption(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Inject corruption into a specific workflow's data structure.

        This method traverses the workflow data (which may contain nested lists of events/outputs),
        randomly selects entries based on `corruption_rate`, and applies the corruption.
        It records every change in the central `corruption_log`.

        Args:
            workflow_id: The unique identifier for the workflow.
            workflow_data: The dictionary containing the workflow's ground truth or log data.

        Returns:
            A tuple (success, list_of_corrupted_entry_ids).
            If no corruption occurred, list is empty.
        """
        corrupted_entries = []
        log_data = self._load_log()
        
        # We need to traverse the dictionary to find list structures containing log entries
        # Assuming structure: { "events": [...], "tool_outputs": [...] }
        # We will recursively find all lists of dicts that look like log entries
        
        entries_to_check = []
        
        def find_entries(obj, path=""):
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        # Heuristic: if it has 'id' or 'timestamp' or 'type', treat as entry
                        if any(k in item for k in ['id', 'timestamp', 'type', 'event_type']):
                            entries_to_check.append((path, i, item))
                    find_entries(item, f"{path}[{i}]")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    find_entries(v, f"{path}.{k}")

        find_entries(workflow_data)

        if not entries_to_check:
            logger.warning(f"No log entries found in workflow {workflow_id} for corruption.")
            return True, []

        # Determine which entries to corrupt
        indices_to_corrupt = []
        for idx, (path, item_idx, item) in enumerate(entries_to_check):
            if random.random() < self.corruption_rate:
                indices_to_corrupt.append(idx)

        if not indices_to_corrupt:
            return True, []

        # Apply corruption
        for idx in indices_to_corrupt:
            path, item_idx, item = entries_to_check[idx]
            
            # Determine type
            if self.corruption_mode == "delete_only":
                ctype = "delete"
            elif self.corruption_mode == "modify_only":
                ctype = "modify"
            else:
                ctype = random.choice(["delete", "modify"])

            original_hash = calculate_sha256(json.dumps(item, sort_keys=True).encode('utf-8'))
            
            # Apply corruption
            new_item = self._corrupt_entry(item.copy(), ctype)
            new_hash = calculate_sha256(json.dumps(new_item, sort_keys=True).encode('utf-8'))

            # Update the actual data structure
            # Navigate to parent list
            parts = path.split('.')
            parent = workflow_data
            for p in parts:
                if p.startswith('[') and p.endswith(']'):
                    index = int(p[1:-1])
                    parent = parent[index]
                else:
                    parent = parent[p]
            
            parent[item_idx] = new_item
            
            # Log the corruption
            log_entry = {
                "workflow_id": workflow_id,
                "path": path,
                "entry_index": item_idx,
                "corruption_type": ctype,
                "original_hash": original_hash,
                "new_hash": new_hash
            }
            log_data["entries"].append(log_entry)
            corrupted_entries.append(f"{path}[{item_idx}]")
            log_data["metadata"]["total_entries_corrupted"] += 1
            if ctype == "delete":
                log_data["metadata"]["total_entries_deleted"] += 1

        # Update metadata
        log_data["metadata"]["total_files_processed"] += 1
        log_data["metadata"]["timestamp"] = os.popen('date -Iseconds').read().strip() if os.name != 'nt' else "2023-01-01T00:00:00" # Fallback for demo

        self._save_log(log_data)
        logger.info(f"Corrupted {len(corrupted_entries)} entries in workflow {workflow_id}")
        return True, corrupted_entries

    def process_workflow_file(self, workflow_id: str, input_path: str, output_path: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Load a workflow file, corrupt it, and save it (if output_path provided).
        Updates the central corruption log.

        Args:
            workflow_id: ID of the workflow.
            input_path: Path to the input JSON file.
            output_path: Optional path to write the corrupted file. If None, modifies in place or raises.

        Returns:
            Tuple (success, result_dict).
        """
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False, {"error": "File not found"}

        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {input_path}: {e}")
            return False, {"error": "Invalid JSON"}

        success, corrupted_ids = self.inject_corruption(workflow_id, data)

        if output_path:
            # Ensure output directory exists
            out_dir = os.path.dirname(output_path)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            
            temp_path = output_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, output_path)
            logger.info(f"Wrote corrupted workflow to {output_path}")
        else:
            # If no output path, we assume the caller wants the data back or in-place modification
            # For safety in this pipeline, we return the data but don't overwrite the ground truth
            # unless explicitly requested. The task says "modify/delete log entries", 
            # implying the output of the executor should be corrupted.
            # However, T023 is the injector. The executor (T021/T022) will use this.
            # Here we just ensure the log is updated.
            pass

        return success, {
            "workflow_id": workflow_id,
            "corrupted_entries": corrupted_ids,
            "count": len(corrupted_ids)
        }

    def get_corruption_stats(self) -> Dict[str, Any]:
        """Retrieve current statistics from the corruption log."""
        if not self.corruption_log_path.exists():
            return {"error": "Log not found"}
        log_data = self._load_log()
        return log_data["metadata"]

def main():
    """CLI entry point for testing the corruption injector."""
    import argparse
    parser = argparse.ArgumentParser(description="Corruption Injector CLI")
    parser.add_argument("--rate", type=float, default=0.1, help="Corruption rate")
    parser.add_argument("--mode", type=str, default="mixed", choices=["mixed", "delete_only", "modify_only"])
    parser.add_argument("--input", type=str, required=True, help="Input workflow file path")
    parser.add_argument("--output", type=str, help="Output file path (optional)")
    args = parser.parse_args()

    # Extract workflow ID from filename if not provided
    workflow_id = Path(args.input).stem
    
    injector = CorruptionInjector(
        corruption_rate=args.rate,
        corruption_mode=args.mode
    )
    
    success, result = injector.process_workflow_file(workflow_id, args.input, args.output)
    
    if success:
        print(f"Success: Corrupted {result['count']} entries in {workflow_id}")
        print(f"Details: {result['corrupted_entries']}")
    else:
        print(f"Failed: {result['error']}")
        exit(1)

if __name__ == "__main__":
    main()
