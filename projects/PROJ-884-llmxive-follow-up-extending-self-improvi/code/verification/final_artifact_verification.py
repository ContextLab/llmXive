import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Constants for required artifacts
REQUIRED_ARTIFACTS = [
    "data/processed/pre_registration.yaml",
    "data/processed/scaling_raw_logs.json",
    "data/processed/literature_gpu_factor.json",
    "data/processed/calibrated_tdp.json",
    "data/processed/neural_baseline_logs.json",
    "data/processed/distribution_validation.json",
    "data/processed/validation_gate.json",
    "data/processed/exclusions.json",
    "data/processed/calibration_run.json",
    "data/processed/distribution_report.json",
]

SCHEMA_CHECKS = {
    "data/processed/pre_registration.yaml": ["framework", "alpha", "hypothesis"],
    "data/processed/scaling_raw_logs.json": ["records"],
    "data/processed/literature_gpu_factor.json": ["factor", "citation", "source"],
    "data/processed/calibrated_tdp.json": ["tdp_watts", "source", "error_margin"],
    "data/processed/neural_baseline_logs.json": ["records"],
    "data/processed/distribution_validation.json": ["is_valid", "power_estimate"],
    "data/processed/validation_gate.json": ["status"],
    "data/processed/exclusions.json": ["events"],
    "data/processed/calibration_run.json": ["workload_type", "estimated_tdp_watts"],
    "data/processed/distribution_report.json": ["sample_size", "distribution"],
}

def load_yaml_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a YAML file and return its contents as a dictionary."""
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file {path}: {e}")
        return None

def load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {path}: {e}")
        return None

def verify_artifact(path: str, schema_keys: List[str]) -> bool:
    """Verify that an artifact exists and contains required keys."""
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return False

    if path.endswith('.yaml'):
        data = load_yaml_file(path)
    elif path.endswith('.json'):
        data = load_json_file(path)
    else:
        print(f"UNKNOWN FORMAT: {path}")
        return False

    if data is None:
        print(f"INVALID CONTENT: {path}")
        return False

    missing_keys = [key for key in schema_keys if key not in data]
    if missing_keys:
        print(f"MISSING KEYS in {path}: {missing_keys}")
        return False

    print(f"VERIFIED: {path}")
    return True

def main():
    """Main entry point for final artifact verification."""
    print("Starting Final Artifact Verification...")
    all_passed = True

    for artifact_path in REQUIRED_ARTIFACTS:
        schema_keys = SCHEMA_CHECKS.get(artifact_path, [])
        if not verify_artifact(artifact_path, schema_keys):
            all_passed = False

    if all_passed:
        print("\n✅ All required artifacts verified successfully.")
        # Write a verification gate pass file
        gate_path = "data/processed/final_verification_gate.json"
        with open(gate_path, 'w') as f:
            json.dump({
                "status": "PASS",
                "timestamp": "2023-10-27T12:00:00Z",
                "artifacts_verified": len(REQUIRED_ARTIFACTS)
            }, f, indent=2)
        print(f"Verification gate file written to {gate_path}")
        return 0
    else:
        print("\n❌ Verification failed. Some artifacts are missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())