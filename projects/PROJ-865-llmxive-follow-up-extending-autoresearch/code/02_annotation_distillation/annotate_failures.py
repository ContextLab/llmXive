"""
Annotate failure cases from parsed reasoning traces.
Validates output against the failure_case schema before writing.
"""
import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import set_seed, RANDOM_SEED

# Set seed for reproducibility
set_seed(RANDOM_SEED)

logger = get_logger(__name__)

# Schema path
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/failure_case.schema.yaml")

# Valid structural features
VALID_FEATURES = [
    "Syntactic Error",
    "Logical Loop",
    "Semantic Ambiguity",
    "Missing Context",
    "Unstructured"
]

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Validate the annotated data against the schema.
    Returns True if valid, raises ValueError if invalid.
    """
    required_keys = set(schema.get('required', []))
    properties = schema.get('properties', {})
    
    for idx, item in enumerate(data):
        # Check required keys
        item_keys = set(item.keys())
        missing_keys = required_keys - item_keys
        if missing_keys:
            raise ValueError(f"Item {idx} missing required keys: {missing_keys}")
        
        # Check types and enums
        for key, value in item.items():
            if key not in properties:
                raise ValueError(f"Item {idx} has unknown key: {key}")
            
            prop_def = properties[key]
            prop_type = prop_def.get('type')
            
            # Type checking
            if prop_type == 'string' and not isinstance(value, str):
                raise ValueError(f"Item {idx}, key '{key}': expected string, got {type(value).__name__}")
            elif prop_type == 'number' and not isinstance(value, (int, float)):
                raise ValueError(f"Item {idx}, key '{key}': expected number, got {type(value).__name__}")
            elif prop_type == 'boolean' and not isinstance(value, bool):
                raise ValueError(f"Item {idx}, key '{key}': expected boolean, got {type(value).__name__}")
            
            # Enum checking
            if 'enum' in prop_def:
                if value not in prop_def['enum']:
                    raise ValueError(
                        f"Item {idx}, key '{key}': value '{value}' not in allowed values: {prop_def['enum']}"
                    )
    
    logger.info(f"Schema validation passed for {len(data)} items")
    return True

def load_parsed_traces(input_path: Path) -> List[Dict[str, Any]]:
    """Load parsed traces from JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        traces = json.load(f)
    
    logger.info(f"Loaded {len(traces)} traces from {input_path}")
    return traces

def classify_failure_heuristic(trace_entry: Dict[str, Any]) -> str:
    """
    Heuristic classification of failure type based on error log content.
    Returns one of the valid structural feature labels.
    """
    error_log = trace_entry.get('raw_error_log', '').lower()
    
    # Syntactic Error
    syntactic_patterns = [
        r'syntaxerror', r'syntax error', r'invalid syntax', r'indentation error',
        r'indentationerror', r'invalid token', r'expected.*colon', r'expected.*)'
    ]
    for pattern in syntactic_patterns:
        if re.search(pattern, error_log):
            return "Syntactic Error"
    
    # Logical Loop
    logical_patterns = [
        r'infinite loop', r'recursion error', r'maximum recursion',
        r'looping', r'circular', r'deadlock'
    ]
    for pattern in logical_patterns:
        if re.search(pattern, error_log):
            return "Logical Loop"
    
    # Semantic Ambiguity
    semantic_patterns = [
        r'semantic', r'ambiguous', r'unclear', r'vague',
        r'confusing', r'misinterpret', r'incorrect meaning'
    ]
    for pattern in semantic_patterns:
        if re.search(pattern, error_log):
            return "Semantic Ambiguity"
    
    # Missing Context
    context_patterns = [
        r'missing context', r'insufficient information', r'not enough data',
        r'undefined', r'not defined', r'no context provided'
    ]
    for pattern in context_patterns:
        if re.search(pattern, error_log):
            return "Missing Context"
    
    # Default to Unstructured if no pattern matches
    return "Unstructured"

def annotate_single_entry(trace_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Annotate a single trace entry with structural feature.
    """
    task_id = trace_entry.get('task_id', 'unknown')
    raw_error_log = trace_entry.get('raw_error_log', '')
    ground_truth_resolution = trace_entry.get('ground_truth_resolution', '')
    
    annotated_feature = classify_failure_heuristic(trace_entry)
    
    return {
        'task_id': task_id,
        'raw_error_log': raw_error_log,
        'ground_truth_resolution': ground_truth_resolution,
        'annotated_structural_feature': annotated_feature
    }

def main():
    """Main entry point for failure annotation pipeline."""
    log_stage_start("annotate_failures")
    
    try:
        # Paths
        input_path = Path("data/derived/parsed_traces.json")
        output_path = Path("data/derived/failure_cases.json")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load schema
        logger.info(f"Loading schema from {SCHEMA_PATH}")
        schema = load_schema(SCHEMA_PATH)
        
        # Load parsed traces
        traces = load_parsed_traces(input_path)
        
        # Annotate each entry
        annotated_failures = []
        for trace in traces:
            annotated = annotate_single_entry(trace)
            annotated_failures.append(annotated)
        
        logger.info(f"Annotated {len(annotated_failures)} failure cases")
        
        # Validate against schema BEFORE writing
        logger.info("Validating annotated data against schema...")
        validate_against_schema(annotated_failures, schema)
        
        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotated_failures, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully wrote {len(annotated_failures)} annotated cases to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        log_stage_end("annotate_failures")

if __name__ == "__main__":
    main()