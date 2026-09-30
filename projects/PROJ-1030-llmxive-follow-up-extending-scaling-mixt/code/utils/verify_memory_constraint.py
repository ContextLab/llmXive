"""
Verify that memory usage during feature extraction stayed within the 7 GB constraint.

This script reads the memory_log.json generated during the extraction phase (T017),
checks the peak memory usage for every batch/clip, and writes a verification report
to data/processed/memory_verification.json.

Artifact: data/processed/memory_verification.json
Dependency: data/processed/memory_log.json (from T017)
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
MEMORY_LOG_PATH = Path("data/processed/memory_log.json")
VERIFICATION_OUTPUT_PATH = Path("data/processed/memory_verification.json")

def load_memory_log(log_path: Path) -> List[Dict[str, Any]]:
    """Load the memory log JSON file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Memory log not found at {log_path}. "
                                "Ensure T017 (logging) has been executed successfully.")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_memory_usage(log_entries: List[Dict[str, Any]]) -> Tuple[bool, float, List[Dict[str, Any]]]:
    """
    Analyze memory log entries to find peak usage and violations.
    
    Returns:
        Tuple of (passed, global_peak_mb, violation_details)
    """
    if not log_entries:
        return False, 0.0, [{"reason": "Empty memory log", "clip_id": "N/A"}]

    global_peak = 0.0
    violations = []

    for entry in log_entries:
        peak_mb = entry.get("peak_mb", 0.0)
        if peak_mb > global_peak:
            global_peak = peak_mb

        if peak_mb > MEMORY_LIMIT_MB:
            violations.append({
                "clip_id": entry.get("clip_id", "unknown"),
                "stage": entry.get("stage", "unknown"),
                "peak_mb": peak_mb,
                "limit_mb": MEMORY_LIMIT_MB,
                "overage_mb": peak_mb - MEMORY_LIMIT_MB,
                "timestamp": entry.get("timestamp", "unknown")
            })

    passed = len(violations) == 0
    return passed, global_peak, violations

def generate_verification_report(
    passed: bool, 
    global_peak_mb: float, 
    violations: List[Dict[str, Any]],
    log_path: str,
    output_path: str
) -> Dict[str, Any]:
    """Generate the verification report dictionary."""
    report = {
        "status": "PASS" if passed else "FAIL",
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "memory_limit_mb": MEMORY_LIMIT_MB,
        "global_peak_memory_mb": round(global_peak_mb, 2),
        "global_peak_memory_gb": round(global_peak_mb / 1024, 4),
        "violations_found": len(violations),
        "violations": violations,
        "source_log": log_path,
        "verification_timestamp": "2023-10-01T12:00:00" # Placeholder, actual time handled by caller if needed
    }
    
    # Save to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    print(f"Starting memory constraint verification...")
    print(f"Checking log: {MEMORY_LOG_PATH}")
    print(f"Limit: {MEMORY_LIMIT_GB} GB ({MEMORY_LIMIT_MB} MB)")

    try:
        log_entries = load_memory_log(MEMORY_LOG_PATH)
        print(f"Loaded {len(log_entries)} memory log entries.")

        passed, global_peak, violations = analyze_memory_usage(log_entries)
        
        report = generate_verification_report(
            passed=passed,
            global_peak_mb=global_peak,
            violations=violations,
            log_path=str(MEMORY_LOG_PATH),
            output_path=str(VERIFICATION_OUTPUT_PATH)
        )

        print("-" * 40)
        print(f"VERIFICATION RESULT: {report['status']}")
        print(f"Global Peak Memory: {report['global_peak_memory_gb']:.4f} GB")
        print(f"Limit: {MEMORY_LIMIT_GB} GB")
        
        if not passed:
            print(f"VIOLATIONS DETECTED: {len(violations)}")
            for v in violations[:5]: # Show first 5
                print(f"  - {v['clip_id']} ({v['stage']}): {v['peak_mb']/1024:.2f} GB")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
        else:
            print("All memory checks passed.")
        
        print(f"Report saved to: {VERIFICATION_OUTPUT_PATH}")
        return 0 if passed else 1

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in memory log: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
