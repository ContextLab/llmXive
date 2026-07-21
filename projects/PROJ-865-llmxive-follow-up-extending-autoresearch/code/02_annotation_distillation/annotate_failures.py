import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import set_seed

# Set seed for reproducibility
set_seed(42)

logger = get_logger(__name__)

# Constants
ANNOTATION_OUTPUT_PATH = Path("data/derived/failure_cases.json")
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/failure_case.schema.yaml")
PARSED_TRACES_PATH = Path("data/derived/parsed_traces.json")

VALID_FEATURES = [
    "Syntactic Error",
    "Logical Loop",
    "Semantic Ambiguity",
    "Missing Context",
    "Unstructured"
]

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from a YAML file (simple parser for this specific schema)."""
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    content = schema_path.read_text()
    # Simple YAML to dict parser for the specific structure we expect
    # In a real scenario, we'd use pyyaml, but we stick to stdlib + existing deps
    # The schema is small enough to parse manually or assume PyYAML is available via requirements.txt
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        # Fallback: manual parsing for the specific schema structure
        # This is a minimal parser for the specific format we generated
        lines = content.split('\n')
        schema = {}
        current_key = None
        current_list = None
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            if line.startswith('  ' * 2): # Level 2 indent
                key = stripped.split(':')[0]
                val = stripped.split(':', 1)[1].strip()
                if key == 'enum':
                    current_key = key
                    current_list = []
                elif current_key == 'enum':
                    # It's an item in the list
                    if val.startswith('-'):
                        current_list.append(val[1:].strip().strip('"').strip("'"))
                    elif val:
                        current_list.append(val.strip('"').strip("'"))
                elif current_key and current_list:
                    schema[current_key] = current_list
                    current_key = None
                    current_list = None
            elif line.startswith('  '): # Level 1 indent
                if current_key and current_list:
                    schema[current_key] = current_list
                    current_key = None
                    current_list = None
                key = stripped.split(':')[0]
                val = stripped.split(':', 1)[1].strip()
                schema[key] = val
        
        if current_key and current_list:
            schema[current_key] = current_list
        
        return schema

def validate_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """Validate data against the schema."""
    required_fields = schema.get('required', [])
    enum_fields = {}
    
    # Extract enum constraints
    if 'properties' in schema:
        for prop, details in schema['properties'].items():
            if 'enum' in details:
                enum_fields[prop] = details['enum']
    
    for i, item in enumerate(data):
        # Check required fields
        for field in required_fields:
            if field not in item:
                logger.error(f"Item {i} missing required field: {field}")
                return False
        
        # Check enum constraints
        for field, allowed_values in enum_fields.items():
            if field in item and item[field] not in allowed_values:
                logger.error(f"Item {i} field '{field}' has invalid value: {item[field]}. Allowed: {allowed_values}")
                return False
        
        # Check additional properties (simple check)
        allowed_props = set(schema.get('properties', {}).keys())
        for key in item.keys():
            if key not in allowed_props and schema.get('additionalProperties') is False:
                logger.error(f"Item {i} has unexpected field: {key}")
                return False
    
    return True

def load_parsed_traces(path: Path) -> List[Dict[str, Any]]:
    """Load parsed traces from JSON file."""
    if not path.exists():
        logger.error(f"Parsed traces file not found: {path}")
        raise FileNotFoundError(f"Parsed traces file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_failure_heuristic(error_log: str, resolution: str) -> str:
    """
    Heuristic classification of failure type based on error log content.
    This is a placeholder for the actual annotation logic which might use an LLM.
    """
    error_lower = error_log.lower()
    
    # Syntactic Error patterns
    syntactic_patterns = [
        r'syntaxerror', r'invalid syntax', r'indentationerror', 
        r'nameerror.*not defined', r'attributeerror', r'importerror'
    ]
    for pattern in syntactic_patterns:
        if re.search(pattern, error_lower):
            return "Syntactic Error"
    
    # Logical Loop patterns
    logical_patterns = [
        r'infinite loop', r'recursion.*limit', r'stack overflow',
        r'while true', r'for.*for' # simplistic
    ]
    for pattern in logical_patterns:
        if re.search(pattern, error_lower):
            return "Logical Loop"
    
    # Semantic Ambiguity patterns
    semantic_patterns = [
        r'ambiguous', r'conflicting', r'unclear', r'meaningless',
        r'does not match expected', r'interpretation'
    ]
    for pattern in semantic_patterns:
        if re.search(pattern, error_lower):
            return "Semantic Ambiguity"
    
    # Missing Context patterns
    missing_context_patterns = [
        r'missing', r'not found', r'undefined variable', r'keyerror',
        r'no such file', r'context.*missing'
    ]
    for pattern in missing_context_patterns:
        if re.search(pattern, error_lower):
            return "Missing Context"
    
    # Default to Unstructured if no pattern matches
    return "Unstructured"

def annotate_single_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Annotate a single trace entry."""
    task_id = entry.get('task_id', 'unknown')
    raw_error_log = entry.get('raw_error_log', '')
    ground_truth_resolution = entry.get('ground_truth_resolution', '')
    
    annotated_feature = classify_failure_heuristic(raw_error_log, ground_truth_resolution)
    
    return {
        "task_id": task_id,
        "raw_error_log": raw_error_log,
        "ground_truth_resolution": ground_truth_resolution,
        "annotated_structural_feature": annotated_feature
    }

def main():
    log_stage_start("annotate_failures")
    log_resource_usage()
    
    try:
        # Load schema
        logger.info(f"Loading schema from {SCHEMA_PATH}")
        schema = load_schema(SCHEMA_PATH)
        
        # Load parsed traces
        logger.info(f"Loading parsed traces from {PARSED_TRACES_PATH}")
        traces = load_parsed_traces(PARSED_TRACES_PATH)
        
        # Annotate each entry
        annotated_data = []
        for entry in traces:
            annotated_entry = annotate_single_entry(entry)
            annotated_data.append(annotated_entry)
        
        logger.info(f"Generated {len(annotated_data)} annotations")
        
        # Validate against schema BEFORE writing
        logger.info("Validating output against schema...")
        if not validate_against_schema(annotated_data, schema):
            logger.error("Schema validation FAILED. Aborting write.")
            sys.exit(1)
        
        logger.info("Schema validation PASSED.")
        
        # Ensure output directory exists
        ANNOTATION_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(ANNOTATION_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(annotated_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully wrote annotated failures to {ANNOTATION_OUTPUT_PATH}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during annotation: {e}")
        sys.exit(1)
    finally:
        log_stage_end("annotate_failures")

if __name__ == "__main__":
    main()