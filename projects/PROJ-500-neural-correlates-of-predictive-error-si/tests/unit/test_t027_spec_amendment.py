import os
import json
import pytest
from pathlib import Path

# Path to the specs directory relative to the project root
SPECS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-neural-correlates-tactile-learning"

class TestT027SpecAmendment:
    """
    Test that the Spec Amendment Task (T027a) has correctly updated
    spec.md, data-model.md, and research.md with the required deviations:
    1. FR-006 updated to "Gaussian LME".
    2. FR-005 and US2 updated to reflect "Lagged Alignment" (50-trial window).
    3. Exclusion of underpowered subjects documented.
    """

    def test_fr_006_gaussian_lme(self):
        """Verify FR-006 in spec.md mentions Gaussian LME."""
        spec_path = SPECS_DIR / "spec.md"
        assert spec_path.exists(), "spec.md does not exist"
        
        content = spec_path.read_text()
        assert "Gaussian" in content, "FR-006 should mention Gaussian LME"
        assert "Linear Mixed-Effects" in content or "LME" in content, "FR-006 should mention LME"
        # Specific check for the formula or description
        assert "Gaussian Linear Mixed-Effects Model" in content or "Gaussian LME" in content

    def test_fr_005_lagged_alignment(self):
        """Verify FR-005 in spec.md mentions Lagged Alignment and 50-trial window."""
        spec_path = SPECS_DIR / "spec.md"
        assert spec_path.exists(), "spec.md does not exist"
        
        content = spec_path.read_text()
        assert "Lagged Alignment" in content, "FR-005 should mention Lagged Alignment"
        assert "50-trial" in content or "50 trial" in content, "FR-005 should mention 50-trial window"

    def test_underpowered_exclusion_in_spec(self):
        """Verify spec.md mentions exclusion of underpowered subjects."""
        spec_path = SPECS_DIR / "spec.md"
        assert spec_path.exists(), "spec.md does not exist"
        
        content = spec_path.read_text()
        assert "underpowered" in content.lower(), "Spec should mention underpowered subjects exclusion"
        assert "exclud" in content.lower(), "Spec should mention exclusion logic"

    def test_data_model_lagged_fields(self):
        """Verify data-model.md includes Lagged Alignment fields."""
        model_path = SPECS_DIR / "data-model.md"
        assert model_path.exists(), "data-model.md does not exist"
        
        content = model_path.read_text()
        assert "source_window_start_trial" in content, "Data model should include source_window_start_trial"
        assert "Lagged Alignment" in content, "Data model should document Lagged Alignment"

    def test_research_deviations(self):
        """Verify research.md documents the methodological corrections."""
        research_path = SPECS_DIR / "research.md"
        assert research_path.exists(), "research.md does not exist"
        
        content = research_path.read_text()
        assert "Gaussian" in content, "Research plan should mention Gaussian LME"
        assert "Lagged Alignment" in content, "Research plan should mention Lagged Alignment"
        assert "Deviations" in content or "Methodological Correction" in content, "Research plan should have a section on deviations"
        assert "underpowered" in content.lower(), "Research plan should document underpowered subject exclusion"