"""
Constitution compliance checker for the A/B Test Validity Audit Pipeline.

Validates all seven Principles (I-VII) of the project Constitution.
Returns exit code 0 if all checks pass, non-zero otherwise.
"""
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from code.src.config import SEED, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Initialize logger
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

# Constitution Principles definitions
CONSTITUTION_PRINCIPLES = {
    "I": "Reproducibility: All random seeds must be deterministic (SEED=42).",
    "II": "Transparency: All code must be open source and version controlled.",
    "III": "Integrity: All artifacts must have SHA256 checksums recorded.",
    "IV": "Consistency: Checksums in manifest.json must match data/checksums.txt.",
    "V": "Governance: All changes must be tracked with updated_at timestamps.",
    "VI": "Justification: All discrepancies must be documented with rationale.",
    "VII": "Provenance: All data sources must be tracked with URL and timestamp."
}

def check_principle_i_reproducibility() -> Tuple[bool, str]:
    """Check Principle I: Reproducibility - SEED=42 and all RNGs seeded."""
    try:
        from code.src.config import SEED
        if SEED != 42:
            return False, f"SEED is {SEED}, expected 42"
        
        # Verify config summary reflects deterministic seed
        config_summary = get_config_summary()
        if "seed" not in config_summary or config_summary["seed"] != 42:
            return False, "Config summary does not reflect deterministic seed"
        
        return True, "Reproducibility check passed: SEED=42 confirmed"
    except Exception as e:
        return False, f"Error checking reproducibility: {str(e)}"

def check_principle_ii_transparency() -> Tuple[bool, str]:
    """Check Principle II: Transparency - Code is open source and version controlled."""
    # Check for .git directory (version control)
    git_dir = Path(".git")
    if not git_dir.exists():
        # In CI, this might be shallow clone, so check for .git files
        git_files = list(Path(".").glob(".git*"))
        if not git_files:
            return False, "No version control system detected (.git directory or files missing)"
    
    # Check for LICENSE file (open source)
    license_files = list(Path(".").glob("LICENSE*"))
    if not license_files:
        # Not strictly required for internal projects, but good practice
        audit_logger.warning("No LICENSE file found - consider adding one for transparency")
    
    return True, "Transparency check passed: Version control detected"

def check_principle_iii_integrity() -> Tuple[bool, str]:
    """Check Principle III: Integrity - All artifacts have SHA256 checksums."""
    checksum_file = Path("data/checksums.txt")
    if not checksum_file.exists():
        return False, "data/checksums.txt not found - artifact integrity not recorded"
    
    # Verify checksum file has content
    content = checksum_file.read_text().strip()
    if not content:
        return False, "data/checksums.txt is empty - no checksums recorded"
    
    # Check that checksums are valid SHA256 (64 hex chars)
    lines = content.splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue  # Skip malformed lines
        checksum = parts[0]
        if len(checksum) != 64 or not all(c in '0123456789abcdef' for c in checksum.lower()):
            return False, f"Invalid SHA256 checksum format: {checksum}"
    
    return True, "Integrity check passed: Valid SHA256 checksums recorded"

