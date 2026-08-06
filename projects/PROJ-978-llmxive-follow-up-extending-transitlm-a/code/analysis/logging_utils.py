"""
Logging utilities for model predictions, validity scores, and risk flags.
Provides structured logging for the evaluation pipeline.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_env_config

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Set up a logger with optional file and console handlers.

    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_prediction(
    logger: logging.Logger,
    route_id: str,
    model_name: str,
    predicted_stations: List[str],
    ground_truth_stations: List[str],
    is_valid: bool,
    confidence: Optional[float] = None
) -> None:
    """
    Log a single model prediction with validity information.

    Args:
        logger: Logger instance
        route_id: Unique route identifier
        model_name: Name of the model used
        predicted_stations: List of predicted stations
        ground_truth_stations: List of ground truth stations
        is_valid: Whether the prediction is valid
        confidence: Optional confidence score
    """
    log_data = {
        "route_id": route_id,
        "model": model_name,
        "predicted": predicted_stations,
        "ground_truth": ground_truth_stations,
        "is_valid": is_valid,
        "confidence": confidence,
        "prediction_length": len(predicted_stations),
        "ground_truth_length": len(ground_truth_stations)
    }

    if is_valid:
        logger.info(f"PREDICTION_VALID: {json.dumps(log_data)}")
    else:
        logger.warning(f"PREDICTION_INVALID: {json.dumps(log_data)}")


def log_validity_score(
    logger: logging.Logger,
    model_name: str,
    category: str,
    route_count: int,
    valid_count: int,
    validity_rate: float
) -> None:
    """
    Log validity score summary for a model and route category.

    Args:
        logger: Logger instance
        model_name: Name of the model
        category: Route category (short, medium, long)
        route_count: Total number of routes
        valid_count: Number of valid routes
        validity_rate: Calculated validity rate
    """
    log_data = {
        "model": model_name,
        "category": category,
        "total_routes": route_count,
        "valid_routes": valid_count,
        "validity_rate": validity_rate,
        "invalid_routes": route_count - valid_count
    }

    logger.info(f"VALIDITY_SCORE: {json.dumps(log_data)}")


def log_risk_flag(
    logger: logging.Logger,
    route_id: str,
    model_name: str,
    risk_level: str,
    reason: str,
    metrics: Dict[str, Any]
) -> None:
    """
    Log a high-risk prediction flag with reasoning.

    Args:
        logger: Logger instance
        route_id: Unique route identifier
        model_name: Name of the model
        risk_level: Risk level (e.g., "HIGH", "MEDIUM", "LOW")
        reason: Reason for the risk flag
        metrics: Additional metrics contributing to the risk assessment
    """
    log_data = {
        "route_id": route_id,
        "model": model_name,
        "risk_level": risk_level,
        "reason": reason,
        "metrics": metrics
    }

    if risk_level == "HIGH":
        logger.error(f"HIGH_RISK_FLAG: {json.dumps(log_data)}")
    elif risk_level == "MEDIUM":
        logger.warning(f"MEDIUM_RISK_FLAG: {json.dumps(log_data)}")
    else:
        logger.info(f"LOW_RISK_FLAG: {json.dumps(log_data)}")


def log_chi_squared_result(
    logger: logging.Logger,
    route_length: int,
    chi_squared_stat: float,
    p_value: float,
    is_significant: bool,
    validity_gap: float
) -> None:
    """
    Log Chi-squared test results for connectivity analysis.

    Args:
        logger: Logger instance
        route_length: Length of the route being tested
        chi_squared_stat: Chi-squared statistic value
        p_value: P-value from the test
        is_significant: Whether the result is statistically significant
        validity_gap: Observed validity gap percentage
    """
    log_data = {
        "route_length": route_length,
        "chi_squared_statistic": chi_squared_stat,
        "p_value": p_value,
        "is_significant": is_significant,
        "validity_gap_percent": validity_gap,
        "threshold_met": is_significant and validity_gap >= 15.0
    }

    if log_data["threshold_met"]:
        logger.warning(f"SIGNIFICANT_DEGRADATION: {json.dumps(log_data)}")
    else:
        logger.info(f"CHI_SQUARED_RESULT: {json.dumps(log_data)}")


def log_evaluation_summary(
    logger: logging.Logger,
    model_name: str,
    total_routes: int,
    overall_validity: float,
    categories: Dict[str, Dict[str, Any]],
    inflection_point: Optional[int],
    high_risk_count: int
) -> None:
    """
    Log a comprehensive evaluation summary.

    Args:
        logger: Logger instance
        model_name: Name of the model
        total_routes: Total number of routes evaluated
        overall_validity: Overall validity rate
        categories: Per-category statistics
        inflection_point: Identified cognitive horizon (if any)
        high_risk_count: Number of high-risk predictions
    """
    log_data = {
        "model": model_name,
        "total_routes": total_routes,
        "overall_validity_rate": overall_validity,
        "categories": categories,
        "inflection_point_route_length": inflection_point,
        "high_risk_predictions": high_risk_count
    }

    logger.info(f"EVALUATION_SUMMARY: {json.dumps(log_data)}")


def log_topological_metrics(
    logger: logging.Logger,
    route_id: str,
    betweenness_centrality: float,
    path_complexity: float,
    category: str
) -> None:
    """
    Log topological metrics for a route.

    Args:
        logger: Logger instance
        route_id: Unique route identifier
        betweenness_centrality: Path-level betweenness centrality
        path_complexity: Computed path complexity metric
        category: Route category
    """
    log_data = {
        "route_id": route_id,
        "category": category,
        "betweenness_centrality": betweenness_centrality,
        "path_complexity": path_complexity
    }

    logger.debug(f"TOPOLOGICAL_METRICS: {json.dumps(log_data)}")


def init_evaluation_logging(
    log_dir: str = "data/analysis/logs",
    log_filename: Optional[str] = None
) -> logging.Logger:
    """
    Initialize the evaluation logger with default configuration.

    Args:
        log_dir: Directory for log files
        log_filename: Optional custom log filename

    Returns:
        Configured logger instance
    """
    config = get_env_config()
    log_level = getattr(logging, config.get("LOG_LEVEL", "INFO"))

    if log_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"evaluation_{timestamp}.log"

    log_path = Path(log_dir) / log_filename
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(
        name="llmXive.evaluation",
        log_file=str(log_path),
        level=log_level,
        console=True
    )

    logger.info(f"Evaluation logging initialized: {log_path}")
    return logger
