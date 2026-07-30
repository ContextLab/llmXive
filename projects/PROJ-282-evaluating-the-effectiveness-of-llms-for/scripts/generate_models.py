"""
Model Generation Script
Reads contracts/*.yaml and generates Pydantic models in src/models/.
This ensures schema drift is prevented by generating code from the contract.
"""
import os
import sys
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this script location (assuming scripts/ is at root)
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
MODELS_DIR = PROJECT_ROOT / "src" / "models"

def get_py_type(json_type: str, nullable: bool = False) -> str:
    """Map JSON Schema types to Python type hints."""
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "List",
        "object": "Dict",
    }
    base = type_map.get(json_type, "Any")
    if nullable:
        return f"Optional[{base}]"
    return base

def generate_model_class(schema_data: Dict[str, Any], class_name: str) -> str:
    """Generate Pydantic model code from schema dict."""
    lines = [
        '"""',
        f"{class_name} Model",
        "Generated from contracts/*.yaml.",
        "Uses Pydantic to ensure strict adherence to the contract.",
        '"""',
        "from pydantic import BaseModel, Field, field_validator",
        "from typing import Optional, List, Dict, Any",
        "import uuid",
        "import json",
        "from pathlib import Path",
        "",
        "",
        f"class {class_name}(BaseModel):",
        f'    """',
        f"    Pydantic model representing a {class_name}.",
        "    Fields are strictly typed and validated against the contract.",
        f'    """',
    ]

    properties = schema_data.get("properties", {})
    required_fields = set(schema_data.get("required", []))

    for field_name, field_def in properties.items():
        field_type = field_def.get("type", "string")
        is_nullable = field_def.get("nullable", False)
        description = field_def.get("description", "")
        
        # Handle Optional for nullable fields
        if field_name not in required_fields or is_nullable:
            py_type = get_py_type(field_type, nullable=True)
            default_val = "Field(None, ...)"
        else:
            py_type = get_py_type(field_type, nullable=False)
            default_val = "Field(...)"

        # Escape quotes in description
        safe_desc = description.replace('"', '\\"')
        
        lines.append(f'    {field_name}: {py_type} = {default_val}, description="{safe_desc}"')

    # Add standard methods
    lines.extend([
        "",
        "    def to_dict(self) -> dict:",
        "        \"\"\"Convert model to dictionary.\"\"\"",
        "        return self.model_dump()",
        "",
        "    def to_json(self, indent: int = 2) -> str:",
        "        \"\"\"Convert model to JSON string.\"\"\"",
        "        return self.model_dump_json(indent=indent)",
        "",
        "    @classmethod",
        "    def from_dict(cls, data: dict) -> 'CodeSnippet':",
        "        \"\"\"Create instance from dictionary.\"\"\"",
        "        return cls(**data)",
        "",
        "    @classmethod",
        "    def from_json(cls, json_str: str) -> 'CodeSnippet':",
        "        \"\"\"Create instance from JSON string.\"\"\"",
        "        return cls.model_validate_json(json_str)",
        "",
    ])

    return "\n".join(lines)

def generate_factory(class_name: str, schema_data: Dict[str, Any]) -> str:
    """Generate factory function."""
    properties = schema_data.get("properties", {})
    required_fields = schema_data.get("required", [])
    
    params = []
    for field_name in required_fields:
        field_def = properties[field_name]
        py_type = get_py_type(field_def.get("type", "string"))
        params.append(f"{field_name}: {py_type}")
    
    # Add optional params
    for field_name, field_def in properties.items():
        if field_name not in required_fields:
            py_type = get_py_type(field_def.get("type", "string"))
            params.append(f"{field_name}: Optional[{py_type}] = None")

    params_str = ", ".join(params)
    
    lines = [
        "",
        f"def create_{class_name.lower()}",
        f"({params_str})",
        f") -> {class_name}:",
        f'    """',
        f"    Factory function to create a {class_name}.",
        f'    """',
        "    ",
    ]
    
    # Generate return statement
    arg_assignments = []
    for field_name in properties.keys():
        arg_assignments.append(f"        {field_name}={field_name},")
    
    lines.append(f"    return {class_name}(")
    lines.extend(arg_assignments)
    lines.append("    )")
    lines.append("")
    
    return "\n".join(lines)

def main():
    if not CONTRACTS_DIR.exists():
        print(f"Error: Contracts directory not found at {CONTRACTS_DIR}")
        sys.exit(1)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for schema_file in CONTRACTS_DIR.glob("*.schema.yaml"):
        print(f"Processing {schema_file.name}...")
        
        with open(schema_file, 'r') as f:
            schema_data = yaml.safe_load(f)
        
        # Extract class name from title or filename
        class_name = schema_data.get("title", schema_file.stem.replace("_", "").title())
        
        # Generate code
        model_code = generate_model_class(schema_data, class_name)
        factory_code = generate_factory(class_name, schema_data)
        
        full_code = f"{model_code}\n{factory_code}"
        
        # Write to file
        output_file = MODELS_DIR / f"{class_name.lower()}.py"
        with open(output_file, 'w') as f:
            f.write(full_code)
        
        print(f"Generated {output_file}")

if __name__ == "__main__":
    main()
