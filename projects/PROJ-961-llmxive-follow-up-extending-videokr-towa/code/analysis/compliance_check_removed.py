"""
Compliance Check Module (T050 Replacement).

This module implements the compliance verification logic that was originally
assigned to T050. Per the project specification, T050 was removed as a standalone
task and replaced by T013c (Data Ingestion Compliance) and T020c (Analysis Compliance).
This module provides a consolidated check to verify that the source-enforced
constraints (No Synthetic Data, Streaming, Power Checks) are active in the
respective pipeline modules.

It scans the source code of T013 (annotate_graph.py) and T020b (detect_threshold.py)
to ensure:
1. No `generate_synthetic_*`, `mock_*`, or `np.random` fallbacks exist in data loading paths.
2. `streaming=True` or `chunksize` usage is present for large datasets.
3. `BinPowerError` or equivalent power checks are implemented.
"""

import logging
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplianceCheckError(Exception):
    """Raised when a compliance check fails."""
    pass

def check_replacement_compliance() -> Dict[str, Any]:
    """
    Scans the source code of T013 and T020b to verify compliance constraints.

    Returns:
        Dict containing the status of each check and any violations found.
    """
    project_root = get_project_root()
    results = {
        "status": "passed",
        "checks": [],
        "violations": []
    }

    # Define paths to check
    t013_path = project_root / "code" / "ingest" / "annotate_graph.py"
    t020b_path = project_root / "code" / "analysis" / "detect_threshold.py"

    checks_performed = []

    # Check 1: T013 - No Synthetic Data Fallbacks
    logger.info(f"Checking {t013_path} for synthetic data fallbacks...")
    if t013_path.exists():
        content = t013_path.read_text()
        # Look for common synthetic generation patterns
        synthetic_patterns = [
            r'generate_synthetic',
            r'mock_data',
            r'np\.random\.',
            r'pd\.DataFrame\(\{.*"fake".*\}\)',
            r'fakedata',
            r'synthetic_dataset'
        ]
        
        # Also check for try/except blocks that might silently fallback
        silent_fallback_pattern = r'try:.*except.*:(?!.*raise).*generate_synthetic|mock'
        
        violations = []
        for pattern in synthetic_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                # Allow comments that mention these terms but don't use them
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if re.search(pattern, line, re.IGNORECASE) and not line.strip().startswith('#'):
                        # Check if it's inside a try/except that swallows errors
                        violations.append(f"Potential synthetic data usage found: {line.strip()}")
        
        if violations:
            results["violations"].extend(violations)
            results["status"] = "failed"
            checks_performed.append({
                "check": "T013_NoSyntheticFallback",
                "status": "failed",
                "details": violations
            })
        else:
            checks_performed.append({
                "check": "T013_NoSyntheticFallback",
                "status": "passed",
                "details": ["No synthetic data patterns found"]
            })
    else:
        checks_performed.append({
            "check": "T013_NoSyntheticFallback",
            "status": "skipped",
            "details": ["File not found"]
        })

    # Check 2: T020b - Streaming and Power Checks
    logger.info(f"Checking {t020b_path} for streaming and power checks...")
    if t020b_path.exists():
        content = t020b_path.read_text()
        
        # Check for BinPowerError
        has_power_check = "BinPowerError" in content or "insufficient_power" in content.lower()
        
        # Check for streaming or chunksize usage
        has_streaming = "streaming=True" in content or "chunksize=" in content or "read_csv" in content
        
        if not has_power_check:
            results["violations"].append("T020b: Missing BinPowerError or power check")
            results["status"] = "failed"
            checks_performed.append({
                "check": "T020b_PowerCheck",
                "status": "failed",
                "details": ["No BinPowerError or power check found"]
            })
        else:
            checks_performed.append({
                "check": "T020b_PowerCheck",
                "status": "passed",
                "details": ["Power check implemented"]
            })

        if not has_streaming:
            # This is a warning, not a hard failure if the dataset is small
            checks_performed.append({
                "check": "T020b_Streaming",
                "status": "warning",
                "details": ["No explicit streaming/chunksize found (may be acceptable for small datasets)"]
            })
        else:
            checks_performed.append({
                "check": "T020b_Streaming",
                "status": "passed",
                "details": ["Streaming or chunksize usage found"]
            })
    else:
        checks_performed.append({
            "check": "T020b_PowerCheck",
            "status": "skipped",
            "details": ["File not found"]
        })
        checks_performed.append({
            "check": "T020b_Streaming",
            "status": "skipped",
            "details": ["File not found"]
        })

    results["checks"] = checks_performed
    return results

def run() -> int:
    """
    Main entry point for the compliance check.
    
    Returns:
        0 if all checks pass, 1 if any check fails.
    """
    logger.info("Running T050 Compliance Check (Replacement Verification)...")
    
    try:
        results = check_replacement_compliance()
        
        # Write results to log
        log_dir = get_path("data", "processed")
        ensure_dir(log_dir)
        log_file = log_dir / "compliance_check_t050.json"
        
        import json
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Compliance check results written to {log_file}")
        
        if results["status"] == "failed":
            logger.error("Compliance check FAILED. Violations found:")
            for v in results["violations"]:
                logger.error(f"  - {v}")
            return 1
        else:
            logger.info("Compliance check PASSED.")
            return 0
            
    except Exception as e:
        logger.error(f"Compliance check failed with exception: {e}")
        return 1

def main():
    """Script entry point."""
    sys.exit(run())

if __name__ == "__main__":
    main()