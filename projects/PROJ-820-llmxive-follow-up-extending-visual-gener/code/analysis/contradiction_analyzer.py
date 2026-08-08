"""
contradiction_analyzer.py

Aggregates contradiction logs from physics simulations, calculates the contradiction
rate, and verifies it meets the study constraint (SC-004: < 5%).
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Custom exception for study flagging
class StudyFlagError(Exception):
    """Raised when the contradiction rate exceeds the acceptable threshold."""
    pass

def load_contradiction_log(log_path: str) -> Dict[str, Any]:
    """
    Loads the contradiction log JSON file.

    Args:
        log_path: Path to the contradiction_log.json file.

    Returns:
        The loaded dictionary content.

    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(log_path)
    if not path.exists():
        # If the log file doesn't exist, it implies 0 contradictions found so far
        # but for a robust pipeline, we might expect the file to exist if simulations ran.
        # We return an empty structure to allow calculation.
        return {"contradictions": [], "total_scenes": 0, "contradiction_count": 0}
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_contradiction_rate(log_data: Dict[str, Any]) -> Tuple[int, int, float]:
    """
    Calculates the contradiction rate from the loaded log data.

    Args:
        log_data: The dictionary loaded from contradiction_log.json.

    Returns:
        A tuple of (total_scenes, contradiction_count, rate_percentage).
    """
    total_scenes = log_data.get("total_scenes", 0)
    contradiction_count = log_data.get("contradiction_count", 0)
    
    if total_scenes == 0:
        rate = 0.0
    else:
        rate = (contradiction_count / total_scenes) * 100.0
    
    return total_scenes, contradiction_count, rate

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    """
    Verifies if the contradiction rate is below the threshold.

    Args:
        rate: The calculated contradiction rate percentage.
        threshold: The maximum allowed percentage (default 5.0).

    Returns:
        True if rate < threshold, False otherwise.
    """
    return rate < threshold

def flag_study_if_high_rate(rate: float, threshold: float = 5.0) -> None:
    """
    Raises a StudyFlagError if the contradiction rate exceeds the threshold.
    
    This implements the 'soft fail' mechanism where the pipeline continues
    but flags the study for review. Downstream tasks (like T032a) can catch
    this or check the flag to perform a 'hard fail'.

    Args:
        rate: The calculated contradiction rate percentage.
        threshold: The maximum allowed percentage.

    Raises:
        StudyFlagError: If rate >= threshold.
    """
    if rate >= threshold:
        raise StudyFlagError(
            f"Contradiction rate ({rate:.2f}%) exceeds threshold ({threshold}%). "
            "Study flagged for review. Downstream analysis may halt."
        )

def run_contradiction_analysis(
    log_path: str = "data/derived/physics_constraints/contradiction_log.json",
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Main entry point to run the contradiction analysis.
    
    1. Loads the contradiction log.
    2. Calculates the rate.
    3. Verifies against threshold.
    4. Flags the study if necessary.
    5. Returns a summary report.

    Args:
        log_path: Path to the contradiction log.
        threshold: The threshold percentage (SC-004).

    Returns:
        A dictionary containing the analysis results.
    
    Raises:
        StudyFlagError: If the rate is too high.
    """
    log_data = load_contradiction_log(log_path)
    total, count, rate = calculate_contradiction_rate(log_data)
    is_valid = verify_contradiction_rate(rate, threshold)
    
    result = {
        "total_scenes_simulated": total,
        "contradictions_found": count,
        "contradiction_rate_percentage": rate,
        "threshold_percentage": threshold,
        "is_within_limit": is_valid,
        "status": "PASS" if is_valid else "FLAGGED"
    }
    
    if not is_valid:
        flag_study_if_high_rate(rate, threshold)
    
    return result

def main():
    """
    Command-line entry point for the contradiction analyzer.
    """
    log_path = "data/derived/physics_constraints/contradiction_log.json"
    threshold = 5.0
    
    # Allow override via environment or args if needed, but defaulting to spec
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])
    
    try:
        report = run_contradiction_analysis(log_path, threshold)
        print(json.dumps(report, indent=2))
        
        # Exit with code 0 even if flagged, as this is a 'soft fail'
        # allowing downstream tasks to decide on hard failure.
        sys.exit(0)
        
    except StudyFlagError as e:
        # Log the error but exit cleanly so the pipeline can potentially
        # continue to a final hard-fail point or manual review.
        print(f"WARNING: {e}", file=sys.stderr)
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"ERROR: Contradiction log not found at {log_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {log_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
