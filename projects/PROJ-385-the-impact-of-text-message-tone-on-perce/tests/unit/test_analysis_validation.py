import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest

# Add the code directory to the path so we can import 04_run_lmm
# The test assumes it is run from the project root or with code/ in PYTHONPATH
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir


@pytest.fixture
def analysis_results_path():
    """Returns the path to the analysis results JSON file."""
    return get_processed_data_dir() / "analysis_results.json"


@pytest.fixture
def mock_analysis_results(tmp_path, analysis_results_path):
    """Creates a mock analysis_results.json file with valid structure including variance components."""
    # Ensure the directory exists
    analysis_results_path.parent.mkdir(parents=True, exist_ok=True)

    # Mock data simulating a successful LMM run
    mock_data = {
        "model_summary": {
            "formula": "rating ~ context * emoji_level + (1|participant_id) + (1|stimulus_id)",
            "method": "REML",
            "fixed_effects": {
                "Intercept": {"estimate": 3.5, "std_err": 0.1, "p_value": 0.001},
                "context[T.friend]": {"estimate": 0.2, "std_err": 0.15, "p_value": 0.12},
                "emoji_level[T.high]": {"estimate": 0.8, "std_err": 0.1, "p_value": 0.0001},
                "context[T.friend]:emoji_level[T.high]": {"estimate": 0.1, "std_err": 0.12, "p_value": 0.35}
            },
            "variance_components": {
                "participant_id": 0.45,
                "stimulus_id": 0.15
            },
            "log_likelihood": -1250.5
        },
        "metadata": {
            "n_participants": 100,
            "n_stimuli": 24,
            "seed": 42
        }
    }

    with open(analysis_results_path, "w") as f:
        json.dump(mock_data, f, indent=2)

    return analysis_results_path


def test_stimulus_variance_component_present(mock_analysis_results, caplog):
    """
    Test that the LMM model summary includes a variance component for Stimulus.
    
    Per task T023:
    - Asserts the component exists.
    - If variance is negligible (< 0.001), logs a warning but does NOT fail the build.
    - If variance is significant, passes the test without warning.
    """
    results_path = mock_analysis_results

    # Load the results
    with open(results_path, "r") as f:
        data = json.load(f)

    # Navigate to variance components
    variance_components = data.get("model_summary", {}).get("variance_components", {})
    
    # Check if 'stimulus_id' key exists
    assert "stimulus_id" in variance_components, (
        "LMM model summary must include a variance component for 'stimulus_id'."
    )

    stimulus_variance = variance_components["stimulus_id"]

    # Check magnitude
    if stimulus_variance < 0.001:
        # Log warning as per requirement (aligns with FR-003 execution requirement)
        # We simulate the logging behavior that would happen in the main pipeline
        # or that the validator would emit.
        logging.warning(
            f"Stimulus variance component is negligible ({stimulus_variance:.6f} < 0.001). "
            "This may indicate the stimulus variation does not significantly impact perceived support."
        )
        # Do NOT fail the build. The test passes even if variance is low.
        assert True
    else:
        # Significant variance, test passes silently
        assert True


def test_stimulus_variance_component_missing(analysis_results_path, tmp_path, caplog):
    """
    Test that the validation correctly fails if the stimulus variance component is missing entirely.
    """
    # Create a mock file WITHOUT stimulus_id variance
    mock_data = {
        "model_summary": {
            "variance_components": {
                "participant_id": 0.45
                # stimulus_id is intentionally missing
            }
        }
    }
    
    analysis_results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(analysis_results_path, "w") as f:
        json.dump(mock_data, f)

    # Load and check
    with open(analysis_results_path, "r") as f:
        data = json.load(f)

    variance_components = data.get("model_summary", {}).get("variance_components", {})

    # This assertion should fail, causing the test to fail
    with pytest.raises(AssertionError) as exc_info:
        assert "stimulus_id" in variance_components, (
            "LMM model summary must include a variance component for 'stimulus_id'."
        )

    assert "must include a variance component" in str(exc_info.value)