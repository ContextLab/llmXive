import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .logging_config import setup_simulation_logger

class SimulationProgressLogger:
    """
    Logger for tracking simulation progress across dataset, epsilon, and noise type combinations.
    
    Logs structured events for:
    - Start of a specific (dataset, epsilon, noise_type) combination
    - Completion of that combination
    - Summary of total progress
    """
    
    def __init__(
        self,
        logger_name: str = "simulation",
        log_file: Optional[Path] = None,
        level: int = logging.INFO
    ):
        """
        Initialize the progress logger.
        
        Args:
            logger_name: Name for the logger instance
            log_file: Optional path to write logs to disk
            level: Logging level
        """
        self.logger = setup_simulation_logger(
            name=logger_name,
            log_file=log_file,
            level=level
        )
        self.total_conditions = 0
        self.completed_conditions = 0
        self.failed_conditions = 0
    
    def set_total_conditions(self, count: int):
        """
        Set the total number of conditions to be processed.
        
        Args:
            count: Total number of (dataset, epsilon, noise_type) combinations
        """
        self.total_conditions = count
        self.logger.info(f"Starting simulation with {self.total_conditions} total conditions.")
    
    def log_start(
        self,
        dataset: str,
        epsilon: float,
        noise_type: str,
        statistic: Optional[str] = None
    ):
        """
        Log the start of processing for a specific condition.
        
        Args:
            dataset: Name of the dataset (e.g., 'adult', 'iris')
            epsilon: Privacy budget value
            noise_type: Type of noise ('laplace' or 'gaussian')
            statistic: Optional statistic name (e.g., 'mean', 'regression_coef')
        """
        context = f"dataset={dataset}, epsilon={epsilon:.4f}, noise_type={noise_type}"
        if statistic:
            context += f", statistic={statistic}"
        
        self.logger.info(f"Starting: {context}")
    
    def log_completion(
        self,
        dataset: str,
        epsilon: float,
        noise_type: str,
        statistic: Optional[str] = None,
        coverage_rate: Optional[float] = None
    ):
        """
        Log the successful completion of a condition.
        
        Args:
            dataset: Name of the dataset
            epsilon: Privacy budget value
            noise_type: Type of noise
            statistic: Optional statistic name
            coverage_rate: Optional empirical coverage rate
        """
        self.completed_conditions += 1
        context = f"dataset={dataset}, epsilon={epsilon:.4f}, noise_type={noise_type}"
        if statistic:
            context += f", statistic={statistic}"
        
        progress_msg = f"[{self.completed_conditions}/{self.total_conditions}]"
        
        if coverage_rate is not None:
            self.logger.info(
                f"{progress_msg} Completed: {context} -> coverage={coverage_rate:.4f}"
            )
        else:
            self.logger.info(f"{progress_msg} Completed: {context}")
    
    def log_failure(
        self,
        dataset: str,
        epsilon: float,
        noise_type: str,
        statistic: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Log a failure for a specific condition.
        
        Args:
            dataset: Name of the dataset
            epsilon: Privacy budget value
            noise_type: Type of noise
            statistic: Optional statistic name
            error_message: Optional description of the failure
        """
        self.failed_conditions += 1
        context = f"dataset={dataset}, epsilon={epsilon:.4f}, noise_type={noise_type}"
        if statistic:
            context += f", statistic={statistic}"
        
        progress_msg = f"[{self.completed_conditions}/{self.total_conditions}]"
        error_msg = f"Failed: {context}"
        
        if error_message:
            error_msg += f" | Error: {error_message}"
        
        self.logger.error(f"{progress_msg} {error_msg}")
    
    def log_summary(self):
        """Log a final summary of the simulation run."""
        self.logger.info("=" * 60)
        self.logger.info("SIMULATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total conditions: {self.total_conditions}")
        self.logger.info(f"Completed successfully: {self.completed_conditions}")
        self.logger.info(f"Failed: {self.failed_conditions}")
        
        if self.total_conditions > 0:
            success_rate = (self.completed_conditions / self.total_conditions) * 100
            self.logger.info(f"Success rate: {success_rate:.2f}%")
        
        self.logger.info("=" * 60)
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress statistics.
        
        Returns:
            Dictionary with progress metrics
        """
        return {
            "total": self.total_conditions,
            "completed": self.completed_conditions,
            "failed": self.failed_conditions,
            "remaining": self.total_conditions - self.completed_conditions - self.failed_conditions,
            "percent_complete": (self.completed_conditions / self.total_conditions * 100) 
                                if self.total_conditions > 0 else 0.0
        }
