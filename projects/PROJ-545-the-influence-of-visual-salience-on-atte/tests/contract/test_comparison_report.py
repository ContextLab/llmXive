"""
Contract test for the comparison report schema.
Verifies that the sensitivity report and comparison analysis outputs
contain the required metrics.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Constants for schema validation
SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.10]
REQUIRED_REPORT_KEYS = ['log_likelihood', 'AIC', 'BIC']


def load_test_artifact(path: str) -> Dict[str, Any]:
    """
    Helper to load a JSON artifact for testing.
    """
    full_path = project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"Contract test artifact not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return json.load(f)


class TestComparisonReportSchema:
    """
    Contract test suite for User Story 3: Model Comparison and Sensitivity Analysis.
    """

    def test_sensitivity_report_contains_metrics(self):
        """
        Contract test: Verify sensitivity report contains log-likelihood and AIC 
        for all threshold values.
        """
        # We expect a JSON report from the sensitivity analysis (T030)
        # The path might be data/processed/sensitivity_report.json or similar
        # Assuming a standard location based on project structure
        artifact_path = "data/processed/sensitivity_report.json"
        
        try:
            report = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T030 (sensitivity) has not been run yet."
            )

        # Structure check: usually a list of dicts or a dict of dicts keyed by threshold
        # Assuming a list of results for each threshold
        if isinstance(report, dict):
            # If it's a dict, check if keys are thresholds
            keys = list(report.keys())
            if not all(isinstance(k, (int, float)) for k in keys):
                # Maybe it's nested
                if 'results' in report:
                    report = report['results']
                else:
                    # Fallback: assume the dict itself has the keys
                    pass

        # Ensure we have entries for the specific thresholds
        found_thresholds = []
        if isinstance(report, list):
            for entry in report:
                if isinstance(entry, dict):
                    # Look for a threshold key
                    thresh = entry.get('threshold') or entry.get('cutoff')
                    if thresh is not None:
                        found_thresholds.append(thresh)
        elif isinstance(report, dict):
            # If keys are thresholds
            found_thresholds = [float(k) for k in report.keys() if isinstance(k, (int, float))]

        # Check that we have at least the required thresholds
        # (The task asks for {0.01, 0.05, 0.10})
        for target_thresh in SENSITIVITY_THRESHOLDS:
            # Allow small float tolerance
            found = any(abs(f - target_thresh) < 1e-6 for f in found_thresholds)
            assert found, (
                f"Contract violation: Sensitivity report missing threshold {target_thresh}. "
                f"Found thresholds: {found_thresholds}"
            )

    def test_sensitivity_report_has_required_metrics(self):
        """
        Contract test: Verify each sensitivity entry contains log-likelihood and AIC.
        """
        artifact_path = "data/processed/sensitivity_report.json"
        
        try:
            report = load_test_artifact(artifact_path)
        except FileNotFoundError:
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "This is expected if T030 (sensitivity) has not been run yet."
            )

        entries = []
        if isinstance(report, list):
            entries = report
        elif isinstance(report, dict):
            # If it's a dict of results, extract values
            if 'results' in report:
                entries = report['results']
            else:
                # Assume values are the entries
                entries = list(report.values())

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            
            for metric in REQUIRED_REPORT_KEYS:
                assert metric in entry, (
                    f"Contract violation: Missing metric '{metric}' in sensitivity entry. "
                    f"Entry keys: {list(entry.keys())}"
                )
                assert isinstance(entry[metric], (int, float)), (
                    f"Contract violation: Metric '{metric}' is not numeric."
                )

    def test_comparison_report_structure(self):
        """
        Contract test: Verify the main comparison report (if JSON) has expected structure.
        """
        # If a specific JSON report is generated for T029/T033
        artifact_path = "data/processed/comparison_report.json"
        
        try:
            report = load_test_artifact(artifact_path)
        except FileNotFoundError:
            # If the report is markdown (T033), skip this JSON check
            pytest.skip(
                f"Artifact {artifact_path} not found. "
                "Comparison might be in markdown format (paper/results/comparison_report.md)."
            )

        # Basic structure check
        assert isinstance(report, dict), "Comparison report must be a JSON object."
        
        # Expect keys for model comparison
        assert 'models' in report or 'results' in report, (
            "Contract violation: Comparison report missing 'models' or 'results' key."
        )
