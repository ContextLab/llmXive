import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
import yaml

# Constants for schema versions
SCHEMA_V1_SYNTHETIC = "1.0.0"
SCHEMA_V2_REAL = "2.0.0"

@dataclass
class VerificationStatus:
    status: str  # "PASS", "FAIL", "WARN"
    message: str

@dataclass
class CitationSchema:
    source: str
    identifier: str
    url: Optional[str] = None

@dataclass
class VerificationResult:
    passed: bool
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]

class ReferenceValidator:
    """
    Validates data manifests against the synthetic_data_manifest_schema.yaml.
    Enforces Constitution Principle I (Reproducibility) by checking:
    1. Schema version compliance.
    2. Generator script checksum integrity (for synthetic).
    3. Presence of Chain of Custody logs (mandatory for real data).
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.schema_path = self.project_root / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "synthetic_data_manifest_schema.yaml"
        self.state_path = self.project_root / "state" / "projects"
        
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {self.schema_path}")

    def load_schema(self) -> Dict[str, Any]:
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculates SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def validate_manifest(self, manifest_path: Path) -> VerificationResult:
        """
        Validates a manifest file against the schema.
        Returns a VerificationResult with pass/fail status and details.
        """
        errors = []
        warnings = []
        
        if not manifest_path.exists():
            return VerificationResult(
                passed=False,
                details={},
                errors=[f"Manifest file not found: {manifest_path}"],
                warnings=[]
            )

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            return VerificationResult(
                passed=False,
                details={},
                errors=[f"Invalid JSON in manifest: {e}"],
                warnings=[]
            )

        schema = self.load_schema()
        data_type = manifest.get("data_type")
        
        if data_type == "synthetic":
            result = self._validate_synthetic(manifest, schema, errors, warnings)
        elif data_type == "real":
            result = self._validate_real(manifest, schema, errors, warnings)
        else:
            errors.append(f"Unknown data_type: {data_type}. Must be 'synthetic' or 'real'.")
            return VerificationResult(passed=False, details={}, errors=errors, warnings=warnings)

        return VerificationResult(
            passed=len(errors) == 0,
            details=result,
            errors=errors,
            warnings=warnings
        )

    def _validate_synthetic(self, manifest: Dict, schema: Dict, errors: List[str], warnings: List[str]) -> Dict:
        """Validates synthetic manifest (schema_v1)."""
        details = {}
        
        # Check version
        if manifest.get("schema_version") != SCHEMA_V1_SYNTHETIC:
            errors.append(f"Invalid schema_version for synthetic data. Expected {SCHEMA_V1_SYNTHETIC}, got {manifest.get('schema_version')}")
        
        # Check generator script existence and checksum
        generator_script = manifest.get("generator_script")
        if not generator_script:
            errors.append("Missing 'generator_script' in synthetic manifest.")
        else:
            script_path = self.project_root / generator_script
            if not script_path.exists():
                errors.append(f"Generator script not found: {generator_script}")
            else:
                actual_checksum = self.calculate_file_checksum(script_path)
                stored_checksum = manifest.get("generator_checksum")
                
                if not stored_checksum:
                    errors.append("Missing 'generator_checksum' in synthetic manifest.")
                elif actual_checksum != stored_checksum:
                    errors.append(f"Generator checksum mismatch. Expected {stored_checksum}, got {actual_checksum}. The script has been modified since data generation.")
                else:
                    details["generator_verified"] = True

        # Check CoC log (should be null for synthetic)
        coc_log = manifest.get("chain_of_custody_log")
        if coc_log is not None:
            warnings.append("Non-null chain_of_custody_log found in synthetic manifest. This is allowed but unusual.")
        else:
            details["coc_log_null"] = True

        # Check note
        if not manifest.get("note"):
            warnings.append("Missing 'note' field in synthetic manifest.")
        
        return details

    def _validate_real(self, manifest: Dict, schema: Dict, errors: List[str], warnings: List[str]) -> Dict:
        """Validates real manifest (schema_v2)."""
        details = {}

        # Check version
        if manifest.get("schema_version") != SCHEMA_V2_REAL:
            errors.append(f"Invalid schema_version for real data. Expected {SCHEMA_V2_REAL}, got {manifest.get('schema_version')}")

        # Check CoC log (MUST exist)
        coc_log = manifest.get("chain_of_custody_log")
        if not coc_log or len(coc_log.strip()) == 0:
            errors.append("CRITICAL: 'chain_of_custody_log' is missing or empty in real data manifest. This violates Constitution Principle I.")
        else:
            details["coc_log_present"] = True

        # Check source details
        if not manifest.get("source_identifier"):
            errors.append("Missing 'source_identifier' in real data manifest.")
        if not manifest.get("source_url"):
            errors.append("Missing 'source_url' in real data manifest.")
        
        return details

    def update_state_with_checksum(self, project_id: str, artifact_path: Path, checksum: str):
        """
        Updates the project state YAML file to record the checksum of an artifact.
        Used to record the checksum of code/data_generator.py in state/projects/...yaml.
        """
        state_file = self.state_path / f"{project_id}.yaml"
        
        # Ensure state directory exists
        self.state_path.mkdir(parents=True, exist_ok=True)

        if state_file.exists():
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        else:
            state_data = {"project_id": project_id, "artifact_hashes": {}}

        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

        # Record the checksum
        artifact_name = artifact_path.name
        state_data["artifact_hashes"][artifact_name] = checksum

        with open(state_file, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)

    def verify_and_record(self, manifest_path: Path, project_id: str):
        """
        Validates the manifest and if valid, records the generator script checksum in the state file.
        """
        result = self.validate_manifest(manifest_path)
        
        if result.passed:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            if manifest.get("data_type") == "synthetic":
                generator_script = manifest.get("generator_script")
                if generator_script:
                    script_path = self.project_root / generator_script
                    if script_path.exists():
                        checksum = self.calculate_file_checksum(script_path)
                        self.update_state_with_checksum(project_id, script_path, checksum)
                        return True, "Validation passed and checksum recorded."
                    else:
                        return False, "Validation passed but generator script not found for checksum recording."
            return True, "Validation passed."
        
        return False, "; ".join(result.errors)

def create_sample_schema():
    """Helper to create a sample schema structure for testing."""
    return {
        "schema_version": SCHEMA_V1_SYNTHETIC,
        "data_type": "synthetic",
        "generator_script": "code/data_generator.py",
        "generator_checksum": "placeholder",
        "parameters": {"seed": 42, "n": 100},
        "chain_of_custody_log": None,
        "note": "Sample synthetic manifest"
    }
