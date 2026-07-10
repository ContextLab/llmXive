"""
tests/unit/test_generator_orchestration.py
Unit tests for code/transform/generator.py orchestration logic.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock the sibling modules to isolate the generator logic
import sys
from types import ModuleType

# Create mock modules if they don't exist in sys.modules (for isolated testing)
mock_formatters = ModuleType('transform.formatters')
mock_black_formatter = ModuleType('transform.formatters.black_formatter')
mock_minified_formatter = ModuleType('transform.formatters.minified_formatter')
mock_renamer = ModuleType('transform.renamer')
mock_ast_renamer = ModuleType('transform.renamer.ast_renamer')
mock_stripper = ModuleType('transform.stripper')
mock_comment_stripper = ModuleType('transform.stripper.comment_stripper')
mock_seed_manager = ModuleType('transform.seed_manager')
mock_validator = ModuleType('transform.validator')

# Define simple pass-through mocks for the generator to use
def mock_black(code): return code + "_black"
def mock_minified(code): return code + "_minified"
def mock_rename(code): return code + "_renamed"
def mock_strip(code): return code + "_stripped"
def mock_validate(code): return True
def mock_log_seed(*args): pass
def mock_hash(*args): return "hash123"

mock_black_formatter.apply_black_format = mock_black
mock_black_formatter.main = lambda: None
mock_minified_formatter.apply_minified_format = mock_minified
mock_minified_formatter.main = lambda: None
mock_ast_renamer.apply_generic_naming = mock_rename
mock_ast_renamer.GenericRenamer = MagicMock
mock_ast_renamer.main = lambda: None
mock_comment_stripper.strip_comments_and_docstrings = mock_strip
mock_comment_stripper.CommentRemover = MagicMock
mock_comment_stripper.main = lambda: None
mock_seed_manager.log_transform_seed = mock_log_seed
mock_seed_manager.compute_mapping_hash = mock_hash
mock_seed_manager.get_seed_entry = lambda *args: {}
mock_seed_manager.verify_reproducibility = lambda *args: True
mock_seed_manager.main = lambda: None
mock_validator.validate_python_syntax = mock_validate
mock_validator.ValidationError = Exception
mock_validator.validate_code_variants = lambda *args: []
mock_validator.filter_valid_variants = lambda *args: []
mock_validator.validate_file = lambda *args: True
mock_validator.save_validation_results = lambda *args: None
mock_validator.main = lambda: None

sys.modules['transform'] = ModuleType('transform')
sys.modules['transform.formatters'] = mock_formatters
sys.modules['transform.formatters.black_formatter'] = mock_black_formatter
sys.modules['transform.formatters.minified_formatter'] = mock_minified_formatter
sys.modules['transform.renamer'] = mock_renamer
sys.modules['transform.renamer.ast_renamer'] = mock_ast_renamer
sys.modules['transform.stripper'] = mock_stripper
sys.modules['transform.stripper.comment_stripper'] = mock_comment_stripper
sys.modules['transform.seed_manager'] = mock_seed_manager
sys.modules['transform.validator'] = mock_validator

from transform.generator import generate_all_variants, _apply_transformations, _generate_variant_id

@pytest.fixture
def sample_functions():
    return [
        {
            "id": "func_001",
            "code": "def add(a, b):\n    return a + b\n# Comment"
        },
        {
            "id": "func_002",
            "code": "def mul(x, y):\n    return x * y"
        }
    ]

@pytest.fixture
def temp_input_file(sample_functions):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"functions": sample_functions}, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_apply_transformations_combinations():
    """Test that all 8 combinations of flags produce distinct suffixes."""
    base = "code"
    
    # 1. Black, Original, Present -> code_black
    res = _apply_transformations(base, True, False, False, False)
    assert res == "code_black"
    
    # 2. Black, Generic, Present -> code_renamed_black
    res = _apply_transformations(base, True, False, True, False)
    assert res == "code_renamed_black"
    
    # 3. Black, Original, Stripped -> code_stripped_black
    res = _apply_transformations(base, True, False, False, True)
    assert res == "code_stripped_black"
    
    # 4. Black, Generic, Stripped -> code_renamed_stripped_black
    res = _apply_transformations(base, True, False, True, True)
    assert res == "code_renamed_stripped_black"
    
    # 5. Minified, Original, Present -> code_minified
    res = _apply_transformations(base, False, True, False, False)
    assert res == "code_minified"
    
    # 6. Minified, Generic, Present -> code_renamed_minified
    res = _apply_transformations(base, False, True, True, False)
    assert res == "code_renamed_minified"
    
    # 7. Minified, Original, Stripped -> code_stripped_minified
    res = _apply_transformations(base, False, True, False, True)
    assert res == "code_stripped_minified"
    
    # 8. Minified, Generic, Stripped -> code_renamed_stripped_minified
    res = _apply_transformations(base, False, True, True, True)
    assert res == "code_renamed_stripped_minified"

def test_generate_variant_id_determinism():
    """Test that the same flags produce the same ID."""
    base = "func_001"
    flags = {"a": True, "b": False}
    id1 = _generate_variant_id(base, flags)
    id2 = _generate_variant_id(base, flags)
    assert id1 == id2
    
    # Different flags should produce different ID (high probability)
    flags_diff = {"a": True, "b": True}
    id3 = _generate_variant_id(base, flags_diff)
    assert id1 != id3

def test_generate_all_variants_creates_8_per_function(temp_input_file):
    """Test that 2 functions produce 16 variants (8 each)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "output.json")
        variants = generate_all_variants(temp_input_file, output_file)
        
        assert len(variants) == 16
        
        # Check flags for a subset
        parent_ids = set(v["parent_id"] for v in variants)
        assert "func_001" in parent_ids
        assert "func_002" in parent_ids
        
        # Check that semantic_opacity flag is set correctly
        opacity_variants = [v for v in variants if v["flags"]["is_semantic_opacity"]]
        assert len(opacity_variants) == 4 # 2 functions * 1 combination (generic+stripped) * 2 formats (black/minified)
        
        for v in opacity_variants:
            assert v["flags"]["is_generic_naming"]
            assert v["flags"]["is_stripped_comments"]
        
        # Check file was created
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data["count"] == 16
        assert "variants" in data

def test_generate_all_variants_handles_invalid_base():
    """Test that functions with invalid base code are skipped."""
    invalid_func = [{"id": "bad", "code": "def bad("}] # Syntax error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"functions": invalid_func}, f)
        temp_path = f.name
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "output.json")
            # Mock validate_python_syntax to return False
            with patch('transform.generator.validate_python_syntax', return_value=False):
                variants = generate_all_variants(temp_path, output_file)
                assert len(variants) == 0
    finally:
        os.unlink(temp_path)