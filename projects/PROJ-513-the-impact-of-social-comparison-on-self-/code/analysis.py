import os
import sys
import json
import time
import random
import numpy as np

from typing import Dict, Any, List, Optional

# Pin random seed as per T011
RANDOM_SEED = 42

def set_random_seed(seed: int = RANDOM_SEED) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def get_random_seed() -> int:
    """Return the current random seed."""
    return RANDOM_SEED

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from a JSON file if it exists."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def validate_environment() -> bool:
    """Validate that required directories and files exist."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/stimuli/ai",
        "data/stimuli/human"
    ]
    for d in required_dirs:
        if not os.path.isdir(d):
            print(f"ERROR: Required directory not found: {d}")
            return False
    return True

def load_processed_data(filepath: str = "data/processed/cleaned_sessions.jsonl") -> List[Dict[str, Any]]:
    """Load processed session data from a JSONL file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def validate_completeness(data: List[Dict[str, Any]], threshold: float = 0.95) -> bool:
    """Validate that at least 95% of rows are complete."""
    if not data:
        return False
    
    complete_count = 0
    for row in data:
        # Check for required fields
        required_fields = ['stimulus_id', 'origin', 'timestamp', 'BISS_score', 
                         'participant_id', 'INCOM_score', 'usage_frequency', 'is_complete']
        if all(field in row and row[field] is not None and row[field] != '' 
               for field in required_fields):
            complete_count += 1
    
    completeness_ratio = complete_count / len(data)
    return completeness_ratio >= threshold

def validate_participant_count(data: List[Dict[str, Any]], min_count: int = 150) -> bool:
    """Validate that there are at least 150 unique participants."""
    participant_ids = set(row.get('participant_id') for row in data if row.get('participant_id'))
    return len(participant_ids) >= min_count

def calculate_completion_rate(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate completion rate (full sequence vs enrolled) for SC-004.
    
    Returns a dictionary with:
    - completion_rate: ratio of completed sessions to total sessions
    - completion_rate_target: target value (0.80)
    - total_sessions: count of all sessions
    - completed_sessions: count of complete sessions
    """
    if not data:
        return {
            "completion_rate": 0.0,
            "completion_rate_target": 0.80,
            "total_sessions": 0,
            "completed_sessions": 0
        }
    
    total_sessions = len(data)
    completed_sessions = sum(1 for row in data if row.get('is_complete', False))
    
    completion_rate = completed_sessions / total_sessions if total_sessions > 0 else 0.0
    
    return {
        "completion_rate": completion_rate,
        "completion_rate_target": 0.80,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions
    }

def run_analysis() -> Dict[str, Any]:
    """Run the full analysis pipeline and return results."""
    start_time = time.time()
    
    # Set random seed
    set_random_seed()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Load processed data
    try:
        data = load_processed_data()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Validate completeness
    if not validate_completeness(data):
        print("ERROR: Data completeness < 95%")
        sys.exit(1)
    
    # Validate participant count
    if not validate_participant_count(data):
        print("ERROR: Participant count < 150")
        sys.exit(1)
    
    # Calculate completion rate (T033)
    completion_metrics = calculate_completion_rate(data)
    
    # Placeholder for LME results (T025) - would be computed here
    # For now, we use the structure expected by the output file
    results = {
        "f_stat": 0.0,
        "p_value": 1.0,
        "eta_squared": 0.0,
        "n": len(data),
        "corrected_p_value": 1.0,
        "outlier_ids": [],
        "sensitivity_analysis_delta_f": 0.0,
        "completion_rate": completion_metrics["completion_rate"],
        "completion_rate_target": completion_metrics["completion_rate_target"],
        "total_sessions": completion_metrics["total_sessions"],
        "completed_sessions": completion_metrics["completed_sessions"],
        "pipeline_runtime_seconds": time.time() - start_time
    }
    
    return results

def main():
    """Main entry point for analysis script."""
    try:
        results = run_analysis()
        
        # Write results to file
        output_path = "data/analysis_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Analysis complete. Results written to {output_path}")
        print(f"Completion Rate: {results['completion_rate']:.2%} (Target: {results['completion_rate_target']:.2%})")
        print(f"Pipeline Runtime: {results['pipeline_runtime_seconds']:.2f} seconds")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
