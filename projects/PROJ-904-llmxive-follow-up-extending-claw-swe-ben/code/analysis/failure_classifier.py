import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

class FailureCategory(str, Enum):
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    MEMORY_ERROR = "memory_error"
    OTHER = "other"

def classify_failure(log: str) -> str:
    if not log:
        return FailureCategory.OTHER.value

    log_lower = log.lower()
    
    if "file not found" in log_lower or "cannot locate" in log_lower:
        return FailureCategory.MISSING_CONTEXT.value
    
    if "timeout" in log_lower or "timed out" in log_lower:
        return FailureCategory.TIMEOUT.value
    
    if "memory" in log_lower or "oom" in log_lower:
        return FailureCategory.MEMORY_ERROR.value
    
    if "assertion" in log_lower or "test failed" in log_lower:
        return FailureCategory.REASONING_ERROR.value
    
    return FailureCategory.OTHER.value

def process_results(results: List[Dict]) -> List[Dict]:
    for result in results:
        log = result.get("error_message", "")
        result["failure_category"] = classify_failure(log)
    return results

def aggregate_failure_modes(results: List[Dict]) -> Dict[str, int]:
    counts = {}
    for result in results:
        cat = result.get("failure_category", FailureCategory.OTHER.value)
        counts[cat] = counts.get(cat, 0) + 1
    return counts

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) < 3:
        logger.error("Usage: python failure_classifier.py --input <input_file> --output <output_file>")
        sys.exit(1)

    input_path = sys.argv[sys.argv.index("--input") + 1]
    output_path = sys.argv[sys.argv.index("--output") + 1]

    try:
        with open(input_path, 'r') as f:
            results = [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"File not found: {input_path}")
        sys.exit(1)

    processed = process_results(results)
    
    with open(output_path, 'w') as f:
        for item in processed:
            f.write(json.dumps(item) + "\n")
    
    logger.info(f"Classified {len(processed)} results")

if __name__ == "__main__":
    main()
