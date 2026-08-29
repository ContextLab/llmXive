"""
Unit tests for axis semantic overlap constraints.

This test file is written first (TDD) and depends on:
- T010a/T010b: Schema definitions for Coarse and Fine axes
- T011: Implementation of the axis_generator service

These tests will FAIL until the implementation is complete, which is expected.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from typing import Dict, List, Any

# Import the validation functions from the service
# These will fail to import if T011 is not implemented yet
try:
    from src.services.axis_generator import validate_axes_semantic_overlap
    from src.cli.axis_input import calculate_lexical_overlap, calculate_semantic_similarity
    AXIS_VALIDATION_AVAILABLE = True
except ImportError:
    AXIS_VALIDATION_AVAILABLE = False

# Sample test data representing valid and invalid axis pairs
VALID_COARSE_AXIS = {
    "character": "Harry Potter",
    "axis_name": "Moral Courage",
    "description": "The character's willingness to stand up for what is right despite personal risk, showing bravery in the face of danger and injustice."
}

VALID_FINE_AXIS = {
    "character": "Harry Potter",
    "axis_name": "Protective Instinct",
    "description": "The character's specific tendency to shield friends and loved ones from harm, often putting their own safety at risk to defend others.",
    "source_observation": "Repeatedly risks himself to protect Ron and Hermione from various threats throughout the series."
}

INVALID_OVERLAP_COARSE = {
    "character": "Harry Potter",
    "axis_name": "Bravery",
    "description": "The character shows bravery and courage in dangerous situations."
}

INVALID_OVERLAP_FINE = {
    "character": "Harry Potter",
    "axis_name": "Courage",
    "description": "The character demonstrates courage and bravery when facing threats.",
    "source_observation": "Shows bravery in the face of danger."
}

@pytest.mark.skipif(not AXIS_VALIDATION_AVAILABLE, reason="Axis validation service not yet implemented (T011)")
class TestLexicalOverlap:
    """Test lexical overlap calculation between axis descriptions."""
    
    def test_low_lexical_overlap(self):
        """Test that semantically distinct descriptions have low lexical overlap."""
        coarse = "The character shows moral courage and stands up for justice."
        fine = "The character protects friends from harm at personal risk."
        
        overlap = calculate_lexical_overlap(coarse, fine)
        
        # Should be below the 0.4 threshold
        assert overlap < 0.4, f"Lexical overlap {overlap} should be below 0.4 for distinct axes"
    
    def test_high_lexical_overlap(self):
        """Test that similar descriptions have high lexical overlap."""
        coarse = "The character shows bravery and courage in dangerous situations."
        fine = "The character demonstrates courage and bravery when facing threats."
        
        overlap = calculate_lexical_overlap(coarse, fine)
        
        # Should be above the 0.4 threshold (indicating invalid overlap)
        assert overlap >= 0.4, f"Lexical overlap {overlap} should be >= 0.4 for similar axes"
    
    def test_empty_strings(self):
        """Test lexical overlap with empty strings."""
        overlap = calculate_lexical_overlap("", "")
        assert overlap == 0.0
    
    def test_case_insensitivity(self):
        """Test that lexical overlap is case-insensitive."""
        coarse = "BRAVERY and courage"
        fine = "bravery and COURAGE"
        
        overlap1 = calculate_lexical_overlap(coarse, fine)
        overlap2 = calculate_lexical_overlap(coarse.lower(), fine.lower())
        
        assert overlap1 == overlap2

@pytest.mark.skipif(not AXIS_VALIDATION_AVAILABLE, reason="Axis validation service not yet implemented (T011)")
class TestSemanticSimilarity:
    """Test semantic similarity calculation using sentence embeddings."""
    
    def test_low_semantic_similarity(self):
        """Test that semantically distinct descriptions have low cosine similarity."""
        coarse = "The character shows moral courage and stands up for justice."
        fine = "The character protects friends from harm at personal risk."
        
        similarity = calculate_semantic_similarity(coarse, fine)
        
        # Should be below the 0.3 threshold (meaning cosine distance > 0.7)
        assert similarity < 0.3, f"Semantic similarity {similarity} should be below 0.3 for distinct axes"
    
    def test_high_semantic_similarity(self):
        """Test that semantically similar descriptions have high cosine similarity."""
        coarse = "The character shows bravery and courage in dangerous situations."
        fine = "The character demonstrates courage and bravery when facing threats."
        
        similarity = calculate_semantic_similarity(coarse, fine)
        
        # Should be above the 0.3 threshold (indicating invalid similarity)
        assert similarity >= 0.3, f"Semantic similarity {similarity} should be >= 0.3 for similar axes"
    
    def test_identical_strings(self):
        """Test that identical strings have perfect similarity."""
        text = "The character shows bravery."
        similarity = calculate_semantic_similarity(text, text)
        assert abs(similarity - 1.0) < 0.01

@pytest.mark.skipif(not AXIS_VALIDATION_AVAILABLE, reason="Axis validation service not yet implemented (T011)")
class TestValidationLogic:
    """Test the overall validation logic for axis independence."""
    
    def test_valid_independent_axes(self):
        """Test that valid independent axes pass validation."""
        coarse_desc = VALID_COARSE_AXIS["description"]
        fine_desc = VALID_FINE_AXIS["description"]
        
        is_valid, reasons = validate_axes_semantic_overlap(
            VALID_COARSE_AXIS, 
            VALID_FINE_AXIS
        )
        
        assert is_valid is True, f"Valid axes should pass validation. Reasons: {reasons}"
        assert len(reasons) == 0 or all("fail" not in r.lower() for r in reasons)
    
    def test_invalid_high_lexical_overlap(self):
        """Test that axes with high lexical overlap fail validation."""
        is_valid, reasons = validate_axes_semantic_overlap(
            INVALID_OVERLAP_COARSE,
            INVALID_OVERLAP_FINE
        )
        
        assert is_valid is False, "Axes with high lexical overlap should fail validation"
        assert any("lexical" in r.lower() for r in reasons), "Should report lexical overlap failure"
    
    def test_invalid_high_semantic_similarity(self):
        """Test that axes with high semantic similarity fail validation."""
        # Create axes that are semantically very similar
        similar_coarse = {
            "character": "Test",
            "axis_name": "Bravery",
            "description": "The character shows great bravery and courage."
        }
        similar_fine = {
            "character": "Test",
            "axis_name": "Courage",
            "description": "The character demonstrates courage and bravery.",
            "source_observation": "Shows bravery."
        }
        
        is_valid, reasons = validate_axes_semantic_overlap(similar_coarse, similar_fine)
        
        # Should fail due to semantic similarity
        assert is_valid is False, "Axes with high semantic similarity should fail validation"
    
    def test_character_mismatch(self):
        """Test that axes for different characters are rejected."""
        different_coarse = VALID_COARSE_AXIS.copy()
        different_fine = VALID_FINE_AXIS.copy()
        different_fine["character"] = "Different Character"
        
        is_valid, reasons = validate_axes_semantic_overlap(different_coarse, different_fine)
        
        assert is_valid is False, "Axes for different characters should fail validation"
        assert any("character" in r.lower() for r in reasons), "Should report character mismatch"
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        incomplete_coarse = {"character": "Test"}  # Missing axis_name and description
        
        is_valid, reasons = validate_axes_semantic_overlap(incomplete_coarse, VALID_FINE_AXIS)
        
        assert is_valid is False, "Axes with missing fields should fail validation"
        assert any("field" in r.lower() or "missing" in r.lower() for r in reasons)

@pytest.mark.skipif(not AXIS_VALIDATION_AVAILABLE, reason="Axis validation service not yet implemented (T011)")
class TestValidationThresholds:
    """Test that validation uses the correct thresholds."""
    
    def test_lexical_threshold_boundary(self):
        """Test validation at the lexical overlap boundary (0.4)."""
        # Create texts that would result in exactly ~0.4 overlap
        # This is a boundary test
        coarse = "The character shows bravery and courage in the face of danger."
        fine = "The character shows bravery and courage when facing threats."
        
        is_valid, reasons = validate_axes_semantic_overlap(
            {"character": "Test", "axis_name": "A", "description": coarse},
            {"character": "Test", "axis_name": "B", "description": fine, "source_observation": "Obs"}
        )
        
        # Should fail because overlap >= 0.4
        assert is_valid is False, "Axes at lexical threshold should fail"
    
    def test_semantic_threshold_boundary(self):
        """Test validation at the semantic similarity boundary (0.3)."""
        # Create texts that would result in exactly ~0.3 similarity
        coarse = "The character demonstrates moral fortitude and ethical strength."
        fine = "The character shows moral strength and ethical fortitude."
        
        is_valid, reasons = validate_axes_semantic_overlap(
            {"character": "Test", "axis_name": "A", "description": coarse},
            {"character": "Test", "axis_name": "B", "description": fine, "source_observation": "Obs"}
        )
        
        # Should fail because similarity >= 0.3
        assert is_valid is False, "Axes at semantic threshold should fail"