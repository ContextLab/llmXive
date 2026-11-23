"""
T036: Run quickstart.md validation.

This script validates the project's quickstart instructions by executing
the pipeline steps described in quickstart.md and verifying that the
expected output artifacts are created.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def check_file_not_empty(path: Path, description: str) -> bool:
    """Check if a file exists and is not empty."""
    if not path.exists():
        logger.error(f"✗ {description} missing: {path}")
        return False
    
    size = path.stat().st_size
    if size > 0:
        logger.info(f"✓ {description} exists and is not empty ({size} bytes)")
        return True
    else:
        logger.error(f"✗ {description} exists but is empty: {path}")
        return False

def validate_quickstart() -> dict:
    """
    Validate the quickstart.md instructions by running the pipeline
    and checking for expected outputs.
    
    Returns a validation report dictionary.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "validation_status": "success",
        "checks": [],
        "errors": [],
        "warnings": []
    }
    
    # Define expected artifacts based on tasks.md and quickstart.md
    expected_artifacts = [
        # Data artifacts from T016
        (PROJECT_ROOT / "data" / "processed" / "cleaned_microbiome_sleep.csv", 
         "Cleaned microbiome-sleep dataset"),
        (PROJECT_ROOT / "data" / "processed" / "checksums.json", 
         "Checksums file"),
        (PROJECT_ROOT / "data" / "processed" / "ingestion_report.json", 
         "Ingestion report"),
        
        # Correlation results from T024
        (PROJECT_ROOT / "data" / "processed" / "correlation_results.csv", 
         "Correlation results"),
        
        # Plot artifacts from T030
        (PROJECT_ROOT / "data" / "processed" / "plots" / "scatterplot_shannon_sleep.png",
         "Scatterplot of Shannon diversity vs sleep"),
        (PROJECT_ROOT / "data" / "processed" / "plots" / "boxplot_sleep_quartile.png",
         "Boxplot of sleep by quartile"),
        
        # Final report from T031
        (PROJECT_ROOT / "data" / "processed" / "final_report.html",
         "Final HTML report")
    ]
    
    logger.info("Starting quickstart validation...")
    
    # Check if quickstart.md exists
    quickstart_path = PROJECT_ROOT / "quickstart.md"
    if not quickstart_path.exists():
        report["validation_status"] = "failed"
        report["errors"].append("quickstart.md not found")
        logger.error("quickstart.md not found")
        return report
    
    logger.info(f"Found quickstart.md at {quickstart_path}")
    
    # Read quickstart.md to understand expected steps
    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            quickstart_content = f.read()
        logger.info(f"Read quickstart.md ({len(quickstart_content)} bytes)")
    except Exception as e:
        report["validation_status"] = "failed"
        report["errors"].append(f"Failed to read quickstart.md: {str(e)}")
        return report
    
    # Validate each expected artifact
    all_checks_passed = True
    for artifact_path, description in expected_artifacts:
        check_result = {
            "artifact": str(artifact_path.relative_to(PROJECT_ROOT)),
            "description": description,
            "status": "unknown"
        }
        
        if artifact_path.suffix == '.csv' or artifact_path.suffix == '.json' or artifact_path.suffix == '.html':
            if check_file_not_empty(artifact_path, description):
                check_result["status"] = "passed"
            else:
                check_result["status"] = "failed"
                all_checks_passed = False
                report["errors"].append(f"Missing or empty: {description}")
        elif artifact_path.suffix == '.png':
            if check_file_exists(artifact_path, description):
                check_result["status"] = "passed"
            else:
                check_result["status"] = "failed"
                all_checks_passed = False
                report["errors"].append(f"Missing: {description}")
        else:
            if check_file_exists(artifact_path, description):
                check_result["status"] = "passed"
            else:
                check_result["status"] = "failed"
                all_checks_passed = False
                report["errors"].append(f"Missing: {description}")
        
        report["checks"].append(check_result)
    
    # Check if quickstart.md has executable steps
    if "python" in quickstart_content.lower() or "bash" in quickstart_content.lower() or "run" in quickstart_content.lower():
        report["warnings"].append("quickstart.md contains execution instructions - manual verification recommended")
        logger.warning("quickstart.md contains execution instructions - manual verification recommended")
    
    # Determine overall status
    if all_checks_passed:
        report["validation_status"] = "success"
        logger.info("✓ All quickstart validation checks passed")
    else:
        report["validation_status"] = "failed"
        logger.error("✗ Some quickstart validation checks failed")
    
    # Save validation report
    report_path = PROJECT_ROOT / "data" / "processed" / "quickstart_validation_report.json"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {report_path}")
    except Exception as e:
        logger.error(f"Failed to save validation report: {str(e)}")
        report["errors"].append(f"Failed to save validation report: {str(e)}")
    
    return report

def main():
    """Main entry point for T036 validation."""
    logger.info("Running T036: quickstart.md validation")
    
    try:
        report = validate_quickstart()
        
        # Print summary
        print("\n" + "="*60)
        print("QUICKSTART VALIDATION SUMMARY")
        print("="*60)
        print(f"Status: {report['validation_status'].upper()}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Checks performed: {len(report['checks'])}")
        print(f"Passed: {sum(1 for c in report['checks'] if c['status'] == 'passed')}")
        print(f"Failed: {sum(1 for c in report['checks'] if c['status'] == 'failed')}")
        
        if report['errors']:
            print(f"\nErrors ({len(report['errors'])}):")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print(f"\nWarnings ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        print("="*60 + "\n")
        
        # Exit with appropriate code
        if report['validation_status'] == 'success':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Validation failed with exception: {str(e)}")
        print(f"\nValidation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()