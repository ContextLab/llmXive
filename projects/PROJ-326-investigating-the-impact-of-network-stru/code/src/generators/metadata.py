import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

METADATA_DIR = "data/metadata"

def save_metadata(metadata: Dict[str, Any]) -> None:
    """
    Save metadata for a generated graph to data/metadata/graph_<id>.json.
    """
    graph_id = metadata.get("graph_id")
    if not graph_id:
        raise ValueError("Metadata must contain a 'graph_id'")

    Path(METADATA_DIR).mkdir(parents=True, exist_ok=True)

    file_path = Path(METADATA_DIR) / f"graph_{graph_id}.json"

    # Add timestamp
    metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

    with open(file_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.debug(f"Saved metadata for graph {graph_id} to {file_path}")
