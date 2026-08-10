"""
Scheduler Setup Module (T015a)

Configures the scheduler logic for the mesh network orchestrator.
This module initializes the Scheduler with configuration parameters,
node lists, and timeout settings as required by T015a.

Dependencies:
  - T013a (node_manager): For node discovery and management
  - T013b (completion_feedback): For task status feedback loop
  - T012 (remote_tools_manager): For tool verification
  - T014a (instrumentor_remote): For remote instrumentation capability
  - T014b (network_saturation_handler): For saturation handling
  - T014c (remote_wall_clock_timer): For wall-clock timing
  - T009 (timeout_guard): For pipeline timeout enforcement
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from orchestrator.config import Config, get_config, save_config
from orchestrator.models import PhysicalNode, TaskChunk, ExecutionRun
from orchestrator.node_manager import NodeManager, create_node_manager
from orchestrator.completion_feedback import CompletionFeedbackManager, create_feedback_manager
from orchestrator.remote_tools_manager import RemoteToolManager, create_tool_manager
from orchestrator.instrumentor_remote import RemoteInstrumentor, create_instrumentor
from orchestrator.remote_wall_clock_timer import RemoteWallClockTimer, create_remote_wall_clock_timer
from orchestrator.network_saturation_handler import NetworkSaturationHandler
from orchestrator.timeout_guard import enforce_pipeline_timeout, PipelineTimeoutError
from orchestrator.logger import get_logger
from orchestrator.scheduler import Scheduler, create_scheduler

# Configure logging
logger = get_logger(__name__)


class SchedulerSetupError(Exception):
    """Exception raised when scheduler setup fails."""
    pass


class SchedulerSetup:
    """
    Main class for configuring and initializing the scheduler.
    
    This class orchestrates the setup of all components required for
    the scheduler to function, including node management, tool verification,
    instrumentation, and timeout handling.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the scheduler setup with configuration.
        
        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.node_manager: Optional[NodeManager] = None
        self.feedback_manager: Optional[CompletionFeedbackManager] = None
        self.tool_manager: Optional[RemoteToolManager] = None
        self.instrumentor: Optional[RemoteInstrumentor] = None
        self.wall_clock_timer: Optional[RemoteWallClockTimer] = None
        self.saturation_handler: Optional[NetworkSaturationHandler] = None
        self.scheduler: Optional[Scheduler] = None
        self._initialized = False
    
    def load_configuration(self) -> Config:
        """
        Load configuration from file or create default.
        
        Returns:
            Config object with scheduler settings.
            
        Raises:
            SchedulerSetupError: If configuration cannot be loaded or created.
        """
        try:
            if self.config_path and os.path.exists(self.config_path):
                self.config = get_config(self.config_path)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                # Create default configuration if file doesn't exist
                self.config = Config(
                    chunk_size_mb=100,
                    min_chunk_size_mb=1,
                    timeout_seconds=3600,
                    node_list=[],
                    granularity="medium",
                    ci_timeout_enabled=True
                )
                if self.config_path:
                    save_config(self.config, self.config_path)
                    logger.info(f"Created default configuration at {self.config_path}")
                else:
                    logger.info("Using default configuration (no config path provided)")
            
            return self.config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise SchedulerSetupError(f"Configuration load failed: {e}")
    
    def initialize_node_manager(self, ip_list: List[str]) -> NodeManager:
        """
        Initialize the node manager for the given IP list.
        
        Args:
            ip_list: List of node IP addresses.
            
        Returns:
            Initialized NodeManager instance.
            
        Raises:
            SchedulerSetupError: If node manager initialization fails.
        """
        try:
            if not ip_list:
                if self.config and self.config.node_list:
                    ip_list = self.config.node_list
                else:
                    raise SchedulerSetupError("No node list provided and no default nodes in config")
            
            self.node_manager = create_node_manager()
            logger.info(f"Initialized NodeManager for {len(ip_list)} nodes")
            return self.node_manager
        except Exception as e:
            logger.error(f"Failed to initialize node manager: {e}")
            raise SchedulerSetupError(f"Node manager initialization failed: {e}")
    
    def initialize_feedback_manager(self) -> CompletionFeedbackManager:
        """
        Initialize the completion feedback manager.
        
        Returns:
            Initialized CompletionFeedbackManager instance.
            
        Raises:
            SchedulerSetupError: If feedback manager initialization fails.
        """
        try:
            self.feedback_manager = create_feedback_manager()
            logger.info("Initialized CompletionFeedbackManager")
            return self.feedback_manager
        except Exception as e:
            logger.error(f"Failed to initialize feedback manager: {e}")
            raise SchedulerSetupError(f"Feedback manager initialization failed: {e}")
    
    def initialize_tool_manager(self) -> RemoteToolManager:
        """
        Initialize the remote tool manager.
        
        Returns:
            Initialized RemoteToolManager instance.
            
        Raises:
            SchedulerSetupError: If tool manager initialization fails.
        """
        try:
            self.tool_manager = create_tool_manager()
            logger.info("Initialized RemoteToolManager")
            return self.tool_manager
        except Exception as e:
            logger.error(f"Failed to initialize tool manager: {e}")
            raise SchedulerSetupError(f"Tool manager initialization failed: {e}")
    
    def initialize_instrumentor(self) -> RemoteInstrumentor:
        """
        Initialize the remote instrumentor.
        
        Returns:
            Initialized RemoteInstrumentor instance.
            
        Raises:
            SchedulerSetupError: If instrumentor initialization fails.
        """
        try:
            self.instrumentor = create_instrumentor()
            logger.info("Initialized RemoteInstrumentor")
            return self.instrumentor
        except Exception as e:
            logger.error(f"Failed to initialize instrumentor: {e}")
            raise SchedulerSetupError(f"Instrumentor initialization failed: {e}")
    
    def initialize_wall_clock_timer(self) -> RemoteWallClockTimer:
        """
        Initialize the remote wall clock timer.
        
        Returns:
            Initialized RemoteWallClockTimer instance.
            
        Raises:
            SchedulerSetupError: If wall clock timer initialization fails.
        """
        try:
            self.wall_clock_timer = create_remote_wall_clock_timer()
            logger.info("Initialized RemoteWallClockTimer")
            return self.wall_clock_timer
        except Exception as e:
            logger.error(f"Failed to initialize wall clock timer: {e}")
            raise SchedulerSetupError(f"Wall clock timer initialization failed: {e}")
    
    def initialize_saturation_handler(self) -> NetworkSaturationHandler:
        """
        Initialize the network saturation handler.
        
        Returns:
            Initialized NetworkSaturationHandler instance.
            
        Raises:
            SchedulerSetupError: If saturation handler initialization fails.
        """
        try:
            self.saturation_handler = NetworkSaturationHandler()
            logger.info("Initialized NetworkSaturationHandler")
            return self.saturation_handler
        except Exception as e:
            logger.error(f"Failed to initialize saturation handler: {e}")
            raise SchedulerSetupError(f"Saturation handler initialization failed: {e}")
    
    def initialize_scheduler(self) -> Scheduler:
        """
        Initialize the main scheduler with all configured components.
        
        Returns:
            Initialized Scheduler instance.
            
        Raises:
            SchedulerSetupError: If scheduler initialization fails.
        """
        try:
            if not self.config:
                raise SchedulerSetupError("Configuration not loaded. Call load_configuration() first.")
            
            if not self.node_manager:
                raise SchedulerSetupError("Node manager not initialized. Call initialize_node_manager() first.")
            
            if not self.feedback_manager:
                raise SchedulerSetupError("Feedback manager not initialized. Call initialize_feedback_manager() first.")
            
            self.scheduler = create_scheduler(
                node_manager=self.node_manager,
                feedback_manager=self.feedback_manager,
                config=self.config
            )
            logger.info("Initialized Scheduler with all components")
            return self.scheduler
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise SchedulerSetupError(f"Scheduler initialization failed: {e}")
    
    def setup_complete(self) -> bool:
        """
        Check if all setup steps have been completed successfully.
        
        Returns:
            True if setup is complete, False otherwise.
        """
        return (
            self.config is not None and
            self.node_manager is not None and
            self.feedback_manager is not None and
            self.tool_manager is not None and
            self.instrumentor is not None and
            self.wall_clock_timer is not None and
            self.saturation_handler is not None and
            self.scheduler is not None
        )
    
    def run_full_setup(self, ip_list: Optional[List[str]] = None, config_path: Optional[str] = None) -> Scheduler:
        """
        Execute the complete setup sequence.
        
        Args:
            ip_list: Optional list of node IPs. If None, uses config or defaults.
            config_path: Optional path to config file. If None, uses default.
            
        Returns:
            Fully initialized Scheduler instance.
            
        Raises:
            SchedulerSetupError: If any setup step fails.
        """
        try:
            # Load configuration
            self.load_configuration()
            if config_path:
                self.config_path = config_path
            
            # Initialize all components
            if ip_list:
                self.initialize_node_manager(ip_list)
            else:
                # Use nodes from config if available
                if self.config and self.config.node_list:
                    self.initialize_node_manager(self.config.node_list)
                else:
                    raise SchedulerSetupError("No node list provided for initialization")
            
            self.initialize_feedback_manager()
            self.initialize_tool_manager()
            self.initialize_instrumentor()
            self.initialize_wall_clock_timer()
            self.initialize_saturation_handler()
            
            # Initialize the scheduler
            self.initialize_scheduler()
            
            self._initialized = True
            logger.info("Full scheduler setup completed successfully")
            return self.scheduler
            
        except Exception as e:
            logger.error(f"Full setup failed: {e}")
            raise SchedulerSetupError(f"Setup failed: {e}")


def main():
    """
    Main entry point for scheduler setup.
    
    This function demonstrates the setup process and can be used
    for testing or as a reference implementation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup the mesh network scheduler")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--nodes", type=str, nargs="+", help="List of node IPs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        setup = SchedulerSetup(config_path=args.config)
        scheduler = setup.run_full_setup(ip_list=args.nodes)
        
        logger.info("Scheduler setup successful!")
        logger.info(f"Chunk size: {scheduler.config.chunk_size_mb} MB")
        logger.info(f"Timeout: {scheduler.config.timeout_seconds} seconds")
        logger.info(f"Granularity: {scheduler.config.granularity}")
        
        return 0
        
    except SchedulerSetupError as e:
        logger.error(f"Setup failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
