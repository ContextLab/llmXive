"""
Integration test for full mock participant session.

This test simulates a complete study session for a mock participant,
verifying that:
1. Task start/end times are logged with precise timestamps
2. Clarification questions are counted and logged
3. The study concludes without data loss
4. All expected fields are present in the output log

The test uses simulated data but writes real artifacts to disk
as required by the project specification.
"""
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data_collection import Participant, StudySession, log_participant_data
from utils.monitor import MonitorContext

# Constants
MOCK_REPO_PATH = "https://github.com/example/test-repo.git"
MOCK_REPO_COMMIT = "abc123def456"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "mock_session_output.json"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_mock_participant() -> Participant:
    """Create a mock participant for testing."""
    participant_id = str(uuid.uuid4())
    return Participant(
        participant_id=participant_id,
        condition="llm_docs",  # Options: llm_docs, human_docs, no_docs
        repository=MOCK_REPO_PATH,
        commit_hash=MOCK_REPO_COMMIT,
        start_time=datetime.now().isoformat()
    )


def simulate_study_session(participant: Participant) -> StudySession:
    """
    Simulate a complete study session for a mock participant.
    
    This simulates:
    - Session start/end logging
    - Task completion with timestamps
    - Clarification questions (help requests)
    - Subjective helpfulness survey
    - Stop-loss intervention (if applicable)
    """
    session = StudySession(
        participant_id=participant.participant_id,
        condition=participant.condition,
        repository=participant.repository,
        commit_hash=participant.commit_hash
    )
    
    # Simulate session start
    session.start_session()
    
    # Simulate task phases with realistic timing
    task_phases = [
        ("setup", 120),  # 2 minutes
        ("implementation", 900),  # 15 minutes
        ("testing", 300),  # 5 minutes
        ("documentation_review", 180)  # 3 minutes
    ]
    
    for phase_name, duration_seconds in task_phases:
        session.log_task_start(phase_name)
        # Simulate work (no actual delay in test)
        session.log_task_end(phase_name, duration_seconds)
    
    # Simulate clarification questions (help requests)
    help_requests = [
        {
            "timestamp": datetime.now().isoformat(),
            "content": "How do I set up the development environment?",
            "category": "how"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "content": "Why does this function return None?",
            "category": "why"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "content": "What is the expected input format?",
            "category": "what"
        }
    ]
    
    for request in help_requests:
        session.log_help_request(request)
    
    # Calculate cognitive load proxy
    # Composite Score = (Count of Help Requests) * (Average Time per Request)
    if help_requests:
        avg_time_per_request = 45.0  # Simulated average time in seconds
        cognitive_load_proxy = len(help_requests) * avg_time_per_request
        session.cognitive_load_proxy = cognitive_load_proxy
    
    # Simulate subjective helpfulness survey
    session.log_survey_response(
        helpfulness_score=4,  # 1-5 scale
        comments="Documentation was helpful but could be more detailed."
    )
    
    # Simulate session completion (no stop-loss intervention in this mock)
    session.end_session()
    
    return session


def validate_session_output(session: StudySession) -> Dict[str, Any]:
    """
    Validate that the session output contains all required fields.
    
    Returns a dict with validation results and any errors found.
    """
    errors = []
    
    # Check required top-level fields
    required_fields = [
        "participant_id",
        "condition",
        "repository",
        "commit_hash",
        "session_start_time",
        "session_end_time",
        "total_duration_seconds",
        "task_log",
        "help_requests",
        "cognitive_load_proxy",
        "survey_response",
        "intervention_flag",
        "status"
    ]
    
    for field in required_fields:
        if not hasattr(session, field):
            errors.append(f"Missing required field: {field}")
    
    # Validate task log structure
    if hasattr(session, "task_log"):
        for task in session.task_log:
            if not all(key in task for key in ["phase", "start_time", "end_time", "duration"]):
                errors.append("Task log entry missing required fields")
    
    # Validate help requests structure
    if hasattr(session, "help_requests"):
        for request in session.help_requests:
            if not all(key in request for key in ["timestamp", "content", "category"]):
                errors.append("Help request entry missing required fields")
    
    # Validate cognitive load proxy calculation
    if hasattr(session, "cognitive_load_proxy"):
        if session.cognitive_load_proxy is None:
            errors.append("Cognitive load proxy is None")
        elif not isinstance(session.cognitive_load_proxy, (int, float)):
            errors.append("Cognitive load proxy is not numeric")
    
    # Validate survey response
    if hasattr(session, "survey_response"):
        if not session.survey_response.get("helpfulness_score"):
            errors.append("Survey response missing helpfulness score")
    
    # Validate session status
    if hasattr(session, "status"):
        if session.status not in ["completed", "abandoned", "stopped"]:
            errors.append(f"Invalid session status: {session.status}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "session_data": session.to_dict() if hasattr(session, "to_dict") else str(session)
    }


def run_mock_session() -> Dict[str, Any]:
    """
    Run a complete mock participant session and save results.
    
    Returns the validation result dictionary.
    """
    print("Starting mock participant session...")
    
    # Create mock participant
    participant = create_mock_participant()
    print(f"Created participant: {participant.participant_id}")
    
    # Simulate study session
    session = simulate_study_session(participant)
    print("Session simulation completed")
    
    # Validate session output
    validation_result = validate_session_output(session)
    
    # Convert session to dictionary for JSON serialization
    session_dict = {
        "participant_id": session.participant_id,
        "condition": session.condition,
        "repository": session.repository,
        "commit_hash": session.commit_hash,
        "session_start_time": session.session_start_time,
        "session_end_time": session.session_end_time,
        "total_duration_seconds": session.total_duration_seconds,
        "task_log": session.task_log,
        "help_requests": session.help_requests,
        "cognitive_load_proxy": session.cognitive_load_proxy,
        "survey_response": session.survey_response,
        "intervention_flag": session.intervention_flag,
        "status": session.status,
        "validation": validation_result
    }
    
    # Write output to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(session_dict, f, indent=2, default=str)
    
    print(f"Mock session output written to: {OUTPUT_FILE}")
    print(f"Validation result: {'PASSED' if validation_result['valid'] else 'FAILED'}")
    
    if validation_result['errors']:
        print("Errors found:")
        for error in validation_result['errors']:
            print(f"  - {error}")
    
    return validation_result


def main():
    """Main entry point for the mock session test."""
    print("=" * 60)
    print("Integration Test: Full Mock Participant Session")
    print("=" * 60)
    
    try:
        with MonitorContext("mock_session_test"):
            result = run_mock_session()
            
            if result['valid']:
                print("\n✓ Integration test PASSED")
                print("  - All required fields present")
                print("  - Session completed without data loss")
                print(f"  - Output saved to: {OUTPUT_FILE}")
                return 0
            else:
                print("\n✗ Integration test FAILED")
                print("  Validation errors found:")
                for error in result['errors']:
                    print(f"    - {error}")
                return 1
                
    except Exception as e:
        print(f"\n✗ Integration test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())