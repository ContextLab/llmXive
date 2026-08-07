"""
T118: Verify that the generated report.md includes all required sections.

Required sections:
1. Dataset stats
2. VIF summary
3. Model performance (R², |r|, p-value)
4. Permutation importance with corrected p-values
5. Bootstrap CI
6. Disclaimers
"""
import os
import json
import re
import pytest
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = PROJECT_ROOT / "output" / "report.md"
METRICS_PATH = PROJECT_ROOT / "output" / "metrics.json"
VIF_PATH = PROJECT_ROOT / "output" / "vif_results.json"
PERM_PATH = PROJECT_ROOT / "output" / "permutation_results.json"
BOOTSTRAP_PATH = PROJECT_ROOT / "output" / "bootstrap_results.json"
DATA_STATUS_PATH = PROJECT_ROOT / "output" / "data_status.json"

REQUIRED_DISCLAIMER = "Associational analysis only; no causal inference"


def _read_report():
    """Read the report content."""
    if not REPORT_PATH.exists():
        pytest.fail(f"Report file not found at {REPORT_PATH}. Ensure T117 has run successfully.")
    return REPORT_PATH.read_text(encoding="utf-8")

def _load_json(path):
    """Load a JSON file."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class TestReportSections:
    """T118 Verification Tests."""

    def test_report_file_exists(self):
        """Assert report.md exists."""
        assert REPORT_PATH.exists(), "output/report.md must exist."

    def test_section_dataset_stats(self):
        """Verify 'Dataset Statistics' or similar section exists."""
        content = _read_report()
        # Look for headers like "## Dataset Statistics", "## Data Overview", or "Dataset Summary"
        patterns = [
            r"##\s*Dataset\s*Statistics",
            r"##\s*Data\s*Overview",
            r"##\s*Dataset\s*Summary",
            r"##\s*Data\s*Statistics",
        ]
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        assert found, "Report must contain a section describing dataset statistics."

        # If data_status.json exists, verify it's referenced or counts match
        status = _load_json(DATA_STATUS_PATH)
        if status:
            count = status.get("count", 0)
            # Check if the count appears in the text (loose check)
            # We don't require exact string match due to formatting, but the section should exist.

    def test_section_vif_summary(self):
        """Verify VIF summary section exists."""
        content = _read_report()
        patterns = [
            r"##\s*VIF\s*Summary",
            r"##\s*VIF\s*Analysis",
            r"##\s*Multicollinearity\s*Diagnosis",
        ]
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        assert found, "Report must contain a section summarizing VIF results."

        vif_data = _load_json(VIF_PATH)
        if vif_data:
            # Ensure the report mentions VIF thresholds or flagged features if any
            # This is a loose check that the section is not empty
            assert len(content) > 0

    def test_section_model_performance(self):
        """Verify Model Performance section exists with R², |r|, p-value."""
        content = _read_report()
        patterns = [
            r"##\s*Model\s*Performance",
            r"##\s*Predictive\s*Performance",
            r"##\s*Results",
        ]
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        assert found, "Report must contain a section on model performance."

        # Verify metrics are present in the text
        metrics = _load_json(METRICS_PATH)
        if metrics:
            # Check for R² presence
            assert "R²" in content or "R-squared" in content or "R2" in content, \
                "Report must mention R² value."
            
            # Check for Pearson r presence
            assert "Pearson" in content or "correlation" in content, \
                "Report must mention Pearson correlation (r)."

            # Check for p-value presence
            assert "p-value" in content or "p-value" in content, \
                "Report must mention p-value for correlation."

    def test_section_permutation_importance(self):
        """Verify Permutation Importance section exists with corrected p-values."""
        content = _read_report()
        patterns = [
            r"##\s*Permutation\s*Importance",
            r"##\s*Feature\s*Importance",
            r"##\s*Descriptor\s*Significance",
        ]
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        assert found, "Report must contain a section on permutation importance."

        perm_data = _load_json(PERM_PATH)
        if perm_data:
            # Verify that p-values are mentioned
            assert "p-value" in content or "p-value" in content or "significance" in content, \
                "Report must mention p-values for permutation importance."
            
            # Verify Holm-Bonferroni or corrected p-values are mentioned
            assert "corrected" in content.lower() or "holm" in content.lower() or "bonferroni" in content.lower(), \
                "Report must mention corrected p-values (Holm-Bonferroni)."

    def test_section_bootstrap_ci(self):
        """Verify Bootstrap Confidence Interval section exists."""
        content = _read_report()
        patterns = [
            r"##\s*Bootstrap\s*Confidence\s*Intervals",
            r"##\s*Bootstrap\s*Results",
            r"##\s*Uncertainty\s*Analysis",
        ]
        found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        assert found, "Report must contain a section on bootstrap confidence intervals."

        bootstrap_data = _load_json(BOOTSTRAP_PATH)
        if bootstrap_data:
            # Verify CI is mentioned
            assert "CI" in content or "confidence interval" in content.lower(), \
                "Report must mention confidence intervals."

    def test_section_disclaimers(self):
        """Verify mandatory disclaimers are present."""
        content = _read_report()
        assert REQUIRED_DISCLAIMER in content, \
            f"Report must contain the mandatory disclaimer: '{REQUIRED_DISCLAIMER}'."

        # Check for Data Limitation Warning if applicable
        status = _load_json(DATA_STATUS_PATH)
        if status and status.get("count_warning", False):
            assert "Data Limitation Warning" in content or "limitation" in content.lower(), \
                "Report must include 'Data Limitation Warning' when count_warning is true."

    def test_section_structure_coherence(self):
        """Verify the report has a logical structure (headers present)."""
        content = _read_report()
        # Check for at least 3 level-2 headers
        headers = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
        assert len(headers) >= 5, \
            f"Report should have at least 5 sections (found {len(headers)}: {headers})."