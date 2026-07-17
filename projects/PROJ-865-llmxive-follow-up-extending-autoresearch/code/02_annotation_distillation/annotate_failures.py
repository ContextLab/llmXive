"""
annotate_failures.py
Annotates parsed reasoning traces with failure types and validates against schema.
"""
import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling utils
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import validate_resource_limits

logger = get_logger(__name__)

# Schema path constant
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/failure_case.schema.yaml")

# Valid failure types based on task description
VALID_FAILURE_TYPES = [
    "Syntactic",
    "Logical",
    "Semantic",
    "Missing Context",
    "Unstructured"
]

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the failure case schema from YAML/JSON."""
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        logger.error(f"Schema file not found: {path}")
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    # Simple YAML/JSON loader (assuming JSON-like structure for validation)
    # Since we don't have pyyaml in imports, we handle basic JSON or simple YAML parsing
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try JSON first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Simple YAML parsing for basic structures
        # This is a minimal parser for the expected schema format
        schema = {}
        lines = content.split('\n')
        current_key = None
        current_list = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('- '):
                if current_key:
                    current_list.append(line[2:].strip())
            elif ':' in line:
                if current_key and current_list:
                    schema[current_key] = current_list
                    current_list = []
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value:
                    schema[key] = value
                else:
                    current_key = key
        
        if current_key and current_list:
            schema[current_key] = current_list
        
        return schema
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        raise

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate annotated failure data against the schema."""
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field in schema validation: {field}")
            return False
    
    # Check field types if defined
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type:
                type_map = {
                    'string': str,
                    'integer': int,
                    'number': (int, float),
                    'boolean': bool,
                    'array': list,
                    'object': dict
                }
                expected_python_type = type_map.get(expected_type)
                if expected_python_type and not isinstance(value, expected_python_type):
                    logger.error(f"Field {field} has wrong type: expected {expected_type}, got {type(value)}")
                    return False
    
    # Check enum values if defined
    for field, value in data.items():
        if field in properties:
            enum_values = properties[field].get('enum')
            if enum_values and value not in enum_values:
                logger.error(f"Field {field} has invalid value: {value}. Must be one of {enum_values}")
                return False
    
    return True

def load_parsed_traces(traces_path: Path) -> List[Dict[str, Any]]:
    """Load parsed reasoning traces from JSON file."""
    if not traces_path.exists():
        logger.error(f"Parsed traces file not found: {traces_path}")
        raise FileNotFoundError(f"Parsed traces file not found: {traces_path}")
    
    with open(traces_path, 'r', encoding='utf-8') as f:
        traces = json.load(f)
    
    return traces

def classify_failure_heuristic(error_log: str) -> str:
    """
    Heuristic classification of failure type based on error log content.
    Returns one of: Syntactic, Logical, Semantic, Missing Context, Unstructured
    """
    error_lower = error_log.lower()
    
    # Syntactic: syntax errors, indentation, missing brackets
    syntactic_patterns = [
        r'syntaxerror', r'indentationerror', r'missing', r'parenthesis',
        r'bracket', r'token', r'syntax', r'invalid syntax', r'expected'
    ]
    for pattern in syntactic_patterns:
        if re.search(pattern, error_lower):
            return "Syntactic"
    
    # Logical: logic errors, infinite loops, wrong algorithm
    logical_patterns = [
        r'logic', r'infinite loop', r'recursion', r'algorithm',
        r'wrong', r'incorrect', r'miscalculation', r'off by one'
    ]
    for pattern in logical_patterns:
        if re.search(pattern, error_lower):
            return "Logical"
    
    # Semantic: meaning errors, wrong interpretation
    semantic_patterns = [
        r'semantic', r'meaning', r'interpretation', r'context',
        r'ambiguity', r'confusing', r'unclear'
    ]
    for pattern in semantic_patterns:
        if re.search(pattern, error_lower):
            return "Semantic"
    
    # Missing Context: lack of information
    context_patterns = [
        r'missing', r'context', r'insufficient', r'unknown',
        r'undefined', r'not found', r'cannot find'
    ]
    for pattern in context_patterns:
        if re.search(pattern, error_lower):
            return "Missing Context"
    
    # Default to Unstructured if no pattern matches
    return "Unstructured"

def annotate_single_entry(entry: Dict[str, Any], schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Annotate a single trace entry with failure type.
    Returns None if entry cannot be annotated.
    """
    try:
        error_log = entry.get('error_log', '')
        if not error_log:
            logger.warning(f"Entry missing error_log: {entry.get('task_id', 'unknown')}")
            return None
        
        # Classify failure type
        failure_type = classify_failure_heuristic(error_log)
        
        # Create annotated entry
        annotated = {
            'task_id': entry.get('task_id', ''),
            'topic': entry.get('topic', ''),
            'error_log': error_log,
            'ground_truth_resolution': entry.get('ground_truth_resolution', ''),
            'failure_type': failure_type,
            'confidence': 0.8,  # Heuristic confidence
            'timestamp': None  # Will be set by caller if needed
        }
        
        # Validate against schema
        if not validate_against_schema(annotated, schema):
            logger.error(f"Annotation failed schema validation for task {annotated['task_id']}")
            return None
        
        return annotated
    except Exception as e:
        logger.error(f"Error annotating entry: {e}")
        return None

def main():
    """Main entry point for failure annotation pipeline."""
    log_stage_start("annotate_failures")
    
    # Validate resource limits
    validate_resource_limits()
    
    # Load schema
    schema = load_schema()
    logger.info(f"Loaded schema with required fields: {schema.get('required', [])}")
    
    # Load parsed traces
    traces_path = Path("data/derived/parsed_traces.json")
    traces = load_parsed_traces(traces_path)
    logger.info(f"Loaded {len(traces)} parsed traces")
    
    # Annotate all entries
    annotated_failures = []
    for i, entry in enumerate(traces):
        if i % 100 == 0:
            log_resource_usage()
        
        annotated = annotate_single_entry(entry, schema)
        if annotated:
            annotated_failures.append(annotated)
    
    logger.info(f"Successfully annotated {len(annotated_failures)} out of {len(traces)} entries")
    
    # Count by failure type
    failure_counts = {}
    for item in annotated_failures:
        ft = item['failure_type']
        failure_counts[ft] = failure_counts.get(ft, 0) + 1
    
    logger.info(f"Failure type distribution: {failure_counts}")
    
    # Save annotated failures
    output_path = Path("data/derived/annotated_failures.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(annotated_failures, f, indent=2)
    
    logger.info(f"Saved {len(annotated_failures)} annotated failures to {output_path}")
    
    # Final validation: ensure all entries match schema
    for item in annotated_failures:
        if not validate_against_schema(item, schema):
            logger.error(f"Final validation failed for item: {item.get('task_id')}")
            sys.exit(1)
    
    log_stage_end("annotate_failures")
    return annotated_failures

if __name__ == "__main__":
    main()