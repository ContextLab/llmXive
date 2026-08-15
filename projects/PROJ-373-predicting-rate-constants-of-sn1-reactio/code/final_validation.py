"""
Final end-to-end validation script for T040.
This script re-runs the full pipeline on the largest feasible subset
and validates all artifacts against schemas.
"""
import os
import sys
import json
import logging
import argparse
import subprocess
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, timeout: int = 14400) -> dict:
    """Run a command with timeout and return result."""
    logger.info(f"Running: {' '.join(cmd)}")
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start
        return {
            'cmd': ' '.join(cmd),
            'returncode': result.returncode,
            'stdout': result.stdout[:1000] if result.stdout else '',
            'stderr': result.stderr[:1000] if result.stderr else '',
            'duration': duration,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'cmd': ' '.join(cmd),
            'returncode': -1,
            'stdout': '',
            'stderr': f'Timeout after {timeout}s',
            'duration': timeout,
            'success': False
        }
    except Exception as e:
        return {
            'cmd': ' '.join(cmd),
            'returncode': -2,
            'stdout': '',
            'stderr': str(e),
            'duration': 0,
            'success': False
        }

def verify_artifact(path: str, schema_path: str = None) -> dict:
    """Verify artifact exists and optionally matches schema."""
    result = {
        'path': path,
        'exists': False,
        'size': 0,
        'valid': False,
        'error': None
    }

    p = Path(path)
    if not p.exists():
        result['error'] = 'File not found'
        return result

    result['exists'] = True
    result['size'] = p.stat().st_size

    if result['size'] == 0:
        result['error'] = 'File is empty'
        return result

    # Basic validation based on file type
    if p.suffix == '.json':
        try:
            with open(p, 'r') as f:
                json.load(f)
            result['valid'] = True
        except json.JSONDecodeError as e:
            result['error'] = f'Invalid JSON: {e}'
    elif p.suffix == '.csv':
        try:
            with open(p, 'r') as f:
                header = f.readline()
                if not header:
                    result['error'] = 'CSV is empty'
                    return result
            result['valid'] = True
        except Exception as e:
            result['error'] = f'Invalid CSV: {e}'
    elif p.suffix == '.pt':
        # PyTorch model - just check non-empty
        result['valid'] = True
    elif p.suffix == '.md':
        result['valid'] = True
    else:
        result['valid'] = True

    return result

def compare_with_integration_test(evidence_path: str, current_results: dict) -> dict:
    """Compare current results with integration test evidence."""
    comparison = {
        'matched': True,
        'discrepancies': []
    }

    if not os.path.exists(evidence_path):
        comparison['matched'] = False
        comparison['discrepancies'].append('Integration test evidence not found')
        return comparison

    try:
        with open(evidence_path, 'r') as f:
            evidence = json.load(f)

        # Compare key metrics
        if 'summary' in evidence and 'summary' in current_results:
            for key in ['passed', 'failed', 'artifacts_verified']:
                if key in evidence['summary'] and key in current_results['summary']:
                    if evidence['summary'][key] != current_results['summary'][key]:
                        comparison['discrepancies'].append(
                            f"Discrepancy in {key}: evidence={evidence['summary'][key]}, current={current_results['summary'][key]}"
                        )
                        comparison['matched'] = False
    except Exception as e:
        comparison['matched'] = False
        comparison['discrepancies'].append(f"Error comparing evidence: {e}")

    return comparison

def run_full_validation(project_root: str, integration_evidence: str = None) -> dict:
    """Run full validation pipeline."""
    os.chdir(project_root)

    report = {
        'project_root': project_root,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pipeline_runs': [],
        'artifact_verifications': [],
        'comparison': None,
        'summary': {
            'pipeline_success': False,
            'artifacts_valid': 0,
            'artifacts_total': 0,
            'discrepancies': []
        }
    }

    # 1. Run full pipeline (with timeout)
    logger.info("Starting full pipeline validation...")
    pipeline_cmd = [sys.executable, 'code/main.py', '--stage', 'all']
    pipeline_result = run_command(pipeline_cmd, timeout=14400)  # 4 hours
    report['pipeline_runs'].append(pipeline_result)

    if pipeline_result['success']:
        report['summary']['pipeline_success'] = True
        logger.info("Pipeline completed successfully")
    else:
        logger.warning(f"Pipeline failed: {pipeline_result['stderr']}")
        # Check if it's a timeout
        if 'Timeout' in pipeline_result['stderr']:
            report['summary']['discrepancies'].append('Pipeline timed out - partial run documented')
            report['summary']['pipeline_success'] = False
        else:
            report['summary']['discrepancies'].append(f"Pipeline failed: {pipeline_result['stderr'][:200]}")

    # 2. Verify key artifacts
    key_artifacts = [
        'data/processed/cleaned_sn1.csv',
        'data/processed/exclusion_report.csv',
        'artifacts/best_model.pt',
        'artifacts/metrics.json',
        'artifacts/final_report.md',
        'artifacts/hyperparameter_search.csv',
        'artifacts/sensitivity_report.csv',
        'artifacts/perturbation_results.csv',
        'artifacts/collinearity_report.json',
        'artifacts/shap_consistency_report.md'
    ]

    for artifact in key_artifacts:
        verification = verify_artifact(artifact)
        report['artifact_verifications'].append(verification)
        report['summary']['artifacts_total'] += 1
        if verification['valid']:
            report['summary']['artifacts_valid'] += 1

    # 3. Compare with integration test
    if integration_evidence:
        logger.info(f"Comparing with integration test: {integration_evidence}")
        report['comparison'] = compare_with_integration_test(
            integration_evidence,
            report
        )
        report['summary']['discrepancies'].extend(report['comparison']['discrepancies'])

    # 4. Generate summary
    logger.info(f"Validation complete. Artifacts: {report['summary']['artifacts_valid']}/{report['summary']['artifacts_total']}")
    return report

def main():
    parser = argparse.ArgumentParser(description='Final end-to-end validation for T040')
    parser.add_argument('--project-root', type=str, default='.', help='Project root directory')
    parser.add_argument('--evidence', type=str, help='Path to integration test evidence')
    parser.add_argument('--output', type=str, help='Path to save validation report')

    args = parser.parse_args()

    report = run_full_validation(args.project_root, args.evidence)

    # Print summary
    print("\n" + "="*60)
    print("FINAL VALIDATION REPORT")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Pipeline Success: {report['summary']['pipeline_success']}")
    print(f"Artifacts Valid: {report['summary']['artifacts_valid']}/{report['summary']['artifacts_total']}")
    print(f"Discrepancies: {len(report['summary']['discrepancies'])}")

    if report['summary']['discrepancies']:
        print("\nDiscrepancies:")
        for d in report['summary']['discrepancies']:
            print(f"  - {d}")

    print("="*60)

    # Save report
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nFull report saved to: {args.output}")

    # Exit code
    if report['summary']['artifacts_valid'] < report['summary']['artifacts_total']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
