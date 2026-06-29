"""Contract test for collinearity_report.txt format validation."""
import json
import pytest
from pathlib import Path


@pytest.fixture
def schema_path():
    return Path(__file__).parent / "../../contracts/collinearity_report_schema.json"


@pytest.fixture
def sample_collinearity_report(tmp_path):
    """Create a valid sample collinearity_report.txt for testing."""
    report = """
COLLINEARITY DIAGNOSTICS REPORT
Generated: 2024-01-15T10:30:00Z
Correlation Threshold: 0.8

HIGH COLLINEARITY PAIRS (|r| > 0.8)
====================================
Predictor 1          Predictor 2          Pearson r    VIF (p1)    VIF (p2)
--------------------------------------------------------------------------------
mean_degree          std_degree           0.85         3.2         2.8

VIF SUMMARY
===========
Predictor          VIF
mean_degree        3.2
std_degree         2.8
clustering_coeff   1.1
susceptibility_score 1.0

RECOMMENDATIONS
===============
1. DROP: mean_degree (VIF > 3, high correlation with std_degree)
   Rationale: Remove one of the correlated pair to reduce multicollinearity

2. KEEP: clustering_coeff, susceptibility_score (VIF < 5)
   Rationale: No significant collinearity issues

SUMMARY
=======
Total Predictors: 4
High Collinearity Pairs: 1
Max VIF: 3.2
Mean VIF: 1.78
"""
    txt_path = tmp_path / "collinearity_report.txt"
    txt_path.write_text(report.strip())
    return txt_path


def test_collinearity_report_schema_loads(schema_path):
    """Test that the collinearity report schema file loads correctly."""
    with open(schema_path) as f:
        schema = json.load(f)
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "collinearity" in schema["title"].lower()


def test_collinearity_report_has_header(sample_collinearity_report):
    """Test that collinearity_report.txt contains required header sections."""
    content = sample_collinearity_report.read_text()
    required_sections = [
        "COLLINEARITY DIAGNOSTICS REPORT",
        "Generated:",
        "Correlation Threshold:",
        "HIGH COLLINEARITY PAIRS",
        "VIF SUMMARY",
        "RECOMMENDATIONS",
        "SUMMARY"
    ]
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"


def test_collinearity_report_has_threshold(sample_collinearity_report):
    """Test that report specifies the correlation threshold."""
    content = sample_collinearity_report.read_text()
    assert "0.8" in content, "Report should specify |r| > 0.8 threshold"


def test_collinearity_report_has_vif_values(sample_collinearity_report):
    """Test that report includes VIF values for predictors."""
    content = sample_collinearity_report.read_text()
    assert "VIF" in content, "Report should include VIF values"