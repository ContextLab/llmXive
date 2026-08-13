"""
Contract test for vignette text integrity (no framing leakage).

This test verifies that the three metaphorical vignette conditions (Battle, Journey, Medical)
maintain distinct metaphorical framing while keeping clinical details constant.

It ensures:
1. Each condition contains its specific metaphor keywords.
2. Each condition does NOT contain keywords from other conditions (no leakage).
3. Clinical details (symptoms, duration, impact) are present in all conditions.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vignette_engine import generate_vignettes


class TestVignetteIntegrity:
    """Contract tests for vignette text integrity."""

    @pytest.fixture
    def vignettes(self):
        """Generate the three vignette conditions."""
        return generate_vignettes()

    def test_all_conditions_present(self, vignettes):
        """Verify all three metaphorical conditions are generated."""
        assert "battle" in vignettes, "Battle condition missing"
        assert "journey" in vignettes, "Journey condition missing"
        assert "medical" in vignettes, "Medical condition missing"
        assert len(vignettes) == 3, "Expected exactly 3 vignette conditions"

    def test_battle_condition_has_battle_metaphors(self, vignettes):
        """Verify Battle condition contains battle-specific metaphor keywords."""
        text = vignettes["battle"].lower()
        battle_keywords = ["battle", "fight", "war", "enemy", "struggle", "defeat", "army", "soldier"]
        
        found_keywords = [kw for kw in battle_keywords if kw in text]
        assert len(found_keywords) >= 3, (
            f"Battle condition must contain at least 3 battle metaphors. "
            f"Found: {found_keywords}"
        )

    def test_journey_condition_has_journey_metaphors(self, vignettes):
        """Verify Journey condition contains journey-specific metaphor keywords."""
        text = vignettes["journey"].lower()
        journey_keywords = ["journey", "path", "road", "step", "direction", "destination", "travel", "navigate"]
        
        found_keywords = [kw for kw in journey_keywords if kw in text]
        assert len(found_keywords) >= 3, (
            f"Journey condition must contain at least 3 journey metaphors. "
            f"Found: {found_keywords}"
        )

    def test_medical_condition_has_medical_metaphors(self, vignettes):
        """Verify Medical condition contains medical-specific metaphor keywords."""
        text = vignettes["medical"].lower()
        medical_keywords = ["treatment", "therapy", "diagnosis", "symptom", "clinical", "medical", "prescription", "intervention"]
        
        found_keywords = [kw for kw in medical_keywords if kw in text]
        assert len(found_keywords) >= 3, (
            f"Medical condition must contain at least 3 medical metaphors. "
            f"Found: {found_keywords}"
        )

    def test_no_battle_keywords_in_journey(self, vignettes):
        """Verify Journey condition does NOT contain battle-specific keywords (no leakage)."""
        text = vignettes["journey"].lower()
        battle_keywords = ["battle", "fight", "war", "enemy", "defeat", "army", "soldier"]
        
        found_keywords = [kw for kw in battle_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Journey condition must NOT contain battle keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_no_battle_keywords_in_medical(self, vignettes):
        """Verify Medical condition does NOT contain battle-specific keywords (no leakage)."""
        text = vignettes["medical"].lower()
        battle_keywords = ["battle", "fight", "war", "enemy", "defeat", "army", "soldier"]
        
        found_keywords = [kw for kw in battle_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Medical condition must NOT contain battle keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_no_journey_keywords_in_battle(self, vignettes):
        """Verify Battle condition does NOT contain journey-specific keywords (no leakage)."""
        text = vignettes["battle"].lower()
        journey_keywords = ["journey", "path", "road", "destination", "travel", "navigate"]
        
        found_keywords = [kw for kw in journey_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Battle condition must NOT contain journey keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_no_journey_keywords_in_medical(self, vignettes):
        """Verify Medical condition does NOT contain journey-specific keywords (no leakage)."""
        text = vignettes["medical"].lower()
        journey_keywords = ["journey", "path", "road", "destination", "travel", "navigate"]
        
        found_keywords = [kw for kw in journey_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Medical condition must NOT contain journey keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_no_medical_keywords_in_battle(self, vignettes):
        """Verify Battle condition does NOT contain medical-specific keywords (no leakage)."""
        text = vignettes["battle"].lower()
        medical_keywords = ["treatment", "therapy", "diagnosis", "symptom", "clinical", "prescription"]
        
        found_keywords = [kw for kw in medical_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Battle condition must NOT contain medical keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_no_medical_keywords_in_journey(self, vignettes):
        """Verify Journey condition does NOT contain medical-specific keywords (no leakage)."""
        text = vignettes["journey"].lower()
        medical_keywords = ["treatment", "therapy", "diagnosis", "symptom", "clinical", "prescription"]
        
        found_keywords = [kw for kw in medical_keywords if kw in text]
        assert len(found_keywords) == 0, (
            f"Journey condition must NOT contain medical keywords (framing leakage detected). "
            f"Found: {found_keywords}"
        )

    def test_clinical_details_consistent_across_conditions(self, vignettes):
        """Verify that core clinical details are present in all conditions."""
        clinical_details = [
            "depression", "anxiety", "sleep", "difficulty", "two years", 
            "work", "relationships", "isolated", "hopeless"
        ]
        
        for condition, text in vignettes.items():
            text_lower = text.lower()
            found_details = [detail for detail in clinical_details if detail in text_lower]
            assert len(found_details) >= 5, (
                f"{condition.capitalize()} condition must contain at least 5 clinical details. "
                f"Found: {found_details}"
            )

    def test_vignette_texts_are_non_empty(self, vignettes):
        """Verify all vignette texts are non-empty strings."""
        for condition, text in vignettes.items():
            assert isinstance(text, str), f"{condition} vignette must be a string"
            assert len(text.strip()) > 0, f"{condition} vignette must not be empty"

    def test_vignette_lengths_are_reasonable(self, vignettes):
        """Verify vignette texts are of reasonable length (not too short or too long)."""
        min_length = 100  # Minimum characters
        max_length = 2000  # Maximum characters
        
        for condition, text in vignettes.items():
            assert min_length <= len(text) <= max_length, (
                f"{condition} vignette length ({len(text)}) is outside acceptable range "
                f"[{min_length}, {max_length}]"
            )
