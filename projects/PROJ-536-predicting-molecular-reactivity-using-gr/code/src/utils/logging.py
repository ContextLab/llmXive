import logging
import os
from typing import Optional, Dict, Any

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name.
    """
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)  # You can adjust this as needed
    return log


def log_invalid_smiles(smiles: str, message: Optional[str] = None):
    """Logs invalid SMILES strings."""
    logger = get_logger(__name__)
    if message:
        logger.warning(f"Invalid SMILES encountered: {smiles}. Reason: {message}")
    else:
        logger.warning(f"Invalid SMILES encountered: {smiles}.")


def log_skipped_reaction(reaction_id: str, reason: str):
    """Logs skipped reactions with a given reason."""
    logger = get_logger(__name__)
    logger.info(f"Skipping reaction {reaction_id}: {reason}")

def log_message(message: str):
      """Logs a generic message"""
      logger = get_logger(__name__)
      logger.info(message)