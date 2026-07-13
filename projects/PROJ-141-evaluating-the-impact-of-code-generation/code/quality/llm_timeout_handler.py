"""
LLM Timeout Handler for GitHub Actions Job-Level Session Management.

Implements job-level session timeout handling distinct from inference-level timeouts.
Provides warning thresholds, force-stop mechanisms, and graceful submission saving
to prevent data loss during experiment sessions.

This module handles:
- Job-level session timeouts (e.g., 6h GitHub Actions limit)
- Warning thresholds (e.g., 90%, 95% of session time)
- Graceful shutdown with submission saving
- Force-stop mechanisms for unresponsive sessions
"""

import os
import sys
import json
import logging
import signal
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

# Import existing project modules
from experiment.submission_handler import SubmissionHandler, SubmissionError
from logs.experiment import log_experiment_event, get_logger
from config.settings import get_config, get_experiment_config

# Configure logging
logger = logging.getLogger(__name__)

# Session timeout configuration constants
# GitHub Actions free-tier limit: 6 hours (21600 seconds)
DEFAULT_SESSION_TIMEOUT_SECONDS = 21600  # 6 hours
WARNING_THRESHOLD_1 = 0.90  # 90% of session time
WARNING_THRESHOLD_2 = 0.95  # 95% of session time
GRACE_PERIOD_SECONDS = 300  # 5 minutes for graceful shutdown

class SessionTimeoutError(Exception):
    """Exception raised when session timeout is reached."""
    pass

class GracefulShutdownError(Exception):
    """Exception raised during graceful shutdown process."""
    pass

