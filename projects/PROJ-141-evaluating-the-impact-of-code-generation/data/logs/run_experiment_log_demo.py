"""
Script to generate a sample experiment.log file for verification.
This script runs the logging functions to produce a real log file.
"""
import sys
import os

# Ensure code is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from logs.experiment import (
    log_consent,
    log_condition_assignment,
    log_session_start,
    log_session_complete
)

def main():
    """Generate a sample experiment log for verification."""
    print("Generating sample experiment log...")
    
    # Simulate a complete experiment flow for a single participant
    participant_id = "P-SAMPLE-001"
    seed = 12345
    
    # 1. Consent
    log_consent(participant_id, True, "IRB-2024-PROJ141")
    
    # 2. Condition Assignment (LLM Assisted)
    log_condition_assignment(participant_id, "llm_assisted", seed)
    
    # 3. Session Start
    log_session_start(participant_id, "llm_assisted", seed, "humaneval")
    
    # 4. Session Complete
    log_session_complete(
        participant_id,
        "llm_assisted",
        seed,
        duration_seconds=1850.5,
        problems_completed=8
    )
    
    # 5. Condition Switch (Baseline)
    log_condition_assignment(participant_id, "baseline", seed)
    
    # 6. Second Session Start
    log_session_start(participant_id, "baseline", seed, "humaneval")
    
    # 7. Second Session Complete
    log_session_complete(
        participant_id,
        "baseline",
        seed,
        duration_seconds=2100.0,
        problems_completed=8
    )
    
    print("Sample log generated successfully.")
    print("Check code/logs/experiment.log for the output.")

if __name__ == "__main__":
    main()
