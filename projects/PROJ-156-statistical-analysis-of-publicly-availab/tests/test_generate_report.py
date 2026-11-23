"""
tests/test_generate_report.py

Tests for generate_report.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestGenerateReport(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data", "processed")
        self.paper_dir = os.path.join(self.temp_dir, "paper")
        self.logs_dir = os.path.join(self.temp_dir, "code", "logs")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.paper_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # Mock config
        config_path = os.path.join(self.temp_dir, "code", "config.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            f.write("games:\n  - test-game\n  - another-game\n")
            f.write("effect_size_assumptions: 0.5\n")

        # Mock data files
        # run_records.csv
        with open(os.path.join(self.data_dir, "run_records.csv"), 'w') as f:
            f.write("run_time_seconds,runner_id,attempt_number,category,submission_date,game_id\n")
            f.write("100.5,abc123,1,any,test-game,2023-01-01T00:00:00Z\n")
            f.write("95.2,def456,2,any,test-game,2023-01-02T00:00:00Z\n")

        # distribution_fits.csv
        with open(os.path.join(self.data_dir, "distribution_fits.csv"), 'w') as f:
            f.write("game_id,distribution_family,mu,sigma,KS_D,KS_pvalue,AIC\n")
            f.write("test-game,log-normal,4.5,0.2,0.05,0.8,100.0\n")
            f.write("another-game,Weibull,2.1,1.5,0.1,0.02,150.0\n")

        # model_results.csv
        with open(os.path.join(self.data_dir, "model_results.csv"), 'w') as f:
            f.write("predictor_name,coefficient,standard_error,p_value,vif,random_effect_variance\n")
            f.write("log(Attempt Number),-0.1,0.02,0.001,1.2,0.05\n")
            f.write("Game Difficulty,0.5,0.1,0.01,1.1,0.05\n")

        # power_pre_evaluation.json
        with open(os.path.join(self.data_dir, "power_pre_evaluation.json"), 'w') as f:
            f.write('{"games": [{"game_id": "low-sample-game", "run_count": 50, "excluded_from_parametric": true}]}')

        # Patch paths in the module
        import code.scripts.generate_report as gr
        self.original_data_dir = gr.DATA_DIR
        self.original_paper_dir = gr.PAPER_DIR
        self.original_logs_dir = gr.LOGS_DIR
        self.original_config_path = gr.CONFIG_PATH
        self.original_project_root = gr.PROJECT_ROOT

        gr.DATA_DIR = Path(self.data_dir)
        gr.PAPER_DIR = Path(self.paper_dir)
        gr.LOGS_DIR = Path(self.logs_dir)
        gr.CONFIG_PATH = Path(config_path)
        gr.PROJECT_ROOT = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directories."""
        # Restore original paths
        import code.scripts.generate_report as gr
        gr.DATA_DIR = self.original_data_dir
        gr.PAPER_DIR = self.original_paper_dir
        gr.LOGS_DIR = self.original_logs_dir
        gr.CONFIG_PATH = self.original_config_path
        gr.PROJECT_ROOT = self.original_project_root
        shutil.rmtree(self.temp_dir)

    def test_draft_generation(self):
        """Test that draft.md is generated."""
        import code.scripts.generate_report as gr
        gr.main()
        draft_path = os.path.join(self.paper_dir, "draft.md")
        self.assertTrue(os.path.exists(draft_path), "draft.md was not created")

    def test_no_causal_language(self):
        """Test that draft does not contain prohibited causal terms."""
        import code.scripts.generate_report as gr
        gr.main()
        draft_path = os.path.join(self.paper_dir, "draft.md")
        with open(draft_path, 'r') as f:
            content = f.read()

        causal_terms = [
            r'\bcauses\b', r'\baffects\b', r'\bimpacts\b', r'\bdetermines\b',
            r'\bleads to\b', r'\bresults in\b', r'\beffect\b', r'\bimpact\b',
            r'\bcause\b', r'\bconsequence\b'
        ]
        pattern = re.compile('|'.join(causal_terms), re.IGNORECASE)
        matches = pattern.findall(content)
        self.assertEqual(len(matches), 0, f"Causal language detected: {matches}")

    def test_power_analysis_section(self):
        """Test that Power Analysis section exists and mentions limitations."""
        import code.scripts.generate_report as gr
        gr.main()
        draft_path = os.path.join(self.paper_dir, "draft.md")
        with open(draft_path, 'r') as f:
            content = f.read()

        self.assertIn("## Power Analysis", content, "Power Analysis section missing")
        # Check for the specific limitation statement
        self.assertIn("limited ability to detect effects for games with <100 runs", content,
                      "Power limitation statement missing")

    def test_excluded_games_listed(self):
        """Test that excluded games are listed in the report."""
        import code.scripts.generate_report as gr
        gr.main()
        draft_path = os.path.join(self.paper_dir, "draft.md")
        with open(draft_path, 'r') as f:
            content = f.read()

        self.assertIn("low-sample-game", content, "Excluded game not listed in report")

if __name__ == "__main__":
    unittest.main()