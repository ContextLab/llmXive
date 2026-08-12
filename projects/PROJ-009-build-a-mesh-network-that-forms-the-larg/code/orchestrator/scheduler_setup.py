"""
Scheduler Setup Module for Mesh Network Supercomputer.

This module configures the scheduler logic by loading chunk sizes,
node lists, and timeout settings from the project configuration.
It acts as the initialization layer before execution (T015b) begins.

Dependencies:
- T013a (node_manager): For node list structure compatibility.
- T013b (completion_feedback): For feedback manager initialization.
- T009 (timeout_guard): For timeout enforcement configuration.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from orchestrator.config import Config, get_config, save_config
from orchestrator.models import PhysicalNode, TaskChunk, ExecutionRun
from orchestrator.timeout_guard import enforce_pipeline_timeout, check_budget_remaining
from orchestrator.completion_feedback import create_feedback_manager, CompletionFeedbackManager
from orchestrator.node_manager import create_node_manager, NodeManager
from orchestrator.logger import get_logger

# Constants
DEFAULT_CHUNK_SIZE_MB = 10  # Default base chunk size in MB
MIN_CHUNK_SIZE_MB = 1       # Minimum allowed chunk size
DEFAULT_TIMEOUT_SECONDS = 3600  # Default hard timeout for a run

class SchedulerSetupError(Exception):
    """Raised when scheduler configuration fails."""
    pass

class SchedulerSetup:
    """
    Handles the configuration and initialization of the scheduler.
    
    This class loads settings, validates the environment, and prepares
    the necessary managers (Node, Feedback, Timeout) for the execution phase.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.config_path = config_path
        self.config: Config = None
        self.node_manager: Optional[NodeManager] = None
        self.feedback_manager: Optional[CompletionFeedbackManager] = None
        self.chunk_size_mb: int = DEFAULT_CHUNK_SIZE_MB
        self.timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
        self.node_list: List[Dict[str, Any]] = []
        self.is_initialized: bool = False

    def load_configuration(self) -> Config:
        """
        Loads the scheduler configuration from the project config.
        
        Raises:
            SchedulerSetupError: If configuration file is missing or invalid.
        """
        try:
            self.config = get_config(self.config_path)
            if not self.config:
                raise SchedulerSetupError("Failed to load configuration. Config object is None.")
            
            # Extract specific scheduler settings
            self.chunk_size_mb = self.config.get('scheduler', {}).get('chunk_size_mb', DEFAULT_CHUNK_SIZE_MB)
            self.timeout_seconds = self.config.get('scheduler', {}).get('timeout_seconds', DEFAULT_TIMEOUT_SECONDS)
            self.node_list = self.config.get('nodes', [])
            
            # Validate constraints
            if self.chunk_size_mb < MIN_CHUNK_SIZE_MB:
                self.logger.warning(f"Chunk size {self.chunk_size_mb}MB is below minimum. Setting to {MIN_CHUNK_SIZE_MB}MB.")
                self.chunk_size_mb = MIN_CHUNK_SIZE_MB

            self.logger.info(f"Configuration loaded: Chunk={self.chunk_size_mb}MB, Timeout={self.timeout_seconds}s, Nodes={len(self.node_list)}")
            return self.config

        except FileNotFoundError:
            raise SchedulerSetupError("Configuration file not found. Ensure config.yaml exists in the project root.")
        except Exception as e:
            raise SchedulerSetupError(f"Error loading configuration: {str(e)}")

    def initialize_managers(self) -> None:
        """
        Initializes the Node Manager and Feedback Manager based on loaded config.
        
        This prepares the system for discovery and task tracking.
        
        Raises:
            SchedulerSetupError: If manager initialization fails.
        """
        if not self.config:
            raise SchedulerSetupError("Configuration not loaded. Call load_configuration() first.")

        try:
            # Initialize Node Manager (T013a dependency)
            # The config provides the IP list, node_manager handles the SSH logic
            self.node_manager = create_node_manager()
            self.logger.info("Node Manager initialized.")

            # Initialize Feedback Manager (T013b dependency)
            self.feedback_manager = create_feedback_manager()
            self.logger.info("Feedback Manager initialized.")

            self.is_initialized = True
        except Exception as e:
            raise SchedulerSetupError(f"Failed to initialize managers: {str(e)}")

    def verify_timeout_enforcement(self) -> bool:
        """
        Verifies that the timeout guard is correctly configured.
        
        Returns:
            bool: True if timeout is valid, False otherwise.
        """
        try:
            # This ensures the timeout guard logic is ready (T009 dependency)
            # We don't run the timeout here, just verify the config is usable
            if self.timeout_seconds <= 0:
                self.logger.error("Invalid timeout configuration: must be > 0")
                return False
            
            self.logger.info(f"Timeout enforcement configured for {self.timeout_seconds} seconds.")
            return True
        except Exception as e:
            self.logger.error(f"Timeout verification failed: {str(e)}")
            return False

    def get_scheduler_state(self) -> Dict[str, Any]:
        """
        Returns the current scheduler state for debugging/logging.
        
        Returns:
            Dict containing current configuration and manager status.
        """
        return {
            "chunk_size_mb": self.chunk_size_mb,
            "timeout_seconds": self.timeout_seconds,
            "node_count": len(self.node_list),
            "is_initialized": self.is_initialized,
            "node_manager_active": self.node_manager is not None,
            "feedback_manager_active": self.feedback_manager is not None
        }

    def run_setup(self) -> Dict[str, Any]:
        """
        Executes the full setup sequence: Load Config -> Init Managers -> Verify Timeout.
        
        Returns:
            Dict: The scheduler state after successful setup.
        
        Raises:
            SchedulerSetupError: If any step in the setup sequence fails.
        """
        self.logger.info("Starting Scheduler Setup sequence...")
        
        # Step 1: Load Configuration
        self.load_configuration()
        
        # Step 2: Initialize Managers
        self.initialize_managers()
        
        # Step 3: Verify Timeout
        if not self.verify_timeout_enforcement():
            raise SchedulerSetupError("Timeout verification failed. Aborting setup.")
        
        self.logger.info("Scheduler Setup completed successfully.")
        return self.get_scheduler_state()


def main():
    """
    Entry point for testing the scheduler setup independently.
    Runs the setup sequence and prints the resulting state.
    """
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)
    
    # Attempt to run setup
    try:
        setup = SchedulerSetup()
        state = setup.run_setup()
        logger.info(f"Final Scheduler State: {state}")
        return 0
    except SchedulerSetupError as e:
        logger.critical(f"Setup failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    exit(main())