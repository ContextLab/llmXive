import unittest
import os
import pandas as pd
from pathlib import Path
import json

from code.analyzer import (
    load_execution_results,
    perform_cox_ph_analysis,
    perform_spearman_correlation,
    generate_statistical_report,
)

class TestAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a minimal execution log CSV
        cls.csv_path = Path("data/processed/test_execution_log.csv")
        cls.csv_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame({
            "instance_id": ["p1", "p2", "p3"],
            "turns_to_converge": [10, 20, 0],
            "convergence_status": ["success", "success", "timeout"],
            "nesting_depth": [3, 5, 4],
            "path_coverage": [0.9, 0.95, 0.0],
            "divergence_from_ground_truth": [0.1, 0.05, 1.0]
        })
        df.to_csv(cls.csv_path, index=False)

    @classmethod
    def tearDownClass(cls):
        if cls.csv_path.is_file():
            cls.csv_path.unlink()

    def test_load_execution_results(self):
        df = load_execution_results(str(self.csv_path))
        self.assertEqual(len(df), 3)
        self.assertIn("instance_id", df.columns)

    def test_cox_ph_analysis(self):
        df = load_execution_results(str(self.csv_path))
        model, summary = perform_cox_ph_analysis(df)
        self.assertIn("hazard_ratios", summary)
        self.assertIn("coefficients", summary)

    def test_spearman_correlation(self):
        df = load_execution_results(str(self.csv_path))
        corr, p = perform_spearman_correlation(df)
        self.assertIsInstance(corr, float)
        self.assertIsInstance(p, float)

    def test_generate_statistical_report(self):
        df = load_execution_results(str(self.csv_path))
        model, summary = perform_cox_ph_analysis(df)
        corr, p = perform_spearman_correlation(df)
        report = generate_statistical_report(summary, corr, p, [40, 50, 60])
        self.assertIn("analysis_type", report)
        self.assertIn("fr_004_compliance", report)

if __name__ == "__main__":
    unittest.main()
