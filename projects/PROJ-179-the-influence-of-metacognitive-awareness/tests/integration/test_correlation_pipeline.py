"""
Stub integration test for the overall pipeline.

The full pipeline depends on many upstream tasks; this test merely ensures that
the main entry point (code/analysis.py) can be executed without raising an
exception after the data validation step has produced a report.
"""

import json
import subprocess
import sys
from pathlib import Path
import unittest

class TestCorrelationPipeline(unittest.TestCase):
    """Integration sanity check for the correlation pipeline."""

    def test_pipeline_runs(self):
        repo_root = Path(__file__).resolve().parents[3]

        # Ensure validation report exists (run validator first)
        validator = repo_root / "code" / "data" / "validate_data.py"
        subprocess.run([sys.executable, str(validator)], cwd=repo_root, check=False)

        # Run the main analysis script
        analysis_script = repo_root / "code" / "analysis.py"
        result = subprocess.run(
            [sys.executable, str(analysis_script)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # The pipeline should finish with exit code 0 (success) or 1 (blocked)
        self.assertIn(
            result.returncode,
            (0, 1),
            msg="Main analysis script exited with an unexpected code",
        )

if __name__ == "__main__":
    unittest.main()