"""
Session management for simulated participant testing.

Handles session state, response capture, and partial session recording for dropouts.
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

from config import get_responses_dir, get_project_root
from utils.logging import get_logger
from data.participant import Participant, Response
from participants.interface import (
    SessionConfig,
    SimulatedParticipantInterface,
    StimulusPresentation,
    DistractorTaskResult,
    RecognitionQuestion,
    RecognitionResult
)

# Constants for partial recording
PARTIAL_RECORDING_THRESHOLD = 0.3  # Flag if less than 30% of questions answered

class SessionState:
    """Represents the current state of a participant session."""
    
    def __init__(self, session_id: str, participant: Participant):
        self.session_id = session_id
        self.participant = participant
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.completed: bool = False
        self.aborted: bool = False
        self.abortion_reason: Optional[str] = None
        self.responses: List[Response] = []
        self.current_stimulus_index: int = 0
        self.total_stimuli: int = 0
        self.distractor_results: List[DistractorTaskResult] = []
        
    def mark_started(self):
        self.start_time = datetime.now()
        
    def mark_completed(self):
        self.end_time = datetime.now()
        self.completed = True
        
    def mark_aborted(self, reason: str):
        self.end_time = datetime.now()
        self.aborted = True
        self.abortion_reason = reason
        
    def add_response(self, response: Response):
        self.responses.append(response)
        
    def get_progress(self) -> float:
        if self.total_stimuli == 0:
            return 0.0
        return self.current_stimulus_index / self.total_stimuli
        
    def is_partial(self) -> bool:
        """Check if this is a partial session (dropout)."""
        if self.completed:
            return False
        if self.aborted:
            return True
        progress = self.get_progress()
        return progress < PARTIAL_RECORDING_THRESHOLD

class SessionManager:
    """Manages participant sessions including partial recording for dropouts."""
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.responses_dir = get_responses_dir()
        self.current_session: Optional[SessionState] = None
        
    def create_session(self, participant: Participant) -> SessionState:
        """Create a new session for a participant."""
        session_id = f"session_{participant.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session = SessionState(session_id, participant)
        self.current_session = session
        self.logger.info(f"Created session {session_id} for participant {participant.id}")
        return session
        
    def start_session(self):
        """Mark session as started."""
        if not self.current_session:
            raise RuntimeError("No active session")
        self.current_session.mark_started()
        self.logger.info(f"Session {self.current_session.session_id} started")
        
    def record_stimulus_view(self, stimulus: StimulusPresentation):
        """Record that a stimulus was presented."""
        if not self.current_session:
            raise RuntimeError("No active session")
        self.current_session.current_stimulus_index += 1
        self.logger.debug(f"Stimulus {stimulus.image_id} presented (progress: {self.current_session.get_progress():.2f})")
        
    def record_distractor(self, result: DistractorTaskResult):
        """Record distractor task result."""
        if not self.current_session:
            raise RuntimeError("No active session")
        self.current_session.distractor_results.append(result)
        self.logger.debug(f"Distractor task completed: {result.accuracy:.2f} accuracy")
        
    def record_response(self, question: RecognitionQuestion, result: RecognitionResult):
        """Record a recognition response."""
        if not self.current_session:
            raise RuntimeError("No active session")
        
        response = Response(
            id=f"resp_{self.current_session.session_id}_{len(self.current_session.responses)}",
            question_id=question.id,
            value=result.answer,
            timestamp=datetime.now(),
            is_correct=result.is_correct,
            response_time=result.response_time
        )
        self.current_session.add_response(response)
        self.logger.debug(f"Response recorded for question {question.id}")
        
    def abort_session(self, reason: str):
        """Abort the current session due to dropout or other reason."""
        if not self.current_session:
            raise RuntimeError("No active session")
        self.current_session.mark_aborted(reason)
        self.logger.warning(f"Session {self.current_session.session_id} aborted: {reason}")
        self._save_partial_session()
        
    def complete_session(self):
        """Mark session as completed and save."""
        if not self.current_session:
            raise RuntimeError("No active session")
        self.current_session.mark_completed()
        self.logger.info(f"Session {self.current_session.session_id} completed")
        self._save_session()
        
    def _ensure_responses_dir(self):
        """Ensure the responses directory exists."""
        os.makedirs(self.responses_dir, exist_ok=True)
        
    def _save_session(self):
        """Save a completed session to disk."""
        if not self.current_session:
            return
            
        self._ensure_responses_dir()
        
        session_data = {
            "session_id": self.current_session.session_id,
            "participant_id": self.current_session.participant.id,
            "condition": self.current_session.participant.condition,
            "start_time": self.current_session.start_time.isoformat() if self.current_session.start_time else None,
            "end_time": self.current_session.end_time.isoformat() if self.current_session.end_time else None,
            "completed": self.current_session.completed,
            "aborted": self.current_session.aborted,
            "abortion_reason": self.current_session.abortion_reason,
            "total_stimuli": self.current_session.total_stimuli,
            "stimuli_viewed": self.current_session.current_stimulus_index,
            "responses": [
                {
                    "id": r.id,
                    "question_id": r.question_id,
                    "value": r.value,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "is_correct": r.is_correct,
                    "response_time": r.response_time
                }
                for r in self.current_session.responses
            ],
            "distractor_results": [
                {
                    "accuracy": dr.accuracy,
                    "time_taken": dr.time_taken
                }
                for dr in self.current_session.distractor_results
            ]
        }
        
        output_path = self.responses_dir / f"{self.current_session.session_id}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
            
        self.logger.info(f"Session saved to {output_path}")
        
    def _save_partial_session(self):
        """Save a partial session with a flag indicating dropout."""
        if not self.current_session:
            return
            
        self._ensure_responses_dir()
        
        session_data = {
            "session_id": self.current_session.session_id,
            "participant_id": self.current_session.participant.id,
            "condition": self.current_session.participant.condition,
            "start_time": self.current_session.start_time.isoformat() if self.current_session.start_time else None,
            "end_time": self.current_session.end_time.isoformat() if self.current_session.end_time else None,
            "completed": False,
            "aborted": True,
            "abortion_reason": self.current_session.abortion_reason,
            "total_stimuli": self.current_session.total_stimuli,
            "stimuli_viewed": self.current_session.current_stimulus_index,
            "progress": self.current_session.get_progress(),
            "partial_session": True,  # Explicit flag for dropouts
            "responses": [
                {
                    "id": r.id,
                    "question_id": r.question_id,
                    "value": r.value,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "is_correct": r.is_correct,
                    "response_time": r.response_time
                }
                for r in self.current_session.responses
            ],
            "distractor_results": [
                {
                    "accuracy": dr.accuracy,
                    "time_taken": dr.time_taken
                }
                for dr in self.current_session.distractor_results
            ]
        }
        
        output_path = self.responses_dir / f"{self.current_session.session_id}_PARTIAL.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
            
        self.logger.warning(f"Partial session saved to {output_path} (dropout flagged)")

def create_session(manager: SessionManager, participant: Participant) -> SessionState:
    """Factory function to create a session."""
    return manager.create_session(participant)

def main():
    """Main entry point for testing session management."""
    logging.basicConfig(level=logging.INFO)
    
    # Create a test session
    config = SessionConfig(
        num_stimuli=5,
        distractor_questions=3,
        recognition_questions_per_stimulus=4
    )
    
    manager = SessionManager(config)
    participant = Participant(
        id="test_participant_001",
        condition="enhanced_detail",
        timestamp=datetime.now()
    )
    
    session = manager.create_session(participant)
    manager.start_session()
    
    # Simulate some stimuli and responses
    for i in range(3):  # Simulate 3 out of 5 stimuli (dropout scenario)
        stimulus = StimulusPresentation(
            image_id=f"img_{i}",
            condition="enhanced_detail",
            presentation_time=5.0
        )
        manager.record_stimulus_view(stimulus)
        
        # Record a few responses
        for j in range(2):
            question = RecognitionQuestion(
                id=f"q_{i}_{j}",
                text=f"Question {i}_{j}",
                is_lure=(j == 1)
            )
            result = RecognitionResult(
                answer="yes" if j == 0 else "no",
                is_correct=(j == 0),
                response_time=2.5
            )
            manager.record_response(question, result)
    
    # Simulate dropout
    manager.abort_session("Participant left early")
    
    print(f"Test completed. Check {get_responses_dir()} for session files.")
    print(f"Partial session file should be named with '_PARTIAL' suffix.")

if __name__ == "__main__":
    main()