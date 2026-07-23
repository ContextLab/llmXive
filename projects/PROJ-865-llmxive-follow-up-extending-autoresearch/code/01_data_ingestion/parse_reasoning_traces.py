import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

logger = get_logger(__name__)

def load_raw_traces(input_path: Path) -> List[Dict[str, Any]]:
    """Load the raw downloaded ARC-Bench data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_trace_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single trace entry to extract relevant fields.
    Returns None if the entry is malformed.
    """
    try:
        # Expected structure based on ARC-Bench format
        task_id = entry.get("task_id") or entry.get("id")
        reasoning = entry.get("reasoning_trace") or entry.get("trace")
        error_log = entry.get("error_log") or entry.get("raw_error") or "No error log found"
        ground_truth = entry.get("ground_truth") or entry.get("solution") or "No ground truth"

        if not task_id:
            logger.warning("Skipping entry with missing task_id")
            return None

        return {
            "task_id": str(task_id),
            "raw_error_log": str(error_log),
            "ground_truth_resolution": str(ground_truth),
            "original_trace": reasoning
        }
    except Exception as e:
        logger.error(f"Error parsing entry: {e}")
        return None

def parse_all_traces(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse all entries in the raw data."""
    parsed = []
    for i, entry in enumerate(raw_data):
        result = parse_trace_entry(entry)
        if result:
            parsed.append(result)
    return parsed

def main():
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "raw" / "arc_bench_subset.json"
    output_path = base_dir / "data" / "derived" / "parsed_traces.json"

    log_stage_start("parse_reasoning_traces", str(input_path), str(output_path))

    try:
        validate_resource_limits()
        
        logger.info(f"Loading raw traces from {input_path}")
        raw_data = load_raw_traces(input_path)
        logger.info(f"Loaded {len(raw_data)} raw entries.")

        logger.info("Parsing traces...")
        parsed_data = parse_all_traces(raw_data)
        logger.info(f"Parsed {len(parsed_data)} valid entries.")

        logger.info(f"Writing parsed traces to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=2)

        log_stage_end("parse_reasoning_traces", success=True)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_stage_end("parse_reasoning_traces", success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()