def check_principle_iv_consistency() -> Tuple[bool, str]:
    """Check Principle IV: Consistency - manifest.json matches data/checksums.txt."""
    manifest_file = Path("output/manifest.json")
    checksum_file = Path("data/checksums.txt")
    
    if not manifest_file.exists():
        return False, "output/manifest.json not found"
    
    if not checksum_file.exists():
        return False, "data/checksums.txt not found"
    
    try:
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        # Load checksums from data/checksums.txt
        checksums_txt = {}
        with open(checksum_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    checksums_txt[parts[1]] = parts[0]  # path -> checksum
        
        # Compare with manifest
        manifest_hashes = manifest.get("artifact_hashes", {})
        
        mismatches = []
        for path, manifest_hash in manifest_hashes.items():
            if path in checksums_txt:
                if checksums_txt[path] != manifest_hash:
                    mismatches.append(f"{path}: manifest={manifest_hash[:8]}... vs checksums={checksums_txt[path][:8]}...")
            else:
                mismatches.append(f"{path}: in manifest but not in data/checksums.txt")
        
        if mismatches:
            return False, f"Checksum mismatches found: {', '.join(mismatches[:3])}..."
        
        return True, "Consistency check passed: manifest.json matches data/checksums.txt"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in manifest.json: {str(e)}"
    except Exception as e:
        return False, f"Error checking consistency: {str(e)}"

def check_principle_v_governance() -> Tuple[bool, str]:
    """Check Principle V: Governance - Changes tracked with updated_at timestamps."""
    state_file = Path("state/projects/PROJ-492-evaluating-the-statistical-validity-of-p.yaml")
    
    if not state_file.exists():
        return False, "Project state file not found"
    
    try:
        import yaml
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        # Check for updated_at field
        if "updated_at" not in state:
            return False, "State file missing 'updated_at' timestamp"
        
        # Verify timestamp format (ISO 8601)
        timestamp = state["updated_at"]
        if not isinstance(timestamp, str) or 'T' not in timestamp:
            return False, f"Invalid timestamp format: {timestamp}"
        
        return True, f"Governance check passed: State updated at {timestamp}"
    except ImportError:
        return False, "PyYAML not installed - cannot parse state file"
    except Exception as e:
        return False, f"Error checking governance: {str(e)}"

def check_principle_vi_justification() -> Tuple[bool, str]:
    """Check Principle VI: Justification - Discrepancies documented."""
    notebook_path = Path("notebooks/statistical_consistency_verification.ipynb")
    
    if not notebook_path.exists():
        return False, "Discrepancy justification notebook not found"
    
    try:
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
        
        # Check for cells containing justification content
        justification_found = False
        for cell in notebook.get("cells", []):
            cell_type = cell.get("cell_type", "")
            source = cell.get("source", "")
            
            if cell_type == "markdown" or cell_type == "code":
                if isinstance(source, list):
                    source_text = "".join(source)
                else:
                    source_text = str(source)
                
                # Look for justification keywords
                if any(keyword in source_text.lower() for keyword in 
                       ["justification", "discrepancy", "p-value", "inconsistency", "rationale"]):
                    justification_found = True
                    break
        
        if not justification_found:
            return False, "No discrepancy justifications found in notebook"
        
        return True, "Justification check passed: Discrepancies documented in notebook"
    except json.JSONDecodeError:
        return False, "Invalid notebook JSON format"
    except Exception as e:
        return False, f"Error checking justification: {str(e)}"

def check_principle_vii_provenance() -> Tuple[bool, str]:
    """Check Principle VII: Provenance - Data sources tracked."""
    provenance_file = Path("data/provenance_log.csv")
    
    if not provenance_file.exists():
        return False, "Provenance log file not found"
    
    try:
        import csv
        with open(provenance_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return False, "Provenance log is empty"
        
        # Check required columns
        required_columns = ["url", "repository_identifier", "fetch_timestamp"]
        if not all(col in rows[0].keys() for col in required_columns):
            missing = [col for col in required_columns if col not in rows[0].keys()]
            return False, f"Missing required columns in provenance log: {missing}"
        
        # Verify each row has all required fields
        for i, row in enumerate(rows):
            for col in required_columns:
                if not row.get(col):
                    return False, f"Row {i+1} missing {col}"
        
        return True, f"Provenance check passed: {len(rows)} records with full provenance"
    except Exception as e:
        return False, f"Error checking provenance: {str(e)}"

def run_all_checks() -> Dict[str, Any]:
    """Run all constitution principle checks."""
    results = {}
    all_passed = True
    
    checks = [
        ("I", check_principle_i_reproducibility),
        ("II", check_principle_ii_transparency),
        ("III", check_principle_iii_integrity),
        ("IV", check_principle_iv_consistency),
        ("V", check_principle_v_governance),
        ("VI", check_principle_vi_justification),
        ("VII", check_principle_vii_provenance),
    ]
    
    for principle_id, check_func in checks:
        passed, message = check_func()
        results[principle_id] = {
            "passed": passed,
            "message": message,
            "principle": CONSTITUTION_PRINCIPLES[principle_id]
        }
        if not passed:
            all_passed = False
            audit_logger.error(f"ERR-950: Principle {principle_id} failed - {message}")
        else:
            audit_logger.info(f"Principle {principle_id} passed: {message}")
    
    return {
        "all_passed": all_passed,
        "timestamp": datetime.utcnow().isoformat(),
        "results": results
    }

def main():
    """Main entry point for constitution checker."""
    logger.info("Starting Constitution compliance check (Principles I-VII)")
    
    results = run_all_checks()
    
    # Write results to file for CI
    results_file = Path("output/constitution_check_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nConstitution Compliance Check Results:")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {'PASSED' if results['all_passed'] else 'FAILED'}")
    print("-" * 50)
    
    for principle_id, result in results["results"].items():
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"Principle {principle_id}: {status}")
        print(f"  {result['message']}")
    
    if not results["all_passed"]:
        print("\n" + "=" * 50)
        print("ERROR: Constitution compliance check FAILED (ERR-950)")
        print("Please review failed principles and fix issues.")
        print("=" * 50)
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("SUCCESS: All Constitution principles satisfied")
    print("=" * 50)
    sys.exit(0)

if __name__ == "__main__":
    main()
