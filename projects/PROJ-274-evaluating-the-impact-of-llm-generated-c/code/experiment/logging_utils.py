"""
Real-time logging utilities for the onboarding experiment.
Implements clarification question detection and logging per FR-004.
"""
import json
import os
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Keywords that indicate a clarification question
CLARIFICATION_KEYWORDS = [
    r'\bhow\b', r'\bwhy\b', r'\bwhat\b', r'\bexplain\b',
    r'\bwhere\b', r'\bwhen\b', r'\bwho\b', r'\bcan you\b',
    r'\bcould you\b', r'\bwould you\b'
]
CLARIFICATION_PATTERN = re.compile('|'.join(CLARIFICATION_KEYWORDS), re.IGNORECASE)

def detect_clarification_source(text: str, is_moderator_tag: bool = False) -> Optional[str]:
    """
    Determine the source of a potential clarification question.
    
    Args:
        text: The raw input text to analyze.
        is_moderator_tag: Boolean flag indicating if a moderator explicitly tagged this.
    
    Returns:
        'moderator' if moderator_tag is True, 'keyword' if text matches keywords, None otherwise.
    """
    if is_moderator_tag:
        return 'moderator'
    
    if CLARIFICATION_PATTERN.search(text):
        return 'keyword'
    
    return None

def log_clarification_event(
    text: str, 
    source: str, 
    participant_id: str, 
    session_id: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Create a clarification event log entry and append it to the participant logs file.
    
    Args:
        text: The text of the clarification question.
        source: 'keyword' or 'moderator'.
        participant_id: ID of the participant.
        session_id: ID of the session.
        output_path: Path to the participant_logs.json file.
    
    Returns:
        The created event dictionary.
    """
    event = {
        'event_type': 'clarification',
        'source': source,
        'text': text,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'participant_id': participant_id,
        'session_id': session_id
    }
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load existing logs or initialize
    logs = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    
    logs.append(event)
    
    # Write back to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return event

def process_raw_input_for_clarifications(
    raw_input: str, 
    participant_id: str, 
    session_id: str, 
    output_path: str,
    is_moderator_tag: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Process a raw input string to detect and log clarification questions.
    
    Args:
        raw_input: The raw input text from the participant or moderator.
        participant_id: ID of the participant.
        session_id: ID of the session.
        output_path: Path to the participant_logs.json file.
        is_moderator_tag: Boolean flag indicating if this was explicitly tagged by a moderator.
    
    Returns:
        The logged event dictionary if a clarification was detected, None otherwise.
    """
    source = detect_clarification_source(raw_input, is_moderator_tag)
    
    if source is None:
        return None
    
    return log_clarification_event(
        text=raw_input,
        source=source,
        participant_id=participant_id,
        session_id=session_id,
        output_path=output_path
    )

def get_clarification_count(output_path: str) -> int:
    """
    Get the total count of clarification questions logged in the file.
    
    Args:
        output_path: Path to the participant_logs.json file.
    
    Returns:
        Integer count of clarification events.
    """
    if not os.path.exists(output_path):
        return 0
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return sum(1 for log in logs if log.get('event_type') == 'clarification')
    except (json.JSONDecodeError, TypeError):
        return 0

def update_logs_with_clarification_counts(logs: List[Dict[str, Any]], output_path: str) -> List[Dict[str, Any]]:
    """
    Update the logs list by adding a 'clarification_question_count' field to session records.
    This function assumes the logs are a list of events and groups them by session/participant.
    
    Args:
        logs: List of log events.
        output_path: Path to write the updated logs.
    
    Returns:
        Updated list of logs with session-level counts.
    """
    # Group by session
    session_counts = {}
    for log in logs:
        if log.get('event_type') == 'clarification':
            session_key = (log.get('participant_id'), log.get('session_id'))
            session_counts[session_key] = session_counts.get(session_key, 0) + 1
    
    # Add counts to session start/end events (or create a summary if needed)
    # For this implementation, we will append a summary event at the end of the list
    # or update the file structure to include a summary section.
    # Based on the task description, we need to ensure the 'clarification_question_count' 
    # field matches the array length. We will add a summary record.
    
    summary_records = []
    for (p_id, s_id), count in session_counts.items():
        summary_records.append({
            'event_type': 'session_summary',
            'participant_id': p_id,
            'session_id': s_id,
            'clarification_question_count': count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    logs.extend(summary_records)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    
    return logs
