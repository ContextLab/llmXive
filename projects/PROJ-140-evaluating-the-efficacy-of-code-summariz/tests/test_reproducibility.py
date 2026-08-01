"""
Reproducibility Verification Tests

Tests numerical tolerance between original and rerun results.
"""
import unittest
import json
import csv
import os
import sys
import numpy as np
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

class TestReproducibility(unittest.TestCase):
    """Test suite for reproducibility verification."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = PROJECT_ROOT
        self.results_path = self.project_root / "data" / "analysis_results" / "results.csv"
        self.baseline_path = self.project_root / "data" / "analysis_results" / "baseline_results.json"
        self.tolerance = 0.05  # 5% tolerance

    @unittest.skipIf(not self.results_path.exists(), "Results file not found")
    def test_results_file_exists(self):
        """Verify that results.csv exists after analysis."""
        self.assertTrue(self.results_path.exists(), "results.csv should exist")

    @unittest.skipIf(not self.results_path.exists(), "Results file not found")
    def test_results_csv_structure(self):
        """Verify CSV structure and required columns."""
        with open(self.results_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertGreater(len(rows), 0, "Results CSV should contain data rows")
        
        required_columns = [
            'comparison', 'metric', 'value', 'p_value', 
            'effect_size', 'ci_lower', 'ci_upper', 'significant'
        ]
        
        for row in rows:
            for col in required_columns:
                self.assertIn(col, row, f"Column '{col}' should be present")

    @unittest.skipIf(not self.results_path.exists(), "Results file not found")
    def test_numerical_validity(self):
        """Verify that numerical values are valid numbers."""
        with open(self.results_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        for row in rows:
            # Check p_value is numeric
            self.assertTrue(
                row['p_value'] not in ['', 'NaN', 'Inf'],
                f"p_value should be numeric: {row}"
            )
            
            # Check effect_size is numeric
            self.assertTrue(
                row['effect_size'] not in ['', 'NaN', 'Inf'],
                f"effect_size should be numeric: {row}"
            )

    @unittest.skipIf(not self.baseline_path.exists(), "Baseline file not found")
    def test_numerical_tolerance(self):
        """
        Verify that rerun results are within 5% tolerance of baseline.
        
        This is the core reproducibility check (SC-004, SC-005).
        """
        # Load baseline results
        with open(self.baseline_path, 'r') as f:
            baseline = json.load(f)
        
        # Load current results
        with open(self.results_path, 'r') as f:
            reader = csv.DictReader(f)
            current = list(reader)
        
        # Create lookup for current results
        current_lookup = {}
        for row in current:
            key = (row['comparison'], row['metric'])
            current_lookup[key] = float(row['value'])
        
        # Compare each baseline value
        discrepancies = []
        for comparison, metric in baseline['results'].keys():
            if (comparison, metric) in current_lookup:
                baseline_val = baseline['results'][comparison, metric]
                current_val = current_lookup[(comparison, metric)]
                
                # Calculate relative difference
                if baseline_val != 0:
                    rel_diff = abs(baseline_val - current_val) / abs(baseline_val)
                else:
                    rel_diff = abs(baseline_val - current_val)
                
                if rel_diff > self.tolerance:
                    discrepancies.append({
                        'comparison': comparison,
                        'metric': metric,
                        'baseline': baseline_val,
                        'current': current_val,
                        'rel_diff': rel_diff
                    })
        
        # Assert no discrepancies exceed tolerance
        self.assertEqual(
            len(discrepancies), 0,
            f"Found {len(discrepancies)} results exceeding {self.tolerance*100}% tolerance:\n"
            + "\n".join([str(d) for d in discrepancies])
        )

    def test_reproducibility_package_integrity(self):
        """
        Verify that the reproducibility package contains required files.
        """
        package_path = self.project_root / "data" / "reproducibility_package_v1.0.tar.gz"
        
        if not package_path.exists():
            self.skipTest("Reproducibility package not found")
        
        import tarfile
        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()
            
            required_files = [
                "reproducibility_package_v1.0/code/analysis/run_statistics.py",
                "reproducibility_package_v1.0/data/analysis_results/results.csv",
                "reproducibility_package_v1.0/data/interaction_logs/anonymized_logs.csv",
                "reproducibility_package_v1.0/README.md",
            ]
            
            for req_file in required_files:
                self.assertIn(
                    req_file, names,
                    f"Required file missing from package: {req_file}"
                )

    def test_sensitive_data_exclusion(self):
        """
        Verify that sensitive data is excluded from the reproducibility package.
        """
        package_path = self.project_root / "data" / "reproducibility_package_v1.0.tar.gz"
        
        if not package_path.exists():
            self.skipTest("Reproducibility package not found")
        
        import tarfile
        with tarfile.open(package_path, "r:gz") as tar:
            names = tar.getnames()
            
            sensitive_patterns = [
                "consent",
                "raw_logs",
                "anonymization_mapping",
                ".env"
            ]
            
            for name in names:
                for pattern in sensitive_patterns:
                    self.assertNotIn(
                        pattern.lower(), name.lower(),
                        f"Sensitive data found in package: {name}"
                    )

if __name__ == '__main__':
    unittest.main()