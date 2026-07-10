"""
Utility functions for logging, exclusion handling, and basic plotting.
"""
import logging
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def plot_fd_distribution(fd_values: np.ndarray, subject_id: str, output_path: Path):
    """
    Plot the distribution of FD values for a subject.
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(fd_values, kde=True)
    plt.axvline(x=0.2, color='r', linestyle='--', label='Threshold (0.2mm)')
    plt.title(f'FD Distribution - Subject {subject_id}')
    plt.xlabel('Framewise Displacement (mm)')
    plt.ylabel('Count')
    plt.legend()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"FD plot saved to {output_path}")

def calculate_exclusion_stats(exclusions: list) -> dict:
    """
    Calculate statistics on exclusions.
    """
    if not exclusions:
        return {'total': 0, 'reasons': {}}
    
    reasons = {}
    for exc in exclusions:
        reason = exc.get('reason', 'unknown')
        reasons[reason] = reasons.get(reason, 0) + 1
        
    return {
        'total': len(exclusions),
        'reasons': reasons
    }
