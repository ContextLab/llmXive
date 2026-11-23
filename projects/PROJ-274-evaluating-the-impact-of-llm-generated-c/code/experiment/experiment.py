import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.seed import set_global_seed
from utils.monitor import monitor_execution, ActiveMonitor
from utils.setup_paths import ensure_project_dirs
from data_collection import ensure_data_directory, save_logs, load_existing_logs, apply_stop_loss_intervention, handle_abandoned_records
from experiment.logging_utils import log_clarification_event, process_raw_input_for_clarifications, get_clarification_count, update_logs_with_clarification_counts

# Configure logging to avoid FileNotFoundError by ensuring directory exists first
def setup_logging():
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "experiment.log"
    
    # Prevent circular import issues by not importing logging module directly as a name
    # Use standard library logging
    import logging as std_logging
    
    std_logging.basicConfig(
        level=std_logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            std_logging.FileHandler(log_file),
            std_logging.StreamHandler(sys.stdout)
        ]
    )
    return std_logging.getLogger(__name__)

def ensure_data_directories():
    """Ensure all required data directories exist."""
    ensure_project_dirs()
    ensure_data_directory("raw")
    ensure_data_directory("processed")
    ensure_data_directory("reports")

def run_mock_experiment(logger, num_participants=3, seed=42):
    """
    Run a mock experiment with simulated participants.
    Implements T016 (clarification logging), T018 (stop-loss), and T019 (incomplete records handling).
    """
    set_global_seed(seed)
    
    output_file = project_root / "data" / "raw" / "participant_logs.json"
    
    # Initialize or load existing logs
    if output_file.exists():
        logs = load_existing_logs(str(output_file))
    else:
        logs = []

    conditions = ["LLM_Doc", "Human_Doc", "No_Doc"]
    
    for i in range(num_participants):
        p_id = f"mock_p_{i+1:03d}"
        condition = random.choice(conditions)
        
        # Simulate session data
        start_time = datetime.now(timezone.utc).isoformat()
        
        # Simulate task duration (random between 300 and 3600 seconds)
        duration_seconds = random.randint(300, 3600)
        end_time = datetime.now(timezone.utc).isoformat()
        
        # Simulate clarification questions
        raw_input_samples = [
            "How do I install this?",
            "Why does this function fail?",
            "What is the architecture?",
            "Explain the API usage.",
            "No questions."
        ]
        raw_input = random.choice(raw_input_samples)
        
        # Process clarification questions (T016)
        clarification_events = process_raw_input_for_clarifications(raw_input, p_id)
        for event in clarification_events:
            log_clarification_event(logs, event)
        
        clarification_count = get_clarification_count(logs, p_id)
        
        # Check for stop-loss intervention (T018)
        intervention_status = None
        max_time = None
        
        if duration_seconds > 2700:
            intervention_status = "stop_loss"
            max_time = 2700
            # Mark as failed/abandoned due to stop-loss
            status = "failed"
        else:
            status = "completed"
        
        # Handle incomplete records (T019)
        # Simulate some incomplete records (e.g., 20% chance of abandonment for mock)
        if random.random() < 0.2 and status != "failed":
            status = "incomplete"
            intervention_status = "abandoned"
            # Record abandonment reason
            abandonment_reason = "Participant left early (mock simulation)"
        
        # Construct record
        record = {
            "participant_id": p_id,
            "condition": condition,
            "session_start": start_time,
            "session_end": end_time,
            "task_duration_seconds": duration_seconds if status != "failed" else max_time,
            "clarification_question_count": clarification_count,
            "clarification_events": [e for e in logs if e.get("participant_id") == p_id and e.get("event_type") == "clarification"],
            "status": status,
            "intervention_status": intervention_status,
            "max_time_applied": max_time,
            "abandonment_reason": abandonment_reason if status == "incomplete" else None,
            "metadata": {
                "is_mock": True,
                "seed": seed
            }
        }
        
        logs.append(record)
        
        logger.info(f"Processed participant {p_id}: status={status}, duration={duration_seconds}s, questions={clarification_count}")

    # T019: Handle incomplete records - flag them and retain for reporting
    # The records are already flagged with status="incomplete" above.
    # We ensure they are retained in the logs file (not excluded from storage).
    # We also calculate summary stats for reporting.
    total_records = len(logs)
    completed_records = sum(1 for r in logs if r["status"] == "completed")
    failed_records = sum(1 for r in logs if r["status"] == "failed")
    incomplete_records = sum(1 for r in logs if r["status"] == "incomplete")
    
    logger.info(f"Experiment Summary: Total={total_records}, Completed={completed_records}, Failed={failed_records}, Incomplete={incomplete_records}")
    
    # Save logs to disk
    save_logs(logs, str(output_file))
    logger.info(f"Saved participant logs to {output_file}")
    
    return logs

def main():
    logger = setup_logging()
    ensure_data_directories()
    
    parser = argparse.ArgumentParser(description="Run the onboarding experiment.")
    parser.add_argument("--mode", type=str, default="mock", choices=["mock", "real"], help="Run mode")
    parser.add_argument("--participants", type=int, default=3, help="Number of mock participants")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    if args.mode == "mock":
        run_mock_experiment(logger, num_participants=args.participants, seed=args.seed)
    else:
        logger.error("Real mode not yet implemented in this task.")
        sys.exit(1)

if __name__ == "__main__":
    main()
