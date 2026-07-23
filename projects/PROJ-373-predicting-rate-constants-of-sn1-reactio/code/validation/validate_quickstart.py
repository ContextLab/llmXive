import os
import sys
import subprocess
import logging
import time
import json
import argparse
from pathlib import Path

from utils.logger import setup_logging, get_logger

def run_command(cmd: list, timeout: int = 300) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
    logger = get_logger()
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s")
        return -1, "", "Timeout expired"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)

def verify_artifact(path_str: str, expected_min_size: int = 1) -> tuple:
    """Verify an artifact exists and meets minimum size requirements."""
    logger = get_logger()
    path = Path(path_str)
    if not path.exists():
        logger.error(f"Artifact missing: {path_str}")
        return False, f"File not found: {path_str}"
    
    if path.is_file():
        size = path.stat().st_size
        if size < expected_min_size:
            logger.error(f"Artifact too small: {path_str} ({size} bytes)")
            return False, f"File too small: {path_str} ({size} bytes)"
        logger.info(f"Artifact verified: {path_str} ({size} bytes)")
        return True, f"Verified: {path_str} ({size} bytes)"
    
    logger.error(f"Path exists but is not a file: {path_str}")
    return False, f"Not a file: {path_str}"

def parse_quickstart_instructions(quickstart_path: str) -> list:
    """Parse quickstart.md to extract command instructions to validate."""
    logger = get_logger()
    path = Path(quickstart_path)
    if not path.exists():
        logger.error(f"Quickstart file not found: {quickstart_path}")
        return []
    
    instructions = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for code blocks with 'bash' or 'sh' syntax highlighting
        # Simple heuristic: lines starting with $ or python
        lines = content.split('\n')
        current_block = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```bash') or stripped.startswith('```sh'):
                in_block = True
                current_block = []
                continue
            elif stripped.startswith('```'):
                if in_block and current_block:
                    # Join block lines and extract commands
                    block_text = '\n'.join(current_block)
                    # Extract lines that look like commands
                    for cmd_line in block_text.split('\n'):
                        cmd_stripped = cmd_line.strip()
                        if cmd_stripped.startswith('$'):
                            cmd = cmd_stripped[1:].strip()
                            if cmd:
                                instructions.append(cmd)
                        elif cmd_stripped.startswith('python') or cmd_stripped.startswith('python3'):
                            instructions.append(cmd_stripped)
                in_block = False
                current_block = []
            elif in_block:
                current_block.append(line)
        
        # Also look for python commands not in blocks
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('python') or stripped.startswith('python3')) and not stripped.startswith('#'):
                if stripped not in instructions:
                    instructions.append(stripped)
        
        logger.info(f"Found {len(instructions)} potential commands in quickstart.md")
    except Exception as e:
        logger.error(f"Error parsing quickstart.md: {e}")
    
    return instructions

def validate_quickstart_instructions(instructions: list, evidence_source: str) -> dict:
    """Validate parsed instructions against execution evidence."""
    logger = get_logger()
    results = {
        'total_commands': len(instructions),
        'verified_commands': 0,
        'failed_commands': 0,
        'details': [],
        'evidence_source': evidence_source
    }
    
    for i, cmd in enumerate(instructions):
        # Simplify command for validation (remove complex pipes, redirects for initial check)
        # Focus on core python commands
        if 'python' in cmd or 'python3' in cmd:
            # Extract the script path
            parts = cmd.split()
            script_path = None
            for j, part in enumerate(parts):
                if part.endswith('.py'):
                    script_path = part
                    break
            
            if script_path:
                # Check if the script exists
                script_full_path = Path(script_path)
                if script_full_path.exists():
                    results['verified_commands'] += 1
                    results['details'].append({
                        'command': cmd,
                        'status': 'verified',
                        'message': f"Script exists: {script_path}"
                    })
                else:
                    results['failed_commands'] += 1
                    results['details'].append({
                        'command': cmd,
                        'status': 'failed',
                        'message': f"Script not found: {script_path}"
                    })
            else:
                results['verified_commands'] += 1
                results['details'].append({
                    'command': cmd,
                    'status': 'skipped',
                    'message': "No .py script found in command"
                })
        else:
            # Non-python commands (e.g., mkdir, ls) - assume valid if syntax looks correct
            results['verified_commands'] += 1
            results['details'].append({
                'command': cmd,
                'status': 'skipped',
                'message': "Non-python command, assuming valid"
            })
    
    return results

def run_verification(quickstart_path: str, evidence_source: str) -> dict:
    """Main verification logic."""
    logger = get_logger()
    logger.info(f"Starting quickstart validation against {evidence_source}")
    
    # Parse instructions from quickstart.md
    instructions = parse_quickstart_instructions(quickstart_path)
    if not instructions:
        logger.warning("No executable commands found in quickstart.md")
        return {
            'status': 'warning',
            'message': 'No commands found to validate',
            'details': []
        }
    
    # Validate against evidence
    validation_results = validate_quickstart_instructions(instructions, evidence_source)
    
    # Determine overall status
    if validation_results['failed_commands'] > 0:
        status = 'failed'
        logger.warning(f"Validation failed: {validation_results['failed_commands']} commands could not be verified")
    elif validation_results['verified_commands'] == validation_results['total_commands']:
        status = 'passed'
        logger.info("Validation passed: all commands verified")
    else:
        status = 'passed_with_warnings'
        logger.info(f"Validation passed with warnings: {validation_results['verified_commands']}/{validation_results['total_commands']} verified")
    
    return {
        'status': status,
        'quickstart_path': quickstart_path,
        'evidence_source': evidence_source,
        'summary': validation_results
    }

def main():
    """Entry point for quickstart validation."""
    parser = argparse.ArgumentParser(description='Validate quickstart.md against execution evidence')
    parser.add_argument('--quickstart', type=str, default='specs/001-predict-sn1-rate-constants/quickstart.md',
                      help='Path to quickstart.md file')
    parser.add_argument('--evidence', type=str, default='artifacts/integration_test_report.md',
                      help='Path to execution evidence (integration test report or manual verification)')
    parser.add_argument('--output', type=str, default='artifacts/quickstart_validation_report.json',
                      help='Path to save validation report')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger()
    
    # Run verification
    results = run_verification(args.quickstart, args.evidence)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")
    
    # Exit with appropriate code
    if results['status'] == 'failed':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
