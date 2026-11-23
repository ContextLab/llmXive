import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.survey.app import validate_all_rated
import streamlit as st

class TestValidationLogic:
    """Test the validation logic for T019."""

    def setup_method(self):
        """Setup test environment."""
        # Initialize minimal session state
        if 'ratings' not in st.session_state:
            st.session_state.ratings = {}

    def teardown_method(self):
        """Cleanup after test."""
        st.session_state.ratings = {}

    def test_validation_fails_with_zero_ratings(self):
        """Test that validation fails when no ratings are present."""
        st.session_state.ratings = {}
        assert validate_all_rated() is False

    def test_validation_fails_with_one_rating(self):
        """Test that validation fails when only one rating is present."""
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 4}
        }
        assert validate_all_rated() is False

    def test_validation_fails_with_two_ratings(self):
        """Test that validation fails when only two ratings are present."""
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 4},
            "Minimalist": {"credibility": 3, "professionalism": 3}
        }
        assert validate_all_rated() is False

    def test_validation_fails_with_three_ratings(self):
        """Test that validation fails when only three ratings are present."""
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 4},
            "Minimalist": {"credibility": 3, "professionalism": 3},
            "Low-Quality": {"credibility": 2, "professionalism": 2}
        }
        assert validate_all_rated() is False

    def test_validation_passes_with_four_ratings(self):
        """Test that validation passes when all four ratings are present."""
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 4},
            "Minimalist": {"credibility": 3, "professionalism": 3},
            "Low-Quality": {"credibility": 2, "professionalism": 2},
            "Neutral": {"credibility": 4, "professionalism": 4}
        }
        assert validate_all_rated() is True

    def test_validation_fails_with_missing_condition(self):
        """Test that validation fails if a specific condition is missing."""
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 4},
            "Minimalist": {"credibility": 3, "professionalism": 3},
            "Neutral": {"credibility": 4, "professionalism": 4}
            # Low-Quality is missing
        }
        assert validate_all_rated() is False