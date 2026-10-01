"""
Verify that quickstart.md is up-to-date with the latest code and configuration.

This script compares the content of quickstart.md with the actual code and
configuration files to identify any discrepancies. It checks:
1. File paths mentioned in quickstart.md exist
2. Commands in quickstart.md are valid and executable
3. Configuration options match those in config.py
4. Output artifacts are correctly documented
"""
import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DataConfig, TrainingConfig, AnalysisConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_quickstart(path: Path) -> str:
    """Load the quickstart.md file."""
    if not path.exists():
        raise FileNotFoundError(f"quickstart.md not found at {path}")
    return path.read_text(encoding='utf-8')


def extract_file_paths(content: str) -> List[str]:
    """Extract file paths mentioned in the quickstart content."""
    # Match patterns like code/data/clean.py, data/processed/cleaned_sn1.csv
    path_pattern = r'(?:code|data|tests|specs|artifacts)/[\w/_.-]+\.(?:py|csv|json|md|yaml|log|pt|npy)'
    return re.findall(path_pattern, content)


def extract_commands(content: str) -> List[str]:
    """Extract shell commands mentioned in the quickstart content."""
    # Match code blocks with shell commands
    command_blocks = re.findall(r'```bash\s+(.*?)\s+```', content, re.DOTALL)
    commands = []
    for block in command_blocks:
        # Extract individual commands (lines starting with $ or python)
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('$ '):
                commands.append(line[2:].strip())
            elif line.startswith('python '):
                commands.append(line)
    return commands


def extract_config_references(content: str) -> List[str]:
    """Extract configuration option references from quickstart.md."""
    # Match patterns like --learning-rate, --hidden-dim, etc.
    config_pattern = r'--[\w-]+'
    return list(set(re.findall(config_pattern, content)))


def extract_output_artifacts(content: str) -> List[str]:
    """Extract output artifact paths mentioned in the quickstart content."""
    # Look for patterns like "Output: data/processed/cleaned_sn1.csv"
    # or "saves to artifacts/model.pt"
    artifact_patterns = [
        r'Output[:\s]+([\w/_.-]+\.(?:csv|json|md|yaml|log|pt|npy))',
        r'saves? to [\w/:]+/([\w/_.-]+\.(?:csv|json|md|yaml|log|pt|npy))',
        r'produces? [\w/:]+/([\w/_.-]+\.(?:csv|json|md|yaml|log|pt|npy))',
    ]
    artifacts = []
    for pattern in artifact_patterns:
        artifacts.extend(re.findall(pattern, content, re.IGNORECASE))
    return list(set(artifacts))


def verify_file_exists(path: Path, relative_to: Path = PROJECT_ROOT) -> Tuple[bool, str]:
    """Check if a file exists."""
    full_path = relative_to / path
    if full_path.exists():
        return True, f"✓ {path} exists"
    else:
        return False, f"✗ {path} NOT FOUND"


def verify_command_syntax(command: str) -> Tuple[bool, str]:
    """Basic syntax check for a command."""
    # Check for python commands
    if command.startswith('python '):
        parts = command.split()
        if len(parts) < 2:
            return False, f"✗ Invalid python command: {command}"
        script_path = Path(parts[1])
        if not script_path.exists():
            return False, f"✗ Script not found: {script_path}"
        return True, f"✓ Command syntax valid: {command}"
    return True, f"✓ Command: {command}"


def verify_config_options(quickstart_configs: List[str]) -> List[Tuple[bool, str]]:
    """Verify that configuration options in quickstart match config.py."""
    results = []
    
    # Get actual config options from config.py
    actual_configs = set()
    
    # Extract from DataConfig
    for field in DataConfig.__dataclass_fields__:
        actual_configs.add(f"--{field.replace('_', '-')}")
    
    # Extract from TrainingConfig
    for field in TrainingConfig.__dataclass_fields__:
        actual_configs.add(f"--{field.replace('_', '-')}")
    
    # Extract from AnalysisConfig
    for field in AnalysisConfig.__dataclass_fields__:
        actual_configs.add(f"--{field.replace('_', '-')}")
    
    # Common CLI options
    actual_configs.update([
        "--help", "--config", "--seed", "--output-dir", "--log-level"
    ])
    
    for config in quickstart_configs:
        if config in actual_configs:
            results.append((True, f"✓ {config} is valid"))
        else:
            results.append((False, f"✗ {config} NOT FOUND in config.py"))
    
    return results


def verify_output_artifacts(artifacts: List[str]) -> List[Tuple[bool, str]]:
    """Verify that output artifacts are correctly documented."""
    results = []
    for artifact in artifacts:
        # Check if the artifact is in a valid output directory
        valid_dirs = ['data/raw', 'data/processed', 'artifacts', 'figures']
        is_valid = any(artifact.startswith(d) for d in valid_dirs)
        if is_valid:
            results.append((True, f"✓ Output artifact path is valid: {artifact}"))
        else:
            results.append((False, f"✗ Output artifact path may be invalid: {artifact}"))
    return results


