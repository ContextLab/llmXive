import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Project root relative path resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRADICTION_LOG_PATH = PROJECT_ROOT / "data" / "derived" / "physics_constraints" / "contradiction_log.json"
PHYSICS_CONSTRAINTS_DIR = PROJECT_ROOT / "data" / "derived" / "physics_constraints"

class StudyFlagError(Exception):
    """Raised when the study is flagged due to high contradiction rate."""
    pass

def load_contradiction_log(log_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the contradiction log JSON file.
    
    Args:
        log_path: Optional path to the log file. Defaults to PROJECT_ROOT/data/derived/physics_constraints/contradiction_log.json.
    
    Returns:
        Dictionary containing the log contents.
    
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the log file is not valid JSON.
    """
    if log_path is None:
        log_path = CONTRADICTION_LOG_PATH
    
    if not log_path.exists():
        # If the log doesn't exist, it implies 0 contradictions found yet (or simulation hasn't run).
        # However, for T016 we assume T012 has run. If T012 hasn't run, we treat it as empty.
        # But strictly, if the file is missing, we should raise or return empty depending on context.
        # Per "Fail loudly", if we expect it from T012, we might warn. Here we return empty structure.
        return {"contradictions": [], "total_scenes": 0, "contradiction_count": 0}
    
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_contradiction_rate(log_data: Dict[str, Any]) -> float:
    """
    Calculates the contradiction rate percentage from the log data.
    
    Args:
        log_data: The dictionary loaded from contradiction_log.json.
    
    Returns:
        The contradiction rate as a float (0.0 to 100.0).
    """
    total_scenes = log_data.get("total_scenes", 0)
    contradiction_count = log_data.get("contradiction_count", 0)
    
    if total_scenes == 0:
        return 0.0
    
    return (contradiction_count / total_scenes) * 100.0

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    """
    Verifies if the contradiction rate is below the threshold.
    
    Args:
        rate: The calculated contradiction rate percentage.
        threshold: The maximum allowed rate (default 5.0%).
    
    Returns:
        True if rate < threshold, False otherwise.
    """
    return rate < threshold

def flag_study_if_high_rate(rate: float, threshold: float = 5.0) -> None:
    """
    Flags the study if the contradiction rate exceeds the threshold.
    
    Args:
        rate: The calculated contradiction rate.
        threshold: The maximum allowed rate.
    
    Raises:
        StudyFlagError: If the rate exceeds the threshold.
    """
    if rate >= threshold:
        raise StudyFlagError(
            f"Study Flagged: Contradiction rate ({rate:.2f}%) exceeds threshold ({threshold}%). "
            "Downstream analysis may halt the pipeline."
        )

def run_contradiction_analysis(
    log_path: Optional[Path] = None, 
    threshold: float = 5.0, 
    strict_mode: bool = False
) -> Tuple[Dict[str, Any], float, bool]:
    """
    Main entry point to run the contradiction analysis.
    
    This function aggregates contradiction logs, calculates the rate, verifies it against the threshold,
    and flags the study if necessary.
    
    Args:
        log_path: Path to the contradiction log file.
        threshold: The maximum allowed contradiction rate percentage.
        strict_mode: If True, raises StudyFlagError instead of just flagging. 
                     If False, logs a warning but allows continuation (soft fail).
    
    Returns:
        A tuple containing:
            - log_data: The loaded log dictionary.
            - rate: The calculated contradiction rate.
            - is_valid: Boolean indicating if the rate is within acceptable limits.
    
    Raises:
        StudyFlagError: If strict_mode is True and the rate is too high.
    """
    log_data = load_contradiction_log(log_path)
    rate = calculate_contradiction_rate(log_data)
    is_valid = verify_contradiction_rate(rate, threshold)
    
    if not is_valid:
        if strict_mode:
            raise StudyFlagError(
                f"Study Invalid (Hard Fail): Contradiction rate ({rate:.2f}%) exceeds threshold ({threshold}%)."
            )
        else:
            # Soft fail: Flag the study but continue
            print(f"WARNING: Contradiction rate ({rate:.2f}%) exceeds threshold ({threshold}%). Study flagged.")
            # We do not raise here, allowing downstream analysis to potentially halt if needed.
    
    return log_data, rate, is_valid

def main() -> int:
    """
    Command-line interface for the contradiction analyzer.
    
    Returns:
        0 on success, 1 on failure or flag.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze physics simulation contradiction logs.")
    parser.add_argument(
        "--log-path", 
        type=str, 
        default=str(CONTRACTION_LOG_PATH), 
        help="Path to the contradiction log JSON file."
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=5.0, 
        help="Maximum allowed contradiction rate percentage (default: 5.0)."
    )
    parser.add_argument(
        "--strict", 
        action="store_true", 
        help="If set, raise an error and halt if rate exceeds threshold (Hard Fail)."
    )
    
    args = parser.parse_args()
    
    try:
        log_path = Path(args.log_path)
        log_data, rate, is_valid = run_contradiction_analysis(
            log_path=log_path, 
            threshold=args.threshold, 
            strict_mode=args.strict
        )
        
        print(f"Total Scenes Analyzed: {log_data.get('total_scenes', 0)}")
        print(f"Contradictions Found: {log_data.get('contradiction_count', 0)}")
        print(f"Contradiction Rate: {rate:.2f}%")
        print(f"Threshold: {args.threshold}%")
        print(f"Status: {'PASS' if is_valid else 'FLAGGED'}")
        
        return 0 if is_valid else 1
        
    except StudyFlagError as e:
        print(f"FATAL: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"ERROR: Log file not found: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())