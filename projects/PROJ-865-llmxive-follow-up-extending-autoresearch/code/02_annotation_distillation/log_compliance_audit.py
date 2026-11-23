import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
FALLBACK_STATUS_PATH = DATA_DERIVED_DIR / "fallback_status.json"
COMPLIANCE_AUDIT_LOG_PATH = DATA_DERIVED_DIR / "compliance_audit_log.json"

def load_fallback_status(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the fallback_status.json file if it exists.
    Returns None if the file does not exist or is empty.
    """
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                return None
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read fallback status: {e}", file=sys.stderr)
        return None

def generate_audit_entry(fallback_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate the compliance audit entry based on the fallback status.
    
    If fallback_data is None (file missing):
      - fallback_method: "none"
      - ram_peak_gb: 0.0 (or a default)
      - attempt_count: 0
      - rule_coverage_pct: 100.0 (assuming full success if no fallback)
    
    If fallback_data exists:
      - Extract method, ram, attempts, coverage from the fallback record.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if fallback_data is None:
        return {
            "timestamp": timestamp,
            "fallback_method": "none",
            "ram_peak_gb": 0.0,
            "attempt_count": 0,
            "rule_coverage_pct": 100.0
        }

    # Map expected keys from fallback_status.json to audit log keys
    # Assuming fallback_status.json has structure similar to T013 description:
    # { "method": "regex", "ram_peak_gb": 7.2, "attempt_count": 2, "coverage": 0.85 }
    # Adjust keys if the actual T013 output uses different names.
    
    method = fallback_data.get("method", fallback_data.get("fallback_method", "unknown"))
    ram = float(fallback_data.get("ram_peak_gb", fallback_data.get("ram_peak", 0.0)))
    attempts = int(fallback_data.get("attempt_count", fallback_data.get("attempts", 0)))
    coverage = float(fallback_data.get("coverage", fallback_data.get("rule_coverage_pct", 0.0))) * 100.0

    return {
        "timestamp": timestamp,
        "fallback_method": method,
        "ram_peak_gb": ram,
        "attempt_count": attempts,
        "rule_coverage_pct": coverage
    }

def save_audit_log(audit_entry: Dict[str, Any], path: Path) -> None:
    """
    Write the audit entry to the compliance audit log file.
    Overwrites the file if it exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(audit_entry, f, indent=2)
    print(f"Compliance audit log saved to: {path}")

def main() -> int:
    """
    Main entry point for T013b.
    Checks for fallback_status.json and generates compliance_audit_log.json.
    """
    # Ensure derived directory exists
    DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    # Load fallback status
    fallback_data = load_fallback_status(FALLBACK_STATUS_PATH)
    
    if fallback_data is None:
        print("No fallback_status.json found. Assuming successful run without fallback.")
    else:
        print(f"Fallback detected. Method: {fallback_data.get('method', 'unknown')}")

    # Generate audit entry
    audit_entry = generate_audit_entry(fallback_data)

    # Save audit log
    save_audit_log(audit_entry, COMPLIANCE_AUDIT_LOG_PATH)

    return 0

if __name__ == "__main__":
    sys.exit(main())