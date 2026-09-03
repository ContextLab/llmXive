import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Generator

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_script_start, log_script_end, log_memory_usage

logger = get_logger(__name__)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the logical rule definition from the JSON schema file.
    
    Args:
        schema_path: Path to the action_schema.json file.
        
    Returns:
        Dictionary containing the schema rules.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    logger.info(f"Loading schema from {schema_path}")
    with open(path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # Validate required keys
    required_keys = ['norm_threshold', 'text_keywords', 'composite_operator']
    for key in required_keys:
        if key not in schema:
            raise ValueError(f"Schema missing required key: {key}")
            
    logger.info(f"Schema loaded: threshold={schema['norm_threshold']}, "
                f"keywords={schema['text_keywords']}, operator={schema['composite_operator']}")
    return schema


def compute_l2_norm_first_k(vector: List[float], k: int = 3) -> float:
    """
    Compute the L2 norm of the first k dimensions of a vector.
    
    Args:
        vector: List of floats representing the action vector.
        k: Number of dimensions to consider (default 3).
        
    Returns:
        L2 norm of the first k dimensions.
        
    Raises:
        ValueError: If vector length is less than k.
    """
    if len(vector) < k:
        raise ValueError(f"Vector length ({len(vector)}) is less than required k ({k})")
    
    first_k = vector[:k]
    # L2 norm: sqrt(sum(x^2))
    norm_sq = sum(x**2 for x in first_k)
    return norm_sq ** 0.5


def check_text_keywords(text: str, keywords: List[str]) -> bool:
    """
    Check if the text contains any of the specified keywords.
    
    Args:
        text: The text description to search.
        keywords: List of keywords to look for.
        
    Returns:
        True if any keyword is found (case-insensitive), False otherwise.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            logger.debug(f"Keyword '{keyword}' found in text")
            return True
    return False


def apply_composite_rule(norm_value: float, text_match: bool, schema: Dict[str, Any]) -> str:
    """
    Apply the composite rule to determine the label.
    
    The rule is: (norm > threshold) AND (text contains keyword)
    If true -> "constraint_violated"
    Else -> "constraint_satisfied"
    
    Args:
        norm_value: The computed L2 norm.
        text_match: Boolean result of keyword check.
        schema: The loaded schema dictionary.
        
    Returns:
        String label: "constraint_violated" or "constraint_satisfied".
    """
    threshold = schema['norm_threshold']
    operator = schema.get('composite_operator', 'AND')
    
    # Currently only 'AND' is supported per spec
    if operator != 'AND':
        logger.warning(f"Unsupported composite operator '{operator}', defaulting to AND")
    
    # Composite rule: norm > threshold AND text_match
    is_violated = (norm_value > threshold) and text_match
    
    if is_violated:
        return "constraint_violated"
    else:
        return "constraint_satisfied"


def process_dataset(input_path: str, output_path: str, schema: Dict[str, Any]) -> int:
    """
    Process the dataset from input JSONL, apply transformation rules, and save to output.
    
    Args:
        input_path: Path to the input JSONL file (bridge_samples.jsonl).
        output_path: Path to the output JSONL file (unified_dataset.jsonl).
        schema: The loaded schema dictionary.
        
    Returns:
        Number of records processed.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    start_time = time.time()
    
    logger.info(f"Starting dataset transformation: {input_path} -> {output_path}")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
         
         for line_num, line in enumerate(infile, 1):
             line = line.strip()
             if not line:
                 continue
             
             try:
                 record = json.loads(line)
             except json.JSONDecodeError as e:
                 logger.error(f"Skipping invalid JSON at line {line_num}: {e}")
                 continue
             
             # Validate required fields
             if 'actions' not in record:
                 logger.warning(f"Skipping line {line_num}: missing 'actions' field")
                 continue
             
             if 'text_description' not in record:
                 # If text_description is missing, text_match will be False
                 record['text_description'] = ""
             
             actions = record['actions']
             
             # Ensure actions is a list of numbers
             if not isinstance(actions, list):
                 logger.warning(f"Skipping line {line_num}: 'actions' is not a list")
                 continue
             
             try:
                 # 1. Compute L2 norm of first 3 dimensions
                 norm_value = compute_l2_norm_first_k(actions, k=3)
                 
                 # 2. Check text keywords
                 text_match = check_text_keywords(
                     record['text_description'], 
                     schema['text_keywords']
                 )
                 
                 # 3. Apply composite rule
                 label = apply_composite_rule(norm_value, text_match, schema)
                 
                 # 4. Add metadata and label to record
                 record['action_norm_3d'] = norm_value
                 record['text_keyword_match'] = text_match
                 record['label'] = label
                 
                 # Write to output
                 outfile.write(json.dumps(record) + '\n')
                 processed_count += 1
                 
             except ValueError as e:
                 logger.error(f"Skipping line {line_num}: {e}")
                 continue
             
             # Log progress every 1000 records
             if line_num % 1000 == 0:
                 elapsed = time.time() - start_time
                 log_memory_usage(logger)
                 logger.info(f"Processed {line_num} lines ({processed_count} valid), "
                             f"elapsed: {elapsed:.2f}s")
    
    elapsed = time.time() - start_time
    logger.info(f"Transformation complete. Processed {processed_count} records in {elapsed:.2f}s. "
                f"Output saved to {output_path}")
    return processed_count


def main():
    """Main entry point for the transform script."""
    log_script_start(logger, "transform")
    
    try:
        # Define paths relative to project root
        # Assuming script is run from code/ or root
        project_root = Path(__file__).parent.parent
        
        schema_path = project_root / "data" / "schema" / "action_schema.json"
        input_path = project_root / "data" / "raw" / "bridge_samples.jsonl"
        output_path = project_root / "data" / "processed" / "unified_dataset.jsonl"
        
        # Convert to strings for compatibility
        schema_path_str = str(schema_path)
        input_path_str = str(input_path)
        output_path_str = str(output_path)
        
        # 1. Load schema
        schema = load_schema(schema_path_str)
        
        # 2. Process dataset
        count = process_dataset(input_path_str, output_path_str, schema)
        
        if count == 0:
            logger.error("No records were processed. Check input data and filtering logic.")
            sys.exit(1)
        
        log_script_end(logger, "transform", success=True)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Fail loudly as per requirements
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during transformation: {e}")
        log_script_end(logger, "transform", success=False)
        sys.exit(1)


if __name__ == "__main__":
    main()