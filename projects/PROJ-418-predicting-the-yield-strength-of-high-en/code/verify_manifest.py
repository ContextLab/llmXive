"""
Verification script for T122: Verify manifest.json contains all required provenance fields.

This script validates that the generated manifest.json file (produced by T047)
contains all mandatory fields as specified in FR-010 and contracts/manifest.schema.yaml.

Required fields:
- seeds: Random seeds used (split, model, bootstrap)
- hyperparameters: Model hyperparameters
- versions: Library versions
- timestamps: Execution timestamps
- checksums: Dataset and artifact checksums
- descriptor_version_hash: Hash of descriptor calculation
- vif_remediation_decisions: VIF remediation details
- permutation_settings: Permutation testing configuration
"""
import os
import sys
import json
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_FIELDS = [
    "seeds",
    "hyperparameters",
    "versions",
    "timestamps",
    "checksums",
    "descriptor_version_hash",
    "vif_remediation_decisions",
    "permutation_settings"
]

SUBFIELD_REQUIREMENTS = {
    "seeds": ["split", "model", "bootstrap"],
    "hyperparameters": ["random_forest", "linear"],
    "versions": ["python", "numpy", "pandas", "scikit-learn"],
    "timestamps": ["pipeline_start", "pipeline_end", "manifest_generated"],
    "checksums": ["raw_dataset", "processed_dataset", "descriptor_table"],
    "permutation_settings": ["n_permutations", "random_state"]
}

def load_manifest(manifest_path: str) -> dict:
    """Load the manifest.json file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_manifest(manifest: dict) -> tuple[bool, list[str]]:
    """
    Validate the manifest against required fields and subfields.
    
    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []
    
    # Check top-level required fields
    for field in REQUIRED_FIELDS:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")
    
    # Check subfields for complex fields
    for field, subfields in SUBFIELD_REQUIREMENTS.items():
        if field in manifest:
            for subfield in subfields:
                if subfield not in manifest[field]:
                    errors.append(f"Missing subfield '{subfield}' in '{field}'")
        
    # Validate checksums are non-empty strings
    if "checksums" in manifest:
        for key, value in manifest["checksums"].items():
            if not value or not isinstance(value, str):
                errors.append(f"Invalid checksum for {key}: must be non-empty string")
    
    # Validate seeds are integers
    if "seeds" in manifest:
        for key, value in manifest["seeds"].items():
            if not isinstance(value, int):
                errors.append(f"Invalid seed for {key}: must be integer")
    
    return len(errors) == 0, errors

def main():
    """Main entry point for manifest verification."""
    logger.info("Starting manifest verification (T122)")
    
    # Determine manifest path
    manifest_path = Path("output/manifest.json")
    
    try:
        # Load manifest
        manifest = load_manifest(str(manifest_path))
        logger.info(f"Loaded manifest from {manifest_path}")
        
        # Validate manifest
        is_valid, errors = validate_manifest(manifest)
        
        if is_valid:
            logger.info("✅ Manifest validation PASSED: All required fields present")
            print(json.dumps({"status": "pass", "message": "Manifest contains all required provenance fields"}, indent=2))
            return 0
        else:
            logger.error("❌ Manifest validation FAILED:")
            for error in errors:
                logger.error(f"  - {error}")
            print(json.dumps({"status": "fail", "errors": errors}, indent=2))
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"❌ Manifest file not found: {e}")
        print(json.dumps({"status": "fail", "error": "Manifest file not found"}, indent=2))
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in manifest: {e}")
        print(json.dumps({"status": "fail", "error": f"Invalid JSON: {str(e)}"}, indent=2))
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error during validation: {e}")
        print(json.dumps({"status": "fail", "error": str(e)}, indent=2))
        return 1

if __name__ == "__main__":
    sys.exit(main())
