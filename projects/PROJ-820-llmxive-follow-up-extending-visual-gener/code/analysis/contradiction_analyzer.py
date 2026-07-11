"""
T016: Analyze contradiction logs to calculate contradiction rate and verify SC-004 compliance.

This module aggregates contradiction logs from `data/derived/physics_constraints/contradiction_log.json`,
calculates the contradiction rate percentage, and verifies it is < 5% (SC-004).

If the rate > 5%, it flags the study (soft fail) but continues to allow downstream analysis
to halt the pipeline if required.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Constants
CONTRADICTION_LOG_PATH = "data/derived/physics_constraints/contradiction_log.json"
CONTRADICTION_RATE_THRESHOLD = 0.05  # 5%
STUDY_FLAG_PATH = "data/derived/physics_constraints/study_flag.json"


class StudyFlagError(Exception):
    """Raised when the study is flagged due to high contradiction rate."""
    pass


def load_contradiction_log(log_path: str = CONTRADICTION_LOG_PATH) -> Dict[str, Any]:
    """
    Load the contradiction log JSON file.
    
    Args:
        log_path: Path to the contradiction log file.
        
    Returns:
        Dictionary containing the contradiction log data.
        
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the log file is not valid JSON.
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Contradiction log not found at {log_path}")
    
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_contradiction_rate(log_data: Dict[str, Any]) -> Tuple[float, int, int]:
    """
    Calculate the contradiction rate from the log data.
    
    Args:
        log_data: The loaded contradiction log dictionary.
        
    Returns:
        Tuple of (contradiction_rate, total_scenes, contradictory_scenes).
    """
    total_scenes = log_data.get("total_scenes", 0)
    contradictory_scenes = log_data.get("contradictory_scenes", 0)
    
    if total_scenes == 0:
        return 0.0, 0, 0
    
    rate = contradictory_scenes / total_scenes
    return rate, total_scenes, contradictory_scenes


def verify_contradiction_rate(rate: float, threshold: float = CONTRADICTION_RATE_THRESHOLD) -> bool:
    """
    Verify if the contradiction rate is below the threshold.
    
    Args:
        rate: The calculated contradiction rate.
        threshold: The maximum allowed rate (default 0.05).
        
    Returns:
        True if rate <= threshold, False otherwise.
    """
    return rate <= threshold


def flag_study_if_high_rate(
    rate: float, 
    total_scenes: int, 
    contradictory_scenes: int,
    threshold: float = CONTRADICTION_RATE_THRESHOLD
) -> Optional[Dict[str, Any]]:
    """
    Flag the study if the contradiction rate exceeds the threshold.
    
    This is a soft fail: it logs the flag but does not halt the pipeline.
    Downstream tasks (e.g., T032a) can read this flag and halt if required.
    
    Args:
        rate: The calculated contradiction rate.
        total_scenes: Total number of scenes processed.
        contradictory_scenes: Number of contradictory scenes.
        threshold: The maximum allowed rate.
        
    Returns:
        A dictionary containing the flag details if rate > threshold, None otherwise.
    """
    if rate > threshold:
        flag_data = {
            "status": "FLAGGED",
            "reason": "Contradiction rate exceeds threshold",
            "contradiction_rate": rate,
            "threshold": threshold,
            "total_scenes": total_scenes,
            "contradictory_scenes": contradictory_scenes,
            "message": f"Study flagged: Contradiction rate ({rate:.2%}) exceeds threshold ({threshold:.2%})."
        }
        
        # Ensure the directory exists
        output_dir = Path(STUDY_FLAG_PATH).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(STUDY_FLAG_PATH, 'w', encoding='utf-8') as f:
            json.dump(flag_data, f, indent=2)
        
        return flag_data
    
    return None


def run_contradiction_analysis(
    log_path: str = CONTRADICTION_LOG_PATH,
    threshold: float = CONTRADICTION_RATE_THRESHOLD
) -> Dict[str, Any]:
    """
    Run the full contradiction analysis pipeline.
    
    1. Load the contradiction log.
    2. Calculate the contradiction rate.
    3. Verify against the threshold (SC-004).
    4. Flag the study if rate > threshold (soft fail).
    
    Args:
        log_path: Path to the contradiction log file.
        threshold: The maximum allowed contradiction rate.
        
    Returns:
        A dictionary containing the analysis results.
    """
    print(f"Loading contradiction log from: {log_path}")
    log_data = load_contradiction_log(log_path)
    
    print("Calculating contradiction rate...")
    rate, total_scenes, contradictory_scenes = calculate_contradiction_rate(log_data)
    
    print(f"Total scenes: {total_scenes}")
    print(f"Contradictory scenes: {contradictory_scenes}")
    print(f"Contradiction rate: {rate:.2%}")
    
    is_valid = verify_contradiction_rate(rate, threshold)
    
    result = {
        "total_scenes": total_scenes,
        "contradictory_scenes": contradictory_scenes,
        "contradiction_rate": rate,
        "threshold": threshold,
        "is_valid": is_valid,
        "status": "PASS" if is_valid else "FLAGGED"
    }
    
    if not is_valid:
        flag_data = flag_study_if_high_rate(rate, total_scenes, contradictory_scenes, threshold)
        result["flag_details"] = flag_data
        print(f"⚠️  STUDY FLAGGED: Contradiction rate ({rate:.2%}) exceeds threshold ({threshold:.2%})")
        print(f"Flag details saved to: {STUDY_FLAG_PATH}")
    else:
        print(f"✅ Contradiction rate ({rate:.2%}) is within threshold ({threshold:.2%})")
    
    return result


def main():
    """Main entry point for the contradiction analyzer."""
    print("=== T016: Contradiction Rate Analysis ===")
    
    try:
        results = run_contradiction_analysis()
        
        # Print summary
        print("\n--- Analysis Summary ---")
        print(f"Status: {results['status']}")
        print(f"Total Scenes: {results['total_scenes']}")
        print(f"Contradictory Scenes: {results['contradictory_scenes']}")
        print(f"Contradiction Rate: {results['contradiction_rate']:.2%}")
        print(f"Threshold: {results['threshold']:.2%}")
        
        if results['status'] == "FLAGGED":
            print("\n⚠️  WARNING: The study has been flagged due to high contradiction rate.")
            print("Downstream analysis may halt the pipeline based on this flag.")
        
        return results
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Ensure T012 has been run and the contradiction log exists.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in contradiction log: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()