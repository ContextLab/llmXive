import os
import re
import pytest

def test_sensitivity_report_exists():
    """Test that the sensitivity report file is generated."""
    assert os.path.exists('output/sensitivity_report.md'), "Sensitivity report not found"

def test_sensitivity_report_no_causal_language():
    """Test that the sensitivity report does not contain causal language."""
    if not os.path.exists('output/sensitivity_report.md'):
        pytest.skip("Sensitivity report not generated yet")
    
    with open('output/sensitivity_report.md', 'r') as f:
        content = f.read()
    
    # Check for forbidden causal keywords
    causal_pattern = r'\b(causes|effect|impact|driven by|leads to|triggers|causal inference)\b'
    matches = re.findall(causal_pattern, content, re.IGNORECASE)
    
    assert len(matches) == 0, f"Causal language detected in report: {matches}"

def test_sensitivity_report_frame_of_reference():
    """Test that the report explicitly states the frame of reference."""
    if not os.path.exists('output/sensitivity_report.md'):
        pytest.skip("Sensitivity report not generated yet")
    
    with open('output/sensitivity_report.md', 'r') as f:
        content = f.read()
    
    required_phrases = [
        "satellite altitude",
        "coordinate artifact",
        "perturbation in gravitational potential",
        "associational"
    ]
    
    for phrase in required_phrases:
        assert phrase.lower() in content.lower(), f"Missing required phrase: '{phrase}'"