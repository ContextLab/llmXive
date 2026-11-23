"""
Backend API for participant interaction handling.

This module implements the backend logic for:
- Handling participant submissions
- Managing session state
- Applying Latin-square assignment logic for task conditions

Depends on:
- code/utils/models.py (Participant, Task, InteractionLog)
- code/utils/assignment_generator.py (generate_latin_square, assign_conditions)
- code/utils/interaction_logger.py (log_interaction, save_raw_logs)
- code/utils/config_manager.py (get_config)
- code/utils/logging_utils.py (get_logger, ErrorHandler)
"""

import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.models import Participant, Task, InteractionLog
from utils.assignment_generator import generate_latin_square, assign_conditions
from utils.interaction_logger import log_interaction, save_raw_logs
from utils.config_manager import get_config
from utils.logging_utils import get_logger, ErrorHandler

logger = get_logger(__name__)

class ParticipantSessionManager:
    """Manages participant session state and task assignments."""
    
    def __init__(self):
        self.config = get_config()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        
    def create_session(self, participant_id: str) -> Dict[str, Any]:
        """
        Create a new participant session with Latin-square assigned conditions.
        
        Args:
            participant_id: Unique identifier for the participant
            
        Returns:
            Session dictionary with assigned tasks and conditions
        """
        try:
            # Generate Latin-square assignment for this participant
            cohort_size = self.config.get('study', {}).get('cohort_size', 30)
            num_conditions = self.config.get('study', {}).get('num_conditions', 3)
            
            # Generate Latin square matrix
            latin_square = generate_latin_square(num_conditions)
            
            # Assign conditions based on participant index (simulated by hash)
            participant_index = hash(participant_id) % cohort_size
            condition_assignment = assign_conditions(
                participant_id=participant_id,
                latin_square=latin_square,
                participant_index=participant_index
            )
            
            # Create session object
            session = {
                'participant_id': participant_id,
                'session_id': str(uuid.uuid4()),
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'condition_assignment': condition_assignment,
                'tasks_completed': [],
                'current_task_index': 0,
                'total_tasks': len(condition_assignment.get('tasks', []))
            }
            
            # Store session
            self.sessions[participant_id] = session
            
            self.logger.info(f"Created session for participant {participant_id} "
                           f"with condition assignment: {condition_assignment}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create session for {participant_id}: {str(e)}")
            raise ErrorHandler.handle_error(e, "Session creation failed")
    
    def get_next_task(self, participant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next task for a participant based on their condition assignment.
        
        Args:
            participant_id: Unique identifier for the participant
            
        Returns:
            Task dictionary or None if all tasks completed
        """
        try:
            if participant_id not in self.sessions:
                raise ValueError(f"No session found for participant {participant_id}")
            
            session = self.sessions[participant_id]
            
            if session['current_task_index'] >= session['total_tasks']:
                self.logger.info(f"All tasks completed for participant {participant_id}")
                return None
            
            # Get task assignment from condition_assignment
            condition_assignment = session['condition_assignment']
            tasks = condition_assignment.get('tasks', [])
            
            if session['current_task_index'] >= len(tasks):
                return None
            
            task_info = tasks[session['current_task_index']]
            
            # Increment task counter
            session['current_task_index'] += 1
            
            task_data = {
                'task_id': task_info.get('task_id'),
                'condition': task_info.get('condition'),
                'method_name': task_info.get('method_name'),
                'summary': task_info.get('summary'),
                'buggy_code': task_info.get('buggy_code'),
                'sequence_number': session['current_task_index']
            }
            
            self.logger.info(f"Assigned task {task_info.get('task_id')} "
                           f"with condition {task_info.get('condition')} "
                           f"to participant {participant_id}")
            
            return task_data
            
        except Exception as e:
            self.logger.error(f"Failed to get next task for {participant_id}: {str(e)}")
            raise ErrorHandler.handle_error(e, "Task retrieval failed")
    
    def submit_interaction(self, participant_id: str, task_id: str,
                         selected_line: int, timestamp_ms: int,
                         response_time_ms: int) -> Dict[str, Any]:
        """
        Record a participant's interaction with a task.
        
        Args:
            participant_id: Unique identifier for the participant
            task_id: Identifier for the task
            selected_line: Line number selected by participant
            timestamp_ms: Timestamp of selection in milliseconds
            response_time_ms: Time taken to make selection in milliseconds
            
        Returns:
            Confirmation dictionary with logged data
        """
        try:
            if participant_id not in self.sessions:
                raise ValueError(f"No active session for participant {participant_id}")
            
            session = self.sessions[participant_id]
            if session['status'] != 'active':
                raise ValueError(f"Session for {participant_id} is not active")
            
            # Create interaction log entry
            interaction = {
                'participant_id': participant_id,
                'session_id': session['session_id'],
                'task_id': task_id,
                'condition': self._get_task_condition(session, task_id),
                'timestamp_ms': timestamp_ms,
                'selected_line': selected_line,
                'response_time_ms': response_time_ms,
                'logged_at': datetime.utcnow().isoformat()
            }
            
            # Log the interaction
            log_interaction(interaction)
            
            # Update session state
            if task_id not in session['tasks_completed']:
                session['tasks_completed'].append(task_id)
            
            self.logger.info(f"Recorded interaction for participant {participant_id}, "
                           f"task {task_id}, selected line {selected_line}")
            
            return {
                'status': 'success',
                'interaction_id': str(uuid.uuid4()),
                'logged': True,
                'interaction': interaction
            }
            
        except Exception as e:
            self.logger.error(f"Failed to submit interaction: {str(e)}")
            raise ErrorHandler.handle_error(e, "Interaction submission failed")
    
    def _get_task_condition(self, session: Dict[str, Any], task_id: str) -> str:
        """Helper to get condition for a specific task in session."""
        tasks = session['condition_assignment'].get('tasks', [])
        for task in tasks:
            if task.get('task_id') == task_id:
                return task.get('condition')
        return 'unknown'
    
    def complete_session(self, participant_id: str) -> Dict[str, Any]:
        """
        Mark a participant's session as complete.
        
        Args:
            participant_id: Unique identifier for the participant
            
        Returns:
            Session summary dictionary
        """
        try:
            if participant_id not in self.sessions:
                raise ValueError(f"No session found for participant {participant_id}")
            
            session = self.sessions[participant_id]
            session['status'] = 'completed'
            session['completed_at'] = datetime.utcnow().isoformat()
            
            # Save session state
            self._save_session_state(participant_id)
            
            self.logger.info(f"Completed session for participant {participant_id}")
            
            return {
                'status': 'completed',
                'participant_id': participant_id,
                'session_id': session['session_id'],
                'tasks_completed': len(session['tasks_completed']),
                'total_tasks': session['total_tasks'],
                'completed_at': session['completed_at']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to complete session for {participant_id}: {str(e)}")
            raise ErrorHandler.handle_error(e, "Session completion failed")
    
    def _save_session_state(self, participant_id: str):
        """Save session state to disk for persistence."""
        try:
            state_dir = self.config.get('paths', {}).get('state_dir', 'state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz')
            state_path = Path(state_dir) / 'sessions'
            state_path.mkdir(parents=True, exist_ok=True)
            
            session_file = state_path / f"{participant_id}_session.json"
            
            with open(session_file, 'w') as f:
                json.dump(self.sessions[participant_id], f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to save session state for {participant_id}: {str(e)}")
    
def get_session_manager() -> ParticipantSessionManager:
    """Get or create the session manager singleton."""
    if not hasattr(get_session_manager, '_instance'):
        get_session_manager._instance = ParticipantSessionManager()
    return get_session_manager._instance

def handle_participant_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for handling participant submissions.
    
    Args:
        data: Dictionary containing:
            - participant_id: str
            - task_id: str
            - selected_line: int
            - timestamp_ms: int
            - response_time_ms: int
            
    Returns:
        Response dictionary with status and logged data
    """
    manager = get_session_manager()
    
    participant_id = data.get('participant_id')
    task_id = data.get('task_id')
    selected_line = data.get('selected_line')
    timestamp_ms = data.get('timestamp_ms')
    response_time_ms = data.get('response_time_ms')
    
    if not all([participant_id, task_id, selected_line is not None, timestamp_ms]):
        raise ValueError("Missing required fields in submission data")
    
    # Ensure session exists
    if participant_id not in manager.sessions:
        manager.create_session(participant_id)
    
    # Submit interaction
    result = manager.submit_interaction(
        participant_id=participant_id,
        task_id=task_id,
        selected_line=selected_line,
        timestamp_ms=timestamp_ms,
        response_time_ms=response_time_ms
    )
    
    return result

def get_next_task_for_participant(participant_id: str) -> Dict[str, Any]:
    """
    Get the next task for a participant.
    
    Args:
        participant_id: Unique identifier for the participant
        
    Returns:
        Task dictionary with method, summary, and condition info
    """
    manager = get_session_manager()
    
    # Ensure session exists
    if participant_id not in manager.sessions:
        manager.create_session(participant_id)
    
    task = manager.get_next_task(participant_id)
    
    if task is None:
        return {
            'status': 'complete',
            'message': 'All tasks completed for this participant'
        }
    
    return {
        'status': 'success',
        'task': task
    }

def main():
    """
    Main function for testing the participant API.
    Simulates a complete participant workflow.
    """
    logger.info("Starting participant API test...")
    
    # Create a test participant
    test_participant_id = "TEST_PARTICIPANT_001"
    
    try:
        # Create session
        manager = get_session_manager()
        session = manager.create_session(test_participant_id)
        logger.info(f"Created session: {session['session_id']}")
        
        # Get and process tasks
        while True:
            task = manager.get_next_task(test_participant_id)
            if task is None:
                break
            
            logger.info(f"Processing task: {task['task_id']} "
                      f"with condition: {task['condition']}")
            
            # Simulate participant interaction
            import time
            timestamp_ms = int(time.time() * 1000)
            response_time_ms = int((time.time() * 1000) - timestamp_ms) + 5000  # Simulate 5s response
            
            result = manager.submit_interaction(
                participant_id=test_participant_id,
                task_id=task['task_id'],
                selected_line=42,  # Simulated selection
                timestamp_ms=timestamp_ms,
                response_time_ms=response_time_ms
            )
            
            logger.info(f"Interaction logged: {result['interaction_id']}")
        
        # Complete session
        completion = manager.complete_session(test_participant_id)
        logger.info(f"Session completed: {completion}")
        
        logger.info("Participant API test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()