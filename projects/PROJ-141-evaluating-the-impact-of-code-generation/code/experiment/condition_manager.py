"""
Condition Manager for LLM-assisted vs Baseline switching.

This module implements the logic for switching between LLM-assisted and baseline conditions
within the experiment. It handles the state management, logging, and disabling of the LLM
assistant when switching to the baseline condition.
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

# Import existing utilities from the project
from experiment.timestamp_recorder import record_condition_switch, get_current_utc_timestamp
from logs.experiment import log_experiment_event, get_logger
from config.settings import get_experiment_config

# Initialize logger for this module
logger = get_logger(__name__)

class ConditionError(Exception):
    """Custom exception for condition management errors."""
    pass

class ConditionManager:
    """
    Manages the switching logic between LLM-assisted and baseline conditions.
    
    Attributes:
        participant_id (str): Unique identifier for the participant.
        current_condition (str): Current active condition ('llm_assisted' or 'baseline').
        session_id (str): Unique identifier for the current session.
        config (Dict): Experiment configuration.
    """
    
    def __init__(self, participant_id: str, session_id: str):
        """
        Initialize the ConditionManager.
        
        Args:
            participant_id: Unique identifier for the participant.
            session_id: Unique identifier for the session.
        """
        self.participant_id = participant_id
        self.session_id = session_id
        self.current_condition = None
        self.config = get_experiment_config()
        self._switch_history = []
        
        logger.info(
            f"ConditionManager initialized for participant {participant_id}, session {session_id}"
        )

    def initialize_condition(self, initial_condition: str) -> str:
        """
        Set the initial condition for the session.
        
        Args:
            initial_condition: The starting condition ('llm_assisted' or 'baseline').
            
        Returns:
            str: The initialized condition.
            
        Raises:
            ConditionError: If the condition is invalid.
        """
        valid_conditions = ['llm_assisted', 'baseline']
        if initial_condition not in valid_conditions:
            raise ConditionError(
                f"Invalid condition '{initial_condition}'. Must be one of {valid_conditions}"
            )
        
        self.current_condition = initial_condition
        timestamp = get_current_utc_timestamp()
        
        # Log the initial condition assignment
        log_experiment_event(
            event_type="condition_initialization",
            participant_id=self.participant_id,
            session_id=self.session_id,
            data={
                "condition": initial_condition,
                "timestamp": timestamp
            }
        )
        
        logger.info(
            f"Initial condition set to '{initial_condition}' for participant {self.participant_id}"
        )
        
        return initial_condition

    def switch_condition(self, new_condition: str) -> Tuple[str, Dict[str, Any]]:
        """
        Switch to a new condition, disabling LLM assistant if moving to baseline.
        
        This method:
        1. Validates the new condition
        2. Records the switch timestamp
        3. Logs the event
        4. Handles LLM assistant state (disables if switching to baseline)
        5. Updates internal state
        
        Args:
            new_condition: The target condition ('llm_assisted' or 'baseline').
            
        Returns:
            Tuple containing:
                - str: The new active condition
                - Dict: Metadata about the switch (timestamp, previous condition, etc.)
                
        Raises:
            ConditionError: If the condition is invalid or switching to the same condition.
        """
        valid_conditions = ['llm_assisted', 'baseline']
        
        if new_condition not in valid_conditions:
            raise ConditionError(
                f"Invalid condition '{new_condition}'. Must be one of {valid_conditions}"
            )
        
        if new_condition == self.current_condition:
            raise ConditionError(
                f"Cannot switch to the same condition '{new_condition}'. "
                f"Current condition is already '{new_condition}'."
            )
        
        previous_condition = self.current_condition
        timestamp = get_current_utc_timestamp()
        unix_timestamp = datetime.now(timezone.utc).timestamp()
        
        # Record the switch in timestamp recorder
        switch_record = record_condition_switch(
            participant_id=self.participant_id,
            session_id=self.session_id,
            from_condition=previous_condition,
            to_condition=new_condition,
            timestamp=timestamp
        )
        
        # Log the condition switch event
        log_event_data = {
            "previous_condition": previous_condition,
            "new_condition": new_condition,
            "timestamp": timestamp,
            "unix_timestamp": unix_timestamp,
            "switch_record_id": switch_record.get("record_id")
        }
        
        log_experiment_event(
            event_type="condition_switch",
            participant_id=self.participant_id,
            session_id=self.session_id,
            data=log_event_data
        )
        
        # Handle LLM assistant state
        llm_state_change = {}
        if new_condition == 'baseline':
            llm_state_change = self._disable_llm_assistant()
        elif new_condition == 'llm_assisted':
            llm_state_change = self._enable_llm_assistant()
        
        # Update internal state
        self.current_condition = new_condition
        self._switch_history.append({
            "from": previous_condition,
            "to": new_condition,
            "timestamp": timestamp,
            "llm_state": llm_state_change
        })
        
        logger.info(
            f"Condition switched from '{previous_condition}' to '{new_condition}' "
            f"for participant {self.participant_id}. LLM state: {llm_state_change}"
        )
        
        return new_condition, {
            "previous_condition": previous_condition,
            "new_condition": new_condition,
            "timestamp": timestamp,
            "unix_timestamp": unix_timestamp,
            "llm_assistant_enabled": (new_condition == 'llm_assisted'),
            "switch_details": switch_record,
            "llm_state_change": llm_state_change
        }

    def _disable_llm_assistant(self) -> Dict[str, Any]:
        """
        Disable the LLM assistant when switching to baseline condition.
        
        Returns:
            Dict: Status of the LLM assistant disablement.
        """
        try:
            # In a real implementation, this would interact with the LLM service
            # to disable generation capabilities. For now, we log the action.
            action_status = "disabled"
            
            # Log the specific action
            log_experiment_event(
                event_type="llm_assistant_disabled",
                participant_id=self.participant_id,
                session_id=self.session_id,
                data={
                    "reason": "condition_switch_to_baseline",
                    "timestamp": get_current_utc_timestamp()
                }
            )
            
            logger.info(
                f"LLM assistant disabled for participant {self.participant_id} "
                f"(baseline condition)"
            )
            
            return {
                "status": action_status,
                "message": "LLM assistant disabled",
                "timestamp": get_current_utc_timestamp()
            }
            
        except Exception as e:
            logger.error(
                f"Failed to disable LLM assistant for participant {self.participant_id}: {e}"
            )
            return {
                "status": "error",
                "message": str(e),
                "timestamp": get_current_utc_timestamp()
            }

    def _enable_llm_assistant(self) -> Dict[str, Any]:
        """
        Enable the LLM assistant when switching to LLM-assisted condition.
        
        Returns:
            Dict: Status of the LLM assistant enablement.
        """
        try:
            action_status = "enabled"
            
            log_experiment_event(
                event_type="llm_assistant_enabled",
                participant_id=self.participant_id,
                session_id=self.session_id,
                data={
                    "reason": "condition_switch_to_llm_assisted",
                    "timestamp": get_current_utc_timestamp()
                }
            )
            
            logger.info(
                f"LLM assistant enabled for participant {self.participant_id} "
                f"(LLM-assisted condition)"
            )
            
            return {
                "status": action_status,
                "message": "LLM assistant enabled",
                "timestamp": get_current_utc_timestamp()
            }
            
        except Exception as e:
            logger.error(
                f"Failed to enable LLM assistant for participant {self.participant_id}: {e}"
            )
            return {
                "status": "error",
                "message": str(e),
                "timestamp": get_current_utc_timestamp()
            }

    def get_current_condition(self) -> str:
        """
        Get the current active condition.
        
        Returns:
            str: The current condition ('llm_assisted' or 'baseline').
        """
        return self.current_condition

    def is_llm_assistant_enabled(self) -> bool:
        """
        Check if the LLM assistant is currently enabled.
        
        Returns:
            bool: True if in 'llm_assisted' condition, False otherwise.
        """
        return self.current_condition == 'llm_assisted'

    def get_switch_history(self) -> list:
        """
        Get the history of condition switches for this session.
        
        Returns:
            list: List of switch records.
        """
        return self._switch_history.copy()

    def validate_condition(self, condition: str) -> bool:
        """
        Validate if a condition string is valid.
        
        Args:
            condition: The condition string to validate.
            
        Returns:
            bool: True if valid, False otherwise.
        """
        return condition in ['llm_assisted', 'baseline']


def main():
    """
    Main function to demonstrate the ConditionManager functionality.
    This can be used for testing or as an entry point for scripts.
    """
    # Create a sample manager
    manager = ConditionManager(
        participant_id="test_participant_001",
        session_id="test_session_001"
    )
    
    try:
        # Initialize with LLM-assisted condition
        initial = manager.initialize_condition("llm_assisted")
        print(f"Initialized condition: {initial}")
        
        # Check if LLM is enabled
        print(f"LLM enabled: {manager.is_llm_assistant_enabled()}")
        
        # Switch to baseline
        new_cond, metadata = manager.switch_condition("baseline")
        print(f"Switched to: {new_cond}")
        print(f"LLM enabled after switch: {manager.is_llm_assistant_enabled()}")
        print(f"Switch metadata: {json.dumps(metadata, indent=2, default=str)}")
        
        # Switch back to LLM-assisted
        new_cond, metadata = manager.switch_condition("llm_assisted")
        print(f"Switched back to: {new_cond}")
        print(f"LLM enabled: {manager.is_llm_assistant_enabled()}")
        
        # Get history
        history = manager.get_switch_history()
        print(f"Switch history length: {len(history)}")
        
    except ConditionError as e:
        print(f"Condition error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
