"""
Integrity Verification Script
Compares checksums of artifacts against the state file.
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path

def calculate_file_checksum(file_path):
    """Calculates SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def load_state_file(state_path):
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: State file not found: {state_path}")
        return None
    except yaml.YAMLError:
        print(f"Error: Invalid YAML in state file: {state_path}")
        return None

def discover_artifacts(data_dir):
    """Discovers all relevant artifact files in the data directory."""
    artifacts = {}
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(('.csv', '.json', '.parquet', '.md')):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(data_dir.parent)
                artifacts[str(rel_path)] = full_path
    return artifacts

def verify_artifacts(artifacts, state_data):
    """Verifies checksums of artifacts against state data."""
    report = {
        'verified': True,
        'details': []
    }

    expected_hashes = state_data.get('artifact_hashes', {})

    for rel_path, full_path in artifacts.items():
        current_hash = calculate_file_checksum(full_path)
        expected_hash = expected_hashes.get(str(rel_path))

        if expected_hash is None:
            report['details'].append({
                'file': str(rel_path),
                'status': 'missing_checksum_in_state',
                'message': 'File exists but no checksum in state file.'
            })
            # Not necessarily a failure, but a warning
            continue

        if current_hash != expected_hash:
            report['verified'] = False
            report['details'].append({
                'file': str(rel_path),
                'status': 'mismatch',
                'expected': expected_hash,
                'actual': current_hash
            })
        else:
            report['details'].append({
                'file': str(rel_path),
                'status': 'verified',
                'hash': current_hash
            })

    return report

def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    state_path = base_dir / 'state' / 'projects' / 'PROJ-340-investigating-the-correlation-between-gu.yaml'
    output_path = base_dir / 'data' / 'results' / 'integrity_verification_report.json'

    # Load State
    state_data = load_state_file(state_path)
    if not state_data:
        print("FATAL: Could not load state file. Integrity check aborted.")
        sys.exit(1)

    # Discover Artifacts
    artifacts = discover_artifacts(data_dir)
    if not artifacts:
        print("WARNING: No artifacts found in data directory.")
        # Still generate a report
    else:
        print(f"Discovered {len(artifacts)} artifacts.")

    # Verify
    report = verify_artifacts(artifacts, state_data)

    # Write Output
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Integrity verification complete. Report saved to {output_path}")
    if not report['verified']:
        print("INTEGRITY CHECK FAILED. Mismatches detected.")
        sys.exit(1)
    else:
        print("INTEGRITY CHECK PASSED.")
        sys.exit(0)

if __name__ == '__main__':
    main()
