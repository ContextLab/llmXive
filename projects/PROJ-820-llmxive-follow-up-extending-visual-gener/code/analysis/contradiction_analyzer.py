import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class StudyFlagError(Exception):
    """Raised when a study needs to be flagged due to high contradiction rates."""
    pass

def load_contradiction_log(log_path: str) -> Dict[str, Any]:
    """
    Load the contradiction log from the specified path.
    
    Args:
        log_path: Path to the contradiction_log.json file.
        
    Returns:
        Dictionary containing the contradiction log data.
        
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Contradiction log not found at {log_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_contradiction_rate(log_data: Dict[str, Any], total_scenes: int) -> float:
    """
    Calculate the contradiction rate from the log data.
    
    Args:
        log_data: The contradiction log dictionary.
        total_scenes: Total number of scenes processed.
        
    Returns:
        The contradiction rate as a percentage (0.0 to 100.0).
        
    Raises:
        ValueError: If total_scenes is zero or negative.
    """
    if total_scenes <= 0:
        raise ValueError("total_scenes must be positive")
    
    contradictions = log_data.get('contradictions', [])
    contradiction_count = len(contradictions)
    
    return (contradiction_count / total_scenes) * 100.0

def verify_contradiction_rate(rate: float, threshold: float = 5.0) -> bool:
    """
    Verify if the contradiction rate is below the threshold.
    
    Args:
        rate: The contradiction rate percentage.
        threshold: The maximum allowed rate (default 5.0%).
        
    Returns:
        True if rate <= threshold, False otherwise.
    """
    return rate <= threshold

def flag_study_if_high_rate(rate: float, threshold: float = 5.0) -> None:
    """
    Flag the study if the contradiction rate exceeds the threshold.
    
    Args:
        rate: The contradiction rate percentage.
        threshold: The maximum allowed rate.
        
    Raises:
        StudyFlagError: If the rate exceeds the threshold.
    """
    if not verify_contradiction_rate(rate, threshold):
        raise StudyFlagError(
            f"Study flagged: Contradiction rate ({rate:.2f}%) exceeds threshold ({threshold}%)"
        )

def run_contradiction_analysis(
    log_path: str,
    total_scenes: int,
    threshold: float = 5.0,
    raise_on_fail: bool = True
) -> Dict[str, Any]:
    """
    Run the full contradiction analysis pipeline.
    
    Args:
        log_path: Path to the contradiction log file.
        total_scenes: Total number of scenes processed.
        threshold: Maximum allowed contradiction rate percentage.
        raise_on_fail: If True, raise an error when threshold is exceeded.
        
    Returns:
        Dictionary containing analysis results.
        
    Raises:
        StudyFlagError: If rate exceeds threshold and raise_on_fail is True.
    """
    log_data = load_contradiction_log(log_path)
    rate = calculate_contradiction_rate(log_data, total_scenes)
    is_valid = verify_contradiction_rate(rate, threshold)
    
    result = {
        'contradiction_rate': rate,
        'threshold': threshold,
        'is_valid': is_valid,
        'contradiction_count': len(log_data.get('contradictions', [])),
        'total_scenes': total_scenes,
        'details': log_data
    }
    
    if not is_valid and raise_on_fail:
        flag_study_if_high_rate(rate, threshold)
        
    return result

def main():
    """Main entry point for the contradiction analyzer script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze contradiction rates in physics simulation logs.')
    parser.add_argument('--log-path', type=str, required=True,
                      help='Path to the contradiction_log.json file')
    parser.add_argument('--total-scenes', type=int, required=True,
                      help='Total number of scenes processed')
    parser.add_argument('--threshold', type=float, default=5.0,
                      help='Maximum allowed contradiction rate percentage')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to save the analysis result JSON (optional)')
    
    args = parser.parse_args()
    
    try:
        result = run_contradiction_analysis(
            args.log_path,
            args.total_scenes,
            args.threshold,
            raise_on_fail=False
        )
        
        print(f"Contradiction Rate: {result['contradiction_rate']:.2f}%")
        print(f"Threshold: {result['threshold']}%")
        print(f"Valid: {result['is_valid']}")
        print(f"Contradictions: {result['contradiction_count']}/{result['total_scenes']}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
            
    except StudyFlagError as e:
        print(f"WARNING: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
