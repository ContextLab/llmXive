"""
Experiment module for User Story 1: Controlled Onboarding Experiment Execution.
Handles participant assignment, mock session generation, logging, and raw data export.
"""
import argparse
import json
import logging
import os
import random
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging to avoid circular import issues with utils/logging.py
# Ensure the logs directory exists before configuring file handlers
LOGS_DIR = Path(__file__).parent.parent / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "experiment.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Output path for raw participant logs
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PARTICIPANT_LOGS_PATH = RAW_DATA_DIR / "participant_logs.json"

# Constants for Stop-Loss intervention
MAX_TASK_TIME_SECONDS = 2700  # 45 minutes

def calculate_checksum(data: Dict[str, Any]) -> str:
    """Calculate SHA-256 checksum of the data dictionary."""
    serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def assign_participant(participant_id: int, mode: str) -> Dict[str, Any]:
    """
    Assign a participant to a condition (LLM, Human, None).
    """
    conditions = ["LLM", "Human", "None"]
    condition = random.choice(conditions) if mode != "mock" else random.choice(conditions)
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "assignment_timestamp": datetime.now().isoformat(),
        "status": "assigned"
    }

def log_session_start(participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Log the start of a study session."""
    participant_data["session_start"] = datetime.now().isoformat()
    participant_data["clarification_questions"] = []
    participant_data["clarification_question_count"] = 0
    participant_data["intervention_status"] = "none"
    participant_data["max_time"] = None
    participant_data["helpfulness_rating"] = None
    participant_data["status"] = "in_progress"
    return participant_data

def log_help_request(participant_data: Dict[str, Any], question_text: str, question_type: str) -> Dict[str, Any]:
    """
    Log a clarification question.
    question_type: 'keyword' (how/why) or 'moderator-tag'
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "content": question_text,
        "type": question_type
    }
    participant_data["clarification_questions"].append(entry)
    participant_data["clarification_question_count"] = len(participant_data["clarification_questions"])
    return participant_data

def apply_stop_loss_intervention(participant_data: Dict[str, Any], elapsed_time: float) -> Dict[str, Any]:
    """
    Apply Stop-Loss intervention if time exceeds threshold.
    """
    if elapsed_time > MAX_TASK_TIME_SECONDS:
        participant_data["intervention_status"] = "stop_loss"
        participant_data["max_time"] = MAX_TASK_TIME_SECONDS
        participant_data["status"] = "failed"
        logger.info(f"Stop-loss triggered for participant {participant_data['participant_id']} at {elapsed_time}s")
    return participant_data

def capture_helpfulness_survey(participant_data: Dict[str, Any], rating: int) -> Dict[str, Any]:
    """Capture subjective helpfulness rating (1-5)."""
    participant_data["helpfulness_rating"] = rating
    return participant_data

def handle_abandoned_records(participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark incomplete records as dropped out.
    """
    if participant_data["status"] == "in_progress":
        participant_data["status"] = "dropped_out"
        participant_data["dropout_reason"] = "incomplete"
    return participant_data

def export_raw_data(logs: List[Dict[str, Any]]) -> str:
    """
    Export raw participant logs to JSON with checksums.
    This function fulfills T020: Create raw data export function.
    """
    if not logs:
        logger.warning("No logs to export.")
        return str(PARTICIPANT_LOGS_PATH)

    # Add checksums to each record if missing
    for log in logs:
        if "checksum" not in log:
            log["checksum"] = calculate_checksum(log)
    
    # Add global metadata
    export_record = {
        "export_timestamp": datetime.now().isoformat(),
        "total_participants": len(logs),
        "checksum": calculate_checksum({"count": len(logs), "records": [l.get("participant_id") for l in logs]}),
        "data": logs
    }

    with open(PARTICIPANT_LOGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(export_record, f, indent=2)
    
    logger.info(f"Raw data exported to {PARTICIPANT_LOGS_PATH}")
    return str(PARTICIPANT_LOGS_PATH)

def run_mock_experiment(num_participants: int) -> List[Dict[str, Any]]:
    """
    Run a mock experiment with simulated participants.
    Generates realistic mock data for T016, T017, T018, T019, and T020.
    """
    logs = []
    
    for i in range(1, num_participants + 1):
        # 1. Assign
        p_data = assign_participant(i, "mock")
        
        # 2. Start Session
        p_data = log_session_start(p_data)
        
        # Simulate some activity
        # Randomly decide if they ask questions (T016)
        num_questions = random.randint(0, 5)
        for _ in range(num_questions):
            q_type = random.choice(["keyword", "moderator-tag"])
            q_text = f"Mock question {random.randint(100, 999)}: How does this work?"
            p_data = log_help_request(p_data, q_text, q_type)
        
        # Simulate time elapsed (T018)
        elapsed = random.randint(1200, 3600) # Between 20 and 60 mins
        p_data = apply_stop_loss_intervention(p_data, elapsed)
        
        # If not failed/stop-loss, simulate survey (T017)
        if p_data["status"] != "failed":
            rating = random.randint(1, 5)
            p_data = capture_helpfulness_survey(p_data, rating)
        
        # Simulate potential dropouts (T019)
        if random.random() < 0.1: # 10% chance of dropout
            p_data = handle_abandoned_records(p_data)
        
        # Finalize
        p_data["session_end"] = datetime.now().isoformat()
        logs.append(p_data)
    
    # T020: Export the data
    export_raw_data(logs)
    
    return logs

def main():
    parser = argparse.ArgumentParser(description="Run the onboarding experiment (mock or real).")
    parser.add_argument("--mode", type=str, default="mock", choices=["mock", "real"], help="Run mode")
    parser.add_argument("--participants", type=int, default=3, help="Number of participants for mock run")
    args = parser.parse_args()

    logger.info(f"Starting experiment in {args.mode} mode with {args.participants} participants.")

    if args.mode == "mock":
        logs = run_mock_experiment(args.participants)
        logger.info(f"Mock experiment completed. Logged {len(logs)} participants.")
    else:
        logger.error("Real mode not implemented for this task. Use --mode mock.")
        sys.exit(1)

    # Verify output file exists
    if PARTICIPANT_LOGS_PATH.exists():
        logger.info(f"Verification: {PARTICIPANT_LOGS_PATH} exists.")
    else:
        logger.error(f"Verification failed: {PARTICIPANT_LOGS_PATH} does not exist.")
        sys.exit(1)

if __name__ == "__main__":
    main()