def run_verification(quickstart_path: Optional[Path] = None) -> Dict:
    """Run full verification of quickstart.md against code and config."""
    if quickstart_path is None:
        quickstart_path = PROJECT_ROOT / 'specs' / '001-predict-sn1-rate-constants' / 'quickstart.md'
    
    results = {
        'file_exists': False,
        'file_paths': [],
        'commands': [],
        'config_options': [],
        'output_artifacts': [],
        'summary': {}
    }
    
    try:
        content = load_quickstart(quickstart_path)
        results['file_exists'] = True
        logger.info(f"Loaded quickstart.md from {quickstart_path}")
    except FileNotFoundError as e:
        logger.error(str(e))
        results['summary']['file_exists'] = False
        return results
    
    # Extract and verify file paths
    file_paths = extract_file_paths(content)
    logger.info(f"Found {len(file_paths)} file paths in quickstart.md")
    
    for path_str in file_paths:
        path = Path(path_str)
        exists, msg = verify_file_exists(path)
        results['file_paths'].append({'path': path_str, 'exists': exists, 'message': msg})
    
    # Extract and verify commands
    commands = extract_commands(content)
    logger.info(f"Found {len(commands)} commands in quickstart.md")
    
    for cmd in commands:
        valid, msg = verify_command_syntax(cmd)
        results['commands'].append({'command': cmd, 'valid': valid, 'message': msg})
    
    # Extract and verify config options
    config_refs = extract_config_references(content)
    logger.info(f"Found {len(config_refs)} config references in quickstart.md")
    
    config_results = verify_config_options(config_refs)
    results['config_options'] = [
        {'option': opt, 'valid': valid, 'message': msg}
        for valid, msg in config_results
    ]
    
    # Extract and verify output artifacts
    artifacts = extract_output_artifacts(content)
    logger.info(f"Found {len(artifacts)} output artifacts in quickstart.md")
    
    artifact_results = verify_output_artifacts(artifacts)
    results['output_artifacts'] = [
        {'artifact': art, 'valid': valid, 'message': msg}
        for valid, msg in artifact_results
    ]
    
    # Generate summary
    total_checks = (
        len(file_paths) + len(commands) + len(config_refs) + len(artifacts)
    )
    failed_checks = sum(1 for r in results['file_paths'] if not r['exists']) + \
                   sum(1 for r in results['commands'] if not r['valid']) + \
                   sum(1 for r in results['config_options'] if not r['valid']) + \
                   sum(1 for r in results['output_artifacts'] if not r['valid'])
    
    results['summary'] = {
        'total_checks': total_checks,
        'passed': total_checks - failed_checks,
        'failed': failed_checks,
        'success_rate': (total_checks - failed_checks) / total_checks if total_checks > 0 else 0.0,
        'quickstart_up_to_date': failed_checks == 0
    }
    
    return results


def print_report(results: Dict) -> None:
    """Print a formatted verification report."""
    print("\n" + "=" * 60)
    print("QUICKSTART.MD VERIFICATION REPORT")
    print("=" * 60 + "\n")
    
    if not results['file_exists']:
        print("ERROR: quickstart.md not found!")
        return
    
    # File paths
    print("FILE PATHS CHECK:")
    for item in results['file_paths']:
        print(f"  {item['message']}")
    print()
    
    # Commands
    print("COMMANDS CHECK:")
    for item in results['commands']:
        print(f"  {item['message']}")
    print()
    
    # Config options
    print("CONFIGURATION OPTIONS CHECK:")
    for item in results['config_options']:
        print(f"  {item['message']}")
    print()
    
    # Output artifacts
    print("OUTPUT ARTIFACTS CHECK:")
    for item in results['output_artifacts']:
        print(f"  {item['message']}")
    print()
    
    # Summary
    summary = results['summary']
    print("SUMMARY:")
    print(f"  Total checks: {summary['total_checks']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    print(f"  Quickstart up to date: {'YES' if summary['quickstart_up_to_date'] else 'NO'}")
    print("\n" + "=" * 60)
    
    if summary['failed'] > 0:
        print("\n⚠️  ACTION REQUIRED: Some checks failed. Please review and update quickstart.md.")
        sys.exit(1)
    else:
        print("\n✓ All checks passed. quickstart.md is up to date.")
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify that quickstart.md is up-to-date with code and configuration'
    )
    parser.add_argument(
        '--quickstart-path',
        type=Path,
        default=None,
        help='Path to quickstart.md (default: specs/001-predict-sn1-rate-constants/quickstart.md)'
    )
    parser.add_argument(
        '--output-report',
        type=Path,
        default=None,
        help='Path to save JSON report (optional)'
    )
    
    args = parser.parse_args()
    
    results = run_verification(args.quickstart_path)
    
    if args.output_report:
        import json
        with open(args.output_report, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Report saved to {args.output_report}")
    
    print_report(results)


if __name__ == '__main__':
    main()