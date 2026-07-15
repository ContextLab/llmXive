"""
Logging utilities for the LLM robustness evaluation pipeline.

This module provides centralized logging configuration and helper functions
for logging various events throughout the pipeline including perturbation
generation, model inference, and execution results.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import ensure_directories


# Global logger instances
_perturbation_logger = None
_execution_logger = None
_inference_logger = None
_budget_logger = None


def init_logging():
    """Initialize all loggers with appropriate handlers and formats."""
    ensure_directories()
    
    # Create log directory if it doesn't exist
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for perturbations
    perturbation_log_file = log_dir / "perturbation_raw.log"
    file_handler = logging.FileHandler(perturbation_log_file)
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console handler for general output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Create and configure perturbation logger
    global _perturbation_logger
    _perturbation_logger = logging.getLogger('perturbation')
    _perturbation_logger.setLevel(logging.DEBUG)
    _perturbation_logger.addHandler(file_handler)
    _perturbation_logger.addHandler(console_handler)
    
    # Create and configure execution logger
    global _execution_logger
    _execution_logger = logging.getLogger('execution')
    _execution_logger.setLevel(logging.INFO)
    _execution_logger.addHandler(console_handler)
    
    # Create and configure inference logger
    global _inference_logger
    _inference_logger = logging.getLogger('inference')
    _inference_logger.setLevel(logging.INFO)
    _inference_logger.addHandler(console_handler)
    
    # Create and configure budget logger
    global _budget_logger
    _budget_logger = logging.getLogger('budget')
    _budget_logger.setLevel(logging.INFO)
    _budget_logger.addHandler(console_handler)


def get_perturbation_logger():
    """Get the perturbation logger, initializing if necessary."""
    global _perturbation_logger
    if _perturbation_logger is None:
        init_logging()
    return _perturbation_logger


def get_execution_logger():
    """Get the execution logger, initializing if necessary."""
    global _execution_logger
    if _execution_logger is None:
        init_logging()
    return _execution_logger


def get_inference_logger():
    """Get the inference logger, initializing if necessary."""
    global _inference_logger
    if _inference_logger is None:
        init_logging()
    return _inference_logger


def get_budget_logger():
    """Get the budget logger, initializing if necessary."""
    global _budget_logger
    if _budget_logger is None:
        init_logging()
    return _budget_logger


def log_perturbation_candidate(perturbation_type: str, original_prompt: str, 
                               perturbed_prompt: str, score: float, 
                               is_valid: bool, reason: Optional[str] = None):
    """
    Log a perturbation candidate with its validation result.
    
    Args:
        perturbation_type: Type of perturbation (synonym, typo, rephrase)
        original_prompt: Original prompt text
        perturbed_prompt: Perturbed prompt text
        score: Semantic similarity score
        is_valid: Whether the perturbation passed validation
        reason: Reason for exclusion if not valid
    """
    logger = get_perturbation_logger()
    status = "INCLUDED" if is_valid else "EXCLUDED"
    logger.info(f"CANDIDATE: type={perturbation_type}, score={score:.4f}, status={status}")
    
    if not is_valid and reason:
        logger.info(f"  Reason: {reason}")
    
    logger.debug(f"  Original: {original_prompt[:200]}...")
    logger.debug(f"  Perturbed: {perturbed_prompt[:200]}...")


def log_excluded_perturbation(perturbation_type: str, original_prompt: str,
                             perturbed_prompt: str, raw_score: float, 
                             reason: str):
    """
    Log excluded perturbations with their raw scores and reasons.
    
    This function specifically logs perturbations that were excluded
    due to failing semantic similarity checks or other validation criteria.
    
    Args:
        perturbation_type: Type of perturbation (synonym, typo, rephrase)
        original_prompt: Original prompt text
        perturbed_prompt: Perturbed prompt text
        raw_score: Raw semantic similarity score before filtering
        reason: Reason for exclusion (e.g., 'score_below_threshold')
    """
    logger = get_perturbation_logger()
    logger.info(f"EXCLUDED: type={perturbation_type}, score={raw_score:.4f}, reason={reason}")
    logger.debug(f"Original: {original_prompt[:200]}...")
    logger.debug(f"Perturbed: {perturbed_prompt[:200]}...")


def log_execution_result(task_id: str, status: str, execution_time: float, 
                        error_type: Optional[str] = None):
    """
    Log the result of code execution.
    
    Args:
        task_id: Identifier for the task
        status: Execution status (pass, fail, timeout, error)
        execution_time: Time taken for execution in seconds
        error_type: Type of error if execution failed
    """
    logger = get_execution_logger()
    logger.info(f"EXECUTION: task={task_id}, status={status}, time={execution_time:.2f}s")
    
    if error_type:
        logger.info(f"  Error type: {error_type}")


def log_inference_event(model_name: str, prompt_type: str, generation_time: float,
                       tokens_generated: int, success: bool):
    """
    Log an inference event.
    
    Args:
        model_name: Name of the model used
        prompt_type: Type of prompt (original, perturbed)
        generation_time: Time taken for generation in seconds
        tokens_generated: Number of tokens generated
        success: Whether the generation was successful
    """
    logger = get_inference_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"INFERENCE: model={model_name}, type={prompt_type}, status={status}, "
               f"time={generation_time:.2f}s, tokens={tokens_generated}")


def log_budget_update(current_count: int, budget_limit: int, remaining: int):
    """
    Log budget update information.
    
    Args:
        current_count: Current number of samples processed
        budget_limit: Maximum budget limit
        remaining: Remaining budget
    """
    logger = get_budget_logger()
    logger.info(f"BUDGET: current={current_count}, limit={budget_limit}, remaining={remaining}")
    if remaining <= 10:
        logger.warning(f"  Low budget warning: only {remaining} samples remaining")