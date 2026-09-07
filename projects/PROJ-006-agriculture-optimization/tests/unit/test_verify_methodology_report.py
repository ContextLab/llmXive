"""
Unit tests for scripts/verify_methodology_report.py
"""
import sys
import tempfile
import os
from pathlib import Path
import pytest

# Add parent directory to path to import the script logic if needed,
# though we are testing the script's behavior via subprocess or direct logic
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.verify_methodology_report import (
    check_ols_contrast,
    check_uncertainty_logic,
    check_disclaimer_requirements
)

class TestOlsContrast:
    def test_positive_match_robust_se(self):
        content = "We use robust standard errors (HC3) which differs from standard OLS."
        assert check_ols_contrast(content) is True

    def test_positive_match_hc3(self):
        content = "The model employs HC3 robust standard errors."
        assert check_ols_contrast(content) is True

    def test_positive_match_contrast(self):
        content = "This approach is a contrast with standard OLS assumptions."
        assert check_ols_contrast(content) is True

    def test_negative_match_no_contrast(self):
        content = "We run a standard regression on the data."
        assert check_ols_contrast(content) is False

class TestUncertaintyLogic:
    def test_positive_match_confidence_interval(self):
        content = "The uncertainty visualization includes 95% confidence intervals."
        assert check_uncertainty_logic(content) is True

    def test_positive_match_sensitivity_plot(self):
        content = "Figure 3 shows the sensitivity plot of coefficient variation."
        assert check_uncertainty_logic(content) is True

    def test_negative_match_no_uncertainty(self):
        content = "The results are presented in a table."
        assert check_uncertainty_logic(content) is False

class TestDisclaimerRequirements:
    def test_positive_match_associational(self):
        content = "The report includes a disclaimer on the associational nature of the findings."
        assert check_disclaimer_requirements(content) is True

    def test_positive_match_not_causal(self):
        content = "We explicitly state that correlation does not imply causation."
        assert check_disclaimer_requirements(content) is True

    def test_negative_match_no_disclaimer(self):
        content = "The study proves that CSA practices cause higher yields."
        assert check_disclaimer_requirements(content) is False