import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from utils.config import get_path, get_hyperparameter
from data.models import TaskOutcome

# Constants for failure categories
EXCLUDED_CATEGORIES = {"latency", "perception"}
SEMANTIC_THRESHOLD = 0.40

def load_categorized_outcomes() -> List[Dict[str, Any]]:
    """
    Load the categorized task outcomes from the processed data directory.
    Expects 'data/processed/evaluation_outcomes.json' (produced by T035).
    """
    path = get_path("processed", "evaluation_outcomes.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Categorized outcomes file not found at {path}. "
            "Ensure T035 (filter_latency_failures) has been executed first."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'outcomes' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'outcomes' in data:
        return data['outcomes']
    else:
        raise ValueError(f"Unexpected format in {path}: expected list or dict with 'outcomes' key")

def calculate_semantic_ratio(outcomes: List[Dict[str, Any]]) -> float:
    """
    Calculate the ratio of semantic failures to total failures, 
    excluding perception and latency failures.
    
    Logic:
    1. Filter outcomes to include only those where 'success' is False.
    2. Further filter to exclude outcomes where 'failure_category' is in [latency, perception].
    3. Count 'semantic' failures in the remaining set.
    4. Calculate ratio: semantic_count / total_filtered_failures.
    
    Returns 0.0 if the denominator is 0 (no relevant failures).
    """
    # Step 1 & 2: Filter for failures excluding perception/latency
    relevant_failures = []
    
    for outcome in outcomes:
        if not outcome.get("success", True):
            failure_cat = outcome.get("failure_category", "").lower()
            if failure_cat not in EXCLUDED_CATEGORIES:
                relevant_failures.append(outcome)
    
    total_relevant = len(relevant_failures)
    
    if total_relevant == 0:
        return 0.0
    
    # Step 3: Count semantic failures
    semantic_count = sum(
        1 for f in relevant_failures 
        if f.get("failure_category", "").lower() == "semantic"
    )
    
    # Step 4: Calculate ratio
    return semantic_count / total_relevant

def write_verification_result(semantic_ratio: float, passed: bool, output_path: Path) -> None:
    """
    Write the verification result to the specified JSON file.
    """
    result = {
        "metric": "semantic_failure_ratio",
        "value": semantic_ratio,
        "threshold": SEMANTIC_THRESHOLD,
        "passed": passed,
        "excluded_categories": list(EXCLUDED_CATEGORIES),
        "timestamp": os.popen('date -Iseconds 2>/dev/null || date').read().strip()
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

def write_research_conclusion(passed: bool, ratio: float, output_path: Path) -> None:
    """
    Write the research conclusion to the research_conclusions.json file.
    """
    conclusion_text = (
        f"Research Conclusion: SC-004 Met" if passed 
        else f"Research Conclusion: SC-004 Not Met"
    )
    
    # Load existing conclusions if any, or start new
    conclusions = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                conclusions = data if isinstance(data, list) else [data]
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Append new conclusion entry
    entry = {
        "check": "SC-004",
        "description": "Semantic Failure Ratio >= 40%",
        "result": "PASSED" if passed else "FAILED",
        "ratio": ratio,
        "conclusion": conclusion_text,
        "timestamp": os.popen('date -Iseconds 2>/dev/null || date').read().strip()
    }
    conclusions.append(entry)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(conclusions, f, indent=2)

def main():
    print("Starting Semantic Failure Analysis (T038)...")
    
    try:
        # Load outcomes
        outcomes = load_categorized_outcomes()
        print(f"Loaded {len(outcomes)} task outcomes.")
        
        # Calculate ratio
        semantic_ratio = calculate_semantic_ratio(outcomes)
        print(f"Calculated Semantic Failure Ratio: {semantic_ratio:.4f}")
        
        # Determine pass/fail
        passed = semantic_ratio >= SEMANTIC_THRESHOLD
        status = "PASSED" if passed else "FAILED"
        print(f"SC-004 Status: {status} (Threshold: {SEMANTIC_THRESHOLD})")
        
        # Define output paths
        artifacts_dir = get_path("artifacts")
        sc004_path = artifacts_dir / "sc004_verification.json"
        conclusions_path = artifacts_dir / "research_conclusions.json"
        
        # Write results
        write_verification_result(semantic_ratio, passed, sc004_path)
        print(f"Wrote verification result to {sc004_path}")
        
        write_research_conclusion(passed, semantic_ratio, conclusions_path)
        print(f"Wrote research conclusion to {conclusions_path}")
        
        if not passed:
            print(f"WARNING: Research Conclusion logged: SC-004 Not Met")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
