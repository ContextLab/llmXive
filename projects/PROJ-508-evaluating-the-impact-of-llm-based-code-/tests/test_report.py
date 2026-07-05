"""
Tests for report text generation and associational framing.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the function under test from the sibling module
try:
    from report_analysis import write_results
except ImportError:
    # Fallback for local execution if the module structure differs
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    from report_analysis import write_results


def test_report_text_uses_associational_framing():
    """
    Verify that the generated report text frames findings as 'associational'
    and explicitly references the observational study design, avoiding causal
    language like 'caused' or 'led to'.
    """
    # Mock analysis results
    mock_results = {
        "models": [
            {
                "proxy": "iteration_count",
                "coefficient": 0.15,
                "se": 0.04,
                "p_value": 0.001,
                "adj_p_value": 0.005,
                "ci_lower": 0.07,
                "ci_upper": 0.23,
                "model_type": "GLMM"
            }
        ],
        "sensitivity_analysis": {
            "thresholds": [1, 2, 3],
            "effect_sizes": [0.14, 0.15, 0.16]
        },
        "vif_flags": {},
        "methodology_notes": [
            "Mixed-Effects Models used with random intercepts.",
            "Bonferroni correction applied."
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "analysis_results.json"
        output_path = Path(tmpdir) / "final_report.md"

        # Write mock results
        with open(input_path, "w") as f:
            json.dump(mock_results, f)

        # Run the report generation
        write_results(str(input_path), str(output_path))

        # Read the generated report
        assert output_path.exists(), "Report file was not generated."
        with open(output_path, "r") as f:
            report_text = f.read()

        # Assert associational framing
        assert "associational" in report_text.lower(), (
            "Report must frame findings as 'associational'."
        )
        assert "observational study" in report_text.lower(), (
            "Report must reference 'observational study' design."
        )
        
        # Assert absence of causal language (basic check)
        # Note: A more robust NLP check could be added, but string presence is a strong signal
        assert "caused by" not in report_text.lower(), (
            "Report must not claim causation."
        )
        assert "led to" not in report_text.lower(), (
            "Report must not claim causation."
        )

        # Assert null hypothesis status is mentioned
        assert "null hypothesis" in report_text.lower(), (
            "Report must state null hypothesis rejection status."
        )


def test_report_includes_theoretical_grounding_section():
    """
    Verify that the report includes the 'Theoretical Grounding' section
    citing Holland et al. on distributed cognition (per FR-009 / T005).
    """
    mock_results = {
        "models": [],
        "sensitivity_analysis": {},
        "vif_flags": {},
        "methodology_notes": []
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "analysis_results.json"
        output_path = Path(tmpdir) / "final_report.md"

        with open(input_path, "w") as f:
            json.dump(mock_results, f)

        write_results(str(input_path), str(output_path))

        with open(output_path, "r") as f:
            report_text = f.read()

        # Assert presence of Holland citation
        assert "Holland" in report_text, (
            "Report must cite Holland et al. in the Theoretical Grounding section."
        )
        assert "distributed cognition" in report_text.lower(), (
            "Report must mention 'distributed cognition'."
        )


def test_report_includes_data_gap_section():
    """
    Verify that the report includes the 'Data Gap' section explicitly stating
    the unavailability of self-report scales (per FR-009 / T005).
    """
    mock_results = {
        "models": [],
        "sensitivity_analysis": {},
        "vif_flags": {},
        "methodology_notes": []
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "analysis_results.json"
        output_path = Path(tmpdir) / "final_report.md"

        with open(input_path, "w") as f:
            json.dump(mock_results, f)

        write_results(str(input_path), str(output_path))

        with open(output_path, "r") as f:
            report_text = f.read()

        # Assert presence of Data Gap section and NASA-TLX mention
        assert "Data Gap" in report_text or "data gap" in report_text, (
            "Report must include a 'Data Gap' section."
        )
        assert "NASA-TLX" in report_text, (
            "Report must mention NASA-TLX as unavailable."
        )
        assert "proxy metrics" in report_text.lower(), (
            "Report must state that proxy metrics are used."
        )


def test_report_includes_exact_nasa_tlx_warning():
    """
    Verify that the report contains the exact required warning string:
    'Note: This study uses proxy metrics for cognitive load. Self-report 
    measures (e.g., NASA-TLX) were not available.'
    """
    mock_results = {
        "models": [],
        "sensitivity_analysis": {},
        "vif_flags": {},
        "methodology_notes": []
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "analysis_results.json"
        output_path = Path(tmpdir) / "final_report.md"

        with open(input_path, "w") as f:
            json.dump(mock_results, f)

        write_results(str(input_path), str(output_path))

        with open(output_path, "r") as f:
            report_text = f.read()

    expected_warning = "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."
    
    # Check if the exact string is present
    if expected_warning not in report_text:
        # Fallback: check for the key components if exact match fails due to minor formatting
        parts = [
            "This study uses proxy metrics for cognitive load",
            "Self-report measures",
            "NASA-TLX",
            "were not available"
        ]
        missing_parts = [p for p in parts if p not in report_text]
        if missing_parts:
            pytest.fail(f"Report is missing required warning components: {missing_parts}")
        # If parts are there but not the exact string, it might be a formatting issue, 
        # but for this test we strictly require the sentence structure or exact match.
        # Given the strict requirement, we fail if the exact string isn't found.
        pytest.fail(f"Report does not contain the exact required warning string: '{expected_warning}'")


def test_report_frames_findings_as_associational_not_causal():
    """
    Specific check to ensure the report avoids causal verbs in the context 
    of LLM adoption impact.
    """
    mock_results = {
        "models": [
            {
                "proxy": "iteration_count",
                "coefficient": 0.15,
                "se": 0.04,
                "p_value": 0.001,
                "adj_p_value": 0.005,
                "ci_lower": 0.07,
                "ci_upper": 0.23,
                "model_type": "GLMM"
            }
        ],
        "sensitivity_analysis": {},
        "vif_flags": {},
        "methodology_notes": []
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "analysis_results.json"
        output_path = Path(tmpdir) / "final_report.md"

        with open(input_path, "w") as f:
            json.dump(mock_results, f)

        write_results(str(input_path), str(output_path))

        with open(output_path, "r") as f:
            report_text = f.read()

        # Check for common causal pitfalls
        forbidden_phrases = [
            "LLM adoption caused",
            "caused by LLM adoption",
            "LLM adoption led to",
            "resulted in LLM adoption",
            "LLM adoption increases", # 'increases' can be causal, 'is associated with increases' is better
            "LLM adoption decreases"
        ]
        
        # We allow "associated with" or "correlated with"
        allowed_phrases = [
            "associated with",
            "correlated with",
            "linked to",
            "relationship between"
        ]

        # Simple check: if a forbidden phrase appears without the allowed context
        # This is a heuristic check.
        for phrase in forbidden_phrases:
            if phrase in report_text:
                # Check if it's in a context that mitigates causality (e.g., "did not cause")
                # For this test, we assume the report generator is smart enough to avoid
                # these unless explicitly testing for the negative.
                # We fail if the phrase appears in a positive assertion.
                pytest.fail(f"Report contains potentially causal phrasing: '{phrase}'")

        # Ensure at least one allowed phrase exists to confirm associational tone
        has_associational_tone = any(phrase in report_text for phrase in allowed_phrases)
        assert has_associational_tone, (
            "Report must use associational language (e.g., 'associated with')."
        )