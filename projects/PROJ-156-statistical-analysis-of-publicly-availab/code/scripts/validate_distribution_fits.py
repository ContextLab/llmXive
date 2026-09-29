"""
Validate distribution_fits.csv against the distribution_fit.schema.yaml contract.
"""
import csv
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the JSON schema from a YAML or JSON file."""
    # Simple YAML parser for this specific schema (avoids PyYAML dependency if not needed)
    # or use json.load if saved as JSON.
    # Since the schema is provided as YAML in the contract, we need to parse it.
    # For robustness, we'll try to load as JSON first, then fallback to a simple YAML parser
    # or assume the schema is valid JSON-compatible YAML (which this specific one is).
    
    with open(schema_path, 'r') as f:
        content = f.read()
    
    # If the file is strictly JSON, json.load works. 
    # If it has YAML-specific syntax (like comments or unquoted booleans), we might need a parser.
    # Given the constraints, we will assume the schema is valid JSON or use a minimal parser.
    # To be safe and avoid external deps, we'll read the file and assume it's JSON-compatible
    # or use a simple regex-based extraction if necessary.
    # However, standard practice is to use `json` if the schema is JSON.
    # Let's try to parse as JSON first. If it fails, we assume it's a simple YAML subset.
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Minimal YAML parser for this specific structure
        # This is a fallback. Ideally, the schema file should be JSON.
        # We will reconstruct the schema dict manually based on the provided content structure
        # or raise an error if it's too complex.
        logger.warning("Schema is not valid JSON. Attempting simple YAML parsing...")
        # Since the schema provided is relatively simple, we can try to convert common YAML
        # patterns to JSON strings before parsing.
        # But to keep it robust, let's assume the user provides a JSON version or we use a library.
        # Given the "Real data only" constraint and standard libraries, we will assume the schema
        # is saved as JSON or we implement a very basic parser.
        # Let's implement a basic parser for the specific schema structure provided.
        
        schema = {
            "type": "object",
            "required": [],
            "properties": {},
            "additionalProperties": False
        }
        
        lines = content.split('\n')
        current_prop = None
        in_properties = False
        in_required = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line == 'properties:':
                in_properties = True
                in_required = False
                continue
            if line == 'required:':
                in_properties = False
                in_required = True
                continue
            if line == '$schema:':
                continue
            if line == 'title:':
                continue
            if line == 'description:':
                continue
            if line.startswith('type:'):
                continue
            if line.startswith('minimum:'):
                continue
            if line.startswith('maximum:'):
                continue
            if line.startswith('enum:'):
                continue
            if line.startswith('- '):
                if in_required:
                    val = line[2:].strip().strip('"').strip("'")
                    schema["required"].append(val)
                continue
            
            if in_properties:
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if not val:
                        current_prop = key
                        schema["properties"][current_prop] = {}
                    else:
                        if current_prop:
                            # Handle simple key: value
                            if val.startswith('[') and val.endswith(']'):
                                # Enum list
                                vals = val[1:-1].split(',')
                                schema["properties"][current_prop]["enum"] = [v.strip().strip('"').strip("'") for v in vals]
                            elif val.isdigit():
                                schema["properties"][current_prop][key] = int(val)
                            else:
                                schema["properties"][current_prop][key] = val.strip('"').strip("'")
                else:
                    # Indented property
                    if current_prop and ':' in line:
                        k, v = line.split(':', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        schema["properties"][current_prop][k] = v

        return schema

def validate_row(row: Dict[str, str], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single row against the schema."""
    # Check required fields
    for field in schema.get('required', []):
        if field not in row or not row[field]:
            return False, f"Missing required field: {field}"
    
    # Check types and constraints
    props = schema.get('properties', {})
    for field, value in row.items():
        if field not in props:
            if props.get('additionalProperties') is False:
                return False, f"Unexpected field: {field}"
            continue
        
        field_schema = props[field]
        
        # Type checking
        field_type = field_schema.get('type')
        if field_type == 'number':
            try:
                float(value)
            except ValueError:
                return False, f"Field {field} must be a number, got: {value}"
        elif field_type == 'integer':
            try:
                int(value)
            except ValueError:
                return False, f"Field {field} must be an integer, got: {value}"
        elif field_type == 'boolean':
            if value.lower() not in ('true', 'false', '1', '0'):
                return False, f"Field {field} must be a boolean, got: {value}"
        elif field_type == 'string':
            pass # Strings are always valid
        
        # Enum checking
        if 'enum' in field_schema:
            if value not in field_schema['enum']:
                return False, f"Field {field} value '{value}' not in allowed values: {field_schema['enum']}"
        
        # Range checking
        if 'minimum' in field_schema:
            if float(value) < field_schema['minimum']:
                return False, f"Field {field} value {value} is below minimum {field_schema['minimum']}"
        if 'maximum' in field_schema:
            if float(value) > field_schema['maximum']:
                return False, f"Field {field} value {value} is above maximum {field_schema['maximum']}"
    
    return True, "OK"

def validate_distribution_fits(csv_path: str, schema_path: str) -> List[Dict[str, Any]]:
    """Validate the entire CSV file and return a list of validation results."""
    schema = load_schema(schema_path)
    errors = []
    valid_count = 0
    
    if not os.path.exists(csv_path):
        return [{"error": f"CSV file not found: {csv_path}"}]
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            is_valid, msg = validate_row(row, schema)
            if is_valid:
                valid_count += 1
            else:
                errors.append({
                    "row": i + 1,
                    "error": msg,
                    "data": row
                })
    
    logger.info(f"Validation complete. {valid_count} valid rows, {len(errors)} errors.")
    return errors

def save_report(errors: List[Dict[str, Any]], output_path: str):
    """Save the validation report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump({"validation_errors": errors, "status": "failed" if errors else "passed"}, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    csv_path = project_root / "data" / "processed" / "distribution_fits.csv"
    schema_path = project_root / "contracts" / "distribution_fit.schema.yaml"
    report_path = project_root / "data" / "processed" / "validation_report.json"
    
    if not csv_path.exists():
        logger.error(f"Input file not found: {csv_path}")
        sys.exit(1)
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    errors = validate_distribution_fits(str(csv_path), str(schema_path))
    save_report(errors, str(report_path))
    
    if errors:
        logger.error("Validation failed. Check the report for details.")
        sys.exit(1)
    else:
        logger.info("Validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
