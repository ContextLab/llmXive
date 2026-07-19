import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils import get_logger
import code_03_analysis as analysis

logger = get_logger(__name__)

class TestAlphaJustification:
    """Unit tests for alpha threshold justification generation."""

    def test_justification_file_exists(self, tmp_path):
        """Test that the justification file is created."""
        output_path = tmp_path / "alpha_threshold_justification.md"
        analysis.generate_alpha_justification(str(output_path))
        
        assert os.path.exists(output_path), "Justification file was not created"
        
    def test_justification_word_count(self, tmp_path):
        """Test that the justification meets minimum word count."""
        output_path = tmp_path / "alpha_threshold_justification.md"
        analysis.generate_alpha_justification(str(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        word_count = len(content.split())
        assert word_count >= 150, f"Justification too short: {word_count} words (min 150)"
        
    def test_justification_contains_citation(self, tmp_path):
        """Test that the justification contains the required citation."""
        output_path = tmp_path / "alpha_threshold_justification.md"
        analysis.generate_alpha_justification(str(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_citation = "Wilkinson, L., & Task Force on Statistical Inference. (1999)"
        assert required_citation in content, f"Required citation not found in justification"
        
    def test_justification_contains_sections(self, tmp_path):
        """Test that the justification contains all required sections."""
        output_path = tmp_path / "alpha_threshold_justification.md"
        analysis.generate_alpha_justification(str(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_sections = [
            "Introduction to the p-value Concept",
            "The 0.05 Threshold as a Community Standard",
            "Citation and Authority",
            "Conclusion"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"
            
    def test_associational_framing_content(self):
        """Test the associational framing text generation."""
        framing = analysis.generate_associational_framing()
        
        assert "associational" in framing.lower(), "Framing should mention 'associational'"
        assert "causal" in framing.lower(), "Framing should mention 'causal'"
        assert "No Causal Claims" in framing, "Framing should explicitly state no causal claims"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])