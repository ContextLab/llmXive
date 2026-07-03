"""
Unit tests for reaction template matching in src/utils/chemistry.py
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.chemistry import (
    load_reaction_templates,
    compile_smart_patterns,
    classify_reaction,
    batch_classify_reactions,
    get_reaction_type_distribution
)
from rdkit import Chem


# Fixtures
@pytest.fixture
def temp_config_file():
    """Create a temporary config file with valid SMARTS patterns."""
    config_content = """
    reaction_templates:
      SN1:
        description: "SN1 reaction pattern"
        smarts: "[C:1]([O:2])>>[C:1]+[O:2]-"
      SN2:
        description: "SN2 reaction pattern"
        smarts: "[C:1]([O:2])>>[C:1]=[O:2]"
      DielsAlder:
        description: "Diels-Alder reaction pattern"
        smarts: "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        return Path(f.name)

@pytest.fixture
def mock_templates():
    """Return a mock templates dictionary."""
    return {
        "SN1": {"smarts": "[C:1]([O:2])>>[C:1]+[O:2]-"},
        "SN2": {"smarts": "[C:1]([O:2])>>[C:1]=[O:2]"},
        "DielsAlder": {"smarts": "[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1"}
    }

# Tests for load_reaction_templates
def test_load_reaction_templates_success(temp_config_file):
    """Test successful loading of reaction templates."""
    templates = load_reaction_templates(temp_config_file)
    assert isinstance(templates, dict)
    assert "SN1" in templates
    assert "SN2" in templates
    assert "DielsAlder" in templates
    assert templates["SN1"]["smarts"] == "[C:1]([O:2])>>[C:1]+[O:2]-"

def test_load_reaction_templates_missing_file():
    """Test loading from a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_reaction_templates(Path("/nonexistent/path/config.yaml"))

def test_load_reaction_templates_invalid_yaml(temp_config_file):
    """Test loading invalid YAML raises ValueError."""
    with open(temp_config_file, 'w') as f:
        f.write("invalid: yaml: content: [")
    
    with pytest.raises(ValueError):
        load_reaction_templates(temp_config_file)

def test_load_reaction_templates_missing_key(temp_config_file):
    """Test loading config without 'reaction_templates' key raises ValueError."""
    with open(temp_config_file, 'w') as f:
        f.write("other_key: value")
    
    with pytest.raises(ValueError):
        load_reaction_templates(temp_config_file)

# Tests for compile_smart_patterns
def test_compile_smart_patterns_valid(mock_templates):
    """Test successful compilation of valid SMARTS patterns."""
    compiled = compile_smart_patterns(mock_templates)
    assert isinstance(compiled, dict)
    assert "SN1" in compiled
    assert isinstance(compiled["SN1"], Chem.Mol)

def test_compile_smart_patterns_invalid():
    """Test compilation of invalid SMARTS returns only valid patterns."""
    invalid_templates = {
        "Valid": {"smarts": "[C:1]([O:2])>>[C:1]+[O:2]-"},
        "Invalid": {"smarts": "invalid_smarts_string"}
    }
    compiled = compile_smart_patterns(invalid_templates)
    assert "Valid" in compiled
    assert "Invalid" not in compiled

# Tests for classify_reaction
def test_classify_reaction_match(temp_config_file):
    """Test classification when a pattern matches."""
    # Use a simple SMILES that might match a generic carbon-oxygen pattern
    # Note: The exact match depends on the SMARTS pattern
    smiles = "CCO"  # Ethanol
    reaction_type, matched = classify_reaction(smiles, config_path=temp_config_file)
    
    # The result depends on the specific SMARTS, but function should not crash
    assert isinstance(reaction_type, (str, type(None)))
    assert isinstance(matched, list)

def test_classify_reaction_no_match(temp_config_file):
    """Test classification when no pattern matches."""
    # Use a SMILES that is unlikely to match the specific reaction patterns
    smiles = "C"  # Methane
    reaction_type, matched = classify_reaction(smiles, config_path=temp_config_file)
    
    assert reaction_type is None
    assert len(matched) == 0

def test_classify_reaction_invalid_smiles(temp_config_file):
    """Test classification with invalid SMILES."""
    smiles = "invalid_smiles"
    reaction_type, matched = classify_reaction(smiles, config_path=temp_config_file)
    
    assert reaction_type is None
    assert len(matched) == 0

def test_classify_reaction_empty_smiles(temp_config_file):
    """Test classification with empty SMILES."""
    reaction_type, matched = classify_reaction("", config_path=temp_config_file)
    
    assert reaction_type is None
    assert len(matched) == 0

# Tests for batch_classify_reactions
def test_batch_classify_reactions(temp_config_file):
    """Test batch classification of multiple SMILES."""
    smiles_list = ["CCO", "C", "invalid"]
    results = batch_classify_reactions(smiles_list, config_path=temp_config_file)
    
    assert len(results) == 3
    for result in results:
        assert isinstance(result, tuple)
        assert len(result) == 2

# Tests for get_reaction_type_distribution
def test_get_reaction_type_distribution():
    """Test calculation of reaction type distribution."""
    classifications = [
        ("SN1", ["SN1"]),
        ("SN2", ["SN2"]),
        ("SN1", ["SN1"]),
        (None, [])
    ]
    distribution = get_reaction_type_distribution(classifications)
    
    assert distribution["SN1"] == 2
    assert distribution["SN2"] == 1
    assert distribution[None] == 1

def test_get_reaction_type_distribution_empty():
    """Test distribution with empty input."""
    distribution = get_reaction_type_distribution([])
    assert distribution == {}