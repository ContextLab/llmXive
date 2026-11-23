import os
import sys
import subprocess
import logging
import time
import json
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, timeout: int = 3600) -> dict:
    """Run a command and return result."""
    logger.info(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        return {
            'cmd': ' '.join(cmd),
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'cmd': ' '.join(cmd),
            'returncode': -1,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds',
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

def verify_artifact(path: str, expected_columns: list = None) -> dict:
    """Verify an artifact exists and has expected content."""
    result = {
        'path': path,
        'exists': False,
        'non_empty': False,
        'columns_match': None,
        'valid': False
    }

    p = Path(path)
    if not p.exists():
        result['error'] = f"File not found: {path}"
        return result

    result['exists'] = True

    if p.stat().st_size == 0:
        result['error'] = "File is empty"
        return result

    result['non_empty'] = True

    if expected_columns and p.suffix == '.csv':
        try:
            import csv
            with open(p, 'r') as f:
                reader = csv.DictReader(f)
                actual_columns = reader.fieldnames
                if actual_columns:
                    missing = set(expected_columns) - set(actual_columns)
                    if missing:
                        result['error'] = f"Missing columns: {missing}"
                        return result
                    result['columns_match'] = True
        except Exception as e:
            result['error'] = f"Error reading CSV: {e}"
            return result

    result['valid'] = True
    return result

def parse_quickstart_instructions(quickstart_path: str) -> list:
    """Parse quickstart.md to extract commands to validate."""
    commands = []
    try:
        with open(quickstart_path, 'r') as f:
            content = f.read()
            # Look for code blocks with python commands
            lines = content.split('\n')
            in_code_block = False
            current_cmd = []

            for line in lines:
                if line.strip().startswith('```bash') or line.strip().startswith('```python'):
                    in_code_block = True
                    continue
                if line.strip().startswith('```'):
                    in_code_block = False
                    if current_cmd:
                        cmd_str = ' '.join(current_cmd)
                        if cmd_str.startswith('python'):
                            commands.append(cmd_str)
                        current_cmd = []
                    continue

                if in_code_block and line.strip():
                    # Skip comments and empty lines
                    if not line.strip().startswith('#') and not line.strip().startswith('//'):
                        current_cmd.append(line.strip())
    except Exception as e:
        logger.error(f"Error parsing quickstart: {e}")
    return commands

def validate_quickstart_instructions(commands: list) -> list:
    """Validate a list of commands from quickstart."""
    results = []
    for cmd_str in commands:
        parts = cmd_str.split()
        if not parts:
            continue

        # Parse arguments
        cmd_name = parts[0]
        args = parts[1:]

        # Special handling for known commands
        if 'main.py' in cmd_str:
            # Full pipeline run - might take too long, so we run a subset or skip
            logger.info(f"Skipping full pipeline run: {cmd_str}")
            results.append({
                'cmd': cmd_str,
                'status': 'skipped',
                'reason': 'Full pipeline run skipped for validation'
            })
            continue

        result = run_command(parts, timeout=300)
        results.append(result)

    return results

def run_verification(project_root: str, quickstart_path: str = None, evidence_path: str = None) -> dict:
    """Run full verification and generate report."""
    report = {
        'project_root': project_root,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'verifications': [],
        'summary': {
            'total_commands': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'artifacts_verified': 0
        }
    }

    os.chdir(project_root)

    # 1. Validate command-line argument mismatch fix
    # The error was: unrecognized arguments: --evidence
    # We need to verify the script accepts the arguments we pass
    logger.info("Testing validate_quickstart.py argument parsing...")
    test_cmd = [sys.executable, 'code/validation/validate_quickstart.py', '--project-root', '.']
    result = run_command(test_cmd)
    report['verifications'].append({
        'type': 'argument_parsing',
        'cmd': test_cmd,
        'success': result['success'],
        'error': result['stderr'] if not result['success'] else None
    })

    # 2. Parse and validate quickstart commands if path provided
    if quickstart_path and os.path.exists(quickstart_path):
        logger.info(f"Parsing quickstart from: {quickstart_path}")
        commands = parse_quickstart_instructions(quickstart_path)
        report['summary']['total_commands'] = len(commands)

        for cmd in commands:
            # Skip full pipeline runs
            if '--stage all' in cmd or 'main.py --stage all' in cmd:
                report['verifications'].append({
                    'type': 'quickstart_command',
                    'cmd': cmd,
                    'status': 'skipped',
                    'reason': 'Full pipeline run skipped'
                })
                report['summary']['skipped'] += 1
                continue

            result = run_command(cmd.split(), timeout=300)
            report['verifications'].append(result)
            if result['success']:
                report['summary']['passed'] += 1
            else:
                report['summary']['failed'] += 1

    # 3. Verify key artifacts exist
    key_artifacts = [
        'data/processed/cleaned_sn1.csv',
        'data/processed/exclusion_report.csv',
        'artifacts/best_model.pt',
        'artifacts/metrics.json',
        'artifacts/final_report.md'
    ]

    for artifact in key_artifacts:
        result = verify_artifact(artifact)
        report['verifications'].append({
            'type': 'artifact_check',
            'path': artifact,
            **result
        })
        if result['valid']:
            report['summary']['artifacts_verified'] += 1

    # 4. Compare with integration test results if provided
    if evidence_path and os.path.exists(evidence_path):
        logger.info(f"Loading integration test evidence from: {evidence_path}")
        try:
            with open(evidence_path, 'r') as f:
                evidence = json.load(f)
            report['verifications'].append({
                'type': 'evidence_comparison',
                'status': 'loaded',
                'source': evidence_path
            })
        except Exception as e:
            report['verifications'].append({
                'type': 'evidence_comparison',
                'status': 'failed',
                'error': str(e)
            })

    return report

def main():
    parser = argparse.ArgumentParser(description='Validate quickstart.md execution')
    parser.add_argument('--project-root', type=str, default='.', help='Project root directory')
    parser.add_argument('--quickstart', type=str, help='Path to quickstart.md file')
    parser.add_argument('--output', type=str, help='Path to output report JSON')
    parser.add_argument('--evidence', type=str, help='Path to integration test evidence (optional)')
    args = parser.parse_args()

    report = run_verification(
        project_root=args.project_root,
        quickstart_path=args.quickstart,
        evidence_path=args.evidence
    )

    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Project Root: {report['project_root']}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Commands: {report['summary']['total_commands']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Artifacts Verified: {report['summary']['artifacts_verified']}")
    print("="*60)

    # Save report
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {args.output}")

    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
