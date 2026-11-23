import pytest
import json
from src.simulator.parser import (
    parse_caption_to_scene_description,
    parse_to_json,
    parse_to_dict,
    ParsedObject,
    ParsedRelationship,
    SceneDescription
)

def create_test_caption():
    """Helper to create a standard test caption."""
    return "A red car is parked next to a blue house with a green tree."

def test_parse_caption_to_scene_description_basic():
    """Test that a basic caption is parsed into a valid SceneDescription."""
    caption = create_test_caption()
    result = parse_caption_to_scene_description(caption)
    
    assert isinstance(result, SceneDescription)
    assert result.scene_id is not None
    assert result.timestamp is not None
    assert isinstance(result.objects, list)
    assert isinstance(result.relationships, list)
    assert result.metadata["mode"] == "perfect"
    assert "source_text" in result.metadata

def test_parse_caption_to_scene_description_structure():
    """Test that the parsed objects and relationships have correct structure."""
    caption = "A cat sits on a mat."
    result = parse_caption_to_scene_description(caption)
    
    # Check objects structure
    for obj in result.objects:
        assert "id" in obj
        assert "name" in obj
        assert "attributes" in obj
        assert "position" in obj
    
    # Check relationships structure
    for rel in result.relationships:
        assert "source_id" in rel
        assert "target_id" in rel
        assert "relation" in rel
        assert "confidence" in rel

def test_parse_to_json():
    """Test that parse_to_json returns a valid JSON string."""
    caption = create_test_caption()
    json_str = parse_to_json(caption)
    
    assert isinstance(json_str, str)
    # Should not raise an exception
    parsed = json.loads(json_str)
    assert "scene_id" in parsed
    assert "objects" in parsed
    assert "relationships" in parsed

def test_parse_to_dict():
    """Test that parse_to_dict returns a valid dictionary."""
    caption = create_test_caption()
    data = parse_to_dict(caption)
    
    assert isinstance(data, dict)
    assert "scene_id" in data
    assert "objects" in data
    assert "relationships" in data

def test_empty_caption_raises_error():
    """Test that an empty caption raises a ValueError."""
    with pytest.raises(ValueError):
        parse_caption_to_scene_description("")

    with pytest.raises(ValueError):
        parse_caption_to_scene_description("   ")

def test_deterministic_output():
    """Test that the same caption produces consistent structure (ignoring timestamps/IDs)."""
    caption = "A dog runs in the park."
    result1 = parse_caption_to_scene_description(caption)
    result2 = parse_caption_to_scene_description(caption)
    
    # The names and relations should be the same
    names1 = sorted([obj["name"] for obj in result1.objects])
    names2 = sorted([obj["name"] for obj in result2.objects])
    assert names1 == names2
    
    rels1 = sorted([(r["source_id"], r["target_id"], r["relation"]) for r in result1.relationships])
    rels2 = sorted([(r["source_id"], r["target_id"], r["relation"]) for r in result2.relationships])
    # Note: IDs might differ due to timestamp, but the structure (relation type) should be consistent
    # We check the relation types
    rel_types1 = sorted([r["relation"] for r in result1.relationships])
    rel_types2 = sorted([r["relation"] for r in result2.relationships])
    assert rel_types1 == rel_types2

def test_complex_caption_parsing():
    """Test parsing a more complex caption with multiple objects and relations."""
    caption = "A large elephant stands near a small bird under a tree."
    result = parse_caption_to_scene_description(caption)
    
    assert len(result.objects) > 0
    # Verify that objects are extracted
    obj_names = [obj["name"].lower() for obj in result.objects]
    assert any("elephant" in name for name in obj_names)
    assert any("bird" in name for name in obj_names)
    assert any("tree" in name for name in obj_names)

def test_scene_description_to_json_method():
    """Test the to_json method of SceneDescription."""
    caption = "Test object"
    result = parse_caption_to_scene_description(caption)
    json_str = result.to_json()
    
    parsed = json.loads(json_str)
    assert parsed["scene_id"] == result.scene_id
    assert len(parsed["objects"]) == len(result.objects)

def test_scene_description_to_dict_method():
    """Test the to_dict method of SceneDescription."""
    caption = "Test object"
    result = parse_caption_to_scene_description(caption)
    data = result.to_dict()
    
    assert data["scene_id"] == result.scene_id
    assert len(data["objects"]) == len(result.objects)