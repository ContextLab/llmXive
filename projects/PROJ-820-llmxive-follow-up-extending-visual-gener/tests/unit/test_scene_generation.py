"""
Unit tests for scene description generation logic.
"""
import pytest
import csv
import sys
from pathlib import Path
from io import StringIO

# Add parent directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.create_scene_descriptions import (
    generate_fallback_scenes,
    validate_prepositions,
    INTERACTION_TEMPLATES
)

class TestSceneGeneration:
    def test_deterministic_generation(self):
        """Test that generation is deterministic with the same seed."""
        scenes1 = generate_fallback_scenes(seed=42, count=10)
        scenes2 = generate_fallback_scenes(seed=42, count=10)
        
        assert scenes1 == scenes2, "Generation should be deterministic with same seed"

    def test_non_deterministic_different_seeds(self):
        """Test that different seeds produce different results."""
        scenes1 = generate_fallback_scenes(seed=42, count=10)
        scenes2 = generate_fallback_scenes(seed=123, count=10)
        
        assert scenes1 != scenes2, "Different seeds should produce different results"

    def test_correct_count(self):
        """Test that the correct number of scenes is generated."""
        count = 50
        scenes = generate_fallback_scenes(seed=42, count=count)
        assert len(scenes) == count, f"Expected {count} scenes, got {len(scenes)}"

    def test_unique_ids(self):
        """Test that all scene IDs are unique."""
        scenes = generate_fallback_scenes(seed=42, count=100)
        ids = [s["scene_id"] for s in scenes]
        assert len(ids) == len(set(ids)), "All scene IDs should be unique"

    def test_required_prepositions_present(self):
        """Test that all required prepositions are present in the generated set."""
        # Generate a larger set to ensure all templates are hit
        scenes = generate_fallback_scenes(seed=42, count=1000)
        assert validate_prepositions(scenes), "All required prepositions should be present"

    def test_invalid_prepositions_detection(self):
        """Test that missing prepositions are detected."""
        # Create a list of scenes missing a specific preposition
        bad_scenes = [
            {"scene_id": "1", "description": "A on B"},
            {"scene_id": "2", "description": "A next to B"},
            # Missing "under", "above", etc.
        ]
        # This should fail because we don't have all prepositions
        # However, the validation function checks against a specific set.
        # Let's just verify the function returns False if data is too sparse
        # to cover all prepositions.
        result = validate_prepositions(bad_scenes)
        # Since we only have 2 templates, it's guaranteed to miss others
        assert result == False, "Validation should fail for incomplete preposition set"

    def test_csv_structure(self):
        """Test that the generated CSV has the correct structure."""
        scenes = generate_fallback_scenes(seed=42, count=5)
        
        # Simulate writing to a string buffer
        output = StringIO()
        fieldnames = ["scene_id", "description"]
        
        import csv
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scenes)
        
        output.seek(0)
        reader = csv.DictReader(output)
        rows = list(reader)
        
        assert len(rows) == 5
        for row in rows:
            assert "scene_id" in row
            assert "description" in row
            assert row["description"] != ""
            assert row["scene_id"].startswith("scene_")