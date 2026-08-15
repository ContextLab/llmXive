"""
Transform script for llmXive follow-up: extending Cosmos 3.
Loads schema, applies composite rule (L2 norm + text keywords),
and processes dataset in streaming mode for memory efficiency.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Generator

# Add parent directory to path to allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

# Constants
SCHEMA_PATH = Path(__file__).parent.parent / "data" / "schema" / "action_schema.json"
INPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "bridge_samples.jsonl"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "processed" / "unified_dataset.jsonl"
BUFFER_SIZE = 5000  # Batch size for throughput optimization
MEMORY_THRESHOLD_MB = 7000  # 7GB limit

logger = get_logger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the composite rule definition from JSON."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_l2_norm_first_k(actions: List[float], k: int = 3) -> float:
    """Compute L2 norm of the first k dimensions of the action vector."""
    if not actions:
        return 0.0
    
    # Take only first k dimensions
    subset = actions[:k]
    # Compute L2 norm: sqrt(sum(x^2))
    return sum(x * x for x in subset) ** 0.5


def check_text_keywords(text_description: str, keywords: List[str]) -> bool:
    """Check if any keyword from the list appears in the text description."""
    if not text_description:
        return False
    
    text_lower = text_description.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def apply_composite_rule(sample: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply the composite rule to a single sample.
    Rule: (L2 norm of first 3 dims > threshold) AND (text contains keyword)
    Label: "constraint_violated" if true, else "constraint_satisfied"
    """
    actions = sample.get("actions", [])
    text_desc = sample.get("text_description", "")
    
    norm = compute_l2_norm_first_k(actions, k=3)
    threshold = schema.get("norm_threshold", 0.5)
    keywords = schema.get("text_keywords", [])
    
    norm_condition = norm > threshold
    text_condition = check_text_keywords(text_desc, keywords)
    
    # Composite: AND
    is_violated = norm_condition and text_condition
    label = "constraint_violated" if is_violated else "constraint_satisfied"
    
    # Add metadata for analysis
    sample["l2_norm_first_3"] = norm
    sample["norm_condition"] = norm_condition
    sample["text_condition"] = text_condition
    sample["composite_violated"] = is_violated
    sample["label"] = label
    
    return sample


def process_dataset(input_path: Path, output_path: Path, schema: Dict[str, Any]) -> int:
    """
    Process the dataset in streaming mode, applying the composite rule.
    Writes results to output JSONL file in batches.
    """
    logger.info(f"Processing dataset from: {input_path}")
    logger.info(f"Writing transformed data to: {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    buffer = []
    processed_count = 0
    start_time = time.time()

    # Read input in streaming fashion (line by line for JSONL)
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
         
        for line_idx, line in enumerate(infile):
            # Memory check every 1000 lines
            if line_idx % 1000 == 0 and line_idx > 0:
                current_mem = get_memory_usage_mb()
                logger.debug(f"Line {line_idx}: Memory usage {current_mem:.2f} MB")
                if current_mem > MEMORY_THRESHOLD_MB:
                    raise MemoryError(f"Memory usage {current_mem:.2f} MB exceeded threshold {MEMORY_THRESHOLD_MB} MB")

            try:
                sample = json.loads(line.strip())
                transformed = apply_composite_rule(sample, schema)
                buffer.append(transformed)
                
                if len(buffer) >= BUFFER_SIZE:
                    # Write batch
                    for item in buffer:
                        outfile.write(json.dumps(item) + "\n")
                    processed_count += len(buffer)
                    buffer = []
                    
                    # Log throughput
                    if processed_count % (BUFFER_SIZE * 10) == 0:
                        elapsed = time.time() - start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        logger.debug(f"Wrote {processed_count} samples ({rate:.1f} samples/sec)...")
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON line {line_idx}: {e}")
                continue

        # Write remaining items
        if buffer:
            for item in buffer:
                outfile.write(json.dumps(item) + "\n")
            processed_count += len(buffer)

    elapsed = time.time() - start_time
    final_rate = processed_count / elapsed if elapsed > 0 else 0
    logger.info(f"Transform complete. Processed {processed_count} samples at {final_rate:.1f} samples/sec.")
    return processed_count


def main():
    log_script_start(__file__)
    
    try:
        # Load schema
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Loaded schema: {schema}")
        
        # Validate input file exists
        if not INPUT_FILE.exists():
            raise FileNotFoundError(f"Input file not found: {INPUT_FILE}. Run T010 (download.py) first.")
        
        # Process dataset
        count = process_dataset(INPUT_FILE, OUTPUT_FILE, schema)
        
        if count == 0:
            logger.warning("No samples were processed.")
        else:
            logger.info(f"Task T027 (transform optimization) completed successfully. Output: {OUTPUT_FILE}")
            
    except Exception as e:
        logger.error(f"Task T027 failed: {e}")
        raise
    finally:
        log_script_end(__file__)


if __name__ == "__main__":
    main()