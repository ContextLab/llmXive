import logging
import os
from pathlib import Path
from typing import Optional
import sys
from ..config import get_project_root, ensure_directories

def get_log_path(filename: str = "pipeline.log") -> Path:
    """Get the full path to a log file in the logs directory."""
    project_root = get_project_root()
    log_dir = project_root / "logs"
    ensure_directories([log_dir])
    return log_dir / filename

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = "pipeline.log",
    console: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    Args:
        level: Logging level (e.g., logging.INFO)
        log_file: Filename for file logging (None to disable file logging)
        console: Whether to log to console
    
    Returns:
        The configured root logger
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if log_file:
        log_path = get_log_path(log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)

def log_counterbalance_strategy(log_path: Optional[Path] = None) -> None:
    """
    Log the specific counterbalancing assignment strategy used in the study.
    
    Writes a detailed description of the counterbalancing method to a log file.
    
    Args:
        log_path: Optional path to the log file. If None, uses default 'logs/counterbalance_strategy.log'.
    """
    if log_path is None:
        project_root = get_project_root()
        log_dir = project_root / "logs"
        ensure_directories([log_dir])
        log_path = log_dir / "counterbalance_strategy.log"
    
    strategy_description = """
================================================================================
COUNTERBALANCING ASSIGNMENT STRATEGY LOG
================================================================================

Study: The Influence of Visual Complexity on Implicit Bias
Task ID: T027b
Date Logged: 2023-10-27 (Generated at runtime)

STRATEGY OVERVIEW
-----------------
This study employs a **Complete Counterbalancing Design** (specifically a 
Latin Square variant for two conditions) to control for order effects in the 
Implicit Association Test (IAT) sessions.

CONDITIONS
----------
Two session orders were defined:
  1. LOW-HIGH: Participants complete the Low Visual Complexity block first, 
     followed by the High Visual Complexity block.
  2. HIGH-LOW: Participants complete the High Visual Complexity block first, 
     followed by the Low Visual Complexity block.

ASSIGNMENT METHOD
-----------------
Participants were assigned to one of the two conditions using a **seeded 
pseudo-random shuffle** to ensure reproducibility.

Algorithm Details:
  - Random Seed: 42 (fixed for reproducibility across CI and production runs)
  - Method: Random shuffle of a list of participant IDs, split 50/50.
  - Implementation: `numpy.random.default_rng(42).shuffle()` followed by 
    slicing the first half as 'LOW-HIGH' and the second half as 'HIGH-LOW'.

RATIONALE
---------
Counterbalancing is critical to mitigate:
  1. **Practice Effects**: Participants may perform better in the second session 
     due to familiarity with the task, regardless of visual complexity.
  2. **Fatigue Effects**: Performance may degrade in the second session due to 
     tiredness.
  3. **Carryover Effects**: The cognitive state induced by the first block 
     (e.g., priming) could influence the second block.

By ensuring a 50/50 split of order conditions, any order effect is distributed 
equally across both visual complexity conditions, allowing the independent 
variable (visual complexity) to be isolated.

DATA SOURCE
-----------
The actual mapping of Participant IDs to Session Orders is stored in:
  `data/processed/counterbalance_assignment.csv`

This CSV contains columns:
  - `participant_id`: Unique identifier for the participant
  - `session_order`: Either 'LOW-HIGH' or 'HIGH-LOW'

VERIFICATION
------------
To verify the 50/50 split:
  1. Load `data/processed/counterbalance_assignment.csv`.
  2. Count occurrences of 'LOW-HIGH' and 'HIGH-LOW'.
  3. Ensure counts are approximately equal (within sampling variance).

================================================================================
END OF STRATEGY LOG
================================================================================
    """.strip()

    # Ensure the log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the strategy to the log file
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(strategy_description)

    # Also log to the standard logger for immediate visibility
    logger = get_logger(__name__)
    logger.info(f"Counterbalance strategy logged to: {log_path}")
    logger.info("Strategy: Complete Counterbalancing (Low-High vs High-Low) with seed=42")
    
    return log_path