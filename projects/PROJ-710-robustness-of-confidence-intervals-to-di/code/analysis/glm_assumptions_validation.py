"""
Integration script for GLM assumption validation.

This script runs the GLM assumption validation on the coverage results
and generates a validation report.
"""
import json
import sys
from pathlib import Path

from .glm_assumptions import main as run_validation


def main():
    """Run GLM assumption validation and save results."""
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    validation_report = run_validation()

    # Save validation report
    report_file = artifacts_dir / "glm_validation_report.json"
    with open(report_file, 'w') as f:
        json.dump(validation_report, f, indent=2, default=str)

    print(f"GLM validation report saved to: {report_file}")
    print(f"Status: {validation_report['status']}")
    print(f"Message: {validation_report['message']}")

    if validation_report.get('recommendations'):
        print("\nRecommendations:")
        for rec in validation_report['recommendations']:
            print(f"  - {rec}")

    # Return exit code based on status
    if validation_report['status'] == 'error':
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
