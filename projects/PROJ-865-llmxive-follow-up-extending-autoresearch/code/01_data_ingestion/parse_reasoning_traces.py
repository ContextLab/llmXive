"""
Task T010: Parse reasoning traces to extract raw error logs and ground-truth resolutions.

This script reads the ARC-Bench subset downloaded by T009, parses the reasoning traces,
and extracts:
  1. Raw error logs (the failure transcripts)
  2. Ground-truth resolutions (the correct solution paths)

Output: data/derived/parsed_traces.json
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

logger = get_logger(__name__)

def load_raw_traces(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the raw ARC-Bench subset JSON.
    Expects the structure produced by download_arc_bench.py.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Run T009 (download_arc_bench.py) first.")
    
    logger.info(f"Loading raw traces from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'data' in data:
        return data['data']
    else:
        # Fallback for unexpected structures, though T009 should normalize
        logger.warning("Unexpected input structure, treating root as list")
        return [data] if not isinstance(data, list) else data

def parse_trace_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract error logs and ground-truth resolution from a single trace entry.
    
    Expected fields in entry (based on ARC-Bench standard):
      - task_id: Unique identifier
      - reasoning_trace: The LLM's step-by-step reasoning (may contain errors)
      - error_log: Explicit error messages if available
      - ground_truth: The correct answer/resolution
      - solution_path: The step-by-step correct path if available
    
    Returns a dict with:
      - task_id
      - raw_error_log: String concatenation of errors
      - ground_truth_resolution: The correct solution
      - metadata: Original topic/subject if available
    """
    task_id = entry.get('task_id')
    if not task_id:
        logger.warning("Skipping entry with no task_id")
        return None

    # Extract error logs
    # Try multiple common field names for error data
    error_log = None
    if 'error_log' in entry:
        error_log = entry['error_log']
    elif 'errors' in entry:
        error_log = str(entry['errors'])
    elif 'reasoning_trace' in entry:
        # Sometimes errors are embedded in the trace with markers
        trace = entry['reasoning_trace']
        if 'ERROR' in trace or 'Exception' in trace or 'Traceback' in trace:
            # Simple heuristic: extract lines containing error indicators
            lines = trace.split('\n')
            error_lines = [l for l in lines if any(ind in l for ind in ['ERROR', 'Exception', 'Traceback', 'Error:'])]
            if error_lines:
                error_log = '\n'.join(error_lines)
      
    # If still no error log, use a placeholder indicating no explicit error found
    if error_log is None:
        error_log = "No explicit error log found in trace."

    # Extract ground truth resolution
    ground_truth = None
    if 'ground_truth' in entry:
        ground_truth = entry['ground_truth']
    elif 'solution' in entry:
        ground_truth = entry['solution']
    elif 'correct_answer' in entry:
        ground_truth = entry['correct_answer']
    elif 'solution_path' in entry:
        ground_truth = entry['solution_path']
    
    if ground_truth is None:
        logger.warning(f"Task {task_id}: No ground truth found, using placeholder")
        ground_truth = "Ground truth not available in source data."

    return {
        "task_id": task_id,
        "raw_error_log": error_log,
        "ground_truth_resolution": ground_truth,
        "metadata": {
            "topic": entry.get('topic', 'unknown'),
            "source": "ARC-Bench",
            "parsed_from": str(entry.get('source_file', 'unknown'))
        }
    }

def parse_all_traces(input_path: Path, output_path: Path) -> int:
    """
    Parse all traces and write to output JSON.
    
    Returns the number of successfully parsed entries.
    """
    raw_data = load_raw_traces(input_path)
    logger.info(f"Processing {len(raw_data)} trace entries")
    
    parsed_entries = []
    for i, entry in enumerate(raw_data):
        try:
            parsed = parse_trace_entry(entry)
            if parsed:
                parsed_entries.append(parsed)
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(raw_data)} entries")
        except Exception as e:
            logger.error(f"Failed to parse entry {i}: {e}")
            continue

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(parsed_entries)} parsed entries to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_entries, f, indent=2, ensure_ascii=False)

    return len(parsed_entries)

def main():
    """Main entry point for T010."""
    log_stage_start("T010-parse_reasoning_traces")
    
    # Validate resources
    validate_resource_limits()
    
    # Define paths relative to project root
    input_file = PROJECT_ROOT / "data" / "raw" / "arc_bench_subset.json"
    output_file = PROJECT_ROOT / "data" / "derived" / "parsed_traces.json"
    
    if not input_file.exists():
        logger.error(f"Input file missing: {input_file}")
        logger.error("Please run T009 (download_arc_bench.py) first to populate data/raw/")
        sys.exit(1)
    
    try:
        count = parse_all_traces(input_file, output_file)
        logger.info(f"Successfully parsed {count} traces. Output: {output_file}")
        log_stage_end("T010-parse_reasoning_traces", success=True)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_stage_end("T010-parse_reasoning_traces", success=False)
        sys.exit(1)

if __name__ == "__main__":
    main()