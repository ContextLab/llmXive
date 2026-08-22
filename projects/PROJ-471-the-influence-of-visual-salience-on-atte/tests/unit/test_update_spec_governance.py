"""
Unit tests for code/scr/update_spec_governance.py (Task T020c).

These tests verify that the script correctly:
1. Removes FR-008 blocks.
2. Updates User Story 2 text to reflect the exclusion of weapons.
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path to import the function
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.scr.update_spec_governance import remove_fr_008, update_user_story_2

class TestRemoveFR008:
    def test_remove_fr_008_basic(self):
        """Test basic removal of FR-008 line."""
        input_text = """
        ## Functional Requirements
        - [ ] FR-007 Correlational only
        - [ ] FR-008 [US1] **Data**: Generate salience maps for "Weapons" ROI.
        - [ ] FR-009 [US2] **Data**: Calculate VIF.
        """
        expected = """
        ## Functional Requirements
        - [ ] FR-007 Correlational only
        - [ ] FR-009 [US2] **Data**: Calculate VIF.
        """
        result = remove_fr_008(input_text)
        # Normalize whitespace for comparison
        assert result.strip() == expected.strip()

    def test_remove_fr_008_with_indented_description(self):
        """Test removal of FR-008 with indented description lines."""
        input_text = """
        - [ ] FR-008 [US1] **Data**: Generate salience maps for "Weapons" ROI.
            This requirement is for the weapons dataset.
            It involves YOLO detection.
        - [ ] FR-009 Next requirement.
        """
        result = remove_fr_008(input_text)
        assert "FR-008" not in result
        assert "Weapons" not in result
        assert "FR-009" in result
        # Ensure the next requirement is intact
        assert "Next requirement" in result

    def test_no_fr_008(self):
        """Test that text without FR-008 remains unchanged."""
        input_text = "Some text without FR-008."
        result = remove_fr_008(input_text)
        assert result == input_text

class TestUpdateUserStory2:
    def test_update_us2_remove_weapons(self):
        """Test updating US-2 to remove weapons references."""
        input_text = """
        ## User Story 2: Attention Metric Extraction
        Goal: Parse eye-tracking data for Face and Weapons ROIs.
        """
        result = update_user_story_2(input_text)
        assert "Weapons" not in result
        assert "Face" in result
        assert "excluded" in result.lower() or "Face" in result

    def test_update_us2_no_weapons_mentioned(self):
        """Test that US-2 without weapons mention is not altered significantly."""
        input_text = """
        ## User Story 2: Attention Metric Extraction
        Goal: Parse eye-tracking data for Face ROIs.
        """
        result = update_user_story_2(input_text)
        # Should remain mostly the same, maybe with a note added if logic dictates, 
        # but definitely not crash or remove valid content.
        assert "Face" in result
        assert "US" in result or "User Story" in result

    def test_us2_not_found(self):
        """Test behavior when US-2 section is missing."""
        input_text = "No User Story 2 here."
        result = update_user_story_2(input_text)
        assert result == input_text