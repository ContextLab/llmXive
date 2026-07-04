from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger

class MetricsCollector:
    """
    Handles real-time collection of usability metrics during simulation sessions.
    
    Tracks:
    - completion_time: Total duration of the session (calculated on end)
    - error_count: Number of errors recorded during the session
    - explanation_engagement_time: Cumulative time spent interacting with XAI overlays
    """
    def __init__(self):
        self.logger = get_logger("metrics_collector")
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(self, session_id: str):
        """Initialize a new session with a timestamp."""
        self.sessions[session_id] = {
            "start_time": datetime.now(),
            "error_count": 0,
            "explanation_engagement_time": 0.0
        }
        self.logger.info(f"Session {session_id} started.")

    def record_error(self, session_id: str):
        """Increment the error count for a specific session."""
        if session_id not in self.sessions:
            self.logger.warning(f"Attempted to record error for unknown session: {session_id}")
            return
        
        self.sessions[session_id]["error_count"] += 1
        self.logger.debug(f"Session {session_id}: Error recorded (Total: {self.sessions[session_id]['error_count']})")

    def record_engagement(self, session_id: str, duration: float):
        """
        Add to the cumulative explanation engagement time.
        
        Args:
            session_id: The active session identifier.
            duration: Time in seconds to add to the engagement total.
        """
        if session_id not in self.sessions:
            self.logger.warning(f"Attempted to record engagement for unknown session: {session_id}")
            return

        if duration < 0:
            self.logger.warning(f"Invalid negative duration {duration} for session {session_id}")
            return

        self.sessions[session_id]["explanation_engagement_time"] += duration
        self.logger.debug(f"Session {session_id}: Engagement added ({duration}s). Total: {self.sessions[session_id]['explanation_engagement_time']:.2f}s")

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        Finalize the session and calculate completion time.
        
        Returns:
            A dictionary containing the final metrics:
            - session_id
            - start_time
            - end_time
            - completion_time (seconds)
            - error_count
            - explanation_engagement_time (seconds)
        """
        if session_id not in self.sessions:
            self.logger.error(f"Cannot end session {session_id}: Session not found.")
            return {}

        data = self.sessions[session_id]
        end_time = datetime.now()
        data["end_time"] = end_time
        
        # Calculate completion time in seconds
        start_time = data["start_time"]
        completion_time = (end_time - start_time).total_seconds()
        data["completion_time"] = completion_time

        # Prepare output payload
        result = {
            "session_id": session_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "completion_time": completion_time,
            "error_count": data["error_count"],
            "explanation_engagement_time": data["explanation_engagement_time"]
        }

        # Clean up internal state
        del self.sessions[session_id]

        self.logger.info(f"Session {session_id} ended. Metrics: {result}")
        return result

    def get_session_snapshot(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current state of a session without finalizing it.
        Useful for mid-session checks or debugging.
        """
        if session_id not in self.sessions:
            return None
        
        data = self.sessions[session_id]
        current_time = datetime.now()
        current_completion = (current_time - data["start_time"]).total_seconds()
        
        return {
            "session_id": session_id,
            "start_time": data["start_time"].isoformat(),
            "current_time": current_time.isoformat(),
            "current_completion_time": current_completion,
            "error_count": data["error_count"],
            "explanation_engagement_time": data["explanation_engagement_time"]
        }

def main():
    """
    Entry point for testing the MetricsCollector module independently.
    Simulates a user session flow to verify metric collection.
    """
    print("Running MetricsCollector self-test...")
    collector = MetricsCollector()
    
    # Simulate a session
    test_session_id = "TEST_SESSION_001"
    collector.start_session(test_session_id)
    
    # Simulate errors
    collector.record_error(test_session_id)
    collector.record_error(test_session_id)
    
    # Simulate engagement with XAI overlays
    collector.record_engagement(test_session_id, 5.5)
    collector.record_engagement(test_session_id, 3.2)
    
    # End session and retrieve results
    results = collector.end_session(test_session_id)
    
    if not results:
        print("ERROR: Session collection failed.")
        return 1
        
    print("\n--- Session Results ---")
    print(f"Session ID: {results['session_id']}")
    print(f"Completion Time: {results['completion_time']:.2f} seconds")
    print(f"Error Count: {results['error_count']}")
    print(f"Explanation Engagement Time: {results['explanation_engagement_time']:.2f} seconds")
    print("-----------------------\n")
    
    # Validation checks
    assert results["error_count"] == 2, "Error count mismatch"
    assert abs(results["explanation_engagement_time"] - 8.7) < 0.01, "Engagement time mismatch"
    assert results["completion_time"] > 0, "Completion time must be positive"
    
    print("Self-test PASSED.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())