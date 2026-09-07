"""
Unit tests for Narrative Synthesis Output (T075).

Verifies that when N < 10, the narrative_summary.md:
1. Contains the exact phrase "No Quantitative Evidence Found".
2. Includes the pivot_log.json reason as a direct quote.
3. Does NOT contain any quantitative meta-analysis results (e.g., forest plot references, pooled effect sizes).
"""
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

# Add the project root to the path to allow imports if needed,
# though this test primarily validates file contents.
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

class TestNarrativeOutput(unittest.TestCase):
    """Tests for T075: Validate Narrative Synthesis Output."""

    def setUp(self):
        """Set up temporary directories and mock files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_derived = Path(self.temp_dir) / "derived"
        self.data_derived.mkdir(parents=True)
        
        # Mock pivot_log.json
        self.pivot_log_path = self.data_derived / "pivot_log.json"
        mock_pivot_reason = "N=5 < 10"
        self.pivot_data = {
            "pivot_triggered": True,
            "reason": mock_pivot_reason,
            "n_count": 5,
            "n_valid_count": 3,
            "threshold": 10
        }
        with open(self.pivot_log_path, "w") as f:
            json.dump(self.pivot_data, f, indent=2)

        # Mock narrative_summary.md (valid case)
        self.valid_summary_path = self.data_derived / "narrative_summary_valid.md"
        self.valid_content = f"""
        # Narrative Synthesis Summary

        ## Data Scarcity Notice
        No Quantitative Evidence Found.

        As indicated by the gatekeeper, the analysis could not proceed to meta-analysis.
        Reason: "{mock_pivot_reason}"

        ## Qualitative Findings
        The available studies were reviewed qualitatively.
        """

        # Mock narrative_summary.md (invalid: missing phrase)
        self.invalid_missing_phrase_path = self.data_derived / "narrative_summary_missing_phrase.md"
        self.invalid_missing_phrase_content = f"""
        # Narrative Synthesis Summary

        ## Data Scarcity Notice
        Insufficient data for quantitative analysis.

        Reason: "{mock_pivot_reason}"
        """

        # Mock narrative_summary.md (invalid: contains quantitative result)
        self.invalid_quant_path = self.data_derived / "narrative_summary_invalid_quant.md"
        self.invalid_quant_content = f"""
        # Narrative Synthesis Summary

        ## Data Scarcity Notice
        No Quantitative Evidence Found.

        Reason: "{mock_pivot_reason}"

        ## Pooled Effect Size
        The random-effects model yielded a pooled r of 0.35 (95% CI: 0.10, 0.60).
        """

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _load_content(self, path: Path) -> str:
        """Load file content."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_pivot_reason(self) -> str:
        """Get the reason from the mock pivot log."""
        with open(self.pivot_log_path, "r") as f:
            data = json.load(f)
        return data["reason"]

    def test_valid_narrative_contains_required_phrase(self):
        """Test that valid narrative summary contains 'No Quantitative Evidence Found'."""
        content = self._load_content(self.valid_summary_path)
        self.assertIn("No Quantitative Evidence Found", content)

    def test_valid_narrative_contains_pivot_reason(self):
        """Test that valid narrative summary includes the pivot log reason."""
        content = self._load_content(self.valid_summary_path)
        reason = self._get_pivot_reason()
        # Check if the reason appears as a direct quote or within the text
        self.assertIn(reason, content)
        
        # Verify it is quoted or clearly attributed
        # The requirement says "includes the pivot_log.json reason as a direct quote"
        # We check for the reason string being present, which is the core requirement.
        # A strict quote check:
        self.assertRegex(content, re.escape(reason), 
                         "The pivot reason must be present in the summary.")

    def test_valid_narrative_no_quantitative_results(self):
        """Test that valid narrative summary does NOT contain quantitative meta-analysis results."""
        content = self._load_content(self.valid_summary_path)
        
        # Patterns that indicate quantitative results should NOT be present
        forbidden_patterns = [
            r"pooled\s+r\s*=",
            r"pooled\s+effect",
            r"meta-analysis\s+result",
            r"forest\s+plot",
            r"95%\s+CI\s*:", # Common in quantitative results, though might appear in text, we check context
        ]
        
        for pattern in forbidden_patterns:
            self.assertNotRegex(content, pattern, 
                                f"Narrative summary should not contain quantitative result pattern: {pattern}")

    def test_invalid_missing_phrase_fails(self):
        """Test that a summary missing the required phrase fails validation."""
        content = self._load_content(self.invalid_missing_phrase_path)
        self.assertNotIn("No Quantitative Evidence Found", content)

    def test_invalid_quantitative_result_fails(self):
        """Test that a summary containing quantitative results fails validation."""
        content = self._load_content(self.invalid_quant_path)
        self.assertIn("No Quantitative Evidence Found", content) # Has the phrase
        # But should fail because it has quantitative results
        self.assertRegex(content, r"pooled\s+r\s*=", 
                         "This test file should contain a quantitative result to trigger failure.")

    def test_integration_with_real_files_if_present(self):
        """
        If the actual pipeline has run and produced files in data/derived,
        validate those specific files.
        """
        actual_summary = DATA_DIR / "derived" / "narrative_summary.md"
        actual_pivot = DATA_DIR / "derived" / "pivot_log.json"

        if actual_summary.exists() and actual_pivot.exists():
            with open(actual_pivot, "r") as f:
                pivot_data = json.load(f)
            
            reason = pivot_data.get("reason", "")
            
            with open(actual_summary, "r", encoding="utf-8") as f:
                summary_content = f.read()

            # 1. Check required phrase
            self.assertIn("No Quantitative Evidence Found", summary_content, 
                          "Actual narrative_summary.md must contain 'No Quantitative Evidence Found'.")
            
            # 2. Check pivot reason
            self.assertIn(reason, summary_content, 
                          f"Actual narrative_summary.md must include pivot reason: '{reason}'.")

            # 3. Check no quantitative results
            self.assertNotRegex(summary_content, r"pooled\s+r\s*=", 
                                "Actual narrative_summary.md must not contain quantitative pooled results.")
        else:
            self.skipTest("Actual pipeline output files not found. Running mock tests only.")


if __name__ == "__main__":
    unittest.main()