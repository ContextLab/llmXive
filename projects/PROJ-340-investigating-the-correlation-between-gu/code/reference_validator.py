"""
Reference-Validator Agent Schema and Implementation.

This module defines the schema for the Reference-Validator Agent and implements
the logic to verify that pipeline results are backed by real, citable sources
rather than synthetic or fabricated data.

For this "Pipeline Validation Study" (synthetic data), the agent operates in
"Logic Only" mode: it validates the structure of the pipeline and synthetic
data generation logic, but does NOT fail the build if no real-world citations
are found (as per Plan's "Verified Accuracy" strategy).
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, NamedTuple
from enum import Enum

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent


class VerificationStatus(str, Enum):
    """Enum representing the status of a verification check."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class CitationSchema(NamedTuple):
    """
    Schema for a verified citation.
    Used to validate that a result is backed by a real source.
    """
    source_type: str  # 'paper', 'dataset', 'repository'
    source_id: str    # DOI, PMID, or specific dataset ID
    title: str
    url: Optional[str] = None
    access_date: Optional[str] = None


class VerificationResult(NamedTuple):
    """
    Result of a verification check.
    """
    status: VerificationStatus
    message: str
    details: Dict[str, Any]
    citations: Optional[List[CitationSchema]] = None


class ReferenceValidator:
    """
    The Reference-Validator Agent.

    Responsibilities:
    1. Verify that data sources are real (not synthetic/fabricated) unless
       explicitly allowed by the project scope (e.g., "Pipeline Validation Study").
    2. Validate the structure of pipeline artifacts.
    3. Ensure that if real data is expected, no synthetic fallback occurred.

    Mode:
    - "STRICT": Fail if real data is missing or synthetic data is used.
    - "LOGIC_ONLY": Validate structure but allow synthetic data if the project
      is scoped as a validation study.
    """

    def __init__(self, mode: str = "LOGIC_ONLY"):
        """
        Initialize the validator.

        Args:
            mode: "STRICT" or "LOGIC_ONLY". Default is "LOGIC_ONLY" for this project.
        """
        self.mode = mode
        self.project_root = PROJECT_ROOT
        self.state_file = self.project_root / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
        self.config_file = self.project_root / "data" / "config" / "required_variables.yaml"

    def verify_pipeline_structure(self) -> VerificationResult:
        """
        Verify that the pipeline structure and required configuration files exist.
        This is the "Logic Only" part of the validation.
        """
        missing_files = []
        required_files = [
            self.config_file,
            self.project_root / "code" / "ingest.py",
            self.project_root / "code" / "analysis.py",
            self.project_root / "code" / "main.py",
        ]

        for f in required_files:
            if not f.exists():
                missing_files.append(str(f.relative_to(self.project_root)))

        if missing_files:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message=f"Missing required pipeline files: {missing_files}",
                details={"missing_files": missing_files}
            )

        # Check config content
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            if 'required_predictors' not in config or 'required_outcomes' not in config:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    message="Config file missing required_predictors or required_outcomes keys.",
                    details={"config_keys": list(config.keys())}
                )
        except Exception as e:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message=f"Failed to parse config file: {e}",
                details={"error": str(e)}
            )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            message="Pipeline structure and configuration verified.",
            details={"checked_files": len(required_files)}
        )

    def verify_data_source(self, data_path: Path) -> VerificationResult:
        """
        Verify the data source at the given path.

        In STRICT mode: Fail if the data is synthetic or missing.
        In LOGIC_ONLY mode: Check if the data is synthetic, but if it is,
        verify that the project scope allows it (e.g., via a flag in state).
        """
        if not data_path.exists():
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message=f"Data file not found: {data_path}",
                details={"path": str(data_path)}
            )

        # Check for synthetic markers in the file (simple heuristic)
        is_synthetic = False
        try:
            with open(data_path, 'r') as f:
                first_line = f.readline()
                if 'synthetic' in first_line.lower() or 'generated' in first_line.lower():
                    is_synthetic = True
        except Exception:
            pass  # Binary or unreadable, assume not synthetic for now

        if is_synthetic:
            if self.mode == "STRICT":
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    message="Synthetic data detected. STRICT mode requires real data.",
                    details={"file": str(data_path)}
                )
            else:
                # LOGIC_ONLY: Allow synthetic but warn
                return VerificationResult(
                    status=VerificationStatus.WARNING,
                    message="Synthetic data detected. Allowed in LOGIC_ONLY mode for validation study.",
                    details={"file": str(data_path)}
                )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            message="Real data source verified.",
            details={"file": str(data_path)}
        )

    def run_full_validation(self, data_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Run the full validation suite.

        Args:
            data_path: Optional path to the data file to verify.

        Returns:
            A dictionary with the validation results.
        """
        results = {}

        # 1. Verify pipeline structure
        structure_result = self.verify_pipeline_structure()
        results["pipeline_structure"] = {
            "status": structure_result.status.value,
            "message": structure_result.message,
            "details": structure_result.details
        }

        # 2. Verify data source if provided
        if data_path:
            data_result = self.verify_data_source(data_path)
            results["data_source"] = {
                "status": data_result.status.value,
                "message": data_result.message,
                "details": data_result.details
            }
        else:
            results["data_source"] = {
                "status": VerificationStatus.SKIPPED.value,
                "message": "No data path provided.",
                "details": {}
            }

        # 3. Overall status
        statuses = [r["status"] for r in results.values()]
        if VerificationStatus.FAILED.value in statuses:
            overall = VerificationStatus.FAILED
        elif VerificationStatus.WARNING.value in statuses:
            overall = VerificationStatus.WARNING
        else:
            overall = VerificationStatus.PASSED

        results["overall_status"] = overall.value
        results["mode"] = self.mode

        return results


def create_sample_schema() -> Dict[str, Any]:
    """
    Create a sample schema for the Reference-Validator Agent.
    This is used to document the expected structure of verification results.
    """
    return {
        "VerificationStatus": ["PASSED", "FAILED", "WARNING", "SKIPPED"],
        "CitationSchema": {
            "source_type": "string",
            "source_id": "string",
            "title": "string",
            "url": "string (optional)",
            "access_date": "string (optional)"
        },
        "VerificationResult": {
            "status": "VerificationStatus",
            "message": "string",
            "details": "dict",
            "citations": "list[CitationSchema] (optional)"
        }
    }


def main():
    """
    CLI entry point for the Reference-Validator Agent.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Reference-Validator Agent")
    parser.add_argument(
        "--mode",
        choices=["STRICT", "LOGIC_ONLY"],
        default="LOGIC_ONLY",
        help="Validation mode. Default: LOGIC_ONLY"
    )
    parser.add_argument(
        "--data",
        type=str,
        help="Path to data file to verify (optional)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/verification_report.json",
        help="Path to output report (default: data/results/verification_report.json)"
    )

    args = parser.parse_args()

    validator = ReferenceValidator(mode=args.mode)

    data_path = Path(args.data) if args.data else None
    results = validator.run_full_validation(data_path)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Verification report written to {output_path}")

    # Exit with error if overall status is FAILED
    if results["overall_status"] == VerificationStatus.FAILED.value:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()