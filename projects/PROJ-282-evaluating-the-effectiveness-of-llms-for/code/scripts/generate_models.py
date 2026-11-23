"""
Script to generate Pydantic models from YAML schema contracts.
Ensures schema drift is prevented by generating code directly from contract files.
"""
import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def get_field_type(yaml_type: str) -> str:
    """Map YAML type to Python type hint string."""
    type_map = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'boolean': 'bool',
        'array': 'List',
        'object': 'Dict',
    }
    return type_map.get(yaml_type, 'Any')


def generate_model_class(schema: Dict[str, Any], class_name: str = "GeneratedModel") -> str:
    """
    Generate a Pydantic model class string from a schema dictionary.
    """
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    lines = [
        'from pydantic import BaseModel, Field',
        'from typing import Optional, List, Any',
        '',
        '',
        f'class {class_name}(BaseModel):',
        f'    """Generated model from schema."""'
    ]
    
    for prop_name, prop_def in properties.items():
        yaml_type = prop_def.get('type', 'string')
        py_type = get_field_type(yaml_type)
        is_required = prop_name in required
        
        if is_required:
            # Required field
            lines.append(f'    {prop_name}: {py_type} = Field(...)')
        else:
            # Optional field
            lines.append(f'    {prop_name}: Optional[{py_type}] = Field(None)')
    
    return '\n'.join(lines)


def verify_generation(schema_path: str, generated_code_path: str, class_name: str) -> bool:
    """
    Verify that the generated code matches the schema requirements.
    Checks if the file exists and contains the expected fields.
    """
    schema = load_schema(schema_path)
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    if not Path(generated_code_path).exists():
        print(f"ERROR: Generated file not found: {generated_code_path}")
        return False
    
    with open(generated_code_path, 'r') as f:
        content = f.read()
    
    # Check for class definition
    if f'class {class_name}' not in content:
        print(f"ERROR: Class {class_name} not found in generated file.")
        return False
    
    # Check for all required fields
    missing_fields = []
    for field_name in properties.keys():
        if field_name not in content:
            missing_fields.append(field_name)
    
    if missing_fields:
        print(f"ERROR: Missing fields in generated code: {missing_fields}")
        return False
    
    print(f"Verification successful: {class_name} matches schema.")
    return True


def main(schema_path: str, output_path: str, class_name: str):
    """
    Main entry point to generate a model from a schema.
    """
    print(f"Loading schema from: {schema_path}")
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    
    print(f"Generating model: {class_name}")
    code = generate_model_class(schema, class_name)
    
    # Add header
    header = f'''"""
{class_name} model generated from {Path(schema_path).name} using pydantic.
DO NOT EDIT MANUALLY. Regenerate if schema changes.
"""
'''
    
    full_code = header + code
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(full_code)
    
    print(f"Generated file written to: {output_path}")
    
    # Verify
    if verify_generation(schema_path, output_path, class_name):
        print("Generation and verification complete.")
        return 0
    else:
        print("Generation failed verification.")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_models.py <schema_path> <output_path> <class_name>")
        sys.exit(1)
    
    schema = sys.argv[1]
    output = sys.argv[2]
    name = sys.argv[3]
    sys.exit(main(schema, output, name))
