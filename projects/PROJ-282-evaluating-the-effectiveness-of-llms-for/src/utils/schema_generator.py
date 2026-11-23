"""
Schema Generator Utility.

This module provides utilities to generate Python dataclasses from JSON Schema/YAML contracts.
Ensures schema drift prevention by enforcing generation from contract files.
"""
import yaml
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import make_dataclass, field as dc_field
import datetime

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML or JSON schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")

def infer_python_type(type_def: Any, nullable: bool = False) -> str:
    """Infer Python type hint from JSON Schema type definition."""
    if isinstance(type_def, str):
        if type_def == "string":
            return "str"
        elif type_def == "integer":
            return "int"
        elif type_def == "number":
            return "float"
        elif type_def == "boolean":
            return "bool"
        elif type_def == "array":
            return "List[Any]"
        elif type_def == "object":
            return "Dict[str, Any]"
        elif type_def == "null":
            return "None"
    
    # Handle complex types
    if isinstance(type_def, dict):
        if "type" in type_def:
            base = infer_python_type(type_def["type"])
            if nullable or type_def.get("nullable", False):
                return f"Optional[{base}]"
            return base
        if "enum" in type_def:
            base = "str" # Default for enums
            if nullable:
                return "Optional[str]"
            return "str"
    
    return "Any"

def generate_dataclass_code(
    schema: Dict[str, Any], 
    class_name: str,
    source_contract: Optional[str] = None
) -> str:
    """
    Generate Python dataclass code from a JSON Schema.
    
    Args:
        schema: The loaded schema dictionary
        class_name: Name of the class to generate
        source_contract: Path to the source contract file for attribution
    
    Returns:
        String containing the generated Python code
    """
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    
    fields = []
    imports = ["from dataclasses import dataclass, field", "from typing import Optional, List, Dict, Any", "import uuid", "import json"]
    
    # Add docstring
    docstring = schema.get("description", f"Data class for {class_name}")
    
    code_lines = [
        '"""',
        f"{class_name} model generated from {source_contract or 'schema'}.",
        "",
        "This file is auto-generated to prevent schema drift.",
        f"Source: {source_contract or 'schema'}",
        '"""',
        "",
        "\n".join(imports),
        "",
        "@dataclass",
        f"class {class_name}:",
        f'    """',
        f"    {docstring}",
        "    ",
        "    Generated from: contracts/dataset.schema.yaml",
        "    Fields:",
    ]
    
    field_defs = []
    
    for prop_name, prop_def in properties.items():
        is_required = prop_name in required_fields
        prop_type = infer_python_type(prop_def, nullable=not is_required and prop_def.get("nullable", False))
        
        # Add field to docstring
        code_lines.append(f"        {prop_name}: {prop_type}")
        
        # Default value handling
        if not is_required:
            default_val = "None"
            field_defs.append((prop_name, prop_type, dc_field(default=None)))
        else:
            field_defs.append((prop_name, prop_type))
    
    code_lines.extend([
        "    \"\"\"",
        "",
    ])
    
    # Generate __init__ signature manually for dataclass decorator
    # The @dataclass decorator handles the __init__ based on field_defs
    # We construct the class body manually to ensure correct generation
    
    # Re-construct the class body with proper field definitions
    final_lines = [
        '"""',
        f"{class_name} model generated from {source_contract or 'schema'}.",
        "",
        "This file is auto-generated to prevent schema drift.",
        f"Source: {source_contract or 'schema'}",
        '"""',
        "",
        "\n".join(imports),
        "",
        "@dataclass",
        f"class {class_name}:",
        f'    """',
        f"    {docstring}",
        "    ",
        "    Generated from: contracts/dataset.schema.yaml",
        "    Fields:",
    ]
    
    for prop_name, prop_def in properties.items():
        is_required = prop_name in required_fields
        prop_type = infer_python_type(prop_def, nullable=not is_required and prop_def.get("nullable", False))
        final_lines.append(f"        {prop_name}: {prop_type}")
    
    final_lines.extend([
        "    \"\"\"",
    ])
    
    # Add field definitions
    for prop_name, prop_def in properties.items():
        is_required = prop_name in required_fields
        prop_type = infer_python_type(prop_def, nullable=not is_required and prop_def.get("nullable", False))
        
        if not is_required:
            final_lines.append(f"    {prop_name}: {prop_type} = None")
        else:
            final_lines.append(f"    {prop_name}: {prop_type}")
    
    # Add validation and helper methods
    final_lines.extend([
        "",
        "    def __post_init__(self):",
        "        \"\"\"Validate required fields and types.\"\"\"",
        "        # Basic validation can be added here if needed",
        "        pass",
        "",
        "    def to_dict(self) -> Dict[str, Any]:",
        "        \"\"\"Convert to dictionary representation.\"\"\"",
        "        return {",
        "            " + ",\n            ".join([f'"{k}": self.{k}' for k in properties.keys()]) + "",
        "        }",
        "",
        "    @classmethod",
        "    def from_dict(cls, data: Dict[str, Any]) -> \"{class_name}\":",
        "        \"\"\"Create instance from dictionary.\"\"\"",
        "        return cls(",
        "            " + ",\n            ".join([f'{k}=data.get("{k}")' for k in properties.keys()]) + "",
        "        )",
        "",
        "    def to_json(self) -> str:",
        "        \"\"\"Serialize to JSON string.\"\"\"",
        "        return json.dumps(self.to_dict())",
        "",
        "    @classmethod",
        "    def from_json(cls, json_str: str) -> \"{class_name}\":",
        "        \"\"\"Deserialize from JSON string.\"\"\"",
        "        return cls.from_dict(json.loads(json_str))",
        "",
        f"def create_{class_name.lower()}(",
    ])
    
    # Factory function signature
    factory_params = []
    for prop_name, prop_def in properties.items():
        is_required = prop_name in required_fields
        prop_type = infer_python_type(prop_def, nullable=not is_required and prop_def.get("nullable", False))
        default = " = None" if not is_required else ""
        factory_params.append(f"    {prop_name}: {prop_type}{default}")
    
    factory_params.append(f") -> {class_name}:")
    final_lines.append(",\n".join(factory_params))
    
    final_lines.extend([
        "    \"\"\"",
        f"    Factory function to create a {class_name} instance.",
        "",
        "    Args:",
        "        " + "\n        ".join([f"{k}: {properties[k].get('description', 'Value')}" for k in properties.keys()]),
        "",
        "    Returns:",
        f"        {class_name} instance",
        "    \"\"\"",
        "    return ",
        f"    {class_name}(",
        "        " + ",\n        ".join([f"{k}={k}" for k in properties.keys()]) + "",
        "    )",
        ""
    ])
    
    return "\n".join(final_lines)

def generate_model_from_schema(
    schema_path: str, 
    output_path: str,
    class_name: Optional[str] = None
) -> None:
    """
    Generate a Python model file from a schema file.
    
    Args:
        schema_path: Path to the YAML/JSON schema
        output_path: Path where the Python file will be written
        class_name: Optional override for the class name (defaults to schema title)
    """
    schema = load_schema(schema_path)
    title = class_name or schema.get("title", "Model")
    
    code = generate_dataclass_code(schema, title, source_contract=schema_path)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"Generated {output_path} from {schema_path}")

if __name__ == "__main__":
    # Example usage for T007b
    import sys
    if len(sys.argv) < 3:
        print("Usage: python schema_generator.py <schema_path> <output_path> [class_name]")
        sys.exit(1)
    
    schema_file = sys.argv[1]
    out_file = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    
    generate_model_from_schema(schema_file, out_file, name)
