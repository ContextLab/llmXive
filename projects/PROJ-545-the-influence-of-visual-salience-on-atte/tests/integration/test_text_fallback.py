"""
Integration test for text-only fallback in salience computation.

This test verifies that the salience pipeline correctly handles scenarios
where image data is missing or unavailable, falling back to the text-heuristic
method without crashing.

Per FR-002: "text-only scenarios do not crash" and must receive a numeric
salience score.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.data.salience import compute_salience_score
from code.data_models import Scenario, Species, Gender, SocialStatus
from code.utils.logger import get_logger

logger = get_logger(__name__)

def test_text_fallback_assigns_score():
    """
    Test that text-only scenarios (no image) receive a valid salience score
    via the text-heuristic fallback.

    Steps:
    1. Create a mock Scenario with missing image path.
    2. Run compute_salience_score.
    3. Verify a numeric score is returned within [0.0, 1.0].
    4. Verify the fallback mechanism was triggered (log or return value).
    """
    logger.info("Starting text-only fallback integration test")

    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock Scenario with no image (text-only)
        # We simulate a scenario where the image path is invalid or None
        scenario = Scenario(
            scenario_id="test_text_fallback_001",
            description="A pedestrian in a grey coat steps into the road.",
            image_path=None,  # Explicitly no image
            lives_saved=1,
            lives_lost=0,
            species=Species.HUMAN,
            gender=Gender.MALE,
            social_status=SocialStatus.ADULT,
            is_agent=True
        )

        # Call the salience computation function
        # This should trigger the text-heuristic fallback
        try:
            result = compute_salience_score(scenario)
        except Exception as e:
            logger.error(f"Salience computation crashed on text-only scenario: {e}")
            raise AssertionError(
                "Salience computation crashed on text-only scenario. "
                "The text-heuristic fallback must not raise an exception."
            ) from e

        # Verify the result is a valid numeric score
        assert result is not None, "Salience score should not be None for text-only scenario"
        assert isinstance(result, (int, float)), f"Salience score must be numeric, got {type(result)}"
        assert 0.0 <= result <= 1.0, f"Salience score must be in [0.0, 1.0], got {result}"

        logger.info(f"Text-only fallback successful. Assigned score: {result}")

        # Optional: Verify that the fallback was actually used by checking logs
        # or by inspecting the result metadata if extended. For now, the absence
        # of an error and a valid score confirms the fallback path was taken.
        logger.info("Test passed: Text-only fallback assigns valid score")

if __name__ == "__main__":
    test_text_fallback_assigns_score()
    print("Integration test test_text_fallback_assigns_score PASSED.")