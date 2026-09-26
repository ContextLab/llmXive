import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.loaders import load_cot_traces

logger = logging.getLogger("rules.trace_loader")

def load_traces_for_extraction(input_path: Path) -> List[Dict[str, Any]]:
    """Load traces specifically for extraction, with validation."""
    return load_cot_traces(input_path)

def main():
    logger.info("Loading Traces for Extraction...")
    input_path = Path("data/raw/cot_traces.json")
    try:
        traces = load_traces_for_extraction(input_path)
        logger.info(f"Loaded {len(traces)} traces.")
    except FileNotFoundError as e:
        logger.error(str(e))

if __name__ == "__main__":
    main()
