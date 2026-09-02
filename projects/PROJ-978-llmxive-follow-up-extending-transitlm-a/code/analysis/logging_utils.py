import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def setup_logger(log_path: str, name: str = "evaluation") -> logging.Logger:
    """
    Set up a logger that writes JSON-formatted logs to a file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(os.path.join(log_path))
    file_handler.setLevel(logging.INFO)
    
    # Custom JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            }
            # Add extra fields if present
            if hasattr(record, 'route_id'):
                log_entry["route_id"] = record.route_id
            if hasattr(record, 'predicted_station'):
                log_entry["predicted_station"] = record.predicted_station
            if hasattr(record, 'validity_score'):
                log_entry["validity_score"] = record.validity_score
            if hasattr(record, 'risk_flag'):
                log_entry["risk_flag"] = record.risk_flag
            
            return json.dumps(log_entry)
    
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger

def log_prediction(logger: logging.Logger, route_id: str, predicted_station: str, 
                  validity_score: float, risk_flag: bool):
    """
    Log a single prediction with required fields.
    """
    logger.info(
        f"Prediction: route={route_id}, predicted={predicted_station}, "
        f"validity={validity_score:.4f}, risk={risk_flag}",
        extra={
            "route_id": route_id,
            "predicted_station": predicted_station,
            "validity_score": validity_score,
            "risk_flag": risk_flag
        }
    )

def log_validity_score(logger: logging.Logger, route_id: str, validity_score: float):
    """
    Log validity score for a route.
    """
    logger.info(
        f"Validity score: route={route_id}, score={validity_score:.4f}",
        extra={
            "route_id": route_id,
            "validity_score": validity_score
        }
    )

def log_risk_flag(logger: logging.Logger, route_id: str, risk_flag: bool):
    """
    Log risk flag for a route.
    """
    logger.info(
        f"Risk flag: route={route_id}, risk={risk_flag}",
        extra={
            "route_id": route_id,
            "risk_flag": risk_flag
        }
    )

def log_chi_squared_result(logger: logging.Logger, route_length: int, 
                           chi2_statistic: float, p_value: float):
    """
    Log chi-squared test result.
    """
    logger.info(
        f"Chi-squared test: length={route_length}, chi2={chi2_statistic:.4f}, "
        f"p_value={p_value:.4f}",
        extra={
            "route_length": route_length,
            "chi2_statistic": chi2_statistic,
            "p_value": p_value
        }
    )

def log_evaluation_summary(logger: logging.Logger, summary: Dict[str, Any]):
    """
    Log evaluation summary.
    """
    logger.info(
        f"Evaluation summary: inflection_point={summary.get('inflection_point')}, "
        f"total_routes={summary.get('total_routes_evaluated')}",
        extra={
            "summary": summary
        }
    )

def log_topological_metrics(logger: logging.Logger, route_id: str, 
                            betweenness_centrality: float):
    """
    Log topological metrics for a route.
    """
    logger.info(
        f"Topological metrics: route={route_id}, betweenness={betweenness_centrality:.4f}",
        extra={
            "route_id": route_id,
            "betweenness_centrality": betweenness_centrality
        }
    )

def init_evaluation_logging(logger: logging.Logger):
    """
    Initialize logging for the evaluation process.
    """
    logger.info("Evaluation logging initialized")
