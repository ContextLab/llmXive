"""
Retry Logic for Disconnected Networks (T018b)

Implements configurable retry logic for graph generation.
References T051 as the primary source of truth for retry behavior.
If a threshold of failed attempts is reached for a specific graph,
logs a warning, flags the run as [DISCONNECTED_NETWORK_FAILURE],
and proceeds to the next graph without halting the entire batch.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import config loader to read thresholds
from code.src.utils.config import load_config

# Import logging utilities
from code.src.utils.logging import log_run

logger = logging.getLogger(__name__)

# Global constant for the failure flag string
DISCONNECTED_NETWORK_FAILURE_FLAG = "[DISCONNECTED_NETWORK_FAILURE]"


def load_retry_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads retry configuration from config.yaml.
    Defaults are used if keys are missing.
    """
    try:
        config = load_config(config_path)
        # T051 defines the primary retry behavior; T018b adds the failure threshold
        retry_config = config.get("generator_params", {}).get("retry", {})
        return {
            "max_attempts": retry_config.get("max_attempts", 10),
            "timeout_seconds": retry_config.get("timeout_seconds", 300),
            "failure_threshold": retry_config.get("failure_threshold", 5)
        }
    except FileNotFoundError:
        logger.warning("config.yaml not found. Using default retry settings.")
        return {
            "max_attempts": 10,
            "timeout_seconds": 300,
            "failure_threshold": 5
        }
    except Exception as e:
        logger.error(f"Error loading retry config: {e}")
        return {
            "max_attempts": 10,
            "timeout_seconds": 300,
            "failure_threshold": 5
        }


def log_retry_failure(run_id: str, graph_id: str, attempts: int, config_path: Optional[str] = None):
    """
    Logs a retry failure event to data/run_log.json.
    Flags the specific graph ID as [DISCONNECTED_NETWORK_FAILURE].
    """
    log_entry = {
        "timestamp": log_run._get_timestamp(),
        "event_type": "retry_failure",
        "run_id": run_id,
        "graph_id": graph_id,
        "failed_attempts": attempts,
        "status": DISCONNECTED_NETWORK_FAILURE_FLAG,
        "message": f"Exceeded max attempts ({attempts}) for graph {graph_id}. Flagging as disconnected failure."
    }

    # Ensure data directory exists
    log_file = Path("data/run_log.json")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log or initialize
    existing_logs: List[Dict] = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_logs = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read existing log file: {e}. Initializing new log.")
            existing_logs = []

    existing_logs.append(log_entry)

    # Write back
    with open(log_file, 'w') as f:
        json.dump(existing_logs, f, indent=2)

    logger.warning(f"Logged retry failure for graph {graph_id}: {DISCONNECTED_NETWORK_FAILURE_FLAG}")


def should_proceed_to_next_graph(
    attempts: int,
    graph_id: str,
    run_id: str,
    config_path: Optional[str] = None
) -> bool:
    """
    Determines if the generation process should stop trying for a specific graph
    and proceed to the next one.

    Logic:
    1. Load config to get 'failure_threshold'.
    2. If attempts >= failure_threshold:
       - Log warning.
       - Flag run as [DISCONNECTED_NETWORK_FAILURE].
       - Return True (proceed to next graph).
    3. Otherwise, return False (continue retrying current graph).

    This references T051 for the retry loop mechanism but implements the
    specific threshold logic required by T018b.
    """
    config = load_retry_config(config_path)
    threshold = config["failure_threshold"]

    if attempts >= threshold:
        logger.warning(
            f"Graph {graph_id} failed to connect after {attempts} attempts. "
            f"Threshold ({threshold}) reached. Proceeding to next graph."
        )
        log_retry_failure(run_id, graph_id, attempts, config_path)
        return True

    return False


def get_retry_limit(config_path: Optional[str] = None) -> int:
    """
    Returns the maximum number of attempts allowed before a retry failure is triggered.
    """
    config = load_retry_config(config_path)
    return config["max_attempts"]
