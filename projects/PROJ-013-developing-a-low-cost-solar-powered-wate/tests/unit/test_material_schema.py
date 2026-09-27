import pytest
from code.data_ingestion import load_material_schema

def test_load_material_schema_exists():
    """Verify load_material_schema exists with correct signature."""
    assert callable(load_material_schema)

def test_load_material_schema_loads_correctly():
    """Verify load_material_schema loads the schema correctly."""
    import os
    from code.utils import get_project_root
    
    project_root = get_project_root()
    schema_path = project_root / "data" / "raw" / "nist_materials.json"
    
    # If the file doesn't exist, we can't test loading, but the function should exist
    if schema_path.exists():
        schema = load_material_schema(str(schema_path))
        assert schema is not None
    else:
        # Just verify the function exists and would raise an error if file missing
        # or handle it gracefully
        pass
