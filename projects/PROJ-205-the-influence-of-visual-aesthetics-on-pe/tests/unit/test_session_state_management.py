import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path to import survey.app
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from survey.app import init_session_state, save_submission, LATIN_SQUARE_SEQUENCES

class TestSessionStateManagement:
    """
    Tests for T020: Client-side state management.
    Verifies in-memory only tracking and state clearing.
    """

    @pytest.fixture(autouse=True)
    def setup_streamlit(self):
        """Mock Streamlit session state for testing."""
        # Reset session state before each test
        st.session_state.clear()
        yield
        st.session_state.clear()

    def test_init_session_state_in_memory_only(self):
        """
        Verify that init_session_state creates in-memory keys
        and does not attempt to use localStorage/sessionStorage.
        """
        init_session_state()
        
        # Verify keys exist in session_state (in-memory)
        assert 'user_id' in st.session_state
        assert 'current_sequence_index' in st.session_state
        assert 'selected_sequence' in st.session_state
        assert 'ratings' in st.session_state
        assert 'consent_given' in st.session_state
        assert 'demographics' in st.session_state

    def test_session_state_clear_on_submission(self):
        """
        Verify that save_submission clears all session state (T020).
        """
        # Setup initial state
        init_session_state()
        st.session_state.ratings = {
            "Professional": {"credibility": 5, "professionalism": 5},
            "Minimalist": {"credibility": 5, "professionalism": 5},
            "Low-Quality": {"credibility": 5, "professionalism": 5},
            "Neutral": {"credibility": 5, "professionalism": 5}
        }
        st.session_state.demographics = {"age": 25, "education": 2}
        st.session_state.selected_sequence = LATIN_SQUARE_SEQUENCES[0]
        st.session_state.current_sequence_index = 4 # Simulate all done

        # Mock dependencies to prevent actual file I/O during test
        with patch('survey.app.format_timestamp', return_value="2023-01-01T00:00:00"), \
             patch('survey.app.hash_ip', return_value="hashed_ip_test"), \
             patch('survey.app.truncate_user_agent', return_value="test_ua"), \
             patch('survey.app.validate_rating_count', return_value=True), \
             patch('survey.app.st.context.headers', {'X-Forwarded-For': '1.2.3.4', 'User-Agent': 'Test'}), \
             patch('pandas.DataFrame.to_csv'), \
             patch('pandas.read_csv', return_value=None), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.mkdir'):
            
            # Call save_submission
            save_submission()

            # Verify state was cleared (T020 requirement)
            # Note: In a real Streamlit app, st.rerun() might happen, but we check the state before that
            # Since we can't easily test the 'after rerun' state in a unit test without a full driver,
            # we verify the clear() logic was called by checking the state is empty or the clear method was invoked.
            # However, st.session_state.clear() modifies the dict.
            assert len(st.session_state) == 0, "Session state should be cleared after successful submission"

    def test_latin_square_sequences_hardcoded(self):
        """
        Verify that Latin Square sequences are hardcoded constants (T016a).
        """
        expected_sequences = [
            ["Professional", "Minimalist", "Low-Quality", "Neutral"],
            ["Minimalist", "Low-Quality", "Neutral", "Professional"],
            ["Low-Quality", "Neutral", "Professional", "Minimalist"],
            ["Neutral", "Professional", "Minimalist", "Low-Quality"]
        ]
        
        assert LATIN_SQUARE_SEQUENCES == expected_sequences
        assert len(LATIN_SQUARE_SEQUENCES) == 4
    
    def test_no_persistence_in_session_state(self):
        """
        Verify that session state does not contain forbidden storage mechanisms.
        This is a code inspection test to ensure no localStorage/sessionStorage calls.
        """
        # This test verifies the code logic doesn't import or use web storage APIs
        # Since we are running in a Python environment, we check that no such modules are imported
        import survey.app
        source = open(Path(survey.app.__file__).parent / "app.py").read()
        
        assert "sessionStorage" not in source, "Forbidden: sessionStorage usage detected"
        assert "localStorage" not in source, "Forbidden: localStorage usage detected"
        assert "cookie" not in source.lower(), "Forbidden: cookie usage detected for PII"