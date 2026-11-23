from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from orchestrator.config import Config, get_config, save_config
from orchestrator.scheduler_state import create_scheduler_state, SchedulerState
from orchestrator.completion_feedback import create_feedback_manager, CompletionFeedbackManager
from orchestrator.heartbeat_monitoring import create_heartbeat_monitor, HeartbeatMonitor
from orchestrator.node_manager import create_node_manager, NodeManager
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError
from orchestrator.logger import get_logger

class SchedulerSetupError(Exception):
    """Raised when scheduler configuration or initialization fails."""
    pass

class SchedulerSetup:
    """
    Configures the scheduler logic by loading settings, initializing
    the state machine, and setting up the necessary managers.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.config: Optional[Config] = None
        self.state: Optional[SchedulerState] = None
        self.feedback_manager: Optional[CompletionFeedbackManager] = None
        self.heartbeat_monitor: Optional[HeartbeatMonitor] = None
        self.node_manager: Optional[NodeManager] = None
        self.config_path = config_path or "config/sweep_config.yaml"

    def load_configuration(self) -> Config:
        """
        Loads the scheduler configuration from the YAML file.
        Specifically retrieves chunk size, node list, and timeout settings.
        """
        try:
            self.config = get_config(self.config_path)
            self.logger.info(f"Configuration loaded from {self.config_path}")
            
            # Validate critical keys exist
            required_keys = ['chunk_size', 'node_list', 'timeout_seconds']
            for key in required_keys:
                if not hasattr(self.config, key) or getattr(self.config, key) is None:
                    raise SchedulerSetupError(f"Missing required config key: {key}")
            
            self.logger.debug(f"Chunk size: {self.config.chunk_size}")
            self.logger.debug(f"Node list: {self.config.node_list}")
            self.logger.debug(f"Timeout: {self.config.timeout_seconds}s")
            
            return self.config
        except FileNotFoundError:
            raise SchedulerSetupError(f"Configuration file not found: {self.config_path}")
        except Exception as e:
            raise SchedulerSetupError(f"Failed to load configuration: {e}")

    def initialize_state_machine(self) -> SchedulerState:
        """
        Initializes the thread-safe SchedulerState object.
        This is the base for the state machine logic (T013d).
        """
        if self.config is None:
            raise SchedulerSetupError("Configuration must be loaded before initializing state.")
        
        self.state = create_scheduler_state(
            initial_timeout=self.config.timeout_seconds,
            node_count=len(self.config.node_list)
        )
        self.logger.info("Scheduler state machine initialized.")
        return self.state

    def initialize_managers(self) -> None:
        """
        Initializes the NodeManager, FeedbackManager, and HeartbeatMonitor.
        Dependencies: T013a (NodeManager), T013b (FeedbackManager), T013c (HeartbeatMonitor).
        """
        if self.config is None or self.state is None:
            raise SchedulerSetupError("Config and State must be initialized first.")

        # Initialize Node Manager (T013a)
        self.node_manager = create_node_manager(self.config.node_list)
        self.logger.info("Node manager initialized.")

        # Initialize Feedback Manager (T013b)
        # This manager will update the state object defined in T013d
        self.feedback_manager = create_feedback_manager(self.state)
        self.logger.info("Feedback manager initialized.")

        # Initialize Heartbeat Monitor (T013c)
        # This monitor will detect losses and trigger re-assignment logic
        self.heartbeat_monitor = create_heartbeat_monitor(
            state=self.state,
            node_manager=self.node_manager
        )
        self.logger.info("Heartbeat monitor initialized.")

    def verify_dependencies(self) -> None:
        """
        Verifies that all required dependencies (T013a, T013b, T013d, T009)
        are correctly integrated and available.
        """
        # Check T013a: NodeManager
        if self.node_manager is None:
            raise SchedulerSetupError("NodeManager (T013a) not initialized.")
        
        # Check T013d: SchedulerState
        if self.state is None:
            raise SchedulerSetupError("SchedulerState (T013d) not initialized.")
        
        # Check T013b: Feedback Manager
        if self.feedback_manager is None:
            raise SchedulerSetupError("CompletionFeedbackManager (T013b) not initialized.")
        
        # Check T009: Timeout Guard
        # We verify the function exists and is callable; actual enforcement happens at runtime
        if not callable(enforce_pipeline_timeout):
            raise SchedulerSetupError("enforce_pipeline_timeout (T009) is not callable.")
        
        self.logger.info("All dependencies verified successfully.")

    def run_setup(self) -> Dict[str, Any]:
        """
        Executes the full setup sequence.
        Returns a dictionary containing the initialized components.
        """
        try:
            self.load_configuration()
            self.initialize_state_machine()
            self.initialize_managers()
            self.verify_dependencies()
            
            return {
                "config": self.config,
                "state": self.state,
                "node_manager": self.node_manager,
                "feedback_manager": self.feedback_manager,
                "heartbeat_monitor": self.heartbeat_monitor,
                "status": "ready"
            }
        except Exception as e:
            self.logger.error(f"Scheduler setup failed: {e}")
            raise

    def save_runtime_config(self, output_path: str = "data/processed/scheduler_runtime_config.json") -> None:
        """
        Saves the effective runtime configuration to a JSON file.
        """
        if self.config is None:
            raise SchedulerSetupError("No configuration to save.")
        
        runtime_data = {
            "chunk_size": self.config.chunk_size,
            "node_list": self.config.node_list,
            "timeout_seconds": self.config.timeout_seconds,
            "min_chunk_size": getattr(self.config, 'min_chunk_size', 1),
            "base_chunk_size": getattr(self.config, 'base_chunk_size', 10)
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        save_config(runtime_data, output_path)
        self.logger.info(f"Runtime config saved to {output_path}")


def main():
    """
    Entry point for scheduler setup verification.
    """
    logger = get_logger(__name__)
    try:
        setup = SchedulerSetup()
        result = setup.run_setup()
        setup.save_runtime_config()
        logger.info("Scheduler setup completed successfully.")
        logger.info(f"State: {result['state'].current_state}")
        logger.info(f"Nodes: {len(result['node_manager'].node_list)}")
    except SchedulerSetupError as e:
        logger.error(f"Setup failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()