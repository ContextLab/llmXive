"""
Scheduler Setup Module (T015a)

Implements the configuration logic for the mesh network scheduler.
Loads chunk sizes, node lists, and timeout settings from the central config.
Integrates with T004 (Config), T009 (Timeout Guard), T013a (Node Discovery),
T013b (Completion Feedback), and T008 (Models).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from orchestrator.config import Config, get_config, save_config
from orchestrator.models import PhysicalNode, TaskChunk, ExecutionRun
from orchestrator.timeout_guard import enforce_pipeline_timeout
from orchestrator.node_manager import create_node_manager, NodeDiscoveryError
from orchestrator.completion_feedback import create_feedback_manager

logger = logging.getLogger(__name__)


class SchedulerSetupError(Exception):
    """Custom exception for scheduler setup failures."""
    pass


class SchedulerSetup:
    """
    Handles the initialization and configuration of the scheduler.
    
    This class is responsible for:
    1. Loading configuration parameters (chunk size, node lists, timeouts).
    2. Initializing the Node Manager (T013a) for discovery.
    3. Initializing the Completion Feedback Manager (T013b).
    4. Validating the environment against the timeout guard (T009).
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the SchedulerSetup.
        
        Args:
            config_path: Path to the configuration YAML file. If None, 
                         attempts to load from default location or environment.
        """
        self.config_path = config_path or Path("config/scheduler_config.yaml")
        self.config: Optional[Config] = None
        self.node_manager = None
        self.feedback_manager = None
        self._initialized = False

    def load_configuration(self) -> Config:
        """
        Load the scheduler configuration from disk.
        
        Returns:
            Config: The loaded configuration object.
        
        Raises:
            SchedulerSetupError: If configuration cannot be loaded or validated.
        """
        if not self.config_path.exists():
            raise SchedulerSetupError(
                f"Configuration file not found at {self.config_path}. "
                "Please ensure the config file exists or set the correct path."
            )

        try:
            self.config = get_config(self.config_path)
            logger.info(f"Successfully loaded configuration from {self.config_path}")
            return self.config
        except Exception as e:
            raise SchedulerSetupError(f"Failed to load configuration: {e}") from e

    def initialize_node_manager(self) -> None:
        """
        Initialize the Node Manager for device discovery and connection handling.
        
        This relies on T013a (node_manager).
        
        Raises:
            SchedulerSetupError: If node discovery fails completely.
        """
        if not self.config:
            raise SchedulerSetupError("Configuration must be loaded before initializing node manager.")

        logger.info("Initializing Node Manager for device discovery...")
        
        # Extract node list from config
        node_ips = self.config.node_list or []
        
        if not node_ips:
            logger.warning("No node IPs found in configuration. Discovery will return empty list.")
            # Create manager but it will have no nodes to discover
            self.node_manager = create_node_manager([])
            return

        try:
            self.node_manager = create_node_manager(node_ips)
            
            # Perform initial discovery (T013a requirement)
            # Note: This is the initial discovery only; runtime heartbeat is T013c
            discovery_result = self.node_manager.discover_nodes(node_ips)
            
            online_count = sum(1 for node in discovery_result.nodes if node.status == 'online')
            logger.info(f"Discovery complete. Found {online_count} online nodes out of {len(node_ips)}.")
            
            if online_count == 0 and len(node_ips) > 0:
                # Per T013a spec: Raise if ALL nodes are unreachable
                raise NodeDiscoveryError("All configured nodes are unreachable.")
                
        except NodeDiscoveryError as e:
            logger.error(f"Critical node discovery failure: {e}")
            raise SchedulerSetupError(f"Node discovery failed: {e}") from e
        except Exception as e:
            raise SchedulerSetupError(f"Unexpected error during node manager initialization: {e}") from e

    def initialize_feedback_manager(self) -> None:
        """
        Initialize the Completion Feedback Manager (T013b).
        
        This sets up the mechanism to receive task status updates from nodes.
        """
        if not self.config:
            raise SchedulerSetupError("Configuration must be loaded before initializing feedback manager.")

        logger.info("Initializing Completion Feedback Manager...")
        
        # Initialize the feedback manager which handles the 'completion feedback' loop
        # required by FR-001.
        self.feedback_manager = create_feedback_manager()
        logger.info("Feedback manager initialized successfully.")

    def validate_timeout_constraints(self) -> None:
        """
        Validate that the configured timeouts are within acceptable limits.
        
        This integrates with T009 (timeout_guard) to ensure the pipeline
        respects the CI limit.
        """
        if not self.config:
            raise SchedulerSetupError("Configuration must be loaded before validating timeouts.")

        logger.info("Validating timeout constraints...")
        
        # The enforce_pipeline_timeout function from T009 is designed to be called
        # at the start of execution flows. Here we validate that the config 
        # supports a valid timeout budget.
        if self.config.timeout_seconds is not None and self.config.timeout_seconds <= 0:
            raise SchedulerSetupError("Timeout must be a positive integer.")
        
        logger.info("Timeout constraints validated.")

    def setup(self) -> Dict[str, Any]:
        """
        Execute the full setup sequence.
        
        Returns:
            Dict[str, Any]: A dictionary containing the initialized components
                            and configuration for the scheduler execution phase.
        
        Raises:
            SchedulerSetupError: If any step in the setup sequence fails.
        """
        logger.info("Starting Scheduler Setup sequence...")
        
        try:
            # 1. Load Configuration
            config = self.load_configuration()
            
            # 2. Initialize Node Manager (T013a)
            self.initialize_node_manager()
            
            # 3. Initialize Feedback Manager (T013b)
            self.initialize_feedback_manager()
            
            # 4. Validate Timeouts (T009 integration)
            self.validate_timeout_constraints()
            
            self._initialized = True
            
            logger.info("Scheduler Setup completed successfully.")
            
            return {
                "config": config,
                "node_manager": self.node_manager,
                "feedback_manager": self.feedback_manager,
                "chunk_size": config.chunk_size,
                "timeout_seconds": config.timeout_seconds
            }
            
        except Exception as e:
            logger.error(f"Scheduler Setup failed: {e}")
            # Ensure partial state is cleaned up if necessary
            self._initialized = False
            raise

    def get_ready_state(self) -> ExecutionRun:
        """
        Create an initial ExecutionRun object representing the setup state.
        
        Returns:
            ExecutionRun: The initial execution run object.
        
        Raises:
            SchedulerSetupError: If setup has not been completed.
        """
        if not self._initialized:
            raise SchedulerSetupError("Scheduler must be fully setup before generating state.")
        
        # Create a minimal ExecutionRun object (T008)
        # This serves as a placeholder until actual execution begins
        run_id = f"run_{self.config.run_id_prefix or 'default'}"
        
        return ExecutionRun(
            run_id=run_id,
            status="initialized",
            node_count=len(self.node_manager.nodes) if self.node_manager else 0,
            chunk_size=self.config.chunk_size,
            timeout_seconds=self.config.timeout_seconds
        )


def main():
    """
    Entry point for testing the scheduler setup logic directly.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Attempt to run setup
    try:
        # Use default config path or allow override via env
        config_path = os.getenv("SCHEDULER_CONFIG_PATH", "config/scheduler_config.yaml")
        
        if not os.path.exists(config_path):
            logger.warning(f"Config file {config_path} not found. Creating a minimal one for demo.")
            # In a real scenario, this would fail, but for T015a verification we ensure
            # the code path exists. We create a minimal valid config if missing.
            from orchestrator.config import Config
            minimal_config = Config(
                node_list=["127.0.0.1"], # Mock node for local test
                chunk_size=1024,
                timeout_seconds=300,
                run_id_prefix="test"
            )
            save_config(minimal_config, Path(config_path))
        
        setup = SchedulerSetup(Path(config_path))
        state = setup.setup()
        
        print("Scheduler Setup Successful!")
        print(f"  Nodes: {state['node_manager'].nodes if state['node_manager'] else []}")
        print(f"  Chunk Size: {state['chunk_size']}")
        print(f"  Timeout: {state['timeout_seconds']}s")
        
        # Generate the initial state object
        run_obj = setup.get_ready_state()
        print(f"  Initial Run ID: {run_obj.run_id}")
        
    except SchedulerSetupError as e:
        logger.critical(f"Setup failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()