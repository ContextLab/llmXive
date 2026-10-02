import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

def load_static_scores(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)

def load_dynamic_scores(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)

def align_and_merge_scores(static: List[Dict], dynamic: List[Dict]) -> List[Dict]:
    """
    Aligns static and dynamic scores by task_id.
    """
    static_map = {item["task_id"]: item for item in static}
    dynamic_map = {item["task_id"]: item for item in dynamic}
    
    merged = []
    for task_id in static_map:
        if task_id in dynamic_map:
            merged.append({
                "task_id": task_id,
                "static_scores": static_map[task_id].get("scores", []),
                "dynamic_scores": dynamic_map[task_id].get("scores", []),
                "status": "MERGED"
            })
    return merged

def save_merged_output(data: List[Dict], path: str):
    ensure_dir(path)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main entry point for generating merged output.
    """
    logger.info("Dynamic output generation module loaded.")

if __name__ == "__main__":
    main()
