#!/usr/bin/env python3
"""
Verify ELBO convergence logs exist in logs/elbo/ with stopping criteria.
Per Constitution Principle VI.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_elbo_log_structure(log_path: Path) -> Dict[str, Any]:
    """Check if an ELBO log file has proper structure."""
    if not log_path.exists():
        return {"exists": False, "error": "File does not exist"}

    try:
        with open(log_path, 'r') as f:
            data = json.load(f)

        # Check for required fields per Constitution Principle VI
        required_fields = ['elbo_values', 'iterations', 'convergence_threshold', 'stopped_early']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {
                "exists": True,
                "error": f"Missing required fields: {missing_fields}",
                "has_stopping_criteria": False
            }

        return {
            "exists": True,
            "has_stopping_criteria": True,
            "convergence_threshold": data.get('convergence_threshold'),
            "stopped_early": data.get('stopped_early'),
            "iterations": data.get('iterations'),
            "elbo_values_count": len(data.get('elbo_values', []))
        }
    except json.JSONDecodeError as e:
        return {"exists": True, "error": f"Invalid JSON: {e}", "has_stopping_criteria": False}
    except Exception as e:
        return {"exists": True, "error": str(e), "has_stopping_criteria": False}


def verify_elbo_logs(project_root: Path) -> Dict[str, Any]:
    """Verify ELBO convergence logs exist with proper stopping criteria."""
    elbo_dir = project_root / "logs" / "elbo"

    result = {
        "directory_exists": elbo_dir.exists(),
        "log_files": [],
        "all_have_stopping_criteria": True,
        "verification_passed": True
    }

    if not elbo_dir.exists():
        result["verification_passed"] = False
        result["error"] = "ELBO logs directory does not exist"
        return result

    # Find all ELBO log files
    log_files = list(elbo_dir.glob("*.json"))

    if not log_files:
        result["verification_passed"] = False
        result["error"] = "No ELBO log files found in logs/elbo/"
        return result

    for log_file in log_files:
        log_info = check_elbo_log_structure(log_file)
        log_info["path"] = str(log_file.relative_to(project_root))
        result["log_files"].append(log_info)

        if not log_info.get("has_stopping_criteria", False):
            result["all_have_stopping_criteria"] = False
            result["verification_passed"] = False

    return result


def main():
    """Main verification entry point."""
    # Determine project root (go up from code/scripts/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    logger.info(f"Project root: {project_root}")
    logger.info("Verifying ELBO convergence logs per Constitution Principle VI...")

    result = verify_elbo_logs(project_root)

    # Print summary
    print("\n" + "="*60)
    print("ELBO CONVERGENCE LOG VERIFICATION REPORT")
    print("="*60)
    print(f"Directory exists: {result['directory_exists']}")
    print(f"Log files found: {len(result['log_files'])}")
    print(f"All have stopping criteria: {result['all_have_stopping_criteria']}")
    print(f"Verification passed: {result['verification_passed']}")

    if result['log_files']:
        print("\nLog file details:")
        for log_info in result['log_files']:
            print(f"  - {log_info['path']}")
            print(f"    Has stopping criteria: {log_info.get('has_stopping_criteria', False)}")
            if log_info.get('error'):
                print(f"    Error: {log_info['error']}")

    # Exit with appropriate code
    if result['verification_passed']:
        print("\n✓ ELBO logs verification PASSED")
        sys.exit(0)
    else:
        print("\n✗ ELBO logs verification FAILED")
        if result.get('error'):
            print(f"  Reason: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
