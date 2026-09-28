"""
T033: Run quickstart.md validation to ensure end-to-end reproducibility.

This script executes the full validation suite defined in the project's
quickstart.md to verify that the pipeline is reproducible from start to finish.

It calls the existing validation module `code/validation/validate_quickstart.py`
which checks:
1. Directory structure
2. Tree output
3. Requirements installation
4. Pre-commit config
5. Data checksums (FEMNIST)
6. Partition metadata existence and schema
7. Training logs (raw_logs.csv)
8. Filtered data (filtered_time.csv, filtered_data.csv)
9. Plots (minority_vs_global_overlay.png)
10. Summary results (summary.csv, validation_report.md, p_values_by_seed.json)

Exit code 0 indicates success; non-zero indicates failure.
"""

import sys
import logging
from pathlib import Path

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Execute the quickstart validation pipeline."""
    logger.info("Starting quickstart validation (T033)...")
    
    # Import the existing validation module
    # Note: We assume this is run from the project root or code/ directory
    # Adjust path if necessary based on execution context
    try:
        from validation.validate_quickstart import run_validation_checks, generate_report
        logger.info("Successfully imported validation module from code/validation/")
    except ImportError:
        # Try alternative import path if running from code/ directory
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from validation.validate_quickstart import run_validation_checks, generate_report
            logger.info("Successfully imported validation module via alternative path")
        except ImportError as e:
            logger.error(f"Failed to import validation module: {e}")
            logger.error("Ensure code/validation/validate_quickstart.py exists and is importable")
            return 1

    project_root = Path(__file__).parent.parent.parent
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        # Run all validation checks
        logger.info("Running validation checks...")
        results = run_validation_checks(project_root)
        
        # Generate detailed report
        logger.info("Generating validation report...")
        report = generate_report(results, project_root)
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for r in results if r.get('passed', False))
        total = len(results)
        
        logger.info(f"Checks passed: {passed}/{total}")
        
        if passed == total:
            logger.info("✅ ALL VALIDATION CHECKS PASSED")
            logger.info("The pipeline is reproducible from end-to-end.")
            logger.info("Quickstart validation completed successfully.")
            return 0
        else:
            failed = total - passed
            logger.warning(f"❌ {failed} validation check(s) failed")
            logger.warning("Quickstart validation completed with errors.")
            
            # Log specific failures
            for r in results:
                if not r.get('passed', False):
                    logger.warning(f"  - {r.get('check', 'Unknown')}: {r.get('message', 'No details')}")
            
            return 1
            
    except Exception as e:
        logger.error(f"Validation execution failed with exception: {e}")
        logger.exception("Full traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())