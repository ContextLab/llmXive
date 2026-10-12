"""Unit tests for quantum-descriptor detection (T014).

Verifies that build_quantum_proxy_report correctly detects the
presence/absence of HOMO-LUMO (quantum-derived) descriptors and
measured conductivity, and that the resulting report contains the
required fields ``homo_lumo_present`` and ``fallback_used``.
"""

import json
import os
import sys
import unittest

import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.target_proxy import (
    detect_homo_lumo_column,
    detect_conductivity_column,
    homo_lumo_data_present,
    build_quantum_proxy_report,
    compute_topological_proxy,
)


class TestColumnDetection(unittest.TestCase):
    def test_detect_homo_lumo_present(self):
        df = pd.DataFrame({"smiles": ["C"], "homo_lumo_gap": [3.2]})
        self.assertEqual(detect_homo_lumo_column(df), "homo_lumo_gap")
        self.assertTrue(homo_lumo_data_present(df))

    def test_detect_homo_lumo_absent(self):
        df = pd.DataFrame({"smiles": ["C"], "conductivity": [1e-4]})
        self.assertIsNone(detect_homo_lumo_column(df))
        self.assertFalse(homo_lumo_data_present(df))

    def test_homo_lumo_column_all_nan_is_absent(self):
        df = pd.DataFrame({"smiles": ["C"], "homo_lumo_gap": [None]})
        self.assertFalse(homo_lumo_data_present(df))

    def test_detect_conductivity(self):
        df = pd.DataFrame({"smiles": ["C"], "conductivity": [1e-4]})
        self.assertEqual(detect_conductivity_column(df), "conductivity")

    def test_detect_conductivity_absent(self):
        df = pd.DataFrame({"smiles": ["C"]})
        self.assertIsNone(detect_conductivity_column(df))


class TestQuantumProxyReport(unittest.TestCase):
    def test_report_fields_with_measured_conductivity(self):
        df = pd.DataFrame({"smiles": ["C", "CC"], "conductivity": [1e-5, 0.1]})
        report = build_quantum_proxy_report(df)
        for field in ("homo_lumo_present", "fallback_used"):
            self.assertIn(field, report)
            self.assertIsInstance(report[field], bool)
        self.assertFalse(report["homo_lumo_present"])
        self.assertFalse(report["fallback_used"])
        self.assertEqual(report["target_type"], "measured_conductivity")

    def test_report_fields_with_homo_lumo(self):
        df = pd.DataFrame({"smiles": ["C"], "homo_lumo_gap": [4.1]})
        report = build_quantum_proxy_report(df)
        self.assertTrue(report["homo_lumo_present"])
        self.assertFalse(report["fallback_used"])
        self.assertEqual(report["target_type"], "homo_lumo_gap")

    def test_report_fallback_when_both_missing(self):
        df = pd.DataFrame({"smiles": ["C"]})
        report = build_quantum_proxy_report(df)
        self.assertFalse(report["homo_lumo_present"])
        self.assertTrue(report["fallback_used"])
        self.assertEqual(report["target_type"], "topological_proxy")

    def test_topological_proxy_value(self):
        self.assertAlmostEqual(compute_topological_proxy(2.0, 5.0), 0.6 * 2 + 0.4 * 5)


class TestReportOnDisk(unittest.TestCase):
    def test_written_report_has_required_fields(self):
        from llmxive_toolkit import paths

        path = paths.data("processed", "quantum_proxy_report.json")
        self.assertTrue(path.exists(), f"{path} missing; run code/target_proxy.py")
        with open(path) as fh:
            report = json.load(fh)
        self.assertIn("homo_lumo_present", report)
        self.assertIn("fallback_used", report)
        self.assertIsInstance(report["homo_lumo_present"], bool)
        self.assertIsInstance(report["fallback_used"], bool)


if __name__ == "__main__":
    unittest.main()