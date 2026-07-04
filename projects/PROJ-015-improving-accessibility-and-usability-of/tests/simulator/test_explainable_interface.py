"""
Unit tests for the ExplainableInterface renderer.

Tests verify:
1. Correct initialization
2. Rule-based overlay generation
3. Input validation
4. Output structure integrity
"""
import pytest
import json
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.simulator.interfaces.explainable import ExplainableInterface, XAIOverlay, ExplainableInterfaceState


class TestExplainableInterfaceInit:
    """Test initialization of ExplainableInterface."""

    def test_init_default_seed(self):
        """Test initialization with default seed."""
        interface = ExplainableInterface()
        assert interface.seed is not None
        assert interface.generator is not None

    def test_init_custom_seed(self):
        """Test initialization with custom seed."""
        interface = ExplainableInterface(seed=12345)
        assert interface.seed == 12345

class TestOverlayGeneration:
    """Test XAI overlay generation rules."""

    def test_text_explanation_always_present(self):
        """Text explanation should always be generated."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        
        overlay_types = [o["type"] for o in result["overlays"]]
        assert "text" in overlay_types

    def test_heatmap_only_for_difficult_tasks(self):
        """Heatmap should only appear for difficulty >= 0.3."""
        interface = ExplainableInterface(seed=42)
        
        # Low difficulty - no heatmap
        result_low = interface.render_task("s1", "t1", 0.2, 0.8)
        overlay_types_low = [o["type"] for o in result_low["overlays"]]
        assert "heatmap" not in overlay_types_low

        # Medium difficulty - heatmap present
        result_med = interface.render_task("s1", "t1", 0.5, 0.8)
        overlay_types_med = [o["type"] for o in result_med["overlays"]]
        assert "heatmap" in overlay_types_med

    def test_confidence_bar_always_present(self):
        """Confidence bar should always be generated."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        
        overlay_types = [o["type"] for o in result["overlays"]]
        assert "bar" in overlay_types

    def test_opacity_calculation(self):
        """Test that opacity increases with difficulty and decreases with confidence."""
        interface = ExplainableInterface(seed=42)
        
        # Low difficulty, high confidence -> low opacity
        result1 = interface.render_task("s1", "t1", 0.1, 0.9)
        heatmap1 = next(o for o in result1["overlays"] if o["type"] == "heatmap")
        
        # High difficulty, low confidence -> high opacity
        result2 = interface.render_task("s1", "t1", 0.9, 0.1)
        heatmap2 = next(o for o in result2["overlays"] if o["type"] == "heatmap")
        
        assert heatmap1["opacity"] < heatmap2["opacity"]

class TestInputValidation:
    """Test input validation."""

    def test_invalid_difficulty_low(self):
        """Should raise ValueError for difficulty < 0.0."""
        interface = ExplainableInterface(seed=42)
        with pytest.raises(ValueError):
            interface.render_task("s1", "t1", -0.1, 0.5)

    def test_invalid_difficulty_high(self):
        """Should raise ValueError for difficulty > 1.0."""
        interface = ExplainableInterface(seed=42)
        with pytest.raises(ValueError):
            interface.render_task("s1", "t1", 1.1, 0.5)

    def test_invalid_confidence_low(self):
        """Should raise ValueError for confidence < 0.0."""
        interface = ExplainableInterface(seed=42)
        with pytest.raises(ValueError):
            interface.render_task("s1", "t1", 0.5, -0.1)

    def test_invalid_confidence_high(self):
        """Should raise ValueError for confidence > 1.0."""
        interface = ExplainableInterface(seed=42)
        with pytest.raises(ValueError):
            interface.render_task("s1", "t1", 0.5, 1.1)

class TestOutputStructure:
    """Test output structure integrity."""

    def test_required_fields_present(self):
        """All required fields should be present in output."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        
        required_fields = [
            "session_id", "task_id", "interface_type", 
            "overlays", "base_task_difficulty", 
            "model_confidence", "explanation_generated"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_interface_type_correct(self):
        """Interface type should be 'explainable'."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        assert result["interface_type"] == "explainable"

    def test_explanation_generated_flag(self):
        """Explanation generated flag should be True."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        assert result["explanation_generated"] is True

    def test_overlay_structure(self):
        """Each overlay should have required fields."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        
        required_overlay_fields = [
            "element_id", "type", "position", "size", 
            "opacity", "color", "label", "value", 
            "confidence", "rule_applied"
        ]
        
        for overlay in result["overlays"]:
            for field in required_overlay_fields:
                assert field in overlay, f"Missing field in overlay: {field}"

    def test_overlay_values_within_bounds(self):
        """Overlay values should be within expected bounds."""
        interface = ExplainableInterface(seed=42)
        result = interface.render_task("s1", "t1", 0.5, 0.5)
        
        for overlay in result["overlays"]:
            assert 0.0 <= overlay["opacity"] <= 1.0
            assert 0.0 <= overlay["value"] <= 1.0
            assert 0.0 <= overlay["confidence"] <= 1.0
            assert 0.0 <= overlay["position"][0] <= 1.0
            assert 0.0 <= overlay["position"][1] <= 1.0

class TestMetadata:
    """Test metadata generation."""

    def test_metadata_structure(self):
        """Metadata should have expected structure."""
        interface = ExplainableInterface(seed=42)
        metadata = interface.get_interface_metadata()
        
        assert "interface_type" in metadata
        assert metadata["interface_type"] == "explainable"
        assert "version" in metadata
        assert "xai_rules" in metadata
        assert "overlay_types" in metadata

if __name__ == "__main__":
    pytest.main([__file__, "-v"])