import argparse
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from utils.logging_config import get_logger, setup_root_logger

logger = get_logger(__name__)

SCHEMA = {
    "required_fields": ["task_id", "constraint_mention", "task_outcome"],
    "constraint_mention_values": ["Yes", "No"],
    "task_outcome_values": ["Correct", "Incorrect"]
}

def validate_schema(labels: List[Dict[str, Any]]) -> bool:
    """Validate the schema of the loaded labels."""
    valid = True
    for i, label in enumerate(labels):
        for field in SCHEMA["required_fields"]:
            if field not in label:
                logger.error(f"Record {i} missing required field: {field}")
                valid = False
        
        if "constraint_mention" in label:
            if label["constraint_mention"] not in SCHEMA["constraint_mention_values"]:
                logger.error(f"Record {i} has invalid constraint_mention: {label['constraint_mention']}")
                valid = False
        
        if "task_outcome" in label:
            if label["task_outcome"] not in SCHEMA["task_outcome_values"]:
                logger.error(f"Record {i} has invalid task_outcome: {label['task_outcome']}")
                valid = False
    
    return valid

def ingest_labels(labels_path: Path) -> List[Dict[str, Any]]:
    """Ingest and validate labels from JSONL file."""
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    
    labels = []
    with open(labels_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                record['_line_number'] = line_num
                labels.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON at line {line_num}: {e}")
                raise
    
    if not validate_schema(labels):
        raise ValueError("Schema validation failed. Check logs for details.")
    
    return labels

def check_traces_consistency(labels: List[Dict], traces_path: Path) -> bool:
    """Check if all labeled task_ids exist in the traces file."""
    if not traces_path.exists():
        logger.warning(f"Traces file not found at {traces_path}, skipping consistency check.")
        return True
    
    trace_ids = set()
    with open(traces_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    trace = json.loads(line)
                    if 'task_id' in trace:
                        trace_ids.add(trace['task_id'])
                except json.JSONDecodeError:
                    continue
    
    missing_ids = []
    for label in labels:
        if label['task_id'] not in trace_ids:
            missing_ids.append(label['task_id'])
    
    if missing_ids:
        logger.error(f"Found {len(missing_ids)} task_ids in labels not present in traces: {missing_ids[:5]}...")
        return False
    
    return True

def main():
    setup_root_logger()
    parser = argparse.ArgumentParser(description="Ingest pilot ground truth labels.")
    parser.add_argument('--labels', type=str, default="data/pilot/pilot_ground_truth_labels.jsonl", help="Path to labels JSONL")
    parser.add_argument('--traces', type=str, default="data/pilot/pilot_traces.jsonl", help="Path to traces JSONL")
    args = parser.parse_args()
    
    labels_path = Path(args.labels)
    traces_path = Path(args.traces)
    
    try:
        labels = ingest_labels(labels_path)
        logger.info(f"Ingested {len(labels)} valid labels.")
        
        if check_traces_consistency(labels, traces_path):
            logger.info("Trace consistency check passed.")
        else:
            logger.warning("Trace consistency check failed. Proceeding with caution.")
        
        # Write a success marker if needed, though the main output is the side effect of validation
        logger.info("Label ingestion complete.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
