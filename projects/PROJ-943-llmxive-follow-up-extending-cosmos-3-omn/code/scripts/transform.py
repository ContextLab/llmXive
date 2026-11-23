"""
Transform continuous action vectors into discrete symbolic tokens.

Implements the composite rule defined in action_schema.json:
1. Compute L2 norm of the first `vector_dimensions` of the 'actions' vector.
2. Check if `text_description` contains any of the `text_keywords`.
3. Apply composite operator (AND) to determine if a constraint is violated.

Output: code/data/processed/unified_dataset.jsonl
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Generator
import numpy as np

# Add parent directory to path for imports if running as script
_code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_code_root))

from utils.logger import get_logger, log_script_start, log_script_end, get_memory_usage_mb

logger = get_logger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the logical rule definition from JSON."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    logger.info(f"Loaded schema: {schema}")
    return schema

def compute_l2_norm_first_k(vector: List[float], k: int) -> float:
    """Compute L2 norm of the first k dimensions of a vector."""
    if not vector:
        return 0.0
    
    # Take only the first k dimensions, padding with 0 if vector is shorter
    subset = vector[:k]
    if len(subset) < k:
        subset = subset + [0.0] * (k - len(subset))
    
    return float(np.linalg.norm(subset))

def check_text_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the specified keywords (case-insensitive)."""
    if not text:
        return False
    
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False

def apply_composite_rule(norm_value: float, threshold: float, 
                         keyword_match: bool, operator: str) -> bool:
    """
    Apply the composite rule: (norm > threshold) AND (keyword_match).
    Currently only 'AND' is supported by the schema.
    """
    norm_condition = norm_value > threshold
    
    if operator == "AND":
        return norm_condition and keyword_match
    elif operator == "OR":
        return norm_condition or keyword_match
    else:
        raise ValueError(f"Unsupported composite operator: {operator}")

def process_dataset(input_path: str, output_path: str, schema: Dict[str, Any]) -> int:
    """
    Process the raw dataset, apply rules, and save to processed JSONL.
    Uses streaming-like chunk processing to manage memory.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    threshold = schema.get("norm_threshold", 0.5)
    keywords = schema.get("text_keywords", [])
    operator = schema.get("composite_operator", "AND")
    vector_dims = schema.get("vector_dimensions", 3)
    
    processed_count = 0
    start_time = time.time()
    
    logger.info(f"Starting processing: {input_path} -> {output_path}")
    logger.info(f"Rules: threshold={threshold}, keywords={keywords}, operator={operator}, dims={vector_dims}")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line_num, line in enumerate(infile, 1):
             line = line.strip()
             if not line:
                 continue
             
             try:
                 record = json.loads(line)
             except json.JSONDecodeError as e:
                 logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                 continue
             
             # Extract actions vector
             actions = record.get("actions")
             if actions is None:
                 # If actions missing, we cannot compute norm. 
                 # Based on T009 filtering, this should ideally not happen, 
                 # but handle gracefully by skipping or defaulting.
                 # Let's skip to ensure data integrity for the rule.
                 logger.debug(f"Skipping line {line_num}: missing 'actions' field")
                 continue
             
             if not isinstance(actions, list):
                 logger.warning(f"Skipping line {line_num}: 'actions' is not a list")
                 continue
             
             # Compute L2 norm of first k dimensions
             norm_value = compute_l2_norm_first_k(actions, vector_dims)
             
             # Check text keywords
             text_desc = record.get("text_description", "")
             keyword_match = check_text_keywords(text_desc, keywords)
             
             # Apply composite rule
             is_violated = apply_composite_rule(norm_value, threshold, keyword_match, operator)
             
             label = "constraint_violated" if is_violated else "constraint_satisfied"
             
             # Construct output record preserving original data + new features
             output_record = {
                 **record,
                 "norm_value": norm_value,
                 "keyword_match": keyword_match,
                 "label": label,
                 "rule_applied": {
                     "threshold": threshold,
                     "operator": operator,
                     "dimensions": vector_dims
                 }
             }
             
             outfile.write(json.dumps(output_record) + "\n")
             processed_count += 1
             
             # Log progress periodically
             if processed_count % 1000 == 0:
                 mem_mb = get_memory_usage_mb()
                 logger.debug(f"Processed {processed_count} records. Memory: {mem_mb:.1f} MB")
    
    elapsed = time.time() - start_time
    logger.info(f"Processing complete. {processed_count} records written to {output_path} in {elapsed:.2f}s")
    return processed_count

def main():
    """Main entry point for the transform script."""
    log_script_start("transform")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "data" / "schema" / "action_schema.json"
    input_path = project_root / "data" / "raw" / "bridge_samples.jsonl"
    output_path = project_root / "data" / "processed" / "unified_dataset.jsonl"
    
    try:
        # 1. Load schema
        schema = load_schema(str(schema_path))
        
        # 2. Process dataset
        count = process_dataset(str(input_path), str(output_path), schema)
        
        if count == 0:
            logger.error("No records were processed. Check input data and schema.")
            sys.exit(1)
        
        logger.info(f"Successfully transformed {count} records.")
        
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during transformation: {e}")
        raise
    finally:
        log_script_end("transform")

if __name__ == "__main__":
    main()