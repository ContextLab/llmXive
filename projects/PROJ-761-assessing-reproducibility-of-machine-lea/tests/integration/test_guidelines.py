"""
Integration test for checklist generation with mock failure logs.

This test verifies that the guidelines generation pipeline correctly:
1. Loads mock failure logs and statistical summaries.
2. Maps failure modes to specific best-practice recommendations.
3. Generates a valid Markdown checklist with >= 5 actionable items.
4. Writes the output to the expected artifact path.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import the guidelines module functions
# Note: Assuming guidelines.py is implemented in code/guidelines.py
# We import the necessary functions to drive the integration test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from guidelines import (
    load_failure_log,
    load_stat_summary,
    map_failure_modes_to_guidelines,
    generate_checklist,
    write_checklist
)
from failure_logger import FailureReason

def test_guidelines_integration():
    """
    Integration test: Generate checklist from mock failure logs and stats.
    """
    # Create a temporary directory for this test run to avoid polluting the project
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Define paths relative to the temp dir (mirroring project structure)
        artifacts_dir = tmp_path / "artifacts"
        reports_dir = artifacts_dir / "reports"
        logs_dir = artifacts_dir / "logs"
        plots_dir = artifacts_dir / "plots"
        
        reports_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        plots_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create Mock Failure Log
        # Simulate a qualitative failure log with various failure modes
        mock_failure_log = [
            {
                "paper_id": "paper_001",
                "reason": "Model Substitution/Unavailable",
                "details": "Original model had 2.5M parameters, exceeded 1M limit.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "paper_id": "paper_002",
                "reason": "Data Unavailable",
                "details": "Missing 'yield' column in dataset.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "paper_id": "paper_003",
                "reason": "Missing Seed",
                "details": "No random seed reported in original paper.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "paper_id": "paper_004",
                "reason": "Version Mismatch",
                "details": "Required RDKit version 2023.1, but 2024.3 available.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "paper_id": "paper_005",
                "reason": "Missing Covariates",
                "details": "Temperature and solvent conditions not specified.",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        failure_log_path = logs_dir / "failure_log.json"
        with open(failure_log_path, 'w') as f:
            json.dump(mock_failure_log, f, indent=2)

        # 2. Create Mock Statistical Summary
        # Simulate stat_summary.json with some heterogeneity and TOST results
        mock_stat_summary = {
            "t_tests": {
                "mae": {"stat": 2.5, "pvalue": 0.01, "significant": True},
                "r2": {"stat": -1.2, "pvalue": 0.25, "significant": False},
                "rho": {"stat": 0.8, "pvalue": 0.40, "significant": False}
            },
            "tost": {
                "mae": {"equivalent": False, "pvalue_low": 0.05, "pvalue_high": 0.06},
                "r2": {"equivalent": True, "pvalue_low": 0.01, "pvalue_high": 0.01},
                "rho": {"equivalent": False, "pvalue_low": 0.10, "pvalue_high": 0.15}
            },
            "mixed_effects": {
                "variance_intercept": 0.05,
                "residual_variance": 0.02
            },
            "heterogeneity": {
                "i2": 45.5,
                "interpretation": "Moderate heterogeneity"
            },
            "pooled_effect": {
                "mae": 0.15,
                "r2": 0.82,
                "rho": 0.75
            },
            "meta": {
                "n_papers": 10,
                "n_excluded": 5,
                "excluded_ids": ["paper_001", "paper_002", "paper_003", "paper_004", "paper_005"]
            }
        }
        
        stat_summary_path = reports_dir / "stat_summary.json"
        with open(stat_summary_path, 'w') as f:
            json.dump(mock_stat_summary, f, indent=2)

        # 3. Run the Guidelines Generation Pipeline
        # Load data
        failure_data = load_failure_log(str(failure_log_path))
        stat_data = load_stat_summary(str(stat_summary_path))
        
        # Map failure modes to guidelines
        guidelines_map = map_failure_modes_to_guidelines(failure_data)
        
        # Generate the checklist content
        checklist_content = generate_checklist(guidelines_map, stat_data)
        
        # Write the checklist to the expected output path
        output_path = reports_dir / "reproducibility_checklist.md"
        write_checklist(checklist_content, str(output_path))

        # 4. Verify the Output
        assert output_path.exists(), "Output checklist file was not created."
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Assertions
        assert "# Reproducibility Checklist" in content or "Reproducibility Checklist" in content, \
            "Checklist must have a title."
        
        # Count numbered items (simple check for "1.", "2.", etc.)
        import re
        numbered_items = re.findall(r'^\d+\.', content, re.MULTILINE)
        assert len(numbered_items) >= 5, \
            f"Checklist must contain at least 5 actionable items. Found: {len(numbered_items)}"
        
        # Verify specific failure modes are referenced
        assert "Missing Seed" in content or "random seed" in content.lower(), \
            "Checklist should reference missing seed failures."
        
        assert "Model Substitution" in content or "parameter limit" in content.lower(), \
            "Checklist should reference model substitution/parameter limits."
        
        assert "Data Unavailable" in content or "missing data" in content.lower(), \
            "Checklist should reference data availability issues."
        
        assert "Version" in content or "library" in content.lower(), \
            "Checklist should reference version mismatches."
        
        assert "Covariates" in content or "conditions" in content.lower(), \
            "Checklist should reference missing covariates/conditions."
        
        # Verify it references guidelines (e.g., "per published guidelines")
        assert "guideline" in content.lower() or "best practice" in content.lower(), \
            "Checklist items should cite best practices or guidelines."

        print("Integration test passed: Checklist generated successfully with >= 5 items referencing failure modes.")

if __name__ == "__main__":
    test_guidelines_integration()
    print("Test execution complete.")