class SessionTimeoutHandler:
    """
    Manages job-level session timeouts for GitHub Actions.

    This handler is distinct from inference-level timeouts (handled by
    execution_sandbox.py) and manages the overall session duration.
    """

    def __init__(
        self,
        session_timeout_seconds: int = DEFAULT_SESSION_TIMEOUT_SECONDS,
        warning_thresholds: List[float] = None,
        grace_period_seconds: int = GRACE_PERIOD_SECONDS,
        submission_handler: Optional[SubmissionHandler] = None
    ):
        """
        Initialize the session timeout handler.

        Args:
            session_timeout_seconds: Total session timeout in seconds
            warning_thresholds: List of warning thresholds (0.0-1.0)
            grace_period_seconds: Time allowed for graceful shutdown
            submission_handler: Optional SubmissionHandler instance
        """
        self.session_timeout_seconds = session_timeout_seconds
        self.warning_thresholds = warning_thresholds or [WARNING_THRESHOLD_1, WARNING_THRESHOLD_2]
        self.grace_period_seconds = grace_period_seconds
        self.submission_handler = submission_handler or SubmissionHandler()

        self.start_time: Optional[float] = None
        self.session_id: Optional[str] = None
        self.participant_id: Optional[str] = None
        self._shutdown_event = threading.Event()
        self._warning_thread: Optional[threading.Thread] = None
        self._force_stop_thread: Optional[threading.Thread] = None
        self._is_active = False
        self._warnings_sent: List[float] = []
        self._graceful_shutdown_initiated = False

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal."""
        logger.info(f"Received SIGTERM signal, initiating graceful shutdown...")
        self.initiate_graceful_shutdown(reason="SIGTERM received")

    def _handle_sigint(self, signum, frame):
        """Handle SIGINT signal."""
        logger.info(f"Received SIGINT signal, initiating graceful shutdown...")
        self.initiate_graceful_shutdown(reason="SIGINT received")

    def start_session(self, session_id: str, participant_id: str):
        """
        Start a new session with timeout monitoring.

        Args:
            session_id: Unique session identifier
            participant_id: Participant identifier
        """
        self.session_id = session_id
        self.participant_id = participant_id
        self.start_time = time.time()
        self._is_active = True
        self._warnings_sent = []
        self._graceful_shutdown_initiated = False

        logger.info(f"Session started: session_id={session_id}, participant_id={participant_id}")
        log_experiment_event(
            event_type="session_timeout_monitor_start",
            session_id=session_id,
            participant_id=participant_id,
            metadata={
                "timeout_seconds": self.session_timeout_seconds,
                "warning_thresholds": self.warning_thresholds,
                "grace_period_seconds": self.grace_period_seconds
            }
        )

        # Start warning threshold monitoring thread
        self._warning_thread = threading.Thread(target=self._monitor_warning_thresholds, daemon=True)
        self._warning_thread.start()

        # Start force-stop monitoring thread
        self._force_stop_thread = threading.Thread(target=self._monitor_force_stop, daemon=True)
        self._force_stop_thread.start()

    def _monitor_warning_thresholds(self):
        """Monitor and send warnings at configured thresholds."""
        while self._is_active and not self._graceful_shutdown_initiated:
            if self.start_time is None:
                time.sleep(1)
                continue

            elapsed = time.time() - self.start_time
            elapsed_ratio = elapsed / self.session_timeout_seconds

            for threshold in self.warning_thresholds:
                if elapsed_ratio >= threshold and threshold not in self._warnings_sent:
                    self._send_warning(threshold, elapsed)
                    self._warnings_sent.append(threshold)

            # Check if we've passed all thresholds
            if all(elapsed_ratio < t for t in self.warning_thresholds) or \
               all(t in self._warnings_sent for t in self.warning_thresholds):
                pass  # Continue monitoring

            time.sleep(10)  # Check every 10 seconds

    def _send_warning(self, threshold: float, elapsed: float):
        """Send a warning at the specified threshold."""
        remaining = self.session_timeout_seconds - elapsed
        percentage = threshold * 100

        warning_message = (
            f"Session timeout warning: {percentage:.0f}% of session time elapsed. "
            f"Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s, "
            f"Session ID: {self.session_id}"
        )

        logger.warning(warning_message)

        log_experiment_event(
            event_type="session_timeout_warning",
            session_id=self.session_id,
            participant_id=self.participant_id,
            metadata={
                "threshold": threshold,
                "threshold_percentage": percentage,
                "elapsed_seconds": elapsed,
                "remaining_seconds": remaining
            }
        )

    def _monitor_force_stop(self):
        """Monitor for force-stop condition."""
        while self._is_active and not self._graceful_shutdown_initiated:
            if self.start_time is None:
                time.sleep(1)
                continue

            elapsed = time.time() - self.start_time

            if elapsed >= self.session_timeout_seconds:
                logger.error(f"Session timeout reached! Forcing shutdown...")
                self._force_stop()
                break

            time.sleep(1)

    def _force_stop(self):
        """Force stop the session and save any pending submissions."""
        logger.critical(f"Force stopping session: {self.session_id}")

        # Attempt to save any pending submissions
        try:
            self._save_pending_submissions()
        except Exception as e:
            logger.error(f"Failed to save pending submissions during force stop: {e}")

        self._is_active = False
        self._shutdown_event.set()

        log_experiment_event(
            event_type="session_force_stop",
            session_id=self.session_id,
            participant_id=self.participant_id,
            metadata={
                "reason": "Session timeout exceeded",
                "elapsed_seconds": time.time() - self.start_time if self.start_time else 0
            }
        )

        raise SessionTimeoutError(f"Session timeout exceeded for session {self.session_id}")

    def initiate_graceful_shutdown(self, reason: str = "Manual shutdown"):
        """
        Initiate graceful shutdown with time to save submissions.

        Args:
            reason: Reason for shutdown
        """
        if self._graceful_shutdown_initiated:
            return

        self._graceful_shutdown_initiated = True
        logger.info(f"Initiating graceful shutdown: {reason}")

        log_experiment_event(
            event_type="session_graceful_shutdown_initiated",
            session_id=self.session_id,
            participant_id=self.participant_id,
            metadata={
                "reason": reason,
                "grace_period_seconds": self.grace_period_seconds
            }
        )

        # Save all pending submissions
        try:
            self._save_pending_submissions()
        except Exception as e:
            logger.error(f"Error during graceful shutdown save: {e}")
            # Continue with shutdown even if save fails

        self._is_active = False
        self._shutdown_event.set()

        logger.info(f"Graceful shutdown completed for session {self.session_id}")

    def _save_pending_submissions(self):
        """Save any pending submissions before shutdown."""
        logger.info(f"Saving pending submissions for session {self.session_id}")

        # This would integrate with the actual submission handler
        # to save any in-progress submissions
        try:
            # Placeholder for actual submission saving logic
            # In a real implementation, this would query pending submissions
            # and save them to the database or file system
            self.submission_handler.flush_pending_submissions()

            log_experiment_event(
                event_type="pending_submissions_saved",
                session_id=self.session_id,
                participant_id=self.participant_id,
                metadata={
                    "shutdown_reason": "Graceful shutdown"
                }
            )
        except Exception as e:
            logger.error(f"Failed to save pending submissions: {e}")
            raise GracefulShutdownError(f"Failed to save pending submissions: {e}")

    def get_elapsed_time(self) -> float:
        """Get elapsed time since session start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_remaining_time(self) -> float:
        """Get remaining time before session timeout."""
        elapsed = self.get_elapsed_time()
        return max(0.0, self.session_timeout_seconds - elapsed)

    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status."""
        elapsed = self.get_elapsed_time()
        remaining = self.get_remaining_time()
        elapsed_ratio = elapsed / self.session_timeout_seconds if self.session_timeout_seconds > 0 else 0

        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "is_active": self._is_active,
            "graceful_shutdown_initiated": self._graceful_shutdown_initiated,
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "elapsed_percentage": elapsed_ratio * 100,
            "timeout_seconds": self.session_timeout_seconds,
            "warnings_sent": self._warnings_sent,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat() if self.start_time else None
        }

    def stop_session(self):
        """Stop the session monitoring."""
        self._is_active = False
        self._shutdown_event.set()
        logger.info(f"Session monitoring stopped: {self.session_id}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with graceful shutdown."""
        self._is_active = False
        self._shutdown_event.set()
        if exc_type is None:
            self.initiate_graceful_shutdown(reason="Normal session completion")
        return False


