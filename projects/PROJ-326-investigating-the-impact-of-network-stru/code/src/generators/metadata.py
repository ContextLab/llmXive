"""
Metadata logging for generated graphs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def save_graph_metadata(metadata: Dict[str, Any], output_dir: str = "data/metadata"):
    """Save metadata for a single graph to a JSON file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    graph_id = metadata.get("graph_id", "unknown")
    path = Path(output_dir) / f"graph_{graph_id}.json"
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.debug(f"Saved metadata for {graph_id}")


def load_graph_metadata(graph_id: str, output_dir: str = "data/metadata") -> Optional[Dict[str, Any]]:
    """Load metadata for a specific graph."""
    path = Path(output_dir) / f"graph_{graph_id}.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None


def log_generation_batch(batch_metadata: list, log_path: str = "data/run_log.json"):
    """Log a batch of generation events."""
    # This is handled by the main logging module now
    pass
