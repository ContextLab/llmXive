"""Verify CI pipeline runs contract tests, unit tests, and integration tests with coverage reporting.

This script validates that the GitHub Actions CI workflow (.github/workflows/ci.yml)
contains the required test stages and coverage reporting configuration as specified
in T069 and T074 requirements.

Exit codes:
    0: All CI pipeline requirements verified
    1: CI workflow file not found
    2: Missing required test stages (contract/unit/integration)
    3: Missing coverage reporting configuration
    4: YAML parsing error
"""

import os
import sys
from pathlib import Path
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory (parent of code/)."""
    return Path(__file__).resolve().parent.parent.parent

def load_ci_workflow() -> dict:
    """Load and parse the CI workflow YAML file."""
    project_root = get_project_root()
    ci_workflow_path = project_root / '.github' / 'workflows' / 'ci.yml'

    if not ci_workflow_path.exists():
        logger.error(f"CI workflow file not found: {ci_workflow_path}")
        return None

    try:
        with open(ci_workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
        return workflow
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse CI workflow YAML: {e}")
        return None

def verify_test_stages(workflow: dict) -> bool:
    """Verify that contract tests, unit tests, and integration tests are present."""
    if workflow is None:
        return False

    required_stages = {
        'contract': False,
        'unit': False,
        'integration': False
    }

    # Check jobs in the workflow
    jobs = workflow.get('jobs', {})
    if not jobs:
        logger.error("No jobs defined in CI workflow")
        return False

    # Search for test stages in job names and steps
    workflow_content = str(workflow).lower()

    # Check for contract tests
    if any(term in workflow_content for term in ['contract', 'contract test']):
        required_stages['contract'] = True
        logger.info("✓ Contract tests stage found in CI workflow")
    else:
        logger.warning("✗ Contract tests stage NOT found in CI workflow")

    # Check for unit tests
    if any(term in workflow_content for term in ['unit', 'unit test', 'unittest']):
        required_stages['unit'] = True
        logger.info("✓ Unit tests stage found in CI workflow")
    else:
        logger.warning("✗ Unit tests stage NOT found in CI workflow")

    # Check for integration tests
    if any(term in workflow_content for term in ['integration', 'integration test']):
        required_stages['integration'] = True
        logger.info("✓ Integration tests stage found in CI workflow")
    else:
        logger.warning("✗ Integration tests stage NOT found in CI workflow")

    all_present = all(required_stages.values())
    if not all_present:
        missing = [k for k, v in required_stages.items() if not v]
        logger.error(f"Missing test stages: {missing}")

    return all_present

def verify_coverage_reporting(workflow: dict) -> bool:
    """Verify that coverage reporting is configured in the CI workflow."""
    if workflow is None:
        return False

    workflow_content = str(workflow).lower()

    # Check for coverage-related terms
    coverage_indicators = [
        'coverage',
        'pytest-cov',
        'coverage.py',
        'codecov',
        'coveralls',
        'coverage report',
        'coverage.xml',
        'htmlcov'
    ]

    coverage_found = any(term in workflow_content for term in coverage_indicators)

    if coverage_found:
        logger.info("✓ Coverage reporting configuration found in CI workflow")
        return True
    else:
        logger.error("✗ Coverage reporting configuration NOT found in CI workflow")
        return False

def verify_workflow_structure(workflow: dict) -> bool:
    """Verify basic workflow structure is valid."""
    if workflow is None:
        return False

    # Check for required top-level keys
    required_keys = ['name', 'on', 'jobs']
    missing_keys = [key for key in required_keys if key not in workflow]

    if missing_keys:
        logger.error(f"Missing required workflow keys: {missing_keys}")
        return False

    # Verify 'on' trigger configuration
    on_config = workflow.get('on', {})
    if isinstance(on_config, dict):
        triggers = list(on_config.keys())
        if 'push' not in triggers and 'pull_request' not in triggers:
            logger.warning("Workflow may not trigger on push or pull_request")

    logger.info("✓ CI workflow structure is valid")
    return True

def generate_verification_report(workflow: dict) -> dict:
    """Generate a detailed verification report."""
    report = {
        'workflow_exists': workflow is not None,
        'structure_valid': False,
        'test_stages_complete': False,
        'coverage_configured': False,
        'all_requirements_met': False,
        'details': {}
    }

    if workflow:
        report['structure_valid'] = verify_workflow_structure(workflow)
        report['test_stages_complete'] = verify_test_stages(workflow)
        report['coverage_configured'] = verify_coverage_reporting(workflow)
        report['all_requirements_met'] = (
            report['structure_valid'] and
            report['test_stages_complete'] and
            report['coverage_configured']
        )

        # Add detailed breakdown
        report['details']['workflow_file'] = '.github/workflows/ci.yml'
        report['details']['workflow_name'] = workflow.get('name', 'Unknown')
        report['details']['jobs'] = list(workflow.get('jobs', {}).keys())

    return report

def main() -> int:
    """Main entry point for CI pipeline verification."""
    logger.info("Starting CI pipeline verification...")
    logger.info("=" * 60)

    # Load CI workflow
    workflow = load_ci_workflow()

    # Generate report
    report = generate_verification_report(workflow)

    # Print summary
    logger.info("=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Workflow file exists: {report['workflow_exists']}")
    logger.info(f"Structure valid: {report['structure_valid']}")
    logger.info(f"Test stages complete: {report['test_stages_complete']}")
    logger.info(f"Coverage configured: {report['coverage_configured']}")
    logger.info(f"All requirements met: {report['all_requirements_met']}")

    if report['all_requirements_met']:
        logger.info("=" * 60)
        logger.info("✓ CI PIPELINE VERIFICATION PASSED")
        logger.info("=" * 60)
        return 0
    else:
        logger.info("=" * 60)
        logger.info("✗ CI PIPELINE VERIFICATION FAILED")
        logger.info("=" * 60)

        # Determine specific exit code
        if not report['workflow_exists']:
            return 1
        if not report['test_stages_complete']:
            return 2
        if not report['coverage_configured']:
            return 3

        return 4

if __name__ == '__main__':
    sys.exit(main())