def create_session_timeout_handler(
    session_timeout_seconds: Optional[int] = None,
    warning_thresholds: Optional[List[float]] = None,
    grace_period_seconds: Optional[int] = None
) -> SessionTimeoutHandler:
    """
    Create a session timeout handler with configuration.

    Args:
        session_timeout_seconds: Session timeout in seconds (defaults to GitHub Actions limit)
        warning_thresholds: List of warning thresholds (0.0-1.0)
        grace_period_seconds: Grace period for shutdown

    Returns:
        Configured SessionTimeoutHandler instance
    """
    # Try to load from config if not provided
    if session_timeout_seconds is None or warning_thresholds is None:
        try:
            config = get_config()
            exp_config = get_experiment_config()

            if session_timeout_seconds is None:
                session_timeout_seconds = exp_config.get("session_timeout_seconds", DEFAULT_SESSION_TIMEOUT_SECONDS)

            if warning_thresholds is None:
                warning_thresholds = exp_config.get("warning_thresholds", [WARNING_THRESHOLD_1, WARNING_THRESHOLD_2])

        except Exception as e:
            logger.warning(f"Could not load config, using defaults: {e}")

    return SessionTimeoutHandler(
        session_timeout_seconds=session_timeout_seconds or DEFAULT_SESSION_TIMEOUT_SECONDS,
        warning_thresholds=warning_thresholds or [WARNING_THRESHOLD_1, WARNING_THRESHOLD_2],
        grace_period_seconds=grace_period_seconds or GRACE_PERIOD_SECONDS
    )


def main():
    """Main function for testing and demonstration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create handler
    handler = create_session_timeout_handler(
        session_timeout_seconds=3600,  # 1 hour for testing
        warning_thresholds=[0.5, 0.75, 0.9],
        grace_period_seconds=60
    )

    # Start a test session
    session_id = "test-session-123"
    participant_id = "participant-456"

    print(f"Starting session: {session_id}")
    handler.start_session(session_id, participant_id)

    # Simulate session activity
    try:
        for i in range(10):
            status = handler.get_session_status()
            print(f"Status update {i+1}: {json.dumps(status, indent=2)}")
            time.sleep(10)  # Simulate work
    except SessionTimeoutError as e:
        print(f"Session timed out: {e}")
    finally:
        handler.stop_session()
        print("Session stopped")


if __name__ == "__main__":
    main()