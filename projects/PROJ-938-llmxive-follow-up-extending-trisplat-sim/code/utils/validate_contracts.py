"""
Contract validation utility for llmXive pipeline.
Validates generated JSON outputs against defined YAML schemas.
"""
import json
import yaml
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # Fallback if jsonschema is not installed, though requirements.txt should include it
    print("ERROR: jsonschema library not found. Please install it: pip install jsonschema")
    sys.exit(1)

logger = logging.getLogger(__name__)

def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} must contain a top-level YAML object.")
    
    return schema

def load_json_output(json_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON output file."""
    if not json_path.exists():
        raise FileNotFoundError(f"JSON output file not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")
    
    return data

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_path: Path) -> Tuple[bool, str]:
    """
    Validate data against a JSON schema.
    Returns (is_valid, error_message).
    """
    try:
        # Ensure schema is a valid JSON Schema (Draft 7 is common)
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        if not errors:
            return True, "Validation successful"
        
        error_msgs = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_msgs.append(f"  - {path}: {error.message}")
        
        return False, "Validation failed:\n" + "\n".join(error_msgs)
        
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"

def find_json_outputs(base_dir: Path) -> List[Path]:
    """Find all JSON files in the project data directories."""
    json_files = []
    data_dirs = [
        base_dir / "data" / "processed",
        base_dir / "data" / "raw",
        base_dir / "data"
    ]
    
    for data_dir in data_dirs:
        if data_dir.exists():
            json_files.extend(data_dir.glob("*.json"))
    
    return sorted(json_files)

def find_schemas(contracts_dir: Path) -> List[Path]:
    """Find all schema files in the contracts directory."""
    if not contracts_dir.exists():
        logger.warning(f"Contracts directory not found: {contracts_dir}")
        return []
    
    return sorted(contracts_dir.glob("*.schema.yaml"))

def validate_all_contracts(project_root: Path) -> Dict[str, Any]:
    """
    Validate all JSON outputs against their corresponding schemas.
    Returns a summary report.
    """
    contracts_dir = project_root / "contracts"
    report = {
        "total_schemas": 0,
        "total_outputs": 0,
        "validations": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    }
    
    schemas = find_schemas(contracts_dir)
    outputs = find_json_outputs(project_root)
    
    report["total_schemas"] = len(schemas)
    report["total_outputs"] = len(outputs)
    
    # Map schema names to outputs (simple heuristic: schema name matches output name)
    schema_map = {}
    for schema_path in schemas:
        schema_name = schema_path.stem.replace(".schema", "")
        schema_map[schema_name] = schema_path
    
    # Validate each output against matching schema
    for output_path in outputs:
        output_name = output_path.stem
        matching_schema = None
        
        # Try to find a matching schema
        for schema_name, schema_path in schema_map.items():
            if schema_name in output_name or output_name in schema_name:
                matching_schema = schema_path
                break
        
        if not matching_schema:
            # If no matching schema, check if there's a generic one or skip
            # For now, we'll log a warning and skip
            logger.warning(f"No matching schema found for {output_path}. Skipping.")
            continue
        
        try:
            schema = load_yaml_schema(matching_schema)
            data = load_json_output(output_path)
            is_valid, message = validate_against_schema(data, schema, matching_schema)
            
            validation_result = {
                "output": str(output_path.relative_to(project_root)),
                "schema": str(matching_schema.relative_to(project_root)),
                "valid": is_valid,
                "message": message
            }
            
            report["validations"].append(validation_result)
            
            if is_valid:
                report["summary"]["passed"] += 1
            else:
                report["summary"]["failed"] += 1
                
        except Exception as e:
            error_result = {
                "output": str(output_path.relative_to(project_root)),
                "schema": str(matching_schema.relative_to(project_root)) if matching_schema else "Unknown",
                "valid": False,
                "message": f"Error during validation: {str(e)}"
            }
            report["validations"].append(error_result)
            report["summary"]["errors"] += 1
            logger.error(f"Error validating {output_path}: {e}")
    
    return report

def main():
    """Main entry point for contract validation."""
    logging.basicConfig(level=logging.INFO)
    
    # Determine project root
    current_dir = Path.cwd()
    # Assume we are running from code/utils/ or code/
    if current_dir.name == "utils":
        project_root = current_dir.parent.parent
    elif current_dir.name == "code":
        project_root = current_dir.parent
    else:
        project_root = current_dir
    
    logger.info(f"Project root: {project_root}")
    
    report = validate_all_contracts(project_root)
    
    # Print summary
    print("\n" + "="*60)
    print("CONTRACT VALIDATION REPORT")
    print("="*60)
    print(f"Schemas found: {report['total_schemas']}")
    print(f"JSON outputs found: {report['total_outputs']}")
    print(f"Validations passed: {report['summary']['passed']}")
    print(f"Validations failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print("="*60)
    
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        print("\nFailed/Errored Validations:")
        for v in report['validations']:
            if not v['valid']:
                print(f"  - {v['output']} vs {v['schema']}")
                print(f"    {v['message']}")
        sys.exit(1)
    else:
        print("\nAll contracts validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
