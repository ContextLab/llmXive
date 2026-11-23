import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

logger = get_logger("parse_reasoning_traces")
OUTPUT_DIR = Path("data/derived")
INPUT_DIR = Path("data/raw")

def load_raw_traces(input_path: Path) -> List[Dict]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with open(input_path, 'r') as f:
        return json.load(f)

def parse_trace_entry(entry: Dict) -> Dict:
    """
    Extracts raw error log and ground truth resolution from a trace entry.
    Assumes the input JSON structure contains 'error_log' and 'resolution' keys.
    """
    task_id = entry.get("task_id", "unknown")
    raw_error_log = entry.get("error_log", "")
    ground_truth_resolution = entry.get("resolution", "")
    
    return {
        "task_id": str(task_id),
        "raw_error_log": str(raw_error_log),
        "ground_truth_resolution": str(ground_truth_resolution)
    }

def parse_all_traces(traces: List[Dict]) -> List[Dict]:
    parsed = []
    for entry in traces:
        try:
            parsed.append(parse_trace_entry(entry))
        except Exception as e:
            logger.warning(f"Failed to parse entry {entry.get('task_id', 'unknown')}: {e}")
    return parsed

def main():
    log_stage_start(logger, "parse_reasoning_traces")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Determine input file - assuming T009 downloaded to data/raw/arc_bench.json
    input_file = INPUT_DIR / "arc_bench.json"
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found. Please run download_arc_bench.py first.")
        sys.exit(1)

    try:
        traces = load_raw_traces(input_file)
        logger.info(f"Loaded {len(traces)} traces from {input_file}")
    except Exception as e:
        logger.error(f"Failed to load traces: {e}")
        sys.exit(1)

    parsed_traces = parse_all_traces(traces)
    
    output_path = OUTPUT_DIR / "parsed_traces.json"
    with open(output_path, 'w') as f:
        json.dump(parsed_traces, f, indent=2)
    
    logger.info(f"Saved {len(parsed_traces)} parsed traces to {output_path}")
    log_stage_end(logger, "parse_reasoning_traces")

if __name__ == "__main__":
    main()